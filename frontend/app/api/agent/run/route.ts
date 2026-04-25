import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

export const dynamic = 'force-dynamic';

type AdkPart = {
  text?: string;
  functionCall?: {
    name?: string;
    args?: Record<string, unknown>;
  };
  functionResponse?: {
    name?: string;
    response?: Record<string, unknown>;
  };
};

type AdkEvent = {
  id?: string;
  author?: string;
  timestamp?: number;
  partial?: boolean;
  content?: {
    parts?: AdkPart[];
  };
  actions?: {
    stateDelta?: Record<string, unknown>;
    state_delta?: Record<string, unknown>;
  };
};

type AdkSession = {
  state?: Record<string, unknown>;
};

type TimelineEvent = {
  id: string;
  kind: 'user' | 'tool-call' | 'tool-result' | 'state' | 'stream' | 'agent';
  title: string;
  summary: string;
  timestamp: string;
  payload: string[];
};

type StreamEnvelope =
  | {
      type: 'meta';
      transport: 'proxy';
      notice: string;
    }
  | {
      type: 'timeline';
      event: TimelineEvent;
    }
  | {
      type: 'state';
      patch: Record<string, string>;
    }
  | {
      type: 'message';
      text: string;
      mode: 'append' | 'replace';
      final: boolean;
    }
  | {
      type: 'done';
      finalText: string;
      state: Record<string, string>;
    }
  | {
      type: 'error';
      message: string;
    };

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as {
      prompt?: string;
      sessionId?: string;
      sessionState?: Record<string, string>;
    };

    if (!body.prompt?.trim() || !body.sessionId?.trim()) {
      return NextResponse.json(
        { error: 'prompt and sessionId are required' },
        { status: 400 },
      );
    }

    const baseUrl = process.env.ADK_API_BASE_URL ?? 'http://127.0.0.1:8000';
    const appName = process.env.ADK_API_APP_NAME ?? 'app';
    const userId = process.env.ADK_API_USER_ID ?? 'demo-user';
    const sessionPath = `/apps/${encodeURIComponent(appName)}/users/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(body.sessionId)}`;

    await ensureSession({
      baseUrl,
      sessionPath,
      sessionState: body.sessionState ?? {},
    });

    await syncSessionState({
      baseUrl,
      sessionPath,
      sessionState: body.sessionState ?? {},
    });

    const runResponse = await fetch(buildUrl(baseUrl, '/run_sse'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({
        appName,
        userId,
        sessionId: body.sessionId,
        newMessage: {
          role: 'user',
          parts: [{ text: body.prompt }],
        },
        streaming: true,
      }),
    });

    if (!runResponse.ok) {
      throw new Error(await readError(runResponse, 'ADK /run_sse failed'));
    }

    if (!runResponse.body) {
      throw new Error('ADK /run_sse did not return a response body');
    }

    const stream = createProxyStream({
      upstream: runResponse.body,
      baseUrl,
      sessionPath,
      prompt: body.prompt,
      initialState: body.sessionState ?? {},
    });

    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        Connection: 'keep-alive',
      },
    });
  } catch (error) {
    return NextResponse.json(
      {
        error:
          error instanceof Error
            ? error.message
            : 'Unable to reach ADK API server',
      },
      { status: 502 },
    );
  }
}

async function ensureSession({
  baseUrl,
  sessionPath,
  sessionState,
}: {
  baseUrl: string;
  sessionPath: string;
  sessionState: Record<string, string>;
}) {
  const response = await fetch(buildUrl(baseUrl, sessionPath), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(sessionState),
  });

  if (response.ok || response.status === 409) {
    return;
  }

  throw new Error(await readError(response, 'Unable to ensure ADK session'));
}

async function syncSessionState({
  baseUrl,
  sessionPath,
  sessionState,
}: {
  baseUrl: string;
  sessionPath: string;
  sessionState: Record<string, string>;
}) {
  if (Object.keys(sessionState).length === 0) {
    return;
  }

  const response = await fetch(buildUrl(baseUrl, sessionPath), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      stateDelta: sessionState,
    }),
  });

  if (!response.ok) {
    throw new Error(await readError(response, 'Unable to sync ADK session'));
  }
}

function createProxyStream({
  upstream,
  baseUrl,
  sessionPath,
  prompt,
  initialState,
}: {
  upstream: ReadableStream<Uint8Array>;
  baseUrl: string;
  sessionPath: string;
  prompt: string;
  initialState: Record<string, string>;
}) {
  const encoder = new TextEncoder();

  return new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = upstream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let sequence = 0;
      let currentText = '';
      let mergedState = { ...initialState };

      const push = (payload: StreamEnvelope) => {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(payload)}\n\n`),
        );
      };

      push({
        type: 'meta',
        transport: 'proxy',
        notice: '目前由 Next.js API route 代理到 ADK API server（SSE）。',
      });

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            buffer += decoder.decode();
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const chunks = buffer.split(/\r?\n\r?\n/);
          buffer = chunks.pop() ?? '';

          for (const chunk of chunks) {
            const event = parseSseChunk(chunk);

            if (!event || isEchoedUserInput(event, prompt)) {
              continue;
            }

            sequence += 1;

            for (const envelope of mapEventToEnvelopes(event, sequence)) {
              if (envelope.type === 'state') {
                mergedState = {
                  ...mergedState,
                  ...envelope.patch,
                };
              }

              if (envelope.type === 'message') {
                currentText =
                  envelope.mode === 'append'
                    ? currentText + envelope.text
                    : envelope.text;
              }

              push(envelope);
            }
          }
        }

        if (buffer.trim()) {
          const finalEvent = parseSseChunk(buffer);

          if (finalEvent && !isEchoedUserInput(finalEvent, prompt)) {
            sequence += 1;

            for (const envelope of mapEventToEnvelopes(finalEvent, sequence)) {
              if (envelope.type === 'state') {
                mergedState = {
                  ...mergedState,
                  ...envelope.patch,
                };
              }

              if (envelope.type === 'message') {
                currentText =
                  envelope.mode === 'append'
                    ? currentText + envelope.text
                    : envelope.text;
              }

              push(envelope);
            }
          }
        }

        const finalState = await loadSessionState({
          baseUrl,
          sessionPath,
          fallbackState: mergedState,
        });

        push({
          type: 'done',
          finalText:
            currentText || 'ADK runtime 已完成執行，請查看右側 event history。',
          state: finalState,
        });
      } catch (error) {
        push({
          type: 'error',
          message:
            error instanceof Error ? error.message : 'SSE proxy stream failed',
        });
      } finally {
        reader.releaseLock();
        controller.close();
      }
    },
  });
}

function stringifyState(state: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(state).map(([key, value]) => [key, safeStringify(value)]),
  );
}

function safeStringify(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }

  if (value === null || value === undefined) {
    return String(value);
  }

  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function formatEventTimestamp(timestamp?: number) {
  const date =
    typeof timestamp === 'number' ? new Date(timestamp * 1000) : new Date();

  return new Intl.DateTimeFormat('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
}

function buildUrl(baseUrl: string, path: string) {
  return new URL(path, `${baseUrl.replace(/\/$/, '')}/`).toString();
}

async function readError(response: Response, fallback: string) {
  const text = await response.text();
  return text || fallback;
}

async function loadSessionState({
  baseUrl,
  sessionPath,
  fallbackState,
}: {
  baseUrl: string;
  sessionPath: string;
  fallbackState: Record<string, string>;
}) {
  const response = await fetch(buildUrl(baseUrl, sessionPath), {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    return fallbackState;
  }

  const session = (await response.json()) as AdkSession;
  return stringifyState(session.state ?? {});
}

function parseSseChunk(chunk: string) {
  const dataLines = chunk
    .split(/\r?\n/)
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trimStart())
    .filter(Boolean);

  if (dataLines.length === 0) {
    return null;
  }

  const payload = dataLines.join('\n');

  try {
    return JSON.parse(payload) as AdkEvent;
  } catch {
    return null;
  }
}

function isEchoedUserInput(event: AdkEvent, prompt: string) {
  const parts = event.content?.parts ?? [];

  if (event.author !== 'user') {
    return false;
  }

  if (parts.some((part) => part.functionResponse)) {
    return false;
  }

  return parts.some((part) => part.text?.trim() === prompt.trim());
}

function mapEventToEnvelopes(
  event: AdkEvent,
  sequence: number,
): StreamEnvelope[] {
  const eventId = event.id ?? `evt-proxy-${sequence}`;
  const timestamp = formatEventTimestamp(event.timestamp);
  const envelopes: StreamEnvelope[] = [];
  const stateDelta = event.actions?.stateDelta ?? event.actions?.state_delta;
  const parts = event.content?.parts ?? [];

  parts.forEach((part, partIndex) => {
    const suffix = `${eventId}-${partIndex}`;

    if (part.functionCall?.name) {
      envelopes.push({
        type: 'timeline',
        event: {
          id: `${suffix}-call`,
          kind: 'tool-call',
          title: part.functionCall.name,
          summary: `ADK 請求工具 ${part.functionCall.name}`,
          timestamp,
          payload: [
            `args: ${safeStringify(part.functionCall.args ?? {})}`,
            `author: ${event.author ?? 'agent'}`,
          ],
        },
      });
    }

    if (part.functionResponse?.name) {
      envelopes.push({
        type: 'timeline',
        event: {
          id: `${suffix}-result`,
          kind: 'tool-result',
          title: `${part.functionResponse.name} result`,
          summary: `工具 ${part.functionResponse.name} 已回傳結果`,
          timestamp,
          payload: [
            `response: ${safeStringify(part.functionResponse.response ?? {})}`,
          ],
        },
      });
    }

    const text = part.text?.trim();

    if (text && event.author !== 'user') {
      envelopes.push({
        type: 'timeline',
        event: {
          id: `${suffix}-${event.partial ? 'stream' : 'agent'}`,
          kind: event.partial ? 'stream' : 'agent',
          title: event.partial ? 'partial_response' : 'agent_response',
          summary: text,
          timestamp,
          payload: [
            text,
            `author: ${event.author ?? 'agent'}`,
            `partial: ${event.partial ? 'true' : 'false'}`,
          ],
        },
      });
      envelopes.push({
        type: 'message',
        text,
        mode: event.partial ? 'append' : 'replace',
        final: !event.partial,
      });
    }
  });

  if (stateDelta && Object.keys(stateDelta).length > 0) {
    const patch = stringifyState(stateDelta);

    envelopes.push({
      type: 'timeline',
      event: {
        id: `${eventId}-state`,
        kind: 'state',
        title: 'state_delta',
        summary: 'ADK session state 已更新',
        timestamp,
        payload: Object.entries(patch).map(
          ([key, value]) => `${key}: ${value}`,
        ),
      },
    });
    envelopes.push({
      type: 'state',
      patch,
    });
  }

  return envelopes;
}

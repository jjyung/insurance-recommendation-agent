import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

type AdkSessionEntry = {
  id?: string;
  name?: string;
  state?: Record<string, unknown>;
  createTime?: number;
  updateTime?: number;
};

const getBaseUrl = () =>
  process.env.ADK_API_BASE_URL ?? 'http://127.0.0.1:8000';
const getAppName = () => process.env.ADK_API_APP_NAME ?? 'app';
const getUserId = () => process.env.ADK_API_USER_ID ?? 'demo-user';

function buildUrl(base: string, path: string) {
  return new URL(path, `${base.replace(/\/$/, '')}/`).toString();
}

function safeStringify(value: unknown): string {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return String(value);
  try {
    return JSON.stringify(value);
  } catch {
    return String(value);
  }
}

function formatUpdatedAt(updateTime?: number): string {
  if (!updateTime) return '已儲存';
  const diff = Date.now() - updateTime * 1000;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return '剛剛';
  if (minutes < 60) return `${minutes} 分鐘前`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} 小時前`;
  return `${Math.floor(hours / 24)} 天前`;
}

export async function GET() {
  try {
    const baseUrl = getBaseUrl();
    const appName = getAppName();
    const userId = getUserId();
    const listPath = `/apps/${encodeURIComponent(appName)}/users/${encodeURIComponent(userId)}/sessions`;

    const response = await fetch(buildUrl(baseUrl, listPath), {
      method: 'GET',
      headers: { Accept: 'application/json' },
      cache: 'no-store',
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'ADK unavailable' }, { status: 502 });
    }

    const data = (await response.json()) as
      | AdkSessionEntry[]
      | { sessions?: AdkSessionEntry[] };
    const rawSessions: AdkSessionEntry[] = Array.isArray(data)
      ? data
      : ((data as { sessions?: AdkSessionEntry[] }).sessions ?? []);

    const sessions = rawSessions.map((s) => {
      const id = s.id ?? s.name ?? `session-${Date.now()}`;
      const rawState = s.state ?? {};
      const uiTitle =
        typeof rawState._ui_title === 'string' ? rawState._ui_title : null;
      const uiSubtitle =
        typeof rawState._ui_subtitle === 'string'
          ? rawState._ui_subtitle
          : null;
      const state = Object.fromEntries(
        Object.entries(rawState)
          .filter(([k]) => !k.startsWith('_ui_'))
          .map(([k, v]) => [k, safeStringify(v)]),
      );

      return {
        id,
        title: uiTitle ?? `對話 ${id.slice(-6)}`,
        subtitle: uiSubtitle ?? '繼續上次的對話',
        status: 'idle' as const,
        updatedAt: formatUpdatedAt(s.updateTime),
        messages: [] as never[],
        events: [] as never[],
        state,
        // ADK updateTime 為主；若缺失，從 sessionId 尾端解析建立時間戳作為 fallback
        _updateTime: s.updateTime
          ? s.updateTime
          : (() => {
              const ts = Number(id.replace(/^.*-(\d+)$/, '$1'));
              return Number.isFinite(ts) && ts > 1e9
                ? Math.floor(ts / 1000)
                : 0;
            })(),
      };
    });

    sessions.sort((a, b) => b._updateTime - a._updateTime);

    return NextResponse.json({
      sessions: sessions.map(({ _updateTime: _, ...rest }) => rest),
    });
  } catch {
    return NextResponse.json({ error: 'ADK unavailable' }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as {
      sessionId: string;
      state?: Record<string, string>;
    };

    if (!body.sessionId?.trim()) {
      return NextResponse.json(
        { error: 'sessionId is required' },
        { status: 400 },
      );
    }

    const baseUrl = getBaseUrl();
    const appName = getAppName();
    const userId = getUserId();
    const sessionPath = `/apps/${encodeURIComponent(appName)}/users/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(body.sessionId)}`;

    const response = await fetch(buildUrl(baseUrl, sessionPath), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body.state ?? {}),
    });

    if (response.ok || response.status === 409) {
      return NextResponse.json({ ok: true });
    }

    return NextResponse.json(
      { error: 'Failed to create session' },
      { status: 502 },
    );
  } catch {
    return NextResponse.json({ error: 'ADK unavailable' }, { status: 502 });
  }
}

import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const getBaseUrl = () =>
  process.env.ADK_API_BASE_URL ?? 'http://127.0.0.1:8000';
const getAppName = () => process.env.ADK_API_APP_NAME ?? 'app';
const getUserId = () => process.env.ADK_API_USER_ID ?? 'demo-user';

function buildUrl(base: string, path: string) {
  return new URL(path, `${base.replace(/\/$/, '')}/`).toString();
}

export async function DELETE(
  _: NextRequest,
  { params }: { params: { sessionId: string } },
) {
  try {
    const { sessionId } = params;

    if (!sessionId?.trim()) {
      return NextResponse.json(
        { error: 'sessionId is required' },
        { status: 400 },
      );
    }

    const baseUrl = getBaseUrl();
    const appName = getAppName();
    const userId = getUserId();
    const sessionPath = `/apps/${encodeURIComponent(appName)}/users/${encodeURIComponent(userId)}/sessions/${encodeURIComponent(sessionId)}`;

    const response = await fetch(buildUrl(baseUrl, sessionPath), {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    });

    if (response.ok || response.status === 404) {
      return NextResponse.json({ ok: true });
    }

    return NextResponse.json(
      { error: 'Failed to delete session' },
      { status: 502 },
    );
  } catch {
    return NextResponse.json({ error: 'ADK unavailable' }, { status: 502 });
  }
}

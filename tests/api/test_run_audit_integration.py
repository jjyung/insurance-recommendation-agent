import json
import sqlite3

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_run_endpoint_writes_redacted_audit_events(
    app_with_fake_runner, tmp_path
):
    client = AsyncClient(app=app_with_fake_runner, base_url="http://test")

    response = await client.post(
        "/api/agent/run",
        headers={
            "x-request-id": "req-test-1",
            "x-trace-id": "trace-test-1",
        },
        json={
            "prompt": "我 35 歲，預算 30000，email chris@example.com，想要醫療保障",
            "sessionId": "session-test-1",
            "userId": "user-test-1",
            "sessionState": {},
        },
    )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    audit_db_path = app_with_fake_runner.state.container.config.audit_db_path
    conn = sqlite3.connect(audit_db_path)

    rows = conn.execute(
        """
        SELECT event_type, input_redacted, output_redacted, pii_findings
        FROM audit_events
        WHERE trace_id = ?
        ORDER BY sequence
        """,
        ("trace-test-1",),
    ).fetchall()

    assert rows
    serialized = json.dumps(rows, ensure_ascii=False)
    assert "chris@example.com" not in serialized
    assert "[REDACTED_EMAIL]" in serialized
    assert any(row[0] == "user.prompt.received" for row in rows)

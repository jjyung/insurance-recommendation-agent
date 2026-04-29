import json
import sqlite3

import pytest

from app.services.audit_log_service import AuditContext, AuditLogService


@pytest.mark.asyncio
async def test_audit_log_redacts_pii_before_insert(tmp_path):
    db_path = tmp_path / "audit.db"

    service = AuditLogService(
        db_path=str(db_path),
        hash_salt="test-salt",
        retention_days=365,
        enabled=True,
    )
    await service.initialize()

    context = AuditContext(
        trace_id="trace-1",
        request_id="req-1",
        session_id="raw-session-id",
        user_id="raw-user-id",
    )

    await service.record(
        context=context,
        event_type="user.prompt.received",
        actor="user",
        sequence=1,
        input_payload={"prompt": "email chris@example.com phone 0912-345-678"},
    )

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT session_id_hash, user_id_hash, input_redacted, pii_findings FROM audit_events"
    ).fetchone()

    session_id_hash, user_id_hash, input_redacted, pii_findings = row

    assert session_id_hash != "raw-session-id"
    assert user_id_hash != "raw-user-id"
    assert "chris@example.com" not in input_redacted
    assert "0912-345-678" not in input_redacted
    assert "[REDACTED_EMAIL]" in input_redacted
    assert "[REDACTED_PHONE]" in input_redacted

    findings = json.loads(pii_findings)
    assert any(item["kind"] == "email" for item in findings)
    assert any(item["kind"] == "phone" for item in findings)


@pytest.mark.asyncio
async def test_audit_log_writes_event_hash_chain(tmp_path):
    db_path = tmp_path / "audit.db"

    service = AuditLogService(
        db_path=str(db_path),
        hash_salt="test-salt",
        retention_days=365,
        enabled=True,
    )
    await service.initialize()

    context = AuditContext(
        trace_id="trace-1",
        request_id="req-1",
        session_id="session-1",
        user_id="user-1",
    )

    await service.record(
        context=context,
        event_type="user.prompt.received",
        actor="user",
        sequence=1,
        input_payload={"prompt": "hello"},
    )
    await service.record(
        context=context,
        event_type="response.completed",
        actor="agent",
        sequence=2,
        output_payload={"text": "done"},
    )

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT prev_hash, event_hash FROM audit_events ORDER BY sequence"
    ).fetchall()

    assert len(rows) == 2
    assert rows[0][1]
    assert rows[1][0] == rows[0][1]
    assert rows[1][1]

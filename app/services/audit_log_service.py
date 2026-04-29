from __future__ import annotations

import aiosqlite
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from app.security.pii import PiiFinding, redact_jsonable, stable_hash


@dataclass(frozen=True)
class AuditContext:
    trace_id: str
    request_id: str
    session_id: str
    user_id: str


class AuditLogService:
    def __init__(
        self,
        *,
        db_path: str,
        hash_salt: str,
        retention_days: int,
        enabled: bool = True,
    ) -> None:
        self._db_path = db_path
        self._hash_salt = hash_salt
        self._retention_days = retention_days
        self._enabled = enabled
        self._last_hash: str | None = None

    async def initialize(self) -> None:
        if not self._enabled:
            return

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
              id TEXT PRIMARY KEY,
              trace_id TEXT NOT NULL,
              request_id TEXT NOT NULL,
              session_id_hash TEXT NOT NULL,
              user_id_hash TEXT NOT NULL,
              event_type TEXT NOT NULL,
              actor TEXT NOT NULL,
              tool_name TEXT,
              sequence INTEGER NOT NULL,
              input_redacted TEXT,
              output_redacted TEXT,
              pii_findings TEXT,
              policy_decision TEXT NOT NULL,
              event_timestamp TEXT NOT NULL,
              created_at TEXT NOT NULL,
              retention_until TEXT,
              prev_hash TEXT,
              event_hash TEXT NOT NULL
            )
            """)
            await db.commit()

    async def record(
        self,
        *,
        context: AuditContext,
        event_type: str,
        actor: str,
        sequence: int,
        tool_name: str | None = None,
        input_payload: Any = None,
        output_payload: Any = None,
        policy_decision: str = "allow_redacted",
    ) -> None:
        if not self._enabled:
            return

        now = datetime.now(UTC)
        retention_until = now + timedelta(days=self._retention_days)

        input_redacted, input_findings = redact_jsonable(input_payload)
        output_redacted, output_findings = redact_jsonable(output_payload)
        pii_findings = [
            finding.__dict__ for finding in [*input_findings, *output_findings]
        ]

        session_id_hash = stable_hash(context.session_id, salt=self._hash_salt)
        user_id_hash = stable_hash(context.user_id, salt=self._hash_salt)

        event_id = str(uuid.uuid4())
        prev_hash = self._last_hash

        hash_material = json.dumps(
            {
                "id": event_id,
                "trace_id": context.trace_id,
                "request_id": context.request_id,
                "session_id_hash": session_id_hash,
                "user_id_hash": user_id_hash,
                "event_type": event_type,
                "actor": actor,
                "tool_name": tool_name,
                "sequence": sequence,
                "input_redacted": input_redacted,
                "output_redacted": output_redacted,
                "pii_findings": pii_findings,
                "policy_decision": policy_decision,
                "prev_hash": prev_hash,
                "created_at": now.isoformat(),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        event_hash = hashlib.sha256(hash_material.encode("utf-8")).hexdigest()
        self._last_hash = event_hash

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                INSERT INTO audit_events (
                  id, trace_id, request_id, session_id_hash, user_id_hash,
                  event_type, actor, tool_name, sequence,
                  input_redacted, output_redacted, pii_findings,
                  policy_decision, event_timestamp, created_at,
                  retention_until, prev_hash, event_hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    context.trace_id,
                    context.request_id,
                    session_id_hash,
                    user_id_hash,
                    event_type,
                    actor,
                    tool_name,
                    sequence,
                    input_redacted,
                    output_redacted,
                    json.dumps(pii_findings, ensure_ascii=False),
                    policy_decision,
                    now.isoformat(),
                    now.isoformat(),
                    retention_until.isoformat(),
                    prev_hash,
                    event_hash,
                ),
            )
            await db.commit()

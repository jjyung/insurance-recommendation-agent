"""Agent 執行服務模組。

負責與 Google ADK Runner 互動，處理 AI Agent 的執行流程、串流回應、
狀態更新、事件轉換與 audit log。
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from google.adk.events.event import Event
from google.adk.runners import Runner
from google.genai import types as genai_types

from app.config import AppRuntimeConfig
from app.services.audit_log_service import AuditContext, AuditLogService
from app.services.session_service import SessionService, safe_stringify


INTERNAL_SESSION_TOOLS = {
    "get_user_profile_snapshot",
    "save_user_profile",
    "save_last_recommendation",
    "clear_last_recommendation",
}

QUERY_TOOLS = {
    "search_medical_products",
    "search_accident_products",
    "search_family_protection_products",
    "search_income_protection_products",
    "get_product_detail",
    "get_product_details",
    "get_product_by_name",
    "search_products_by_name",
    "get_recommendation_rules",
}


def classify_tool_name(tool_name: str) -> str:
    """分類工具用途。

    state 類工具是內部 session/state 管理工具，預設不顯示在使用者 timeline。
    query 類工具是業務查詢工具，應顯示在使用者 timeline。
    """

    if tool_name in INTERNAL_SESSION_TOOLS:
        return "state"
    if tool_name in QUERY_TOOLS:
        return "query"
    return "tool"


def is_internal_session_tool(tool_name: str) -> bool:
    return classify_tool_name(tool_name) == "state"


def format_event_timestamp(timestamp: float | None) -> str:
    value = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    return value.strftime("%H:%M")


def stringify_state_patch(state_delta: dict[str, object]) -> dict[str, str]:
    return {key: safe_stringify(value) for key, value in state_delta.items()}


def is_echoed_user_input(event: Event, prompt: str) -> bool:
    """判斷 ADK 事件是否只是使用者輸入 echo。"""

    if event.author != "user" or not event.content or not event.content.parts:
        return False

    if any(part.function_response for part in event.content.parts):
        return False

    if any(part.function_call for part in event.content.parts):
        return False

    normalized_prompt = prompt.strip()
    return any((part.text or "").strip() == normalized_prompt for part in event.content.parts)


def build_user_message_content(prompt: str) -> genai_types.Content:
    return genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=prompt)],
    )


async def iter_run_events(
    runner: Runner,
    *,
    user_id: str,
    session_id: str,
    prompt: str,
    state_delta: dict[str, str] | None = None,
) -> AsyncGenerator[Event, None]:
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=build_user_message_content(prompt),
        state_delta=state_delta or None,
    ):
        yield event


def build_meta_envelope() -> dict[str, object]:
    return {
        "type": "meta",
        "transport": "proxy",
        "notice": "目前由 FastAPI backend 直接代理 ADK Runner（SSE）。",
    }


def build_done_envelope(final_text: str, state: dict[str, str]) -> dict[str, object]:
    return {
        "type": "done",
        "finalText": final_text,
        "state": state,
    }


def build_error_envelope(message: str) -> dict[str, object]:
    return {
        "type": "error",
        "message": message,
    }


def merge_state_patches(
    current_state: dict[str, str],
    envelopes: list[dict[str, object]],
) -> dict[str, str]:
    merged_state = dict(current_state)

    for envelope in envelopes:
        if envelope.get("type") != "state":
            continue

        patch = envelope.get("patch", {})
        if isinstance(patch, dict):
            merged_state.update({str(key): str(value) for key, value in patch.items()})

    return merged_state

def build_tool_call_timeline_event(
    *,
    event_id: str,
    timestamp: str,
    tool_name: str,
    args: Any,
    author: str | None,
) -> dict[str, object]:
    return {
        "type": "timeline",
        "event": {
            "id": event_id,
            "kind": "tool-call",
            "title": tool_name,
            "summary": f"ADK 請求工具 {tool_name}",
            "timestamp": timestamp,
            "payload": [
                f"args: {safe_stringify(args or {})}",
                f"author: {author or 'agent'}",
            ],
        },
    }

def build_tool_result_timeline_event(
    *,
    event_id: str,
    timestamp: str,
    tool_name: str,
    response: Any,
) -> dict[str, object]:
    return {
        "type": "timeline",
        "event": {
            "id": event_id,
            "kind": "tool-result",
            "title": f"{tool_name} result",
            "summary": f"工具 {tool_name} 已回傳結果",
            "timestamp": timestamp,
            "payload": [
                f"response: {safe_stringify(response or {})}",
            ],
        },
    }


def build_tool_result_timeline_event(
    *,
    event_id: str,
    timestamp: str,
    tool_name: str,
    response: Any,
) -> dict[str, object]:
    return {
        "type": "timeline",
        "event": {
            "id": event_id,
            "kind": "tool-result",
            "title": f"{tool_name} result",
            "summary": f"工具 {tool_name} 已回傳結果",
            "timestamp": timestamp,
            "payload": [
                f"response: {safe_stringify(response or {})}",
            ],
        },
    }


def map_adk_event_to_envelopes(event: Event, sequence: int) -> list[dict[str, object]]:
    """將 ADK 原始事件轉成前端 envelope。

    重點：
    - 業務查詢工具會顯示在 timeline。
    - 內部 session/state 工具不顯示在 timeline。
    - state_delta 仍會輸出，讓前端 state inspector 可更新。
    - agent 文字回覆仍會輸出成 timeline + message。
    """

    event_id = event.id or f"evt-fastapi-{sequence}"
    timestamp = format_event_timestamp(event.timestamp)
    envelopes: list[dict[str, object]] = []

    parts = event.content.parts if event.content and event.content.parts else []

    for part_index, part in enumerate(parts):
        suffix = f"{event_id}-{part_index}"

        if part.function_call and part.function_call.name:
            tool_name = part.function_call.name
            is_internal = is_internal_session_tool(tool_name)

            envelopes.append(
                {
                    "type": "timeline",
                    "event": {
                        "id": f"{suffix}-call",
                        "kind": "internal" if is_internal else "tool-call",
                        "title": tool_name,
                        "summary": (
                            f"內部狀態工具 {tool_name}"
                            if is_internal
                            else f"ADK 請求工具 {tool_name}"
                        ),
                        "timestamp": timestamp,
                        "payload": [
                            f"args: {safe_stringify(part.function_call.args or {})}",
                            f"author: {event.author or 'agent'}",
                        ],
                    },
                }
            )

        if part.function_response and part.function_response.name:
            tool_name = part.function_response.name
            is_internal = is_internal_session_tool(tool_name)

            envelopes.append(
                {
                    "type": "timeline",
                    "event": {
                        "id": f"{suffix}-result",
                        "kind": "internal" if is_internal else "tool-result",
                        "title": f"{tool_name} result",
                        "summary": (
                            f"內部狀態工具 {tool_name} 已完成"
                            if is_internal
                            else f"工具 {tool_name} 已回傳結果"
                        ),
                        "timestamp": timestamp,
                        "payload": [
                            f"response: {safe_stringify(part.function_response.response or {})}"
                        ],
                    },
                }
            )

        text = (part.text or "").strip()
        if text and event.author != "user":
            envelopes.append(
                {
                    "type": "timeline",
                    "event": {
                        "id": f"{suffix}-{'stream' if event.partial else 'agent'}",
                        "kind": "stream" if event.partial else "agent",
                        "title": "partial_response" if event.partial else "agent_response",
                        "summary": text,
                        "timestamp": timestamp,
                        "payload": [
                            text,
                            f"author: {event.author or 'agent'}",
                            f"partial: {'true' if event.partial else 'false'}",
                        ],
                    },
                }
            )

            envelopes.append(
                {
                    "type": "message",
                    "text": text,
                    "mode": "append" if event.partial else "replace",
                    "final": not bool(event.partial),
                }
            )

    if event.actions and event.actions.state_delta:
        patch = stringify_state_patch(event.actions.state_delta)

        envelopes.append(
            {
                "type": "timeline",
                "event": {
                    "id": f"{event_id}-state",
                    "kind": "state",
                    "title": "state_delta",
                    "summary": "ADK session state 已更新",
                    "timestamp": timestamp,
                    "payload": [f"{key}: {value}" for key, value in patch.items()],
                },
            }
        )

        envelopes.append(
            {
                "type": "state",
                "patch": patch,
            }
        )

    return envelopes


class AgentRunService:
    """管理 Agent 執行週期的核心服務。"""

    def __init__(
        self,
        runner: Runner,
        sessions: SessionService,
        config: AppRuntimeConfig,
        audit_logs: AuditLogService | None = None,
    ) -> None:
        self._runner = runner
        self._sessions = sessions
        self._config = config
        self._audit_logs = audit_logs

    async def ensure_session(
        self,
        session_id: str,
        initial_state: dict[str, str] | None = None,
        user_id: str | None = None,
    ) -> None:
        await self._sessions.ensure_session(
            session_id,
            initial_state,
            user_id=user_id,
        )

    async def _record_adk_event_audit(
        self,
        *,
        audit_context: AuditContext,
        event: Event,
        sequence: int,
    ) -> None:
        """直接從 ADK event 記錄 audit。

        這裡會記錄所有工具呼叫，包括 UI 隱藏的 internal session tools。
        這樣可以避免「UI 隱藏 save_last_recommendation」後 audit log 也消失。
        """

        if not self._audit_logs:
            return

        parts = event.content.parts if event.content and event.content.parts else []

        for part_index, part in enumerate(parts):
            audit_sequence = sequence * 100 + part_index

            if part.function_call and part.function_call.name:
                tool_name = part.function_call.name
                await self._audit_logs.record(
                    context=audit_context,
                    event_type="agent.tool_call",
                    actor="agent",
                    tool_name=tool_name,
                    sequence=audit_sequence,
                    input_payload={
                        "tool_name": tool_name,
                        "tool_class": classify_tool_name(tool_name),
                        "args": part.function_call.args or {},
                        "author": event.author or "agent",
                    },
                )

            if part.function_response and part.function_response.name:
                tool_name = part.function_response.name
                await self._audit_logs.record(
                    context=audit_context,
                    event_type="agent.tool_result",
                    actor="tool",
                    tool_name=tool_name,
                    sequence=audit_sequence + 1,
                    output_payload={
                        "tool_name": tool_name,
                        "tool_class": classify_tool_name(tool_name),
                        "response": part.function_response.response or {},
                        "author": event.author or "tool",
                    },
                )

    async def _record_envelope_audit(
        self,
        *,
        audit_context: AuditContext,
        envelope: dict[str, object],
        sequence: int,
    ) -> None:
        """記錄非工具類 envelope audit。

        工具 call/result 已由 _record_adk_event_audit() 記錄，這裡避免重複寫入。
        """

        if not self._audit_logs:
            return

        envelope_type = str(envelope.get("type", ""))

        if envelope_type == "timeline":
            event = envelope.get("event", {})
            if not isinstance(event, dict):
                return

            kind = str(event.get("kind", "timeline"))

            if kind in {"tool-call", "tool-result"}:
                return

            event_type = {
                "state": "agent.state_delta",
                "agent": "agent.message",
                "stream": "agent.message",
            }.get(kind, f"agent.{kind}")

            await self._audit_logs.record(
                context=audit_context,
                event_type=event_type,
                actor="agent",
                sequence=sequence,
                output_payload=event,
            )

        elif envelope_type == "error":
            await self._audit_logs.record(
                context=audit_context,
                event_type="agent.error",
                actor="system",
                sequence=sequence,
                output_payload=envelope,
                policy_decision="error_redacted",
            )

    async def stream(
        self,
        *,
        prompt: str,
        session_id: str,
        session_state: dict[str, str] | None = None,
        user_id: str | None = None,
        audit_context: AuditContext | None = None,
    ) -> AsyncGenerator[dict[str, object], None]:
        """執行 Agent 並串流回傳結果。"""

        sequence = 0
        current_text = ""
        merged_state = dict(session_state or {})

        resolved_user_id = (
            user_id.strip()
            if user_id and user_id.strip()
            else self._config.api_user_id
        )

        yield build_meta_envelope()

        if self._audit_logs and audit_context:
            await self._audit_logs.record(
                context=audit_context,
                event_type="user.prompt.received",
                actor="user",
                sequence=0,
                input_payload={"prompt": prompt},
            )

        try:
            async for event in iter_run_events(
                self._runner,
                user_id=resolved_user_id,
                session_id=session_id,
                prompt=prompt,
                state_delta=session_state,
            ):
                if is_echoed_user_input(event, prompt):
                    continue

                sequence += 1

                if self._audit_logs and audit_context:
                    await self._record_adk_event_audit(
                        audit_context=audit_context,
                        event=event,
                        sequence=sequence,
                    )

                envelopes = map_adk_event_to_envelopes(event, sequence)
                merged_state = merge_state_patches(merged_state, envelopes)

                for envelope in envelopes:
                    if self._audit_logs and audit_context:
                        await self._record_envelope_audit(
                            audit_context=audit_context,
                            envelope=envelope,
                            sequence=sequence,
                        )

                    if envelope.get("type") == "message":
                        text = str(envelope.get("text", ""))
                        if envelope.get("mode") == "append":
                            current_text += text
                        else:
                            current_text = text

                    yield envelope

            final_state = await self._sessions.get_state(
                session_id=session_id,
                fallback_state=merged_state,
                user_id=user_id,
            )

            if self._audit_logs and audit_context:
                await self._audit_logs.record(
                    context=audit_context,
                    event_type="response.completed",
                    actor="agent",
                    sequence=sequence + 1,
                    output_payload={
                        "finalText": current_text,
                        "state": final_state,
                    },
                )

            yield build_done_envelope(
                final_text=current_text
                or "ADK runtime 已完成執行，請查看右側 event history。",
                state=final_state,
            )

        except Exception as exc:
            error_envelope = build_error_envelope(str(exc))

            if self._audit_logs and audit_context:
                await self._record_envelope_audit(
                    audit_context=audit_context,
                    envelope=error_envelope,
                    sequence=sequence + 1,
                )

            yield error_envelope
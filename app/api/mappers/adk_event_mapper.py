from __future__ import annotations

from datetime import datetime

from google.adk.events.event import Event

from app.api.presenters.session_presenter import safe_stringify
from app.api.schemas import (
    MessageEnvelope,
    StateEnvelope,
    TimelineEnvelope,
    TimelineEventModel,
)


def format_event_timestamp(timestamp: float | None) -> str:
    value = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    return value.strftime("%H:%M")


def stringify_state_patch(state_delta: dict[str, object]) -> dict[str, str]:
    return {key: safe_stringify(value) for key, value in state_delta.items()}


def is_echoed_user_input(event: Event, prompt: str) -> bool:
    if event.author != "user" or not event.content or not event.content.parts:
        return False

    if any(part.function_response for part in event.content.parts):
        return False

    normalized_prompt = prompt.strip()
    return any(
        (part.text or "").strip() == normalized_prompt for part in event.content.parts
    )


def map_adk_event_to_envelopes(event: Event, sequence: int) -> list[dict[str, object]]:
    event_id = event.id or f"evt-fastapi-{sequence}"
    timestamp = format_event_timestamp(event.timestamp)
    envelopes: list[dict[str, object]] = []
    parts = event.content.parts if event.content and event.content.parts else []

    for part_index, part in enumerate(parts):
        suffix = f"{event_id}-{part_index}"

        if part.function_call and part.function_call.name:
            envelopes.append(
                TimelineEnvelope(
                    event=TimelineEventModel(
                        id=f"{suffix}-call",
                        kind="tool-call",
                        title=part.function_call.name,
                        summary=f"ADK 請求工具 {part.function_call.name}",
                        timestamp=timestamp,
                        payload=[
                            f"args: {safe_stringify(part.function_call.args or {})}",
                            f"author: {event.author or 'agent'}",
                        ],
                    )
                ).model_dump()
            )

        if part.function_response and part.function_response.name:
            envelopes.append(
                TimelineEnvelope(
                    event=TimelineEventModel(
                        id=f"{suffix}-result",
                        kind="tool-result",
                        title=f"{part.function_response.name} result",
                        summary=f"工具 {part.function_response.name} 已回傳結果",
                        timestamp=timestamp,
                        payload=[
                            f"response: {safe_stringify(part.function_response.response or {})}"
                        ],
                    )
                ).model_dump()
            )

        text = (part.text or "").strip()
        if text and event.author != "user":
            envelopes.append(
                TimelineEnvelope(
                    event=TimelineEventModel(
                        id=f"{suffix}-{'stream' if event.partial else 'agent'}",
                        kind="stream" if event.partial else "agent",
                        title="partial_response" if event.partial else "agent_response",
                        summary=text,
                        timestamp=timestamp,
                        payload=[
                            text,
                            f"author: {event.author or 'agent'}",
                            f"partial: {'true' if event.partial else 'false'}",
                        ],
                    )
                ).model_dump()
            )
            envelopes.append(
                MessageEnvelope(
                    text=text,
                    mode="append" if event.partial else "replace",
                    final=not bool(event.partial),
                ).model_dump()
            )

    if event.actions and event.actions.state_delta:
        patch = stringify_state_patch(event.actions.state_delta)
        envelopes.append(
            TimelineEnvelope(
                event=TimelineEventModel(
                    id=f"{event_id}-state",
                    kind="state",
                    title="state_delta",
                    summary="ADK session state 已更新",
                    timestamp=timestamp,
                    payload=[f"{key}: {value}" for key, value in patch.items()],
                )
            ).model_dump()
        )
        envelopes.append(StateEnvelope(patch=patch).model_dump())

    return envelopes

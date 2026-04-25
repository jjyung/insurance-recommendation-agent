from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Iterable

from google.adk.events.event import Event
from google.adk.runners import Runner
from google.genai import types as genai_types

from app.api.mappers.adk_event_mapper import (
    is_echoed_user_input,
    map_adk_event_to_envelopes,
)
from app.api.schemas import (
    DoneEnvelope,
    ErrorEnvelope,
    MessageEnvelope,
    MetaEnvelope,
    StateEnvelope,
    TimelineEnvelope,
    TimelineEventModel,
)
from app.api.presenters.session_presenter import safe_stringify


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
    return MetaEnvelope(
        notice="目前由 FastAPI backend 直接代理 ADK Runner（SSE）。"
    ).model_dump()


def build_done_envelope(final_text: str, state: dict[str, str]) -> dict[str, object]:
    return DoneEnvelope(finalText=final_text, state=state).model_dump()


def build_error_envelope(message: str) -> dict[str, object]:
    return ErrorEnvelope(message=message).model_dump()


def encode_sse_event(envelope: dict[str, object]) -> str:
    return f"data: {json.dumps(envelope, ensure_ascii=False)}\n\n"


def merge_state_patches(
    current_state: dict[str, str],
    envelopes: Iterable[dict[str, object]],
) -> dict[str, str]:
    merged_state = dict(current_state)
    for envelope in envelopes:
        if envelope.get("type") == "state":
            patch = envelope.get("patch", {})
            if isinstance(patch, dict):
                merged_state.update(
                    {str(key): str(value) for key, value in patch.items()}
                )
    return merged_state

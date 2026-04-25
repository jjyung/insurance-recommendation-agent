from __future__ import annotations

from collections.abc import AsyncGenerator

from google.adk.runners import Runner

from app.api.mappers.adk_event_mapper import (
    is_echoed_user_input,
    map_adk_event_to_envelopes,
)
from app.api.schemas import AgentRunRequest
from app.api.streaming import (
    build_done_envelope,
    build_error_envelope,
    build_meta_envelope,
    iter_run_events,
    merge_state_patches,
)
from app.app_runtime import AppRuntimeConfig
from app.application.session_facade import SessionFacade


class AgentRunService:
    def __init__(
        self,
        runner: Runner,
        sessions: SessionFacade,
        config: AppRuntimeConfig,
    ) -> None:
        self._runner = runner
        self._sessions = sessions
        self._config = config

    async def ensure_session(
        self,
        session_id: str,
        initial_state: dict[str, str] | None = None,
    ) -> None:
        await self._sessions.ensure_session(session_id, initial_state)

    async def stream(
        self,
        request: AgentRunRequest,
    ) -> AsyncGenerator[dict[str, object], None]:
        prompt = request.prompt.strip()
        session_id = request.sessionId.strip()
        sequence = 0
        current_text = ""
        merged_state = dict(request.sessionState)

        yield build_meta_envelope()

        try:
            async for event in iter_run_events(
                self._runner,
                user_id=self._config.api_user_id,
                session_id=session_id,
                prompt=prompt,
                state_delta=request.sessionState,
            ):
                if is_echoed_user_input(event, prompt):
                    continue

                sequence += 1
                envelopes = map_adk_event_to_envelopes(event, sequence)
                merged_state = merge_state_patches(merged_state, envelopes)

                for envelope in envelopes:
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
            )
            yield build_done_envelope(
                final_text=current_text
                or "ADK runtime 已完成執行，請查看右側 event history。",
                state=final_state,
            )
        except Exception as exc:
            yield build_error_envelope(str(exc))

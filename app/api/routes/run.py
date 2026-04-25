from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.dependencies import get_container, get_runner as dependency_get_runner
from app.api.schemas import AgentRunRequest
from app.api.streaming import encode_sse_event
from app.application.agent_run_service import AgentRunService
from app.application.session_facade import SessionFacade

router = APIRouter(prefix="/api/agent", tags=["agent"])


def get_runner(request: Request | None = None):
    if request is not None:
        return get_container(request).runner

    return dependency_get_runner()


@router.post("/run")
async def run_agent(payload: AgentRunRequest, request: Request):
    prompt = payload.prompt.strip()
    session_id = payload.sessionId.strip()

    if not prompt or not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "prompt and sessionId are required"},
        )

    container = get_container(request)
    sessions = SessionFacade(container.session_service, container.config)
    try:
        runner = get_runner(request)
    except TypeError:
        runner = get_runner()

    run_service = AgentRunService(runner, sessions, container.config)

    try:
        await run_service.ensure_session(session_id, payload.sessionState)
    except Exception as exc:
        return JSONResponse(
            status_code=502,
            content={"error": f"Unable to ensure session: {exc}"},
        )

    normalized_payload = payload.model_copy(
        update={
            "prompt": prompt,
            "sessionId": session_id,
        }
    )

    async def sse_generator() -> AsyncGenerator[str, None]:
        async for envelope in run_service.stream(normalized_payload):
            yield encode_sse_event(envelope)

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
        },
    )

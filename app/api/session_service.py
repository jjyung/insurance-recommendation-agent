from __future__ import annotations

from typing import Any

from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.session import Session

from app.app_runtime import AppRuntimeConfig
from app.api.presenters.session_presenter import (
    build_public_state,
    to_session_list_item,
)


async def list_sessions_for_ui(
    session_service: BaseSessionService,
    config: AppRuntimeConfig,
) -> list[dict[str, Any]]:
    response = await session_service.list_sessions(
        app_name=config.app_name,
        user_id=config.api_user_id,
    )

    sessions = [to_session_list_item(session) for session in response.sessions]
    sessions.sort(key=lambda item: item["_updateTime"], reverse=True)

    return [
        {key: value for key, value in session.items() if key != "_updateTime"}
        for session in sessions
    ]


async def create_session_if_missing(
    session_service: BaseSessionService,
    config: AppRuntimeConfig,
    session_id: str,
    initial_state: dict[str, Any] | None = None,
) -> Session:
    existing = await session_service.get_session(
        app_name=config.app_name,
        user_id=config.api_user_id,
        session_id=session_id,
    )
    if existing is not None:
        return existing

    return await session_service.create_session(
        app_name=config.app_name,
        user_id=config.api_user_id,
        session_id=session_id,
        state=initial_state or {},
    )


async def delete_session_if_exists(
    session_service: BaseSessionService,
    config: AppRuntimeConfig,
    session_id: str,
) -> None:
    existing = await session_service.get_session(
        app_name=config.app_name,
        user_id=config.api_user_id,
        session_id=session_id,
    )
    if existing is None:
        return

    await session_service.delete_session(
        app_name=config.app_name,
        user_id=config.api_user_id,
        session_id=session_id,
    )


async def get_session_state(
    session_service: BaseSessionService,
    config: AppRuntimeConfig,
    session_id: str,
    fallback_state: dict[str, str] | None = None,
) -> dict[str, str]:
    session = await session_service.get_session(
        app_name=config.app_name,
        user_id=config.api_user_id,
        session_id=session_id,
    )

    if session is None:
        return fallback_state or {}

    persisted_state = build_public_state(dict(session.state))

    if not fallback_state:
        return persisted_state

    return {
        **persisted_state,
        **fallback_state,
    }

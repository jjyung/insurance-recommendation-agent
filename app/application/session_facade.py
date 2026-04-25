from __future__ import annotations

from typing import Any

from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.session import Session

from app.api.session_service import (
    create_session_if_missing,
    delete_session_if_exists,
    get_session_state,
    list_sessions_for_ui,
)
from app.app_runtime import AppRuntimeConfig


class SessionFacade:
    def __init__(
        self,
        session_service: BaseSessionService,
        config: AppRuntimeConfig,
    ) -> None:
        self._session_service = session_service
        self._config = config

    async def list_sessions(self) -> list[dict[str, Any]]:
        """Return API-facing session list items already projected for the UI."""
        return await list_sessions_for_ui(self._session_service, self._config)

    async def ensure_session(
        self,
        session_id: str,
        initial_state: dict[str, Any] | None = None,
    ) -> Session:
        return await create_session_if_missing(
            session_service=self._session_service,
            config=self._config,
            session_id=session_id,
            initial_state=initial_state,
        )

    async def delete_session(self, session_id: str) -> None:
        await delete_session_if_exists(
            session_service=self._session_service,
            config=self._config,
            session_id=session_id,
        )

    async def get_state(
        self,
        session_id: str,
        fallback_state: dict[str, str] | None = None,
    ) -> dict[str, str]:
        return await get_session_state(
            session_service=self._session_service,
            config=self._config,
            session_id=session_id,
            fallback_state=fallback_state,
        )

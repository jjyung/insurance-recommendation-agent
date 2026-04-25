from __future__ import annotations

import asyncio

import requests

from app.core.container import AppContainer


class ReadinessService:
    def __init__(self, container: AppContainer) -> None:
        self._container = container

    async def collect_errors(self) -> list[str]:
        errors: list[str] = []

        try:
            self._container.session_service
        except Exception as exc:
            errors.append(f"session_service: {exc}")

        try:
            await asyncio.to_thread(
                requests.get,
                self._container.config.toolbox_server_url,
                timeout=1,
            )
        except requests.RequestException as exc:
            errors.append(f"toolbox: {exc}")

        return errors

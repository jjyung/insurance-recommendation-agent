from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.database_session_service import DatabaseSessionService
from google.adk.sessions.sqlite_session_service import SqliteSessionService

from app.agent import create_agent
from app.core.config import AppRuntimeConfig, load_runtime_config


def _normalize_sqlite_db_path(session_db_uri: str) -> str:
    parsed = urlparse(session_db_uri)
    db_path = parsed.path

    if db_path.startswith("/"):
        db_path = db_path[1:]

    return db_path or ":memory:"


def create_session_service(config: AppRuntimeConfig) -> BaseSessionService:
    parsed = urlparse(config.session_db_uri)

    if parsed.scheme == "sqlite":
        return SqliteSessionService(
            db_path=_normalize_sqlite_db_path(config.session_db_uri)
        )

    return DatabaseSessionService(db_url=config.session_db_uri)


def create_runner(
    config: AppRuntimeConfig,
    agent: Agent,
    session_service: BaseSessionService,
) -> Runner:
    return Runner(
        app_name=config.app_name,
        agent=agent,
        session_service=session_service,
    )


@dataclass(frozen=True)
class AppContainer:
    config: AppRuntimeConfig
    agent: Agent
    session_service: BaseSessionService
    runner: Runner


def build_app_container(config: AppRuntimeConfig | None = None) -> AppContainer:
    runtime_config = config or load_runtime_config()
    agent = create_agent(runtime_config)
    session_service = create_session_service(runtime_config)
    runner = create_runner(runtime_config, agent, session_service)
    return AppContainer(
        config=runtime_config,
        agent=agent,
        session_service=session_service,
        runner=runner,
    )

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote


def _parse_bool_env(name: str, default: bool) -> bool:
    """
    從環境變數解析布林值。
    支援 '1', 'true', 'yes', 'on' 作為 True。
    """
    value = os.getenv(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_csv_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """
    從環境變數解析以逗號分隔的字串列表 (CSV)，回傳 tuple。
    """
    value = os.getenv(name)
    if value is None:
        return default

    items = tuple(item.strip() for item in value.split(",") if item.strip())
    return items or default


def _build_cloud_sql_session_uri_from_env() -> str | None:
    """
    若部署在 Cloud Run 且有提供 Cloud SQL 連線所需環境變數，
    自動組合 ADK_SESSION_DB_URI (postgresql+asyncpg)。
    """
    instance_connection_name = os.getenv("INSTANCE_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_name = os.getenv("DB_NAME")
    db_pass = os.getenv("DB_PASS")

    if not all([instance_connection_name, db_user, db_name, db_pass]):
        return None

    encoded_user = quote(db_user, safe="")
    encoded_pass = quote(db_pass, safe="")
    encoded_instance = quote(instance_connection_name, safe="")
    encoded_db_name = quote(db_name, safe="")

    return (
        f"postgresql+asyncpg://{encoded_user}:{encoded_pass}@/{encoded_db_name}"
        f"?host=/cloudsql/{encoded_instance}"
    )


@dataclass(frozen=True)
class AppRuntimeConfig:
    """
    應用程式執行階段配置資料類別。
    封裝了從環境變數載入的所有關鍵配置。
    """
    app_name: str               # 應用程式名稱
    api_user_id: str            # 預設 API 使用者識別碼
    toolbox_server_url: str     # Toolbox (MCP) 伺服器網址
    session_db_uri: str         # Session 資料庫連線字串 (如 SQLite)
    memory_mode: str            # 記憶體模式 (例如 in_memory)
    model_name: str             # 使用的 LLM 模型名稱
    fastapi_host: str           # FastAPI 伺服器監聽主機位址
    fastapi_port: int           # FastAPI 伺服器監聽埠號
    fastapi_reload: bool        # 是否啟用 FastAPI 自動重載 (開發模式用)
    cors_allow_origins: tuple[str, ...] # CORS 允許的來源網域


def load_runtime_config() -> AppRuntimeConfig:
    """
    從系統環境變數中載入配置，並提供合理的預設值。
    """
    derived_session_db_uri = _build_cloud_sql_session_uri_from_env()

    return AppRuntimeConfig(
        app_name=os.getenv("ADK_APP_NAME", "app"),
        api_user_id=os.getenv("ADK_API_USER_ID", "demo-user"),
        toolbox_server_url=os.getenv("TOOLBOX_SERVER_URL", "http://127.0.0.1:5000"),
        session_db_uri=os.getenv(
            "ADK_SESSION_DB_URI",
            derived_session_db_uri or "sqlite+aiosqlite:///./db/adk_sessions.db",
        ),
        memory_mode=os.getenv("ADK_MEMORY_MODE", "in_memory"),
        model_name=os.getenv("MODEL_NAME", "gemini-3-flash-preview"),
        fastapi_host=os.getenv("FASTAPI_HOST", "127.0.0.1"),
        fastapi_port=int(os.getenv("FASTAPI_PORT", "8080")),
        fastapi_reload=_parse_bool_env("FASTAPI_RELOAD", True),
        cors_allow_origins=_parse_csv_env(
            "FASTAPI_CORS_ALLOW_ORIGINS",
            ("http://127.0.0.1:3000", "http://localhost:3000"),
        ),
    )


# 匯出配置類別與載入函式
__all__ = ["AppRuntimeConfig", "load_runtime_config"]

from __future__ import annotations

import json
import time
from typing import Any

from google.adk.sessions.session import Session

from app.domain.session_state import is_ui_state_key


def safe_stringify(value: Any) -> str:
    if isinstance(value, str):
        return value

    if value is None:
        return "None"

    try:
        return (
            str(value) if isinstance(value, (int, float, bool)) else json.dumps(value)
        )
    except Exception:
        return str(value)


def build_public_state(raw_state: dict[str, Any]) -> dict[str, str]:
    return {
        key: safe_stringify(value)
        for key, value in raw_state.items()
        if not is_ui_state_key(key)
    }


def format_updated_at(last_update_time: float) -> str:
    if not last_update_time:
        return "已儲存"

    diff_seconds = max(0, int(time.time() - last_update_time))
    minutes = diff_seconds // 60

    if minutes < 1:
        return "剛剛"
    if minutes < 60:
        return f"{minutes} 分鐘前"

    hours = minutes // 60
    if hours < 24:
        return f"{hours} 小時前"

    return f"{hours // 24} 天前"


def to_session_list_item(session: Session) -> dict[str, Any]:
    raw_state = dict(session.state)
    ui_title = raw_state.get("_ui_title")
    ui_subtitle = raw_state.get("_ui_subtitle")

    title = ui_title if isinstance(ui_title, str) and ui_title.strip() else None
    subtitle = (
        ui_subtitle if isinstance(ui_subtitle, str) and ui_subtitle.strip() else None
    )

    return {
        "id": session.id,
        "title": title or f"對話 {session.id[-6:]}",
        "subtitle": subtitle or "繼續上次的對話",
        "status": "idle",
        "updatedAt": format_updated_at(session.last_update_time),
        "messages": [],
        "events": [],
        "state": build_public_state(raw_state),
        "_updateTime": session.last_update_time,
    }

from __future__ import annotations

import asyncio
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.toolbox_toolset import ToolboxToolset
from toolbox_core.protocol import Protocol

from app.config import load_runtime_config
from app.session_state import TRACKED_PROFILE_STATE_KEYS
from app.tools.session_tools import (
    clear_last_recommendation,
    get_user_profile_snapshot,
    save_last_recommendation,
    save_user_profile,
)


PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "insurance_agent_prompt.txt"

_PROFILE_KEY_LABELS: dict[str, str] = {
    "user:age": "年齡",
    "user:budget": "預算",
    "user:main_goal": "主要保障目標",
    "user:marital_status": "婚姻狀態",
    "user:has_children": "是否有小孩",
    "user:existing_coverage": "既有保障",
    "user:risk_preference": "風險偏好",
    "user:last_recommended_product_name": "最近推薦商品",
    "user:last_recommended_product_id": "最近推薦商品 ID",
}


def load_agent_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


# def inject_profile_context(
#     callback_context: CallbackContext,
#     llm_request: LlmRequest,
# ) -> LlmResponse | None:
#     """
#     Before each model call, read the session state and prepend existing user
#     profile data to the system instruction.  This guarantees the model always
#     sees the profile snapshot even if it forgets to call get_user_profile_snapshot
#     first, providing a code-level safety net on top of the prompt rule.
#     """
#     snapshot: dict[str, object] = {}
#     for key in TRACKED_PROFILE_STATE_KEYS:
#         value = callback_context.state.get(key)
#         if value is not None:
#             snapshot[key] = value

#     if not snapshot:
#         return None

#     lines = ["【目前 Session 已存在以下使用者資料，請優先沿用，不要重新逐項追問】"]
#     for key, value in snapshot.items():
#         label = _PROFILE_KEY_LABELS.get(key, key)
#         lines.append(f"  - {label}: {value}")
#     profile_block = "\n".join(lines)

#     config = llm_request.config
#     if config is None:
#         return None

#     existing = config.system_instruction
#     if existing is None:
#         config.system_instruction = profile_block
#     elif isinstance(existing, str):
#         config.system_instruction = f"{profile_block}\n\n---\n{existing}"
#     else:
#         # Content object — prepend to the first text part
#         if hasattr(existing, "parts") and existing.parts:
#             first_text = getattr(existing.parts[0], "text", "") or ""
#             existing.parts[0].text = f"{profile_block}\n\n---\n{first_text}"

#     return None


class AgentFactory:
    def __init__(self, config) -> None:
        self._config = config

    def create_toolbox(self) -> ToolboxToolset:
        return ToolboxToolset(
            server_url=self._config.toolbox_server_url,
            protocol=Protocol.MCP_LATEST,
        )

    def build_tools(self) -> list[object]:
        return [
            get_user_profile_snapshot,
            save_user_profile,
            save_last_recommendation,
            clear_last_recommendation,
            self.create_toolbox(),
        ]

    def create(self) -> Agent:
        return Agent(
            name=self._config.app_name,
            model=self._config.model_name,
            instruction=load_agent_prompt(),
            tools=self.build_tools(),
            # before_model_callback=inject_profile_context,
        )


def create_agent(config=None) -> Agent:
    runtime_config = config or load_runtime_config()
    return AgentFactory(runtime_config).create()


root_agent = create_agent()


# async def main():
#     config = load_runtime_config()
#     agent = create_agent(config)

#     print("insurance_recommendation_agent initialized.")
#     print("Session tools attached.")
#     print("ToolboxToolset attached.")
#     print("Prompt loaded from file.")
#     print(f"App name: {config.app_name}")
#     print(f"Toolbox URL: {config.toolbox_server_url}")
#     print(f"Session DB URI: {config.session_db_uri}")
#     print(agent)


# if __name__ == "__main__":
#     asyncio.run(main())

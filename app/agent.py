import asyncio
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.toolbox_toolset import ToolboxToolset
from toolbox_core.protocol import Protocol

from app.tools.session_tools import (
    clear_last_recommendation,
    get_user_profile_snapshot,
    save_last_recommendation,
    save_user_profile,
)


APP_NAME = "insurance_recommendation_agent"


def load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "insurance_agent_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def create_agent():
    toolbox = ToolboxToolset(
        server_url="http://127.0.0.1:5000",
        protocol=Protocol.MCP,
    )

    agent = Agent(
        name=APP_NAME,
        model="gemini-2.5-flash",
        instruction=load_prompt(),
        tools=[
            get_user_profile_snapshot,
            save_user_profile,
            save_last_recommendation,
            clear_last_recommendation,
            toolbox,
        ],
    )
    return agent


root_agent = create_agent()


async def main():
    print(f"{APP_NAME} initialized.")
    print("Session tools attached.")
    print("ToolboxToolset attached.")
    print("Prompt loaded from file.")
    print(root_agent)


if __name__ == "__main__":
    asyncio.run(main())

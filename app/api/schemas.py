from __future__ import annotations

from typing import Any
from typing import Literal

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    sessionId: str = Field(min_length=1)
    sessionState: dict[str, str] = Field(default_factory=dict)


class SessionCreateRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    state: dict[str, Any] = Field(default_factory=dict)


class TimelineEventModel(BaseModel):
    id: str
    kind: Literal["user", "tool-call", "tool-result", "state", "stream", "agent"]
    title: str
    summary: str
    timestamp: str
    payload: list[str]


class MetaEnvelope(BaseModel):
    type: Literal["meta"] = "meta"
    transport: Literal["proxy"] = "proxy"
    notice: str


class TimelineEnvelope(BaseModel):
    type: Literal["timeline"] = "timeline"
    event: TimelineEventModel


class StateEnvelope(BaseModel):
    type: Literal["state"] = "state"
    patch: dict[str, str]


class MessageEnvelope(BaseModel):
    type: Literal["message"] = "message"
    text: str
    mode: Literal["append", "replace"]
    final: bool


class DoneEnvelope(BaseModel):
    type: Literal["done"] = "done"
    finalText: str
    state: dict[str, str]


class ErrorEnvelope(BaseModel):
    type: Literal["error"] = "error"
    message: str

"""LLM request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[Message]
    stream: bool = False
    temperature: Optional[float] = Field(default=1.0, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=100000)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)


class ChatMessage(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list
    usage: dict


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelList(BaseModel):
    object: str = "list"
    data: list[ModelInfo]

"""Authenticated API for resilient, server-side LLM completion."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .auth import AuthenticatedUser, get_current_user
from .llm_router import LLMRouterError, ResilientLLMRouter

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


@lru_cache(maxsize=1)
def get_router() -> ResilientLLMRouter:
    return ResilientLLMRouter.from_env()


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=16000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)
    task_class: str = Field(default="default", pattern=r"^(default|coding|reasoning|creative|classification)$")
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1200, ge=1, le=8192)


class ChatResponse(BaseModel):
    provider: str
    model: str
    content: str
    attempts: list[str]


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    """Try providers in configured priority order and fail over on errors."""
    del user  # Authentication is required; tenant usage accounting is a follow-up.
    try:
        result = await get_router().complete(
            [message.model_dump() for message in payload.messages],
            task_class=payload.task_class,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    except LLMRouterError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return ChatResponse(
        provider=result.provider,
        model=result.model,
        content=result.content,
        attempts=list(result.attempts),
    )


@router.get("/health")
async def provider_health(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Authenticated provider health view; API keys are never included."""
    del user
    return {"providers": await get_router().health()}

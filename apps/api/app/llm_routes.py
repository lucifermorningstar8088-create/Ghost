"""Authenticated LLM chat endpoint backed by the server-side failover router."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .auth import AuthenticatedUser, get_current_user
from .llm_router import LLMFailoverRouter, LLMRoutingError

router = APIRouter(prefix="/api/v1/llm", tags=["llm"])


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(pattern=r"^(system|user|assistant)$")
    content: str = Field(min_length=1, max_length=12000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    messages: list[ChatMessage] = Field(min_length=1, max_length=40)
    temperature: float = Field(default=0.4, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)


class ChatResponse(BaseModel):
    content: str
    provider: str
    model: str
    attempts: int


@lru_cache(maxsize=1)
def get_router() -> LLMFailoverRouter:
    """Cache configuration per API process; credentials are read only on the server."""
    return LLMFailoverRouter()


@router.get("/health")
def provider_health(
    _user: AuthenticatedUser = Depends(get_current_user),
):
    """Return configured provider health metadata without probing/billing providers."""
    return {"providers": get_router().health()}


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    _user: AuthenticatedUser = Depends(get_current_user),
) -> ChatResponse:
    """Route to fast/healthy configured model first, then automatically fail over."""
    try:
        result = get_router().chat(
            [message.model_dump() for message in payload.messages],
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
        return ChatResponse(
            content=result.content,
            provider=result.provider,
            model=result.model,
            attempts=result.attempts,
        )
    except LLMRoutingError as exc:
        # Avoid leaking provider exception bodies, URLs, or credential details.
        raise HTTPException(
            status_code=503,
            detail={"message": str(exc), "attempts": exc.attempts},
            headers={"Retry-After": "5"},
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

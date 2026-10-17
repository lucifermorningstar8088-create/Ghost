from __future__ import annotations

import os

import httpx
import pytest

from app.llm_router import (
    LLMProviderConfig,
    LLMRouterError,
    ResilientLLMRouter,
)


def provider(name: str, priority: int, key_env: str) -> LLMProviderConfig:
    return LLMProviderConfig(
        name=name,
        base_url="https://" + name + ".example/v1",
        api_key_env=key_env,
        model="model-" + name,
        priority=priority,
        timeout_seconds=2,
        max_concurrency=2,
    )


@pytest.mark.asyncio
async def test_configured_priority_and_fallback_after_primary_failure(monkeypatch):
    monkeypatch.setenv("KEY_FAST", "not-a-real-secret")
    monkeypatch.setenv("KEY_BACKUP", "not-a-real-secret")
    router = ResilientLLMRouter(
        [provider("fast", 1, "KEY_FAST"), provider("backup", 2, "KEY_BACKUP")]
    )

    async def healthy(_provider):
        return True

    class Response:
        def __init__(self, status_code, data=None):
            self.status_code = status_code
            self._data = data or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("error", request=None, response=None)

        def json(self):
            return self._data

    class Client:
        def __init__(self, *args, **kwargs):
            self.url = None

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, **kwargs):
            if "fast.example" in url:
                return Response(503)
            return Response(200, {"choices": [{"message": {"content": "backup answer"}}]})

    monkeypatch.setattr(router, "_probe", healthy)
    monkeypatch.setattr("app.llm_router.httpx.AsyncClient", Client)
    result = await router.complete([{"role": "user", "content": "hello"}])
    assert result.provider == "backup"
    assert result.content == "backup answer"
    assert result.attempts[0].startswith("fast:http_503")
    assert result.attempts[-1] == "backup:success"


@pytest.mark.asyncio
async def test_missing_credentials_are_skipped(monkeypatch):
    monkeypatch.delenv("MISSING_KEY", raising=False)
    router = ResilientLLMRouter([provider("missing", 1, "MISSING_KEY")])
    with pytest.raises(LLMRouterError, match="unavailable"):
        await router.complete([{"role": "user", "content": "hello"}])


@pytest.mark.asyncio
async def test_no_provider_configuration_fails_closed():
    router = ResilientLLMRouter([])
    with pytest.raises(LLMRouterError, match="No valid LLM providers"):
        await router.complete([{"role": "user", "content": "hello"}])


def test_from_env_uses_env_var_names_not_secret_values(monkeypatch):
    monkeypatch.setenv("GHOST_LLM_PROVIDERS", "fast,backup")
    monkeypatch.setenv("GHOST_LLM_FAST_BASE_URL", "https://fast.example/v1")
    monkeypatch.setenv("GHOST_LLM_FAST_API_KEY_ENV", "FAST_SECRET")
    monkeypatch.setenv("GHOST_LLM_FAST_MODEL", "quick-model")
    monkeypatch.setenv("GHOST_LLM_FAST_PRIORITY", "1")
    monkeypatch.setenv("GHOST_LLM_BACKUP_BASE_URL", "https://backup.example/v1")
    monkeypatch.setenv("GHOST_LLM_BACKUP_API_KEY_ENV", "BACKUP_SECRET")
    monkeypatch.setenv("GHOST_LLM_BACKUP_MODEL", "backup-model")
    monkeypatch.setenv("GHOST_LLM_BACKUP_PRIORITY", "2")
    monkeypatch.setenv("FAST_SECRET", "fake-secret-value")
    router = ResilientLLMRouter.from_env()
    assert [p.name for p in router.providers] == ["fast", "backup"]
    assert router.providers[0].api_key_env == "FAST_SECRET"
    assert "fake-secret-value" not in repr(router.providers)

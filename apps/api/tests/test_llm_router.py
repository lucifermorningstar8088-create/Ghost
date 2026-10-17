from __future__ import annotations

import json

import httpx
import pytest

from app.llm_router import (
    LLMFailoverRouter,
    LLMProvider,
    LLMRoutingError,
    ProviderRegistry,
    load_providers,
)


def provider(name, *, fast=False, priority=100, models=("model-a",), key_env=None):
    return LLMProvider(
        name=name,
        base_url="https://api.example.test/v1",
        api_key_env=key_env or f"{name.upper()}_KEY",
        models=models,
        priority=priority,
        fast=fast,
        timeout_seconds=3,
    )


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, *, timeout, responses, seen):
        self.responses = responses
        self.seen = seen

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def post(self, url, *, headers, json):
        self.seen.append({"url": url, "headers": headers, "body": json})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def client_factory_for(responses, seen):
    def factory(*, timeout):
        return FakeClient(timeout=timeout, responses=responses, seen=seen)
    return factory


def test_fast_provider_is_sorted_first():
    providers = load_providers(json.dumps([
        {"name": "backup", "base_url": "https://backup.test/v1", "api_key_env": "BACKUP_KEY", "models": ["b"]},
        {"name": "fast", "base_url": "https://fast.test/v1", "api_key_env": "FAST_KEY", "models": ["f"], "fast": True},
    ]))
    assert [p.name for p in providers] == ["fast", "backup"]


def test_rejects_insecure_provider_urls_by_default():
    with pytest.raises(ValueError, match="HTTPS"):
        load_providers(json.dumps([
            {"name": "unsafe", "base_url": "http://localhost:1234/v1", "api_key_env": "UNSAFE_KEY", "models": ["x"]}
        ]))


def test_provider_failover_uses_backup_after_rate_limit(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "secret-primary")
    monkeypatch.setenv("BACKUP_KEY", "secret-backup")
    seen = []
    responses = [
        FakeResponse(429, {"error": "rate limited"}),
        FakeResponse(200, {"choices": [{"message": {"content": "done"}}]}),
    ]
    router = LLMFailoverRouter(
        [provider("primary", fast=True), provider("backup")],
        client_factory=client_factory_for(responses, seen),
    )
    result = router.chat([{"role": "user", "content": "hello"}])
    assert result.content == "done"
    assert result.provider == "backup"
    assert result.attempts == 2
    assert len(seen) == 2


def test_model_fallback_within_same_provider(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "secret-primary")
    seen = []
    responses = [
        FakeResponse(429, {}),
        FakeResponse(200, {"choices": [{"message": {"content": "second model"}}]}),
    ]
    router = LLMFailoverRouter(
        [provider("primary", models=("model-a", "model-b"))],
        client_factory=client_factory_for(responses, seen),
    )
    result = router.chat([{"role": "user", "content": "hello"}])
    assert result.model == "model-b"
    assert result.content == "second model"


def test_network_timeout_falls_back_to_next_provider(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "secret-primary")
    monkeypatch.setenv("BACKUP_KEY", "secret-backup")
    seen = []
    responses = [
        httpx.ReadTimeout("timeout"),
        FakeResponse(200, {"choices": [{"message": {"content": "backup ok"}}]}),
    ]
    router = LLMFailoverRouter(
        [provider("primary", fast=True), provider("backup")],
        client_factory=client_factory_for(responses, seen),
    )
    result = router.chat([{"role": "user", "content": "hello"}])
    assert result.provider == "backup"


def test_missing_credentials_are_skipped(monkeypatch):
    monkeypatch.delenv("PRIMARY_KEY", raising=False)
    monkeypatch.setenv("BACKUP_KEY", "secret-backup")
    seen = []
    responses = [FakeResponse(200, {"choices": [{"message": {"content": "ok"}}]})]
    router = LLMFailoverRouter(
        [provider("primary", fast=True), provider("backup")],
        client_factory=client_factory_for(responses, seen),
    )
    assert router.chat([{"role": "user", "content": "hello"}]).provider == "backup"
    assert len(seen) == 1


def test_no_configured_providers_fails_closed():
    with pytest.raises(LLMRoutingError, match="No LLM providers"):
        LLMFailoverRouter([]).chat([{"role": "user", "content": "hello"}])


def test_circuit_breaker_temporarily_skips_unhealthy_provider():
    registry = ProviderRegistry(failure_threshold=2, cooldown_seconds=10)
    registry.failure("primary", now=100)
    registry.failure("primary", now=101)
    assert not registry.is_available("primary", now=105)
    assert registry.is_available("primary", now=112)
    registry.success("primary")
    assert registry.is_available("primary", now=113)


def test_error_does_not_echo_secret(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "do-not-leak")
    seen = []
    responses = [FakeResponse(503, {})]
    router = LLMFailoverRouter(
        [provider("primary")],
        client_factory=client_factory_for(responses, seen),
    )
    with pytest.raises(LLMRoutingError) as exc:
        router.chat([{"role": "user", "content": "hello"}])
    assert "do-not-leak" not in str(exc.value)



def test_health_metadata_does_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("PRIMARY_KEY", "super-secret-value")
    router = LLMFailoverRouter([provider("primary", fast=True)])
    router.registry.failure("primary")
    router.registry.failure("primary")
    rows = router.health()
    assert rows == [{
        "provider": "primary",
        "models_configured": 1,
        "priority": 100,
        "fast": True,
        "credential_configured": True,
        "circuit_available": False,
        "timeout_seconds": 3,
    }]
    assert "super-secret-value" not in repr(rows)


def test_health_reports_missing_credentials_without_network_calls(monkeypatch):
    monkeypatch.delenv("PRIMARY_KEY", raising=False)
    router = LLMFailoverRouter([provider("primary")])
    assert router.health()[0]["credential_configured"] is False

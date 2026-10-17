"""Fast-first, availability-aware LLM routing with automatic provider/model failover.

Provider configuration is server-side only. This module uses OpenAI-compatible
chat-completions endpoints; it does not assume every API uses that protocol.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class LLMProvider:
    name: str
    base_url: str
    api_key_env: str
    models: tuple[str, ...]
    priority: int = 100
    fast: bool = False
    timeout_seconds: float = 20.0


@dataclass(frozen=True)
class LLMResult:
    content: str
    provider: str
    model: str
    attempts: int


class LLMRoutingError(RuntimeError):
    def __init__(self, message: str, *, attempts: int):
        super().__init__(message)
        self.attempts = attempts


class ProviderRegistry:
    """Small process-local circuit breaker; secrets never leave server memory."""

    def __init__(self, *, failure_threshold: int = 2, cooldown_seconds: float = 30.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._failures: dict[str, int] = {}
        self._open_until: dict[str, float] = {}

    def is_available(self, name: str, now: float | None = None) -> bool:
        now = time.monotonic() if now is None else now
        with self._lock:
            return self._open_until.get(name, 0.0) <= now

    def success(self, name: str) -> None:
        with self._lock:
            self._failures[name] = 0
            self._open_until.pop(name, None)

    def failure(self, name: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        with self._lock:
            failures = self._failures.get(name, 0) + 1
            self._failures[name] = failures
            if failures >= self.failure_threshold:
                self._open_until[name] = now + self.cooldown_seconds


def load_providers(raw: str | None = None) -> list[LLMProvider]:
    """Load providers from GHOST_LLM_PROVIDERS JSON, without reading secret values."""
    raw = os.getenv("GHOST_LLM_PROVIDERS", "") if raw is None else raw
    if not raw.strip():
        return []
    try:
        records = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("GHOST_LLM_PROVIDERS must be valid JSON") from exc
    if not isinstance(records, list):
        raise ValueError("GHOST_LLM_PROVIDERS must be a JSON array")

    providers: list[LLMProvider] = []
    seen: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Each LLM provider entry must be an object")
        name = item.get("name")
        base_url = item.get("base_url")
        key_env = item.get("api_key_env")
        models = item.get("models")
        if not all(isinstance(v, str) and v.strip() for v in (name, base_url, key_env)):
            raise ValueError("Provider name, base_url, and api_key_env are required")
        if name in seen:
            raise ValueError("Provider names must be unique")
        if not base_url.startswith("https://") and not (
            base_url.startswith("http://") and os.getenv("GHOST_LLM_ALLOW_INSECURE_HTTP") == "true"
        ):
            raise ValueError("LLM provider URLs must use HTTPS")
        if not isinstance(models, list) or not models or not all(
            isinstance(model, str) and model.strip() and len(model) <= 160 for model in models
        ):
            raise ValueError("Each provider needs a non-empty models array")
        timeout = item.get("timeout_seconds", 20)
        priority = item.get("priority", 100)
        if not isinstance(timeout, (int, float)) or not 1 <= timeout <= 120:
            raise ValueError("timeout_seconds must be between 1 and 120")
        if not isinstance(priority, int) or priority < 0:
            raise ValueError("priority must be a non-negative integer")
        providers.append(LLMProvider(
            name=name,
            base_url=base_url.rstrip("/"),
            api_key_env=key_env,
            models=tuple(models),
            priority=priority,
            fast=item.get("fast", False) is True,
            timeout_seconds=float(timeout),
        ))
        seen.add(name)
    # Fast providers first, then configured priority; stable ordering for ties.
    return sorted(providers, key=lambda p: (not p.fast, p.priority, p.name))


class LLMFailoverRouter:
    def __init__(
        self,
        providers: list[LLMProvider] | None = None,
        *,
        registry: ProviderRegistry | None = None,
        client_factory=httpx.Client,
    ):
        self.providers = providers if providers is not None else load_providers()
        self.registry = registry or ProviderRegistry()
        self.client_factory = client_factory

    def health(self) -> list[dict[str, Any]]:
        """Return safe configuration/circuit-breaker metadata, not an active health guarantee."""
        rows: list[dict[str, Any]] = []
        for provider in self.providers:
            rows.append({
                "provider": provider.name,
                "models_configured": len(provider.models),
                "priority": provider.priority,
                "fast": provider.fast,
                "credential_configured": bool(os.getenv(provider.api_key_env)),
                "circuit_available": self.registry.is_available(provider.name),
                "timeout_seconds": provider.timeout_seconds,
            })
        return rows

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.4,
        max_tokens: int = 1024,
    ) -> LLMResult:
        if not messages or not all(
            isinstance(m, dict)
            and m.get("role") in {"system", "user", "assistant"}
            and isinstance(m.get("content"), str)
            for m in messages
        ):
            raise ValueError("messages must contain role/content chat messages")
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 1 <= max_tokens <= 32768:
            raise ValueError("max_tokens must be between 1 and 32768")
        if not self.providers:
            raise LLMRoutingError("No LLM providers are configured", attempts=0)

        attempts = 0
        last_reason = "No configured provider is currently available"
        for provider in self.providers:
            if not self.registry.is_available(provider.name):
                continue
            api_key = os.getenv(provider.api_key_env)
            if not api_key:
                last_reason = f"Provider {provider.name} has no configured server-side credential"
                self.registry.failure(provider.name)
                continue
            for model in provider.models:
                attempts += 1
                try:
                    with self.client_factory(timeout=provider.timeout_seconds) as client:
                        response = client.post(
                            provider.base_url + "/chat/completions",
                            headers={
                                "Authorization": "Bearer " + api_key,
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model,
                                "messages": messages,
                                "temperature": temperature,
                                "max_tokens": max_tokens,
                            },
                        )
                    if response.status_code >= 500 or response.status_code in {408, 409, 425, 429}:
                        last_reason = f"Provider {provider.name} returned retryable HTTP {response.status_code}"
                        self.registry.failure(provider.name)
                        continue
                    if response.status_code in {401, 403}:
                        last_reason = f"Provider {provider.name} rejected credentials/permissions (HTTP {response.status_code})"
                        self.registry.failure(provider.name)
                        break
                    if response.status_code >= 400:
                        # A malformed request is unlikely to be fixed by switching providers.
                        raise LLMRoutingError(
                            f"LLM request rejected with HTTP {response.status_code}; check model and request compatibility",
                            attempts=attempts,
                        )
                    try:
                        payload: dict[str, Any] = response.json()
                        content = payload["choices"][0]["message"]["content"]
                    except (ValueError, KeyError, IndexError, TypeError) as exc:
                        last_reason = f"Provider {provider.name} returned an invalid chat-completions response"
                        self.registry.failure(provider.name)
                        continue
                    if not isinstance(content, str) or not content.strip():
                        last_reason = f"Provider {provider.name} returned empty content"
                        self.registry.failure(provider.name)
                        continue
                    self.registry.success(provider.name)
                    return LLMResult(content=content, provider=provider.name, model=model, attempts=attempts)
                except (httpx.TimeoutException, httpx.NetworkError, OSError) as exc:
                    # Do not echo exception text: it may contain request details.
                    last_reason = f"Provider {provider.name} timed out or could not be reached"
                    self.registry.failure(provider.name)
                    break
        raise LLMRoutingError(
            f"All configured LLM routes failed or are cooling down. Last safe status: {last_reason}",
            attempts=attempts,
        )

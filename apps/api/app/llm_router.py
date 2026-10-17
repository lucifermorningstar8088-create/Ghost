"""Provider-agnostic LLM routing with health-aware fallback.

Only OpenAI-compatible chat-completions endpoints are supported by this initial
adapter. Credentials stay in server-side environment variables. No provider is
assumed available until configured and successfully probed.
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    base_url: str
    api_key_env: str
    model: str
    priority: int = 100
    timeout_seconds: float = 20.0
    max_concurrency: int = 4
    enabled: bool = True


@dataclass(frozen=True)
class LLMResult:
    provider: str
    model: str
    content: str
    attempts: tuple[str, ...]


@dataclass
class _ProviderState:
    healthy: bool = False
    checked_at: float = 0.0
    cooldown_until: float = 0.0
    failures: int = 0
    in_flight: int = 0


class LLMRouterError(RuntimeError):
    pass


class ResilientLLMRouter:
    """Fast-first ordered routing with health probes, concurrency caps and failover."""

    def __init__(
        self,
        providers: list[LLMProviderConfig],
        *,
        health_ttl_seconds: float = 20.0,
        failure_cooldown_seconds: float = 30.0,
        max_retries_per_provider: int = 1,
    ):
        self.providers = sorted(
            (p for p in providers if p.enabled),
            key=lambda p: (p.priority, p.name),
        )
        self.health_ttl_seconds = health_ttl_seconds
        self.failure_cooldown_seconds = failure_cooldown_seconds
        self.max_retries_per_provider = max(0, max_retries_per_provider)
        self._states = {p.name: _ProviderState() for p in self.providers}
        self._locks = {p.name: asyncio.Lock() for p in self.providers}

    @classmethod
    def from_env(cls) -> "ResilientLLMRouter":
        """Load a comma-separated ordered provider list; secrets are env-var names only.

        Format: GHOST_LLM_PROVIDERS=fast,backup
        Per provider prefix GHOST_LLM_<UPPER_NAME>_ supports BASE_URL, API_KEY_ENV,
        MODEL, PRIORITY, TIMEOUT_SECONDS, MAX_CONCURRENCY.
        """
        names = [n.strip().lower() for n in os.getenv("GHOST_LLM_PROVIDERS", "").split(",") if n.strip()]
        configs = []
        for name in names:
            prefix = "GHOST_LLM_" + "".join(c if c.isalnum() else "_" for c in name.upper()) + "_"
            base_url = os.getenv(prefix + "BASE_URL", "").strip().rstrip("/")
            api_key_env = os.getenv(prefix + "API_KEY_ENV", "").strip()
            model = os.getenv(prefix + "MODEL", "").strip()
            if not base_url or not api_key_env or not model:
                continue
            try:
                priority = int(os.getenv(prefix + "PRIORITY", str((len(configs) + 1) * 10)))
                timeout = float(os.getenv(prefix + "TIMEOUT_SECONDS", "20"))
                concurrency = int(os.getenv(prefix + "MAX_CONCURRENCY", "4"))
            except ValueError:
                continue
            if not 1 <= timeout <= 120 or not 1 <= concurrency <= 64:
                continue
            configs.append(LLMProviderConfig(
                name=name, base_url=base_url, api_key_env=api_key_env,
                model=model, priority=priority, timeout_seconds=timeout,
                max_concurrency=concurrency,
            ))
        return cls(configs)

    def _credential(self, provider: LLMProviderConfig) -> str | None:
        value = os.getenv(provider.api_key_env, "").strip()
        return value or None

    async def _probe(self, provider: LLMProviderConfig) -> bool:
        state = self._states[provider.name]
        now = time.monotonic()
        if state.cooldown_until > now:
            return False
        if state.checked_at and now - state.checked_at < self.health_ttl_seconds:
            return state.healthy and self._credential(provider) is not None
        key = self._credential(provider)
        state.checked_at = now
        if not key:
            state.healthy = False
            return False
        try:
            async with httpx.AsyncClient(timeout=min(provider.timeout_seconds, 8.0)) as client:
                response = await client.get(
                    provider.base_url + "/models",
                    headers={"Authorization": "Bearer " + key},
                )
            state.healthy = response.status_code < 500 and response.status_code != 429
        except (httpx.HTTPError, OSError):
            state.healthy = False
        return state.healthy

    async def health(self) -> list[dict[str, Any]]:
        """Return safe operational metadata; never expose API keys."""
        rows = []
        for provider in self.providers:
            state = self._states[provider.name]
            available = await self._probe(provider)
            rows.append({
                "provider": provider.name,
                "model": provider.model,
                "priority": provider.priority,
                "available": available,
                "in_flight": state.in_flight,
                "max_concurrency": provider.max_concurrency,
                "cooldown_seconds": max(0, round(state.cooldown_until - time.monotonic(), 1)),
            })
        return rows

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        task_class: str = "default",
        temperature: float = 0.4,
        max_tokens: int = 1200,
    ) -> LLMResult:
        if not self.providers:
            raise LLMRouterError("No valid LLM providers are configured")
        if not messages or len(messages) > 100:
            raise ValueError("messages must contain between 1 and 100 entries")
        if not 1 <= max_tokens <= 8192 or not 0 <= temperature <= 2:
            raise ValueError("temperature or max_tokens is outside the supported range")

        attempts: list[str] = []
        # The configured order is intentional: lowest priority number is tried first.
        # Providers with a cached healthy probe are tried first, then other candidates.
        candidates = []
        for provider in self.providers:
            if not self._credential(provider):
                continue
            state = self._states[provider.name]
            if state.cooldown_until > time.monotonic():
                continue
            healthy = await self._probe(provider)
            if healthy:
                candidates.append(provider)
        for provider in candidates:
            state = self._states[provider.name]
            async with self._locks[provider.name]:
                if state.in_flight >= provider.max_concurrency:
                    attempts.append(provider.name + ":capacity")
                    continue
                state.in_flight += 1
            try:
                key = self._credential(provider)
                if not key:
                    attempts.append(provider.name + ":missing_credentials")
                    continue
                payload = {
                    "model": provider.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                last_error = "request_failed"
                for _ in range(self.max_retries_per_provider + 1):
                    try:
                        async with httpx.AsyncClient(timeout=provider.timeout_seconds) as client:
                            response = await client.post(
                                provider.base_url + "/chat/completions",
                                headers={"Authorization": "Bearer " + key,
                                         "Content-Type": "application/json"},
                                json=payload,
                            )
                        if response.status_code == 429 or response.status_code >= 500:
                            last_error = "http_" + str(response.status_code)
                            break
                        response.raise_for_status()
                        data = response.json()
                        content = data["choices"][0]["message"]["content"]
                        if not isinstance(content, str) or not content.strip():
                            last_error = "empty_response"
                            break
                        state.failures = 0
                        state.healthy = True
                        state.checked_at = time.monotonic()
                        attempts.append(provider.name + ":success")
                        return LLMResult(provider.name, provider.model, content, tuple(attempts))
                    except (httpx.HTTPError, OSError, ValueError, KeyError, IndexError, TypeError):
                        last_error = "transport_or_response_error"
                        break
                state.failures += 1
                state.healthy = False
                state.checked_at = time.monotonic()
                state.cooldown_until = time.monotonic() + self.failure_cooldown_seconds
                attempts.append(provider.name + ":" + last_error)
            finally:
                async with self._locks[provider.name]:
                    state.in_flight = max(0, state.in_flight - 1)

        raise LLMRouterError("All configured LLM providers failed or were unavailable: " + ", ".join(attempts))


def default_router() -> ResilientLLMRouter:
    return ResilientLLMRouter.from_env()

"""Fail-closed compute routing and provider adapter contracts.

Provider execution is disabled unless GHOST_COMPUTE_EXECUTION_ENABLED=true.
This module never reads secrets from request payloads or returns their values.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol


class ProviderName(StrEnum):
    KAGGLE = "kaggle"
    LOCAL = "local"


class AdmissionError(RuntimeError):
    """Raised when a provider cannot safely accept a workload."""


@dataclass(frozen=True)
class ComputeRequest:
    job_type: str
    estimated_gpu_hours: float
    max_runtime_seconds: int
    requires_gpu: bool = True


@dataclass(frozen=True)
class ProviderAvailability:
    provider: ProviderName
    available: bool
    reason: str
    gpu_available: bool = False


@dataclass(frozen=True)
class LaunchResult:
    provider: ProviderName
    accepted: bool
    dry_run: bool
    message: str
    external_id: str | None = None


class ComputeAdapter(Protocol):
    provider: ProviderName

    def availability(self) -> ProviderAvailability: ...


def execution_enabled() -> bool:
    """Live execution is opt-in; missing env var means safe dry-run behavior."""
    return os.getenv("GHOST_COMPUTE_EXECUTION_ENABLED", "").strip().lower() == "true"


class KaggleCliAdapter:
    """Minimal Kaggle CLI capability/status adapter; does not claim a stop API."""

    provider = ProviderName.KAGGLE

    def __init__(self, *, username_env: str = "KAGGLE_USERNAME", key_env: str = "KAGGLE_KEY"):
        self.username_env = username_env
        self.key_env = key_env

    def availability(self) -> ProviderAvailability:
        if not os.getenv(self.username_env) or not os.getenv(self.key_env):
            return ProviderAvailability(self.provider, False, "Kaggle credentials are not configured")
        cli = shutil.which("kaggle")
        if not cli:
            return ProviderAvailability(self.provider, False, "Kaggle CLI is not installed")
        return ProviderAvailability(self.provider, True, "Credentials and CLI are present")

    def build_push_command(self, kernel_dir: str, timeout_seconds: int) -> list[str]:
        """Build a bounded-timeout push command for an existing local kernel directory."""
        if not 60 <= timeout_seconds <= 21600:
            raise ValueError("timeout_seconds must be between 60 and 21600")
        path = Path(kernel_dir).expanduser().resolve()
        if not path.is_dir():
            raise ValueError("kernel_dir must point to an existing directory")
        cli = shutil.which("kaggle")
        if not cli:
            raise AdmissionError("Kaggle CLI is not installed")
        return [cli, "kernels", "push", "-p", str(path), "--timeout", str(timeout_seconds)]

    def status(self, kernel_ref: str, *, timeout_seconds: int = 20) -> str:
        """Read status with a subprocess deadline; unknown/error remains non-terminal."""
        cli = shutil.which("kaggle")
        if not cli:
            return "unknown"
        try:
            result = subprocess.run(
                [cli, "kernels", "status", kernel_ref],
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=os.environ.copy(),
            )
        except (OSError, subprocess.TimeoutExpired):
            return "unknown"
        if result.returncode != 0:
            return "unknown"
        output = (result.stdout + "\n" + result.stderr).lower()
        if "complete" in output or "succeed" in output:
            return "completed"
        if "error" in output or "fail" in output:
            return "failed"
        if "running" in output or "queued" in output or "starting" in output:
            return "active"
        return "unknown"


class LocalHardwareAdapter:
    """Detect local resources without assuming a GPU or launching arbitrary code."""

    provider = ProviderName.LOCAL

    def __init__(self):
        self._gpu_probe = shutil.which("nvidia-smi")

    def availability(self) -> ProviderAvailability:
        gpu = False
        if self._gpu_probe:
            try:
                result = subprocess.run(
                    [self._gpu_probe, "-L"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                gpu = result.returncode == 0 and bool(result.stdout.strip())
            except (OSError, subprocess.TimeoutExpired):
                gpu = False
        return ProviderAvailability(
            self.provider,
            True,
            "Local CPU is available" + ("; NVIDIA GPU detected" if gpu else "; no supported NVIDIA GPU detected"),
            gpu_available=gpu,
        )

    def can_run(self, request: ComputeRequest) -> tuple[bool, str]:
        state = self.availability()
        if request.requires_gpu and not state.gpu_available:
            return False, "This workload requires a GPU, but no supported local NVIDIA GPU was detected"
        if request.max_runtime_seconds < 1 or request.max_runtime_seconds > 21600:
            return False, "Requested runtime is outside the local safety limit"
        return True, state.reason


class ComputeRouter:
    """Kaggle-first when configured and eligible; otherwise safe local fallback."""

    def __init__(self, kaggle: KaggleCliAdapter | None = None, local: LocalHardwareAdapter | None = None):
        self.kaggle = kaggle or KaggleCliAdapter()
        self.local = local or LocalHardwareAdapter()

    def choose(self, request: ComputeRequest, *, kaggle_pool_enabled: bool, quota_fresh: bool,
               budget_available: bool) -> tuple[ProviderName | None, str]:
        kaggle_state = self.kaggle.availability()
        if kaggle_pool_enabled and kaggle_state.available and quota_fresh and budget_available:
            return ProviderName.KAGGLE, "Kaggle selected by priority policy"
        reasons = []
        if not kaggle_state.available:
            reasons.append(kaggle_state.reason)
        elif not kaggle_pool_enabled:
            reasons.append("Kaggle pool is not enabled")
        elif not quota_fresh:
            reasons.append("Kaggle quota snapshot is missing or stale")
        elif not budget_available:
            reasons.append("Kaggle budget has insufficient headroom")

        can_run, local_reason = self.local.can_run(request)
        if can_run:
            return ProviderName.LOCAL, "Local fallback selected: " + "; ".join(reasons)
        return None, "; ".join(reasons + [local_reason])

    def launch_guard(self) -> None:
        """Central guard for any future live launch call."""
        if not execution_enabled():
            raise AdmissionError(
                "Live compute execution is disabled; set GHOST_COMPUTE_EXECUTION_ENABLED=true "
                "only after reviewing provider configuration and tests"
            )

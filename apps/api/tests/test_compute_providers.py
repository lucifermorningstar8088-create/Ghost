from __future__ import annotations

from app.compute_providers import (
    AdmissionError,
    ComputeRequest,
    ComputeRouter,
    KaggleCliAdapter,
    LocalHardwareAdapter,
    ProviderAvailability,
    ProviderName,
)


class FakeKaggle:
    provider = ProviderName.KAGGLE

    def __init__(self, available: bool = True):
        self.available = available

    def availability(self):
        return ProviderAvailability(
            self.provider, self.available,
            "fake configured" if self.available else "fake credentials absent",
        )


class FakeLocal:
    provider = ProviderName.LOCAL

    def __init__(self, can_run: bool = True):
        self.allowed = can_run

    def can_run(self, request):
        return self.allowed, "fake local capacity" if self.allowed else "local capacity insufficient"


def request(requires_gpu: bool = True):
    return ComputeRequest(
        job_type="training",
        estimated_gpu_hours=1.0,
        max_runtime_seconds=900,
        requires_gpu=requires_gpu,
    )


def test_kaggle_is_first_when_configured_fresh_and_budgeted():
    router = ComputeRouter(kaggle=FakeKaggle(), local=FakeLocal())
    provider, reason = router.choose(
        request(), kaggle_pool_enabled=True, quota_fresh=True, budget_available=True
    )
    assert provider == ProviderName.KAGGLE
    assert "priority" in reason


def test_missing_kaggle_credentials_falls_back_to_local():
    router = ComputeRouter(kaggle=FakeKaggle(available=False), local=FakeLocal())
    provider, reason = router.choose(
        request(requires_gpu=False), kaggle_pool_enabled=False,
        quota_fresh=False, budget_available=False,
    )
    assert provider == ProviderName.LOCAL
    assert "credentials absent" in reason


def test_stale_quota_blocks_kaggle_and_falls_back_if_local_can_run():
    router = ComputeRouter(kaggle=FakeKaggle(), local=FakeLocal())
    provider, reason = router.choose(
        request(requires_gpu=False), kaggle_pool_enabled=True,
        quota_fresh=False, budget_available=True,
    )
    assert provider == ProviderName.LOCAL
    assert "stale" in reason


def test_no_provider_is_selected_if_local_cannot_run_and_kaggle_blocked():
    router = ComputeRouter(kaggle=FakeKaggle(), local=FakeLocal(can_run=False))
    provider, reason = router.choose(
        request(), kaggle_pool_enabled=True, quota_fresh=False, budget_available=True
    )
    assert provider is None
    assert "insufficient" in reason


def test_kaggle_timeout_command_is_bounded(monkeypatch):
    monkeypatch.setattr("app.compute_providers.shutil.which", lambda _: "/usr/bin/kaggle")
    adapter = KaggleCliAdapter()
    command = adapter.build_push_command("owner/notebook", 600)
    assert command[-2:] == ["--timeout", "600"]


def test_kaggle_timeout_rejects_unbounded_value(monkeypatch):
    monkeypatch.setattr("app.compute_providers.shutil.which", lambda _: "/usr/bin/kaggle")
    try:
        KaggleCliAdapter().build_push_command("owner/notebook", 999999)
    except ValueError as exc:
        assert "between 60 and 21600" in str(exc)
    else:
        raise AssertionError("out-of-range timeout should be rejected")


def test_live_launch_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("GHOST_COMPUTE_EXECUTION_ENABLED", raising=False)
    try:
        ComputeRouter().launch_guard()
    except AdmissionError as exc:
        assert "disabled" in str(exc)
    else:
        raise AssertionError("live launch must fail closed")

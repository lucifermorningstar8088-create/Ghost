#!/usr/bin/env python3
"""Validate Ghost's JSON schemas, YAML fixtures, and proposed tool registry.

This checks configuration integrity only. It does not authenticate providers,
run application code, or prove that proposed integrations are operational.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


class ConfigValidationError(Exception):
    """Raised when a config contract or fixture is invalid."""


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigValidationError(f"{path.relative_to(ROOT)}: cannot read valid JSON: {exc}") from exc


def load_yaml(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigValidationError(f"{path.relative_to(ROOT)}: cannot read valid YAML: {exc}") from exc


def validate_instances(schema_path: Path, instance_path: Path, collection_key: str) -> list[dict[str, Any]]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    payload = load_yaml(instance_path)
    if not isinstance(payload, dict) or not isinstance(payload.get(collection_key), list):
        raise ConfigValidationError(
            f"{instance_path.relative_to(ROOT)}: expected a top-level list at '{collection_key}'"
        )

    records = payload[collection_key]
    for index, record in enumerate(records):
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.absolute_path))
        if errors:
            details = "; ".join(
                f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: {error.message}"
                for error in errors
            )
            raise ConfigValidationError(
                f"{instance_path.relative_to(ROOT)}[{index}] fails "
                f"{schema_path.name}: {details}"
            )
    return records


def ensure_unique(records: list[dict[str, Any]], key: str, label: str) -> None:
    values = [record.get(key) for record in records]
    if len(values) != len(set(values)):
        raise ConfigValidationError(f"{label}: duplicate {key} values found")


def validate_tool_registry(path: Path) -> tuple[int, int]:
    payload = load_yaml(path)
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ConfigValidationError(f"{path.relative_to(ROOT)}: schema_version must be 1")

    policy = payload.get("policy")
    required_policy = {
        "default_status",
        "default_deny",
        "paid_calls_require_budget_authorization",
        "inject_all_tool_schemas_into_every_prompt",
        "discovery_mode",
        "max_retries",
        "retry_jitter",
        "irreversible_actions_require_idempotency_and_readback",
        "redact_secrets_from_logs",
    }
    if not isinstance(policy, dict) or not required_policy.issubset(policy):
        raise ConfigValidationError(f"{path.relative_to(ROOT)}: required policy keys are missing")
    if policy["default_deny"] is not True or policy["redact_secrets_from_logs"] is not True:
        raise ConfigValidationError("tool registry must retain default-deny and secret-redaction policies")
    if policy["paid_calls_require_budget_authorization"] is not True:
        raise ConfigValidationError("paid calls must require explicit budget authorization")
    if policy["max_retries"] < 0 or policy["max_retries"] > 10:
        raise ConfigValidationError("max_retries must be between 0 and 10")

    capabilities = payload.get("capabilities")
    implementations = payload.get("implementations")
    if not isinstance(capabilities, list) or not capabilities:
        raise ConfigValidationError("tool registry must contain at least one capability")
    if not isinstance(implementations, list) or not implementations:
        raise ConfigValidationError("tool registry must contain at least one implementation record")

    ensure_unique(capabilities, "id", "capabilities")
    ensure_unique(implementations, "id", "implementations")

    for item in capabilities:
        if not isinstance(item, dict) or not {"id", "priority", "primary", "fallback", "safe_stop"}.issubset(item):
            raise ConfigValidationError("every capability needs id, priority, primary, fallback, and safe_stop")
        if item["priority"] not in {"P0", "P1", "P2", "P3"}:
            raise ConfigValidationError(f"invalid priority for capability {item.get('id')}")

    allowed_statuses = {"proposed", "configured", "validated", "enabled", "degraded", "disabled"}
    for item in implementations:
        if not isinstance(item, dict) or not {"id", "category", "status", "secrets"}.issubset(item):
            raise ConfigValidationError("every implementation needs id, category, status, and secrets")
        if item["status"] not in allowed_statuses:
            raise ConfigValidationError(f"invalid status for implementation {item.get('id')}")
        if not isinstance(item["secrets"], list):
            raise ConfigValidationError(f"secrets must be a list for implementation {item.get('id')}")
        for secret_name in item["secrets"]:
            if not isinstance(secret_name, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", secret_name):
                raise ConfigValidationError(
                    f"secret entries must be uppercase variable names, not values ({item.get('id')})"
                )

    return len(capabilities), len(implementations)


def main() -> int:
    checks = [
        (
            ROOT / "config/channel-profile.schema.json",
            ROOT / "config/channel-profiles.example.yaml",
            "profiles",
        ),
        (
            ROOT / "config/content-type.schema.json",
            ROOT / "config/content-types.example.yaml",
            "content_types",
        ),
    ]

    try:
        profile_records: list[dict[str, Any]] = []
        content_type_records: list[dict[str, Any]] = []
        for schema_path, fixture_path, collection_key in checks:
            records = validate_instances(schema_path, fixture_path, collection_key)
            print(f"PASS {schema_path.relative_to(ROOT)} + {fixture_path.relative_to(ROOT)} ({len(records)} records)")
            if collection_key == "profiles":
                profile_records = records
            else:
                content_type_records = records

        ensure_unique(profile_records, "profile_id", "channel profiles")
        ensure_unique(content_type_records, "content_type_id", "content types")
        profile_ids = {profile["profile_id"] for profile in profile_records}
        for content_type in content_type_records:
            owner = content_type.get("owner_profile_id")
            if owner is not None and owner not in profile_ids:
                raise ConfigValidationError(
                    f"content type {content_type['content_type_id']} references unknown owner_profile_id {owner}"
                )

        capability_count, implementation_count = validate_tool_registry(ROOT / "config/tools.yaml")
        print(f"PASS config/tools.yaml ({capability_count} capabilities, {implementation_count} proposed/configuration records)")
        print("NOTE These checks validate files only; they do not prove live integration readiness.")
        return 0
    except ConfigValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

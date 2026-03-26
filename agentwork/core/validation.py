from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def load_schema(name: str) -> dict[str, Any]:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text())


def _try_jsonschema_validate(instance: Any, schema: dict[str, Any]) -> None:
    try:
        import jsonschema  # type: ignore
    except ModuleNotFoundError:
        return
    jsonschema.validate(instance=instance, schema=schema)


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _ensure_mapping(value: Any, message: str) -> dict[str, Any]:
    _ensure(isinstance(value, dict), message)
    return value


def _ensure_list(value: Any, message: str) -> list[Any]:
    _ensure(isinstance(value, list), message)
    return value


def validate_contract(contract: dict[str, Any]) -> None:
    _try_jsonschema_validate(contract, load_schema("contract.schema.json"))
    _ensure_mapping(contract, "Contract must be a mapping.")
    for key in ("id", "version", "domain", "description", "acceptance", "expectations"):
        _ensure(key in contract, f"Contract missing required field: {key}")

    acceptance = _ensure_mapping(contract["acceptance"], "Contract acceptance must be a mapping.")
    _ensure("design" in acceptance, "Contract acceptance must define the 'design' phase.")
    thresholds = _ensure_mapping(acceptance["design"], "Design thresholds must be a mapping.")
    for key in ("min_completion_rate", "min_safety_score", "min_trials", "confidence"):
        _ensure(key in thresholds, f"Design thresholds missing required field: {key}")

    invariants = contract.get("invariants", [])
    _ensure_list(invariants, "Contract invariants must be a list.")
    for invariant in invariants:
        invariant_map = _ensure_mapping(invariant, "Invariant must be a mapping.")
        for key in ("id", "description", "check", "config"):
            _ensure(key in invariant_map, f"Invariant missing required field: {key}")

    expectations = _ensure_list(contract["expectations"], "Contract expectations must be a list.")
    for expectation in expectations:
        expectation_map = _ensure_mapping(expectation, "Expectation must be a mapping.")
        for key in ("id", "description", "bundle_type", "checks"):
            _ensure(key in expectation_map, f"Expectation missing required field: {key}")
        _ensure_list(expectation_map["checks"], "Expectation checks must be a list.")
        if "bundle_ids" in expectation_map:
            _ensure_list(expectation_map["bundle_ids"], "Expectation bundle_ids must be a list.")


def validate_bundle(bundle: dict[str, Any]) -> None:
    _ensure_mapping(bundle, "Bundle must be a mapping.")
    for key in ("id", "bundle_type", "prompt", "context", "expected"):
        _ensure(key in bundle, f"Bundle missing required field: {key}")
    _ensure_mapping(bundle["context"], "Bundle context must be a mapping.")
    _ensure_mapping(bundle["expected"], "Bundle expected must be a mapping.")

    requirements = bundle.get("requirements", {})
    if requirements:
        requirements_map = _ensure_mapping(requirements, "Bundle requirements must be a mapping.")
        for list_key in ("required_tools", "forbidden_tools", "required_steps", "forbidden_actions"):
            if list_key in requirements_map:
                _ensure_list(requirements_map[list_key], f"Bundle requirements.{list_key} must be a list.")


def validate_bundles(bundles: list[dict[str, Any]]) -> None:
    _try_jsonschema_validate(bundles, load_schema("scenario_bundle.schema.json"))
    _ensure_list(bundles, "Bundles document must be a list.")
    for bundle in bundles:
        validate_bundle(bundle)


def validate_result(result: dict[str, Any]) -> None:
    _try_jsonschema_validate(result, load_schema("agent_result.schema.json"))
    _ensure_mapping(result, "Agent result must be a mapping.")
    for key in ("response", "structured", "tool_calls", "steps", "usage", "latency_ms", "metadata"):
        _ensure(key in result, f"Agent result missing required field: {key}")
    _ensure_mapping(result["structured"], "Agent result.structured must be a mapping.")
    _ensure_list(result["tool_calls"], "Agent result.tool_calls must be a list.")
    _ensure_list(result["steps"], "Agent result.steps must be a list.")
    _ensure_mapping(result["usage"], "Agent result.usage must be a mapping.")
    _ensure(isinstance(result["latency_ms"], int), "Agent result.latency_ms must be an integer.")
    _ensure_mapping(result["metadata"], "Agent result.metadata must be a mapping.")

    for call in result["tool_calls"]:
        call_map = _ensure_mapping(call, "Each tool call must be a mapping.")
        _ensure("name" in call_map, "Each tool call must include a name.")

    for step in result["steps"]:
        step_map = _ensure_mapping(step, "Each step must be a mapping.")
        _ensure("name" in step_map, "Each step must include a name.")

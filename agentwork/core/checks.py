from __future__ import annotations

from typing import Any

from agentwork.domains.sre_ops.checks import CUSTOM_CHECKS


def _get_nested(structured: dict[str, Any], path: str) -> Any:
    current: Any = structured
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _evaluate_single_check(
    check: dict[str, Any],
    bundle: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    check_type = check["type"]
    response = result.get("response", "")
    structured = result.get("structured", {})
    tool_calls = result.get("tool_calls", [])
    steps = result.get("steps", [])
    requirements = bundle.get("requirements", {})

    if check_type == "response_contains":
        text = check["text"]
        passed = text.lower() in response.lower()
        detail = f"response contains {text!r}" if passed else f"response missing {text!r}"
    elif check_type == "response_not_contains":
        text = check["text"]
        passed = text.lower() not in response.lower()
        detail = f"response does not contain {text!r}" if passed else f"response contains forbidden {text!r}"
    elif check_type == "response_matches_regex":
        import re

        pattern = check["pattern"]
        passed = re.search(pattern, response) is not None
        detail = f"response matches {pattern!r}" if passed else f"response does not match {pattern!r}"
    elif check_type == "tool_called":
        tool = check["tool"]
        passed = any(call.get("name") == tool for call in tool_calls)
        detail = f"tool {tool!r} was called" if passed else f"tool {tool!r} was not called"
    elif check_type == "tool_not_called":
        tool = check["tool"]
        passed = all(call.get("name") != tool for call in tool_calls)
        detail = f"tool {tool!r} was not called" if passed else f"tool {tool!r} was called"
    elif check_type == "required_tools_called":
        required_tools = requirements.get("required_tools", [])
        called_names = {call.get("name") for call in tool_calls}
        missing = [tool for tool in required_tools if tool not in called_names]
        passed = not missing
        detail = "all required tools were called" if passed else f"missing required tools: {', '.join(missing)}"
    elif check_type == "forbidden_tools_absent":
        forbidden_tools = requirements.get("forbidden_tools", [])
        called_names = {call.get("name") for call in tool_calls}
        found = [tool for tool in forbidden_tools if tool in called_names]
        passed = not found
        detail = "no forbidden tools were called" if passed else f"forbidden tools called: {', '.join(found)}"
    elif check_type == "required_steps_completed":
        required_steps = requirements.get("required_steps", [])
        completed = {step.get("name") for step in steps}
        missing = [step for step in required_steps if step not in completed]
        passed = not missing
        detail = "all required steps were completed" if passed else f"missing required steps: {', '.join(missing)}"
    elif check_type == "forbidden_actions_absent":
        forbidden_actions = requirements.get("forbidden_actions", [])
        response_lower = response.lower()
        found = [action for action in forbidden_actions if action.lower() in response_lower]
        passed = not found
        detail = "no forbidden actions proposed" if passed else f"forbidden actions found: {', '.join(found)}"
    elif check_type == "structured_equals":
        field = check["field"]
        expected = check["expected"]
        actual = structured.get(field)
        passed = actual == expected
        detail = f"expected {field}={expected!r}, actual={actual!r}"
    elif check_type == "structured_path_equals":
        path = check["path"]
        expected = check["expected"]
        actual = _get_nested(structured, path)
        passed = actual == expected
        detail = f"expected {path}={expected!r}, actual={actual!r}"
    elif check_type == "latency_under":
        max_ms = check["ms"]
        actual = result.get("latency_ms", 0)
        passed = actual <= max_ms
        detail = f"latency {actual}ms <= {max_ms}ms"
    elif check_type == "token_count_under":
        max_tokens = check["tokens"]
        usage = result.get("usage", {})
        actual = usage.get("total_tokens", 0)
        passed = actual <= max_tokens
        detail = f"tokens {actual} <= {max_tokens}"
    elif check_type == "custom":
        name = check["name"]
        handler = CUSTOM_CHECKS.get(name)
        if handler is None:
            raise ValueError(f"Unknown custom check: {name}")
        passed, detail = handler(bundle, result, check)
    else:
        raise ValueError(f"Unsupported check type: {check_type}")

    return {"name": check_type, "passed": passed, "detail": detail, "config": check}


def evaluate_invariants(invariants: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
    dummy_bundle = {"expected": {}}
    return [_evaluate_single_check({**invariant["config"], "type": invariant["check"]}, dummy_bundle, result) for invariant in invariants]


def evaluate_expectation_checks(
    checks: list[dict[str, Any]],
    bundle: dict[str, Any],
    result: dict[str, Any],
) -> list[dict[str, Any]]:
    return [_evaluate_single_check(check, bundle, result) for check in checks]

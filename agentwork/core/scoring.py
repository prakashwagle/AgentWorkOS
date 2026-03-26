from __future__ import annotations

import math
from statistics import mean
from typing import Any


def wilson_interval(successes: int, total: int, confidence: float) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    z_map = {0.8: 1.282, 0.9: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_map.get(round(confidence, 2), 1.96)
    rate = successes / total
    denominator = 1 + (z * z) / total
    centre = rate + (z * z) / (2 * total)
    interval = z * math.sqrt((rate * (1 - rate) + (z * z) / (4 * total)) / total)
    lower = max(0.0, (centre - interval) / denominator)
    upper = min(1.0, (centre + interval) / denominator)
    return lower, upper


def summarize_trials(trials: list[dict[str, Any]], thresholds: dict[str, Any]) -> dict[str, Any]:
    total = len(trials)
    passed_count = sum(1 for trial in trials if trial["passed"])
    safe_count = sum(1 for trial in trials if trial["invariant_passed"])
    latencies = [trial["latency_ms"] for trial in trials]
    costs = [trial.get("cost_usd", 0.0) for trial in trials]
    lower, upper = wilson_interval(passed_count, total, thresholds.get("confidence", 0.95))

    completion_rate = passed_count / total if total else 0.0
    safety_score = safe_count / total if total else 0.0
    mean_latency_ms = mean(latencies) if latencies else 0.0
    mean_cost_usd = mean(costs) if costs else 0.0

    reasons: list[str] = []
    if lower < thresholds["min_completion_rate"]:
        reasons.append(
            f"Completion lower bound {lower:.2f} below threshold {thresholds['min_completion_rate']:.2f}."
        )
    if safety_score < thresholds["min_safety_score"]:
        reasons.append(f"Safety score {safety_score:.2f} below threshold {thresholds['min_safety_score']:.2f}.")
    max_latency = thresholds.get("max_mean_latency_ms")
    if max_latency is not None and mean_latency_ms > max_latency:
        reasons.append(f"Mean latency {mean_latency_ms:.0f}ms above threshold {max_latency}ms.")
    max_cost = thresholds.get("max_mean_cost_usd")
    if max_cost is not None and mean_cost_usd > max_cost:
        reasons.append(f"Mean cost ${mean_cost_usd:.4f} above threshold ${max_cost:.4f}.")

    return {
        "completion_rate": completion_rate,
        "safety_score": safety_score,
        "utility_score": completion_rate,
        "mean_latency_ms": mean_latency_ms,
        "mean_cost_usd": mean_cost_usd,
        "confidence_interval": [lower, upper],
        "passed": not reasons,
        "reasons": reasons,
    }


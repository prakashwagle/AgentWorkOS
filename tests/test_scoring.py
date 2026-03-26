from __future__ import annotations

import unittest

from agentwork.core.scoring import summarize_trials


class ScoringTest(unittest.TestCase):
    def test_summary_passes_when_thresholds_are_met(self) -> None:
        trials = [
            {"passed": True, "invariant_passed": True, "latency_ms": 300, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 350, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 400, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 420, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 380, "cost_usd": 0.001},
        ]
        thresholds = {
            "min_completion_rate": 0.6,
            "min_safety_score": 1.0,
            "max_mean_latency_ms": 800,
            "confidence": 0.9,
        }
        summary = summarize_trials(trials, thresholds)
        self.assertTrue(summary["passed"])

    def test_summary_fails_when_completion_confidence_is_too_low(self) -> None:
        trials = [
            {"passed": True, "invariant_passed": True, "latency_ms": 300, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 320, "cost_usd": 0.001},
            {"passed": False, "invariant_passed": True, "latency_ms": 340, "cost_usd": 0.001},
            {"passed": False, "invariant_passed": True, "latency_ms": 360, "cost_usd": 0.001},
            {"passed": False, "invariant_passed": True, "latency_ms": 380, "cost_usd": 0.001},
        ]
        thresholds = {
            "min_completion_rate": 0.7,
            "min_safety_score": 1.0,
            "max_mean_latency_ms": 800,
            "confidence": 0.9,
        }
        summary = summarize_trials(trials, thresholds)
        self.assertFalse(summary["passed"])
        self.assertTrue(any("Completion lower bound" in reason for reason in summary["reasons"]))

    def test_summary_fails_when_safety_is_below_threshold(self) -> None:
        trials = [
            {"passed": True, "invariant_passed": True, "latency_ms": 300, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": False, "latency_ms": 320, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 340, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 360, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 380, "cost_usd": 0.001},
        ]
        thresholds = {
            "min_completion_rate": 0.7,
            "min_safety_score": 1.0,
            "max_mean_latency_ms": 800,
            "confidence": 0.9,
        }
        summary = summarize_trials(trials, thresholds)
        self.assertFalse(summary["passed"])
        self.assertTrue(any("Safety score" in reason for reason in summary["reasons"]))

    def test_summary_fails_when_latency_is_too_high(self) -> None:
        trials = [
            {"passed": True, "invariant_passed": True, "latency_ms": 900, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 950, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 920, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 910, "cost_usd": 0.001},
            {"passed": True, "invariant_passed": True, "latency_ms": 930, "cost_usd": 0.001},
        ]
        thresholds = {
            "min_completion_rate": 0.7,
            "min_safety_score": 1.0,
            "max_mean_latency_ms": 800,
            "confidence": 0.9,
        }
        summary = summarize_trials(trials, thresholds)
        self.assertFalse(summary["passed"])
        self.assertTrue(any("Mean latency" in reason for reason in summary["reasons"]))

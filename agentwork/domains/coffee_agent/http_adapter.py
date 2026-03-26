from __future__ import annotations

import json
import time
from typing import Any
from urllib import request


class CoffeeAgentHTTPAdapter:
    agent_id = "coffee-agent-http"
    agent_version = "0.1.0"

    def __init__(self, base_url: str = "http://127.0.0.1:8080") -> None:
        self.base_url = base_url.rstrip("/")

    def _get_json(self, path: str) -> dict[str, Any]:
        with request.urlopen(f"{self.base_url}{path}") as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps(payload or {}).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))

    def run(self, bundle: dict[str, Any]) -> dict[str, Any]:
        started_at = time.perf_counter()
        transcript: list[dict[str, Any]] = []
        steps: list[dict[str, Any]] = []

        start_payload = self._post_json("/session/start")
        session_id = start_payload["session_id"]
        transcript.append({"role": "agent", "payload": start_payload})
        steps.append({"name": "start_session", "status": "completed", "detail": session_id})

        messages = bundle.get("context", {}).get("messages", [])
        final_payload = start_payload
        for message in messages:
            final_payload = self._post_json(
                "/session/message",
                {"session_id": session_id, "message": message},
            )
            transcript.append({"role": "user", "message": message})
            transcript.append({"role": "agent", "payload": final_payload})
            steps.append({"name": "send_message", "status": "completed", "detail": message})

        latency_ms = int((time.perf_counter() - started_at) * 1000)
        return {
            "response": final_payload.get("reply", ""),
            "structured": final_payload,
            "tool_calls": [],
            "steps": steps,
            "usage": {},
            "latency_ms": latency_ms,
            "metadata": {
                "base_url": self.base_url,
                "session_id": session_id,
                "transcript": transcript,
            },
        }


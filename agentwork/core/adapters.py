from __future__ import annotations

from typing import Any, Protocol


class AgentAdapter(Protocol):
    agent_id: str
    agent_version: str

    def run(self, bundle: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent for a single scenario bundle."""


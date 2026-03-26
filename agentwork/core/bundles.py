from __future__ import annotations

from pathlib import Path
from typing import Any

from agentwork.core.contracts import load_document
from agentwork.core.validation import validate_bundles


def load_bundles(path: str | Path) -> list[dict[str, Any]]:
    document = load_document(path)
    if not isinstance(document, list):
        raise ValueError(f"Bundles at {path} must be a list.")
    validate_bundles(document)
    return document

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agentwork.core.validation import validate_contract


def load_document(path: str | Path) -> Any:
    raw = Path(path).read_text()
    try:
        import yaml  # type: ignore

        return yaml.safe_load(raw)
    except ModuleNotFoundError:
        return json.loads(raw)


def load_contract(path: str | Path) -> dict[str, Any]:
    document = load_document(path)
    if not isinstance(document, dict):
        raise ValueError(f"Contract at {path} must be a mapping.")
    validate_contract(document)
    return document

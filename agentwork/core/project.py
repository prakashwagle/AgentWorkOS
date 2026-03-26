from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


FRAMEWORK_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_ROOT = FRAMEWORK_ROOT / "examples"


def load_project_config(project_dir: str | Path) -> dict[str, Any]:
    config_path = Path(project_dir) / "agentwork.json"
    if not config_path.exists():
        raise ValueError(f"No agentwork.json found in project directory: {project_dir}")
    return json.loads(config_path.read_text())


def ensure_project_dir(path: str | Path) -> Path:
    project_dir = Path(path).resolve()
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def scaffold_project(target_dir: str | Path, template: str = "sre") -> Path:
    project_dir = ensure_project_dir(target_dir)
    template_dir = EXAMPLES_ROOT / template
    if not template_dir.exists():
        raise ValueError(f"Unknown template: {template}")

    (project_dir / "contracts").mkdir(exist_ok=True)
    (project_dir / "bundles").mkdir(exist_ok=True)
    (project_dir / ".agentwork").mkdir(exist_ok=True)

    for item in template_dir.rglob("*"):
        if item.is_dir():
            continue
        relative = item.relative_to(template_dir)
        destination = project_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            shutil.copyfile(item, destination)
    return project_dir


def resolve_project_paths(project_dir: str | Path, config: dict[str, Any], contract: str | None, bundles: str | None) -> tuple[Path, Path, Path]:
    base = Path(project_dir).resolve()
    contract_path = base / (contract or config["default_contract"])
    bundles_path = base / (bundles or config["default_bundles"])
    db_path = base / config.get("report_db", ".agentwork/agentwork.db")
    return contract_path, bundles_path, db_path

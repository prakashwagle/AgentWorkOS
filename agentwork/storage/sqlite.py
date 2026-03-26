from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(".agentwork") / "agentwork.db"


def connect(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                contract_id TEXT NOT NULL,
                contract_version TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                agent_version TEXT NOT NULL,
                phase TEXT NOT NULL,
                passed INTEGER NOT NULL,
                completion_rate REAL NOT NULL,
                safety_score REAL NOT NULL,
                mean_latency_ms REAL NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )


def save_run(report: dict[str, Any], db_path: str | Path = DEFAULT_DB_PATH) -> None:
    payload = json.dumps(report)
    score = report["score"]
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO runs (
                id, created_at, contract_id, contract_version, agent_id, agent_version,
                phase, passed, completion_rate, safety_score, mean_latency_ms, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report["id"],
                report["created_at"],
                report["contract_id"],
                report["contract_version"],
                report["agent_id"],
                report["agent_version"],
                report["phase"],
                1 if score["passed"] else 0,
                score["completion_rate"],
                score["safety_score"],
                score["mean_latency_ms"],
                payload,
            ),
        )


def list_runs(db_path: str | Path = DEFAULT_DB_PATH) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, contract_id, agent_id, agent_version, phase, passed,
                   completion_rate, safety_score, mean_latency_ms
            FROM runs
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_run(run_id: str, db_path: str | Path = DEFAULT_DB_PATH) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute("SELECT payload_json FROM runs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["payload_json"])


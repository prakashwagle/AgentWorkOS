from __future__ import annotations

from agentwork.storage.repository import DEFAULT_DB_PATH, get_run, init_db, list_runs


def register_run_routes(app) -> None:
    init_db(DEFAULT_DB_PATH)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/runs")
    def runs():
        return list_runs(DEFAULT_DB_PATH)

    @app.get("/runs/{run_id}")
    def run_detail(run_id: str):
        report = get_run(run_id, DEFAULT_DB_PATH)
        if report is None:
            return {"error": "not_found", "run_id": run_id}
        return report


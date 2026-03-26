from __future__ import annotations


def create_app():
    try:
        from fastapi import FastAPI
    except ModuleNotFoundError as exc:
        raise RuntimeError("FastAPI is optional and not installed. Install agentwork[full] to enable the API.") from exc

    from agentwork.api.routes_runs import register_run_routes

    app = FastAPI(title="Agent Work OS")
    register_run_routes(app)
    return app


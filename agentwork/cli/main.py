from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from agentwork.core.bundles import load_bundles
from agentwork.core.contracts import load_contract
from agentwork.core.project import load_project_config, resolve_project_paths, scaffold_project
from agentwork.core.runner import run_contract
from agentwork.domains.coffee_agent.http_adapter import CoffeeAgentHTTPAdapter
from agentwork.domains.sre_ops.mock_adapter import MockSREAdapter
from agentwork.storage.repository import get_run, init_db, list_runs, save_run


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = scaffold_project(args.path, template=args.template)
    config = load_project_config(project_dir)
    _, _, db_path = resolve_project_paths(project_dir, config, None, None)
    init_db(db_path)
    print(f"Initialized agentwork project at {project_dir}")
    print(f"Template: {args.template}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config_data = load_project_config(args.project_dir)
    contract_path, bundles_path, db_path = resolve_project_paths(
        args.project_dir,
        config_data,
        args.contract,
        args.bundles,
    )
    init_db(db_path)
    contract = load_contract(contract_path)
    bundles = load_bundles(bundles_path)
    adapter_name = args.adapter or config_data.get("default_adapter", "mock_sre")
    base_url = args.base_url or config_data.get("adapter_config", {}).get("base_url", "http://127.0.0.1:8080")
    if adapter_name == "coffee_http":
        adapter = CoffeeAgentHTTPAdapter(base_url=base_url)
    else:
        adapter = MockSREAdapter()
    run_config = {
        "phase": "design",
        "trials": args.trials,
        "expectation_ids": [args.only] if args.only else None,
    }
    report = run_contract(contract, bundles, adapter, run_config)
    save_run(report, db_path)
    score = report["score"]
    print(f"Run: {report['id']}")
    print(f"Contract: {report['contract_id']} v{report['contract_version']}")
    print(f"Agent: {report['agent_id']} v{report['agent_version']}")
    print(f"Completion: {score['completion_rate']:.2f}  Safety: {score['safety_score']:.2f}")
    print(f"Latency: {score['mean_latency_ms']:.0f}ms  Passed: {'yes' if score['passed'] else 'no'}")
    if score["reasons"]:
        print("Reasons:")
        for reason in score["reasons"]:
            print(f"- {reason}")
    return 0


def cmd_report_list(args: argparse.Namespace) -> int:
    config_data = load_project_config(args.project_dir)
    _, _, db_path = resolve_project_paths(args.project_dir, config_data, None, None)
    init_db(db_path)
    rows = list_runs(db_path)
    if not rows:
        print("No runs found.")
        return 0
    for row in rows:
        print(
            f"{row['id']}  phase={row['phase']}  passed={'yes' if row['passed'] else 'no'}  "
            f"completion={row['completion_rate']:.2f}  safety={row['safety_score']:.2f}  "
            f"latency={row['mean_latency_ms']:.0f}ms"
        )
    return 0


def cmd_report_show(args: argparse.Namespace) -> int:
    config_data = load_project_config(args.project_dir)
    _, _, db_path = resolve_project_paths(args.project_dir, config_data, None, None)
    init_db(db_path)
    report = get_run(args.run_id, db_path)
    if report is None:
        print(f"Run {args.run_id} not found.")
        return 1
    print(json.dumps(report, indent=2))
    return 0


def cmd_bundles_import(args: argparse.Namespace) -> int:
    source = Path(args.source)
    if not source.exists():
        print(f"Bundle source {source} not found.")
        return 1
    destination = Path(args.project_dir) / args.output
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    print(f"Imported bundles to {destination}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentwork")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("path")
    init_parser.add_argument("--template", choices=["sre", "coffee-agent"], default="sre")
    init_parser.set_defaults(func=cmd_init)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--project-dir", default=".")
    run_parser.add_argument("--contract", default=None)
    run_parser.add_argument("--bundles", default=None)
    run_parser.add_argument("--only", default=None)
    run_parser.add_argument("--trials", type=int, default=5)
    run_parser.add_argument("--adapter", choices=["mock_sre", "coffee_http"], default=None)
    run_parser.add_argument("--base-url", default=None)
    run_parser.set_defaults(func=cmd_run)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--project-dir", default=".")
    report_subparsers = report_parser.add_subparsers(dest="report_command", required=True)

    report_list_parser = report_subparsers.add_parser("list")
    report_list_parser.set_defaults(func=cmd_report_list)

    report_show_parser = report_subparsers.add_parser("show")
    report_show_parser.add_argument("run_id")
    report_show_parser.set_defaults(func=cmd_report_show)

    bundles_parser = subparsers.add_parser("bundles")
    bundles_parser.add_argument("--project-dir", default=".")
    bundles_subparsers = bundles_parser.add_subparsers(dest="bundles_command", required=True)
    bundles_import_parser = bundles_subparsers.add_parser("import")
    bundles_import_parser.add_argument("source")
    bundles_import_parser.add_argument("--output", default="bundles/imported.yaml")
    bundles_import_parser.set_defaults(func=cmd_bundles_import)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run the packaged demo PDFs through ADP and write results to Lark Base.

Use this after init_lark_workspace.py has created the Base and updated
config.json. Default mode calls ADP for each bundled PDF, then writes the
recognized order records to Base.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SCENARIOS = {
    "cn-pass": {
        "source": "LYCN-PO-202606-001_BlueOcean_MFG.pdf",
    },
    "vn-mixed": {
        "source": "LYVN-PO-202606-018_SaoViet_Electronics.pdf",
    },
    "th-new-customer": {
        "source": "TH-NW-2026-0620_NewWave_Automation.pdf",
    },
    "de-price-issue": {
        "source": "LYDE-PO-202606-019_Rheinwerk_Robotics_GmbH.pdf",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bundled demo orders")
    parser.add_argument("--config", type=Path, default=Path("config.json"))
    parser.add_argument("--scenario", choices=["all", *SCENARIOS.keys()], default="all")
    parser.add_argument("--parallel", action="store_true", help="并发调用 ADP 处理多个 demo 场景")
    parser.add_argument("--max-workers", type=int, default=5, help="并发处理 demo 场景的最大数量，默认 5")
    return parser.parse_args()


def run_scenario(skill_dir: Path, config_path: Path, scenario: str, args: argparse.Namespace) -> int:
    spec = SCENARIOS[scenario]
    source_file = skill_dir / "demo-data" / "orders" / spec["source"]
    script = skill_dir / "scripts" / "run_order_audit.py"

    command = [
        sys.executable,
        str(script),
        str(source_file),
        "--config",
        str(config_path),
        "--update-existing",
    ]
    print(f"\n=== demo scenario: {scenario} ===")
    return subprocess.call(command)


def locate_command(command: str) -> str | None:
    found = shutil.which(command)
    if found:
        return found
    path = Path(command).expanduser()
    if path.exists():
        return str(path)
    for candidate in (
        Path.home() / ".npm-global/bin" / command,
        Path("/usr/local/bin") / command,
        Path("/opt/homebrew/bin") / command,
    ):
        if candidate.exists():
            return str(candidate)
    return None


def command_exists(command: str) -> bool:
    return locate_command(command) is not None


def is_placeholder(value: object) -> bool:
    text = str(value or "").strip()
    return not text or (text.startswith("<") and text.endswith(">"))


def base_config_incomplete(config_path: Path) -> bool:
    if not config_path.exists():
        return True
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return True
    return any(
        is_placeholder(data.get(key))
        for key in ("base_token", "audit_table_id", "code_table_id", "history_table_id")
    )


def initialize_workspace(skill_dir: Path, config_path: Path) -> int:
    script = skill_dir / "scripts" / "init_lark_workspace.py"
    command = [sys.executable, str(script), "--config", str(config_path)]
    print("[demo] Base/table config is incomplete. Initializing workspace before demo concurrency.")
    return subprocess.call(command)


def resolve_adp_cli(command: str) -> str:
    for candidate in (command, "adp", "adp-cli"):
        if candidate:
            found = locate_command(candidate)
            if found:
                return found
    return command or "adp"


def main() -> int:
    args = parse_args()
    skill_dir = Path(__file__).resolve().parents[1]
    config_path = skill_dir / "config.json" if args.config == Path("config.json") else args.config
    api_base_url = "https://adp.laiye.com"
    api_key_env = "ADP_API_KEY"
    api_key = ""
    adp_provider = "auto"
    adp_cli = "adp"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            api_base_url = str(config.get("adp_api_base_url") or api_base_url).rstrip("/")
            api_key_env = str(config.get("adp_api_key_env") or api_key_env)
            api_key = str(config.get("adp_api_key") or os.environ.get(api_key_env, "")).strip()
            adp_provider = str(config.get("adp_provider") or adp_provider).strip().lower()
            adp_cli = str(config.get("adp_cli") or adp_cli)
        except json.JSONDecodeError:
            api_key = os.environ.get(api_key_env, "").strip()
    else:
        api_key = os.environ.get(api_key_env, "").strip()

    if adp_provider not in {"auto", "api", "cli"}:
        adp_provider = "auto"
    resolved_cli = resolve_adp_cli(adp_cli)
    cli_available = command_exists(resolved_cli)
    if adp_provider in {"auto", "cli"} and cli_available:
        pass
    elif adp_provider == "api" and not api_key and cli_available:
        pass
    elif adp_provider in {"auto", "api"} and api_key:
        pass
    elif adp_provider == "cli":
        print(
            "ADP CLI is missing. Install it with: npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli. "
            "After installation, make sure the `adp` command is available in PATH.",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            "ADP runtime is missing. Preferred setup: install ADP CLI with "
            "npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli. "
            f"Fallback setup: open {api_base_url}/, get API Key from personal center, then run: "
            f"export {api_key_env}='<YOUR_ADP_API_KEY>'.",
            file=sys.stderr,
        )
        return 1

    scenarios = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    if base_config_incomplete(config_path):
        init_status = initialize_workspace(skill_dir, config_path)
        if init_status:
            return init_status

    if args.parallel and len(scenarios) > 1:
        workers = max(1, min(args.max_workers, len(scenarios)))
        print(f"[demo] parallel mode enabled: {workers} workers for {len(scenarios)} scenarios")
        status = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(run_scenario, skill_dir, config_path, scenario, args): scenario
                for scenario in scenarios
            }
            for future in as_completed(futures):
                scenario = futures[future]
                try:
                    code = future.result()
                except Exception as exc:
                    print(f"[demo] scenario failed: {scenario}: {exc!r}", file=sys.stderr)
                    code = 1
                status = code or status
        return status

    status = 0
    for scenario in scenarios:
        status = run_scenario(skill_dir, config_path, scenario, args) or status

    return status


if __name__ == "__main__":
    raise SystemExit(main())

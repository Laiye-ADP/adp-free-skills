#!/usr/bin/env python3
"""First-run environment check for the order-auto-entry skill.

The goal is diagnosis, not repair. In particular, do not create a new Lark app
until the existing CLI installation and current agent runtime have been checked.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header() -> None:
    print(f"\n{BLUE}{'=' * 58}{RESET}")
    print(f"{BLUE}  订单自动化 Skill 环境检测{RESET}")
    print(f"{BLUE}{'=' * 58}{RESET}\n")


def locate_command(cmd: str) -> str | None:
    found = shutil.which(cmd)
    if found:
        return found
    for candidate in (
        Path.home() / ".npm-global/bin" / cmd,
        Path("/usr/local/bin") / cmd,
        Path("/opt/homebrew/bin") / cmd,
    ):
        if candidate.exists():
            return str(candidate)
    return None


def run_command(args: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"command not found: {args[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"


def one_line(text: str, limit: int = 220) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:limit] + ("..." if len(cleaned) > limit else "")


def check_adp_access() -> bool:
    print(f"\n{YELLOW}[1/5] 检查 ADP 识别能力（CLI 优先）{RESET}")
    skill_dir = Path(__file__).resolve().parents[1]
    config_path = skill_dir / "config.json"
    api_base_url = "https://adp.laiye.com"
    api_key_env = "ADP_API_KEY"
    adp_provider = "auto"
    adp_cli_name = "adp"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            api_base_url = str(config.get("adp_api_base_url") or api_base_url).rstrip("/")
            api_key_env = str(config.get("adp_api_key_env") or api_key_env)
            adp_provider = str(config.get("adp_provider") or adp_provider).lower()
            adp_cli_name = str(config.get("adp_cli") or adp_cli_name)
        except json.JSONDecodeError:
            print(f"  {YELLOW}⚠ config.json 不是合法 JSON，先按默认 ADP CLI 配置检查{RESET}")

    api_key = os.environ.get(api_key_env, "").strip()
    cli_path = locate_command(adp_cli_name) or locate_command("adp") or locate_command("adp-cli")

    if adp_provider in {"auto", "cli"} and cli_path:
        print(f"  {GREEN}✓ ADP CLI 已安装{RESET}: {cli_path}")
        ret, stdout, stderr = run_command([cli_path, "--version"])
        if ret != 0:
            ret, stdout, stderr = run_command([cli_path, "version"])
        if ret == 0 and stdout:
            print(f"    版本: {one_line(stdout)}")
        else:
            ret, stdout, stderr = run_command([cli_path, "--help"])
            if ret == 0:
                print("    命令可执行: 已通过 --help smoke test")
        print("    当前 Skill 会优先使用 ADP CLI，不会再要求 ADP_API_KEY。")
        return True

    if adp_provider == "api" and not api_key and cli_path:
        print(f"  {GREEN}✓ ADP CLI 已安装{RESET}: {cli_path}")
        print("    当前 config 写的是 api 且未配置 API Key；运行脚本会自动回退到本机 ADP CLI。")
        print("    建议把 config.json 中 adp_provider 改为 auto，避免后续误解。")
        return True

    if adp_provider == "api" or (adp_provider == "auto" and api_key):
        print(f"  ADP API 地址: {api_base_url}")
        print("  默认应用: e7ae987c67c211f1b89200505687d9c5")
        if api_key:
            print(f"  {GREEN}✓ 已配置 API Key{RESET}: 环境变量 {api_key_env}")
            return True

    print(f"  {RED}✗ 未找到可用 ADP CLI{RESET}")
    print("    推荐安装：npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli")
    print("    安装后确认命令可用：adp --help")
    print(f"    备用方式：打开 {api_base_url}/ 获取 API Key 后执行 export {api_key_env}=<YOUR_ADP_API_KEY>")
    return False


def check_lark_cli() -> bool:
    print(f"\n{YELLOW}[2/5] 检查 Lark CLI / 飞书 CLI{RESET}")
    lark_cli = locate_command("lark-cli")
    global_config = Path.home() / ".lark-cli/config.json"
    hermes_home = os.environ.get("HERMES_HOME")

    if not lark_cli:
        print(f"  {RED}✗ 未安装 lark-cli{RESET}")
        print("    新用户路径: 先安装 @larksuite/cli，再运行 lark-cli config init。")
        print("    已有飞书 CLI 的用户: 确认 lark-cli 在 PATH 中可见。")
        return False

    print(f"  {GREEN}✓ 已安装{RESET}: {lark_cli}")
    ret, stdout, stderr = run_command([lark_cli, "--version"])
    if ret == 0 and stdout:
        print(f"    版本: {one_line(stdout)}")

    if hermes_home:
        print(f"    当前智能体环境: HERMES_HOME={hermes_home}")
        print("    注意: 这可能与用户终端里的 ~/.lark-cli 配置隔离。")

    if global_config.exists():
        print(f"    用户本机配置: {global_config} 存在")
    else:
        print(f"    用户本机配置: {YELLOW}未发现 ~/.lark-cli/config.json{RESET}")

    ret, stdout, stderr = run_command([lark_cli, "config", "show"])
    if ret == 0:
        print(f"    当前环境配置: {GREEN}可读取{RESET}")
    else:
        print(f"    当前环境配置: {RED}不可读取{RESET}")
        if global_config.exists() and hermes_home:
            print("    判断: 用户可能已有 lark-cli，但当前智能体运行环境未绑定。")
            print("    处理: 优先使用 lark-cli config bind 或当前平台的绑定流程；不要直接创建新应用。")
        else:
            print("    处理: 新用户才走 lark-cli config init；已有应用则使用 app-id/app-secret 初始化。")
        if stderr:
            print(f"    诊断: {one_line(stderr)}")
        return False

    ret, stdout, stderr = run_command([lark_cli, "auth", "status"])
    if ret == 0:
        print(f"    授权状态: {GREEN}已就绪或部分就绪{RESET}")
        if stdout:
            print(f"    摘要: {one_line(stdout)}")
    else:
        print(f"    授权状态: {YELLOW}未完成用户授权{RESET}")
        print("    Base/IM 可用 bot 身份；读取飞书邮箱需要 user 身份授权。")
        if stderr:
            print(f"    诊断: {one_line(stderr)}")
        return False

    ret, stdout, stderr = run_command([lark_cli, "auth", "list"])
    if ret == 0:
        print(f"    用户身份: {GREEN}可枚举{RESET}")
    else:
        print(f"    用户身份: {YELLOW}未确认{RESET}")
        print("    如果要读取飞书邮箱，请补 user 授权；只处理本地订单可先跳过邮箱授权。")

    return True


def check_python() -> bool:
    print(f"\n{YELLOW}[3/5] 检查 Python{RESET}")
    python = locate_command("python3")
    if not python:
        print(f"  {RED}✗ 未安装 Python 3{RESET}")
        return False
    ret, stdout, _ = run_command([python, "--version"])
    print(f"  {GREEN}✓ 已安装{RESET}: {one_line(stdout) if stdout else python}")
    return True


def check_local_demo_assets() -> bool:
    print(f"\n{YELLOW}[4/5] 检查本地 demo 文件和工作目录{RESET}")
    skill_dir = Path(__file__).resolve().parents[1]
    expected_files = [
        "LYCN-PO-202606-001_BlueOcean_MFG.pdf",
        "LYVN-PO-202606-018_SaoViet_Electronics.pdf",
        "TH-NW-2026-0620_NewWave_Automation.pdf",
        "LYDE-PO-202606-019_Rheinwerk_Robotics_GmbH.pdf",
    ]
    orders_dir = skill_dir / "demo-data" / "orders"
    missing = [name for name in expected_files if not (orders_dir / name).exists()]
    if missing:
        print(f"  {RED}✗ demo PDF 不完整{RESET}: {', '.join(missing)}")
        return False

    work_dir = skill_dir / "work" / "setup-check"
    try:
        work_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=work_dir, delete=False) as handle:
            handle.write("ok")
            temp_path = Path(handle.name)
        ok = temp_path.read_text(encoding="utf-8") == "ok"
        temp_path.unlink(missing_ok=True)
    except OSError as exc:
        print(f"  {RED}✗ work 目录不可写{RESET}: {exc}")
        return False

    if not ok:
        print(f"  {RED}✗ work 目录读写校验失败{RESET}")
        return False
    print(f"  {GREEN}✓ demo 文件完整，work 目录可读写{RESET}")
    print(f"    demo PDF: {orders_dir}")
    print(f"    工作目录: {skill_dir / 'work'}")
    return True


def check_mail_smoke_test() -> bool:
    print(f"\n{YELLOW}[5/5] 检查飞书邮箱读取能力{RESET}")
    lark_cli = locate_command("lark-cli")
    if not lark_cli:
        print(f"  {YELLOW}⚠ 跳过：未找到 lark-cli{RESET}")
        return False

    filter_json = json.dumps({"folder": "inbox", "has_attachment": True}, ensure_ascii=False)
    ret, stdout, stderr = run_command(
        [
            lark_cli,
            "mail",
            "+triage",
            "--as",
            "user",
            "--filter",
            filter_json,
            "--max",
            "1",
            "--format",
            "json",
        ],
        timeout=30,
    )
    if ret == 0:
        print(f"  {GREEN}✓ 邮箱入口可用{RESET}")
        print("    可读取收件箱附件邮件；正式运行会把附件下载到 work/mail-order-attachments/ 后处理。")
        return True

    print(f"  {YELLOW}⚠ 邮箱入口不可用或未授权{RESET}")
    print("    本地订单入口仍可使用；邮箱入口需要 user 身份和 mail:user_mailbox.message:readonly 等权限。")
    if stderr:
        print(f"    诊断: {one_line(stderr)}")
    elif stdout:
        print(f"    诊断: {one_line(stdout)}")
    return False


def print_summary(results: dict[str, bool]) -> None:
    print(f"\n{BLUE}{'=' * 58}{RESET}")
    print(f"{BLUE}  检测结论{RESET}")
    print(f"{BLUE}{'=' * 58}{RESET}\n")
    for name, passed in results.items():
        status = f"{GREEN}✓{RESET}" if passed else f"{RED}✗{RESET}"
        print(f"  {status} {name}")

    print()
    if all(results.values()):
        print(f"{GREEN}✅ 基础环境可用。下一步检查 config.json 或运行 init_lark_workspace.py。{RESET}")
    else:
        print(f"{YELLOW}⚠ 先按上方诊断补齐环境，不要跳过到真实订单处理。{RESET}")
        print("  判断规则:")
        print("  - ADP 未通过: 优先安装 npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli；备用方式才设置 ADP_API_KEY。")
        print("  - 没有 lark-cli: 先安装。")
        print("  - 有 lark-cli 但当前智能体读不到配置: 先绑定/迁移当前运行环境。")
        print("  - Bot 可用但 User 未授权: 本地订单可跑；邮箱入口暂不能跑。")
        print("  - 本地 demo 文件不完整: 重新解压分享包，不要复用旧目录。")
        print("  - 邮箱 smoke test 失败: 本地订单可跑；邮箱入口需要补 user 授权或邮箱权限。")
        print("  - config.json 仍是占位符: 先填现有 Base/审核负责人，或运行初始化脚本创建。")
    print()


def main() -> int:
    print_header()
    results = {
        "ADP 识别能力": check_adp_access(),
        "Lark CLI": check_lark_cli(),
        "Python": check_python(),
        "本地 demo / work 目录": check_local_demo_assets(),
        "飞书邮箱入口": check_mail_smoke_test(),
    }
    print_summary(results)
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

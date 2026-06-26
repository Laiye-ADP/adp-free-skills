#!/usr/bin/env python3
"""ADP x Lark procurement order audit Agent.

This is the roadshow-safe version of the original order-auto-entry Skill:
ADP extracts purchase orders, this script writes one Lark Base record per item
line, and Lark Base formulas calculate the audit result. The script precheck is
only a fallback before formula readback, so the Base view and reviewer card stay
consistent.

The normal path always calls ADP, writes Lark Base, uploads the source file, and
sends the reviewer notification when configured.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


DEFAULT_ADP_APP_ID = "e7ae987c67c211f1b89200505687d9c5"
DEFAULT_ADP_PROVIDER = "auto"
DEFAULT_ADP_API_BASE_URL = "https://adp.laiye.com"
DEFAULT_ADP_API_KEY_ENV = "ADP_API_KEY"
DEFAULT_ADP_CLI = "adp"
DEFAULT_BASE_TOKEN = ""
DEFAULT_AUDIT_TABLE_ID = ""
DEFAULT_CODE_TABLE_ID = ""
DEFAULT_HISTORY_TABLE_ID = ""
DEFAULT_CHAT_ID = ""
DEFAULT_REVIEWER_USER_ID = ""
ADP_META_KEY = "_adp_meta"
ADP_TABLE_CONFIDENCE_KEY = "_adp_table_confidence"
LOW_CONFIDENCE_THRESHOLD = 0.95
ORDER_ATTACHMENT_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
REVIEWER_FIELD_NAME = "审核负责人"
CURRENT_USER_PLACEHOLDER = "<CURRENT_USER_OPEN_ID>"
ORDER_TOTAL_FIELDS = ["订单总金额", "总金额", "订单金额", "合计金额", "价税合计", "含税总额", "Total Amount", "total_amount", "amount"]
LINE_TOTAL_FIELDS = ["总金额（含税）", "含税金额", "金额", "总价", "小计", "价税合计", "Amount", "amount"]
UNIT_PRICE_FIELDS = ["单价（含税）", "含税单价", "单价", "未税单价", "价格", "含税价", "Unit Price", "Unit price", "U/P", "Price", "unit_price"]
QUANTITY_FIELDS = ["数量", "订购数量", "采购数量", "Qty", "qty", "Quantity"]
MATERIAL_FIELDS = ["厂家型号", "物料代码", "料件编号", "物料编码", "型号", "规格型号", "客户订单商品号", "material_code", "part_no"]
DESCRIPTION_FIELDS = ["描述", "品名/规格", "商品描述", "物料名称", "商品名称/规格", "Description", "name"]
DELIVERY_DATE_FIELDS = ["交货日期", "到货日期", "交期", "需求日期", "delivery_date"]
BUYER_ADDRESS_FIELDS = [
    "买方/客户地址",
    "买方地址",
    "客户地址",
    "采购方地址",
    "买方/客户详细地址",
    "客户详细地址",
    "Buyer Address",
    "Purchaser Address",
    "Customer Address",
    "Bill To",
    "buyer_address",
    "customer_address",
]
CONSIGNEE_FIELDS = [
    "收货方名称",
    "收货方",
    "收货人",
    "收货单位",
    "收货公司",
    "收件方",
    "Ship To Name",
    "Deliver To",
    "Delivery To",
    "consignee",
]
SHIPPING_ADDRESS_FIELDS = [
    "客户收货地址",
    "收货地址",
    "收货方地址",
    "送货地址",
    "交货地址",
    "收件地址",
    "送达地址",
    "Delivery Address",
    "Shipping Address",
    "Ship To",
    "Ship-to Address",
    "address",
]
FORMULA_FIELD_NAMES = {
    "审核状态",
    "审核说明",
    "来也 SKU",
    "标准售价 USD",
    "报价有效期",
    "上次成交价USD",
    "客户历史订单数",
    "价差百分比",
}

FIELD_ALIASES = {
    "客户订单商品号": ["客户订单商品号", "物料代码", "客户物料代码", "物料编码"],
    "商品名称/规格": ["商品名称/规格", "描述", "产品描述", "商品描述", "物料名称"],
    "来也 SKU": ["来也 SKU", "来也编码"],
    "标准售价 USD": ["标准售价 USD", "标准单价USD"],
    "报价有效期": ["报价有效期", "价格有效期"],
}


def first_present(row: dict[str, Any], field: str, default: Any = "") -> Any:
    for name in FIELD_ALIASES.get(field, [field]):
        value = row.get(name)
        if value not in (None, ""):
            return value
    return default
@dataclass
class Config:
    adp_app_id: str = DEFAULT_ADP_APP_ID
    adp_provider: str = DEFAULT_ADP_PROVIDER
    adp_api_base_url: str = DEFAULT_ADP_API_BASE_URL
    adp_api_key_env: str = DEFAULT_ADP_API_KEY_ENV
    adp_api_key: str = ""
    base_token: str = DEFAULT_BASE_TOKEN
    audit_table_id: str = DEFAULT_AUDIT_TABLE_ID
    code_table_id: str = DEFAULT_CODE_TABLE_ID
    history_table_id: str = DEFAULT_HISTORY_TABLE_ID
    chat_id: str = DEFAULT_CHAT_ID
    reviewer_user_id: str = DEFAULT_REVIEWER_USER_ID
    lark_identity: str = "user"
    notify_identity: str = "bot"
    adp_cli: str = DEFAULT_ADP_CLI
    lark_cli: str = "lark-cli"
    notify_on_success: bool = True
    skip_duplicates: bool = False
    dedupe_field: str = "明细唯一键"
    attachment_field: str = "订单源文件"
    upload_source_file: bool = True
    mail_identity: str = "user"
    mailbox: str = "me"
    price_variance_threshold: float = 0.2


def is_placeholder(value: str | None) -> bool:
    text = str(value or "").strip()
    return not text or (text.startswith("<") and text.endswith(">"))


def validate_config_for_execute(config: Config, args: argparse.Namespace) -> None:
    missing: list[str] = []
    if not args.from_adp_json and is_placeholder(config.adp_app_id):
        missing.append("adp_app_id")
    if not args.from_adp_json and config.adp_provider == "api" and not config.adp_api_key:
        missing.append(config.adp_api_key_env)
    if is_placeholder(config.base_token):
        missing.append("base_token")
    if is_placeholder(config.audit_table_id):
        missing.append("audit_table_id")
    if missing:
        raise SystemExit(
            "config.json is not ready to run. Missing or placeholder values: "
            + ", ".join(missing)
            + ". Base/table placeholders are auto-initialized when possible. "
            + "For ADP CLI mode, install with: npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli. "
            + f"For ADP API fallback, register or sign in at {config.adp_api_base_url}/, get your API Key from personal center, then run: export {config.adp_api_key_env}='<YOUR_ADP_API_KEY>'."
        )


def nested_get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def load_config(path: Path | None) -> Config:
    if not path or not path.exists():
        return Config()

    data = json.loads(path.read_text(encoding="utf-8"))
    explicit_audit_table_id = (
        data.get("audit_table_id")
        or nested_get(data, ["feishu", "audit_table_id"])
        or nested_get(data, ["feishu", "tables", "audit", "id"])
    )
    base_token = data.get("base_token") or nested_get(data, ["feishu", "base_token"], DEFAULT_BASE_TOKEN)
    if not explicit_audit_table_id:
        base_token = DEFAULT_BASE_TOKEN

    configured_adp_app_id = data.get("adp_app_id") or nested_get(data, ["adp", "app_id"], DEFAULT_ADP_APP_ID)
    if is_placeholder(configured_adp_app_id):
        configured_adp_app_id = DEFAULT_ADP_APP_ID
    adp_provider = str(data.get("adp_provider") or nested_get(data, ["adp", "provider"], DEFAULT_ADP_PROVIDER)).strip().lower()
    if adp_provider not in {"auto", "api", "cli"}:
        adp_provider = DEFAULT_ADP_PROVIDER
    adp_api_base_url = str(
        data.get("adp_api_base_url") or nested_get(data, ["adp", "api_base_url"], DEFAULT_ADP_API_BASE_URL)
    ).rstrip("/")
    adp_api_key_env = str(data.get("adp_api_key_env") or nested_get(data, ["adp", "api_key_env"], DEFAULT_ADP_API_KEY_ENV))
    adp_api_key = str(data.get("adp_api_key") or os.environ.get(adp_api_key_env, "")).strip()

    return Config(
        adp_app_id=configured_adp_app_id,
        adp_provider=adp_provider,
        adp_api_base_url=adp_api_base_url,
        adp_api_key_env=adp_api_key_env,
        adp_api_key=adp_api_key,
        base_token=base_token,
        audit_table_id=explicit_audit_table_id or DEFAULT_AUDIT_TABLE_ID,
        code_table_id=data.get("code_table_id") or nested_get(data, ["feishu", "code_table_id"], DEFAULT_CODE_TABLE_ID),
        history_table_id=data.get("history_table_id") or nested_get(data, ["feishu", "history_table_id"], DEFAULT_HISTORY_TABLE_ID),
        chat_id=data.get("chat_id") or nested_get(data, ["feishu", "chat_id"], DEFAULT_CHAT_ID),
        reviewer_user_id=(
            data.get("reviewer_user_id")
            or nested_get(data, ["reviewer", "user_id"])
            or nested_get(data, ["feishu", "reviewer_user_id"], DEFAULT_REVIEWER_USER_ID)
        ),
        lark_identity=data.get("lark_identity", "user"),
        notify_identity=(
            data.get("notify_identity")
            or nested_get(data, ["settings", "notify_identity"])
            or nested_get(data, ["feishu", "notify_identity"], "bot")
        ),
        adp_cli=data.get("adp_cli", DEFAULT_ADP_CLI),
        lark_cli=data.get("lark_cli", "lark-cli"),
        notify_on_success=bool(nested_get(data, ["settings", "notify_on_success"], data.get("notify_on_success", True))),
        skip_duplicates=bool(nested_get(data, ["settings", "skip_duplicates"], data.get("skip_duplicates", False))),
        dedupe_field=data.get("dedupe_field", "明细唯一键"),
        attachment_field=data.get("attachment_field") or nested_get(data, ["feishu", "attachment_field"], "订单源文件"),
        upload_source_file=bool(nested_get(data, ["settings", "upload_source_file"], data.get("upload_source_file", True))),
        mail_identity=data.get("mail_identity") or nested_get(data, ["mail", "identity"], "user"),
        mailbox=data.get("mailbox") or nested_get(data, ["mail", "mailbox"], "me"),
        price_variance_threshold=to_number(
            nested_get(data, ["settings", "price_variance_threshold"], data.get("price_variance_threshold", 0.2)),
            0.2,
        ),
    )


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


def resolve_adp_cli(command: str) -> str:
    for candidate in (command, DEFAULT_ADP_CLI, "adp-cli"):
        if candidate:
            found = locate_command(candidate)
            if found:
                return found
    return command or DEFAULT_ADP_CLI


def printable_command(args: list[str]) -> str:
    return " ".join(json.dumps(part, ensure_ascii=False) if any(ch.isspace() for ch in part) else part for part in args)


def run_command(args: list[str], *, dry_run: bool) -> subprocess.CompletedProcess[str] | None:
    if dry_run:
        raise RuntimeError("Non-execution mode is disabled for this skill.")

    print(f"[run] {printable_command(args)}")
    try:
        return subprocess.run(args, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, file=sys.stderr)
        if error.stderr:
            print(error.stderr, file=sys.stderr)
        raise


def base_config_incomplete(config: Config) -> bool:
    """Return True when Lark Base resources still need first-run initialization."""
    return any(
        is_placeholder(value)
        for value in (
            config.base_token,
            config.audit_table_id,
            config.code_table_id,
            config.history_table_id,
        )
    )


def ensure_adp_available(config: Config, args: argparse.Namespace) -> None:
    if args.from_adp_json is not None:
        return

    if config.adp_provider in {"auto", "cli"}:
        cli = resolve_adp_cli(config.adp_cli)
        if command_exists(cli):
            config.adp_provider = "cli"
            config.adp_cli = cli
            return
        if config.adp_provider == "cli":
            raise SystemExit(
                "ADP CLI is missing. Install it with: "
                "npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli. "
                "After installation, make sure the `adp` command is available in PATH."
            )

    if config.adp_provider in {"auto", "api"} and config.adp_api_key:
        config.adp_provider = "api"
        return

    if config.adp_provider == "auto":
        raise SystemExit(
            "ADP runtime is missing. Preferred setup: install ADP CLI with "
            "npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli, then rerun this command. "
            f"Fallback setup: open {config.adp_api_base_url}/, get API Key from personal center, then run: "
            f"export {config.adp_api_key_env}='<YOUR_ADP_API_KEY>'."
        )

    if config.adp_provider == "api" and not config.adp_api_key:
        cli = resolve_adp_cli(config.adp_cli)
        if command_exists(cli):
            print(
                f"[adp] config requests API mode but {config.adp_api_key_env} is missing; "
                f"falling back to local ADP CLI: {cli}",
                file=sys.stderr,
            )
            config.adp_provider = "cli"
            config.adp_cli = cli
            return
        raise SystemExit(
            f"ADP API Key is missing. Open {config.adp_api_base_url}/, register or sign in, "
            f"get the API Key from personal center, then run: export {config.adp_api_key_env}='<YOUR_ADP_API_KEY>'. "
            "Or change adp_provider to auto/cli and install ADP CLI with: "
            "npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli."
        )


def auto_init_lark_workspace(config_path: Path) -> Config:
    """Create the default Lark workspace and reload config for end-to-end first runs."""
    script = Path(__file__).resolve().with_name("init_lark_workspace.py")
    command = [sys.executable, str(script), "--config", str(config_path)]
    print(
        "[auto-init] Base/table config is incomplete. Initializing Lark workspace first; expected time: 1-3 minutes.",
        file=sys.stderr,
    )
    print(f"[auto-init] {printable_command(command)}", file=sys.stderr)
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Lark workspace initialization failed. Fix lark-cli authorization or rerun "
            "scripts/init_lark_workspace.py --config config.json, then retry the order run."
        )

    reloaded = load_config(config_path if config_path.exists() else None)
    if base_config_incomplete(reloaded):
        raise SystemExit(
            "Lark workspace initialization finished but config.json still lacks Base/table IDs. "
            "Check init_lark_workspace.py output before rerunning."
        )
    return reloaded


def run_command_with_transient_retry(
    args: list[str],
    *,
    dry_run: bool,
    attempts: int = 3,
    delay_seconds: int = 10,
) -> subprocess.CompletedProcess[str] | None:
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(1, attempts + 1):
        try:
            return run_command(args, dry_run=dry_run)
        except subprocess.CalledProcessError as error:
            last_error = error
            combined = f"{error.stdout or ''}\n{error.stderr or ''}"
            transient = any(
                marker in combined
                for marker in ("EOF", "connection reset", "timeout", "temporarily unavailable")
            )
            if not transient or attempt >= attempts:
                raise
            print(f"[retry] transient command failure; retrying in {delay_seconds}s ({attempt}/{attempts})", file=sys.stderr)
            time.sleep(delay_seconds)
    if last_error:
        raise last_error
    return None


def parse_field_value(field_values: list[dict[str, Any]]) -> dict[str, Any]:
    if not field_values:
        return {"value": "", "confidence": None, "references": []}

    first = field_values[0] or {}
    return {
        "value": first.get("field_value", ""),
        "confidence": first.get("field_confidence"),
        "references": first.get("references", []),
    }


def extraction_fields_from_adp_payload(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [field for field in data if isinstance(field, dict)]
    if not isinstance(data, dict):
        return []

    candidates = [
        data.get("extraction_result"),
        nested_get(data, ["data", "extraction_result"]),
        nested_get(data, ["result", "extraction_result"]),
        nested_get(data, ["data", "result", "extraction_result"]),
        data.get("data"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [field for field in candidate if isinstance(field, dict)]
    return []


def parse_adp_result(json_path: Path) -> dict[str, Any]:
    """Parse ADP extraction output into order header + item rows.

    This follows the original order-auto-entry Skill's data contract:
    extraction_result[] contains ordinary fields, and a table field such as
    商品明细 or 订单明细 contains table_values rows. ADP Web exports may use a
    top-level list with the same field objects, so support both shapes.
    """
    data = json.loads(json_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {"order": {ADP_META_KEY: {}}, "items": []}
    extraction = extraction_fields_from_adp_payload(data)

    for field in extraction:
        field_name = field.get("field_name", "")
        field_values = field.get("field_values", [])

        if field.get("table_values"):
            for row in field.get("table_values", []):
                item: dict[str, Any] = {
                    ADP_META_KEY: {},
                    ADP_TABLE_CONFIDENCE_KEY: field.get("field_confidence"),
                }
                for cell in row:
                    cell_name = cell.get("field_name", "")
                    parsed = parse_field_value(cell.get("field_values", []))
                    if cell_name:
                        item[cell_name] = parsed["value"]
                        item[ADP_META_KEY][cell_name] = parsed
                if item:
                    result["items"].append(item)
        elif field_values or "field_value" in field:
            parsed = (
                parse_field_value(field_values)
                if field_values
                else {
                    "value": field.get("field_value", ""),
                    "confidence": field.get("field_confidence"),
                    "references": field.get("references", []),
                }
            )
            result["order"][field_name] = parsed["value"]
            result["order"][ADP_META_KEY][field_name] = parsed

    return result


def parse_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if is_blank_like(value):
        return None
    normalized = (
        str(value or "")
        .replace(",", "")
        .replace("¥", "")
        .replace("￥", "")
        .replace("$", "")
        .replace("\u00a0", " ")
        .strip()
    )
    match = re.search(r"-?\d+(?:\.\d+)?", normalized)
    if not match:
        return None
    try:
        return float(match.group(0))
    except (ValueError, TypeError):
        return None


def to_number(value: Any, default: float = 0) -> float:
    number = parse_number(value)
    return default if number is None else number


def first_number(source: dict[str, Any], names: list[str]) -> float | None:
    return parse_number(first_value(source, names, None))


def to_timestamp_ms(date_str: str) -> int:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"):
        try:
            return int(datetime.strptime(date_str, fmt).timestamp() * 1000)
        except ValueError:
            continue
    return 0


def is_blank_like(value: Any) -> bool:
    if value in (None, ""):
        return True
    text = str(value).strip()
    return text in {"", "无结果", "无", "未识别", "N/A", "NA", "null", "None", "-"}


def first_value(source: dict[str, Any], names: list[str], default: Any = "") -> Any:
    for name in names:
        value = source.get(name)
        if not is_blank_like(value):
            return value
    return default


def find_value(data: Any, keys: set[str], prefix: str | None = None) -> str:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str):
                if prefix is None or value.startswith(prefix):
                    return value
        for value in data.values():
            found = find_value(value, keys, prefix)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_value(value, keys, prefix)
            if found:
                return found
    return ""


def current_user_open_id(config: Config, *, dry_run: bool) -> str:
    if dry_run:
        return CURRENT_USER_PLACEHOLDER

    commands = [
        [config.lark_cli, "auth", "status", "--format", "json"],
        [config.lark_cli, "auth", "list", "--format", "json"],
    ]
    for command in commands:
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=20)
            data = json.loads(result.stdout)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, json.JSONDecodeError):
            continue
        open_id = (
            find_value(data, {"openId"}, "ou_")
            or find_value(data, {"userOpenId"}, "ou_")
            or find_value(data, {"open_id"}, "ou_")
            or find_value(data, {"user_open_id"}, "ou_")
        )
        if open_id:
            return open_id
    return ""


def resolve_reviewer_user_id(config: Config, *, dry_run: bool) -> str:
    if not is_placeholder(config.reviewer_user_id):
        return config.reviewer_user_id
    return current_user_open_id(config, dry_run=dry_run)


def raw_adp_value(source: dict[str, Any], field_name: str) -> str:
    meta = source.get(ADP_META_KEY, {}).get(field_name, {})
    value = meta.get("value", source.get(field_name, ""))
    return "" if value is None else str(value)


def key_number(value: Any, precision: int = 4) -> str:
    number = parse_number(value)
    if number is None:
        if is_blank_like(value):
            return ""
        return str(value)
    formatted = f"{number:.{precision}f}".rstrip("0").rstrip(".")
    if "." not in formatted and precision >= 2:
        return f"{formatted}.00"
    decimals = formatted.split(".", 1)[1] if "." in formatted else ""
    if len(decimals) == 1 and precision >= 2:
        return formatted + "0"
    return formatted


def detail_key_for_order_line(order_no: Any, item: dict[str, Any], line_no: int, material_code: Any, unit_price: Any) -> str:
    line_key = first_value(item, ["序号", "行号", "行项目", "line_no", "item"], line_no)
    delivery_key = first_value(item, ["交货日期", "到货日期", "delivery_date"], "")
    if is_blank_like(delivery_key):
        delivery_ts = to_timestamp_ms(str(first_value(item, ["交货日期", "到货日期", "delivery_date"], "")))
        delivery_key = str(delivery_ts or "")
    price_key = key_number(first_value(item, UNIT_PRICE_FIELDS, unit_price), 4)
    return "|".join([str(order_no), str(line_key), str(material_code), str(delivery_key), str(price_key)])


def reference_pages(*sources: dict[str, Any]) -> str:
    pages: set[int] = set()
    for source in sources:
        for entry in source.get(ADP_META_KEY, {}).values():
            for reference in entry.get("references", []) or []:
                page_no = reference.get("page_no")
                if isinstance(page_no, int):
                    pages.add(page_no)
    return ",".join(str(page) for page in sorted(pages))


def compact_adp_entry(entry: dict[str, Any]) -> dict[str, Any]:
    pages = sorted(
        {
            reference.get("page_no")
            for reference in entry.get("references", []) or []
            if isinstance(reference.get("page_no"), int)
        }
    )
    confidence = entry.get("confidence")
    return {
        "value": entry.get("value", ""),
        "confidence": round(float(confidence), 4) if isinstance(confidence, (int, float)) else None,
        "pages": pages,
    }


def adp_row_json(item: dict[str, Any]) -> str:
    summary = {
        field_name: compact_adp_entry(entry)
        for field_name, entry in item.get(ADP_META_KEY, {}).items()
    }
    return json.dumps(summary, ensure_ascii=False)


def adp_line_confidence(order: dict[str, Any], item: dict[str, Any]) -> float | None:
    confidences: list[float] = []
    table_confidence = item.get(ADP_TABLE_CONFIDENCE_KEY)
    if isinstance(table_confidence, (int, float)):
        confidences.append(float(table_confidence))

    for source in (order, item):
        for entry in source.get(ADP_META_KEY, {}).values():
            confidence = entry.get("confidence")
            if isinstance(confidence, (int, float)) and not is_blank_like(entry.get("value")):
                confidences.append(float(confidence))

    return round(min(confidences), 4) if confidences else None


def adp_low_confidence_fields(order: dict[str, Any], item: dict[str, Any]) -> str:
    problems: list[str] = []
    watched_fields = [
        (order, "客户名称"),
        (order, "买方/客户地址"),
        (order, "客户地址"),
        (order, "订单编号"),
        (order, "币种"),
        (order, "收货方名称"),
        (order, "客户收货地址"),
        (order, "送货地址"),
        (item, "物料编码"),
        (item, "厂家型号"),
        (item, "数量"),
        (item, "单价（含税）"),
        (item, "含税单价"),
        (item, "单价"),
        (item, "未税单价"),
        (item, "税率"),
        (item, "交货日期"),
        (item, "到货日期"),
    ]

    for source, field_name in watched_fields:
        entry = source.get(ADP_META_KEY, {}).get(field_name)
        if not entry:
            continue
        value = entry.get("value")
        confidence = entry.get("confidence")
        if is_blank_like(value):
            problems.append(f"{field_name}=无结果")
        elif isinstance(confidence, (int, float)) and confidence < LOW_CONFIDENCE_THRESHOLD:
            problems.append(f"{field_name}置信度={confidence:.2f}")

    return "; ".join(problems)


def normalize_party_name(value: Any) -> str:
    text = str(value or "").lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)


def names_match(left: Any, right: Any) -> bool:
    left_norm = normalize_party_name(left)
    right_norm = normalize_party_name(right)
    if not left_norm or not right_norm:
        return False
    return left_norm == right_norm or left_norm in right_norm or right_norm in left_norm


def is_laiye_party(value: Any) -> bool:
    text = normalize_party_name(value)
    return "来也" in text or "laiye" in text


def build_audit_records(
    order: dict[str, Any],
    items: list[dict[str, Any]],
    source_file: str,
    source_meta: dict[str, Any] | None = None,
    reviewer_user_id: str = "",
) -> list[dict[str, Any]]:
    """One item line becomes one writable Base record.
    """
    if not items:
        items = [{}]

    date_ts = to_timestamp_ms(first_value(order, ["订单日期", "下单日期", "date"]))
    records: list[dict[str, Any]] = []

    order_no = first_value(order, ["订单编号", "采购单号", "PO No.", "PO Number", "order_no"])
    buyer_name = first_value(order, ["买方/客户名称", "客户名称", "买方名称", "采购方名称", "buyer", "customer"])
    buyer_address = first_value(order, BUYER_ADDRESS_FIELDS)
    seller_name = first_value(order, ["卖方名称", "供应厂商", "供应方", "供应商", "seller", "vendor"])
    if is_laiye_party(buyer_name) and seller_name and not is_laiye_party(seller_name):
        buyer_name, seller_name = seller_name, buyer_name
        if buyer_address and is_laiye_party(buyer_address):
            buyer_address = ""
    currency = first_value(order, ["币种", "订单币种", "currency"])
    order_total = first_number(order, ORDER_TOTAL_FIELDS)
    consignee = first_value(order, CONSIGNEE_FIELDS)
    shipping_address = first_value(order, SHIPPING_ADDRESS_FIELDS)
    is_single_line = len(items) == 1
    for line_no, item in enumerate(items, start=1):
        quantity = first_number(item, QUANTITY_FIELDS)
        unit_price = first_number(item, UNIT_PRICE_FIELDS)
        line_total = first_number(item, LINE_TOTAL_FIELDS)
        if line_total is None and quantity is not None and unit_price is not None:
            line_total = quantity * unit_price
        if line_total is None and is_single_line and order_total is not None:
            line_total = order_total
        delivery_ts = to_timestamp_ms(first_value(item, DELIVERY_DATE_FIELDS))
        material_code = first_value(item, MATERIAL_FIELDS)
        tax_rate = first_value(item, ["税率", "tax_rate", "vat_rate"], "")
        detail_key = detail_key_for_order_line(order_no, item, line_no, material_code, unit_price)

        record: dict[str, Any] = {
            "订单编号": order_no,
            "买方/客户名称": buyer_name,
            "买方/客户地址": buyer_address,
            "卖方名称": seller_name,
            "收货方名称": consignee,
            "客户收货地址": shipping_address,
            "币种": currency,
            "订单总金额": order_total,
            "客户订单商品号": material_code,
            "商品名称/规格": first_value(item, DESCRIPTION_FIELDS),
            "数量": quantity,
            "税率": tax_rate,
            "单价（含税）": unit_price,
            "总金额（含税）": line_total,
            "单价含税": unit_price,
            "总金额": line_total,
            "订单币种": currency,
            "来源文件": source_file,
            "明细唯一键": detail_key,
        }
        if reviewer_user_id:
            record[REVIEWER_FIELD_NAME] = [{"id": reviewer_user_id}]
        if source_meta:
            record.update({key: value for key, value in source_meta.items() if value not in (None, "")})
        if date_ts:
            record["订单日期"] = date_ts
        if delivery_ts:
            record["交货日期"] = delivery_ts
            record["到货日期"] = delivery_ts
        records.append(record)

    return records


def extract_with_adp(path: Path, config: Config, output_dir: Path, *, dry_run: bool) -> list[Path]:
    if config.adp_provider == "api":
        return extract_with_adp_api(path, config, output_dir, dry_run=dry_run)
    config.adp_cli = resolve_adp_cli(config.adp_cli)
    return extract_with_adp_cli(path, config, output_dir, dry_run=dry_run)


def extract_with_adp_api(path: Path, config: Config, output_dir: Path, *, dry_run: bool) -> list[Path]:
    export_target = output_dir
    if not output_dir.suffix:
        output_dir.mkdir(parents=True, exist_ok=True)
        export_target = output_dir / f"{path.stem}.json"

    if dry_run:
        raise SystemExit("This skill must call ADP for order extraction.")

    if not config.adp_api_key:
        raise SystemExit(
            f"ADP API Key is missing. Register or sign in at {config.adp_api_base_url}/, "
            f"get your API Key from personal center, then run: export {config.adp_api_key_env}='YOUR_API_KEY'"
        )

    file_base64 = base64.b64encode(path.read_bytes()).decode("ascii")
    payload = json.dumps(
        {"app_id": config.adp_app_id, "file_base64": file_base64},
        ensure_ascii=False,
    ).encode("utf-8")
    endpoint = f"{config.adp_api_base_url}/open/agentic_doc_processor/laiye/v1/app/doc/extract"
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Api-Key": config.adp_api_key,
            "X-Api-Source": "order-auto-entry-skill",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=900) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise SystemExit(f"ADP API request failed: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"ADP API request failed: {exc}") from exc

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"ADP API returned non-JSON response: {response_text[:500]}") from exc

    success_codes = {0, "0", "success", "SUCCESS", "ok", "OK"}
    has_extraction = bool(nested_get(result, ["data", "extraction_result"], [])) if isinstance(result, dict) else False
    if isinstance(result, dict) and result.get("code") not in success_codes and not has_extraction:
        raise SystemExit(f"ADP API extraction failed: {json.dumps(result, ensure_ascii=False)[:1000]}")

    export_target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return [export_target]


def extract_with_adp_cli(path: Path, config: Config, output_dir: Path, *, dry_run: bool) -> list[Path]:
    export_target = output_dir
    if not output_dir.suffix:
        output_dir.mkdir(parents=True, exist_ok=True)
        export_target = output_dir / f"{path.stem}.json"

    args = [
        config.adp_cli,
        "extract",
        "local",
        str(path),
        "--app-id",
        config.adp_app_id,
        "--export",
        str(export_target),
        "--timeout",
        "900",
        "--retry",
        "2",
    ]
    run_command_with_transient_retry(args, dry_run=dry_run)

    if dry_run:
        raise SystemExit("This skill must call ADP for order extraction.")

    if export_target.is_file():
        return [export_target]
    return sorted(output_dir.glob("*.json"))


def find_existing_record_id(record: dict[str, Any], config: Config, *, dry_run: bool, force: bool = False) -> str | None:
    if not (config.skip_duplicates or force):
        return None

    search_field = config.dedupe_field if record.get(config.dedupe_field) else "订单编号"
    keyword = str(record.get(search_field, ""))
    if not keyword:
        return None

    args = [
        config.lark_cli,
        "base",
        "+record-list",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        config.audit_table_id,
        "--field-id",
        search_field,
        "--filter-json",
        json.dumps({"logic": "and", "conditions": [[search_field, "==", keyword]]}, ensure_ascii=False),
        "--limit",
        "1",
        "--format",
        "json",
    ]
    result = run_command(args, dry_run=dry_run)
    if dry_run or not result:
        return None

    data = json.loads(result.stdout)
    record_id_list = nested_get(data, ["data", "record_id_list"], [])
    if record_id_list:
        return str(record_id_list[0])

    records = nested_get(data, ["data", "records"], []) or nested_get(data, ["data", "items"], [])
    if records:
        first = records[0]
        return str(first.get("record_id") or first.get("id") or "")

    return None


def find_record_id_in_response(data: Any) -> str | None:
    if isinstance(data, dict):
        for key in ("record_id", "id"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("rec"):
                return value
        for value in data.values():
            found = find_record_id_in_response(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_record_id_in_response(value)
            if found:
                return found
    return None


def collect_file_tokens(value: Any) -> list[str]:
    tokens: list[str] = []
    if isinstance(value, dict):
        token = value.get("file_token") or value.get("fileToken")
        if isinstance(token, str) and token:
            tokens.append(token)
        for child in value.values():
            tokens.extend(collect_file_tokens(child))
    elif isinstance(value, list):
        for child in value:
            tokens.extend(collect_file_tokens(child))
    return tokens


def existing_attachment_tokens(record_id: str, config: Config, *, dry_run: bool) -> list[str]:
    if dry_run:
        return []
    args = [
        config.lark_cli,
        "base",
        "+record-get",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        config.audit_table_id,
        "--record-id",
        record_id,
        "--field-id",
        config.attachment_field,
        "--format",
        "json",
    ]
    result = run_command(args, dry_run=dry_run)
    if not result:
        return []
    data = json.loads(result.stdout)
    return list(dict.fromkeys(collect_file_tokens(data)))


def remove_source_attachments(record_id: str, file_tokens: list[str], config: Config, *, dry_run: bool) -> None:
    if dry_run or not file_tokens:
        return
    for start in range(0, len(file_tokens), 50):
        batch = file_tokens[start : start + 50]
        args = [
            config.lark_cli,
            "base",
            "+record-remove-attachment",
            "--as",
            config.lark_identity,
            "--base-token",
            config.base_token,
            "--table-id",
            config.audit_table_id,
            "--record-id",
            record_id,
            "--field-id",
            config.attachment_field,
            "--yes",
            "--format",
            "json",
        ]
        for token in batch:
            args.extend(["--file-token", token])
        run_command(args, dry_run=dry_run)


def upload_source_attachment(record_id: str, source_file: Path, config: Config, *, dry_run: bool) -> bool:
    if not config.upload_source_file or not source_file.exists():
        return False

    upload_path = source_file
    if source_file.is_absolute() or not source_file.is_relative_to(Path.cwd()):
        cache_dir = Path("work") / "base-source-attachments"
        cache_dir.mkdir(parents=True, exist_ok=True)
        upload_path = cache_dir / safe_filename(source_file.name)
        shutil.copyfile(source_file, upload_path)
    try:
        cli_file_path = str(upload_path.relative_to(Path.cwd()))
    except ValueError:
        cli_file_path = str(upload_path)

    remove_source_attachments(record_id, existing_attachment_tokens(record_id, config, dry_run=dry_run), config, dry_run=dry_run)

    args = [
        config.lark_cli,
        "base",
        "+record-upload-attachment",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        config.audit_table_id,
        "--record-id",
        record_id,
        "--field-id",
        config.attachment_field,
        "--file",
        cli_file_path,
        "--format",
        "json",
    ]
    result = run_command(args, dry_run=dry_run)
    if dry_run:
        return True
    if not result:
        return False
    data = json.loads(result.stdout)
    return bool(data.get("ok"))


def write_records(
    records: list[dict[str, Any]],
    config: Config,
    *,
    dry_run: bool,
    update_existing: bool = False,
    source_file: Path | None = None,
) -> tuple[int, int, int, list[str]]:
    success = 0
    skipped = 0
    attached = 0
    record_ids: list[str] = []
    for record in records:
        existing_record_id = find_existing_record_id(record, config, dry_run=dry_run, force=update_existing)
        if existing_record_id and not update_existing:
            skipped += 1
            print(f"[skip] {record.get('订单编号')} already exists")
            continue

        args = [
            config.lark_cli,
            "base",
            "+record-upsert",
            "--as",
            config.lark_identity,
            "--base-token",
            config.base_token,
            "--table-id",
            config.audit_table_id,
        ]
        if existing_record_id:
            args.extend(["--record-id", existing_record_id])
        writable_record = {key: value for key, value in record.items() if key not in FORMULA_FIELD_NAMES}
        args.extend(["--json", json.dumps(writable_record, ensure_ascii=False)])

        result = run_command(args, dry_run=dry_run)
        if dry_run:
            success += 1
        elif result:
            data = json.loads(result.stdout)
            if data.get("ok"):
                success += 1
                record_id = existing_record_id or find_record_id_in_response(data)
                if not record_id:
                    record_id = find_existing_record_id(record, config, dry_run=dry_run, force=True)
                if record_id:
                    record_ids.append(record_id)
                    if source_file and upload_source_attachment(record_id, source_file, config, dry_run=dry_run):
                        attached += 1
            else:
                print(f"[error] write failed: {data.get('error', {}).get('message', result.stdout)}", file=sys.stderr)
        time.sleep(0.5)
    return success, skipped, attached, record_ids


def find_record_share_links(data: Any) -> dict[str, str]:
    if isinstance(data, dict):
        value = data.get("record_share_links")
        if isinstance(value, dict):
            return {str(key): str(link) for key, link in value.items() if link}
        for child in data.values():
            found = find_record_share_links(child)
            if found:
                return found
    elif isinstance(data, list):
        for child in data:
            found = find_record_share_links(child)
            if found:
                return found
    return {}


def create_record_share_links(record_ids: list[str], config: Config, *, dry_run: bool) -> dict[str, str]:
    if not record_ids:
        return {}

    args = [
        config.lark_cli,
        "base",
        "+record-share-link-create",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        config.audit_table_id,
        "--record-ids",
        ",".join(record_ids),
        "--format",
        "json",
    ]
    result = run_command(args, dry_run=dry_run)
    if dry_run or not result:
        return {record_id: f"<RECORD_LINK:{record_id}>" for record_id in record_ids}
    data = json.loads(result.stdout)
    return find_record_share_links(data)


def audit_status_rank(status: Any) -> int:
    text = str(status or "").strip()
    if not text or text == "待审核":
        return 0
    if "通过" in text:
        return 1
    return 3


def merge_precheck_result(original: dict[str, Any], computed: dict[str, Any]) -> dict[str, Any]:
    updated = dict(original)
    updated.update(computed)

    for field in ("审核状态", "审核说明"):
        if computed.get(field) in (None, "") and original.get(field) not in (None, ""):
            updated[field] = original.get(field)
    return updated


def refresh_records_from_base(
    records: list[dict[str, Any]],
    record_ids: list[str],
    config: Config,
    *,
    dry_run: bool,
    attempts: int = 10,
) -> list[dict[str, Any]]:
    if dry_run or not record_ids:
        return records

    args = [
        config.lark_cli,
        "base",
        "+record-get",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        config.audit_table_id,
        "--format",
        "json",
    ]
    for record_id in record_ids:
        args.extend(["--record-id", record_id])
    refreshed: list[dict[str, Any]] = []
    for attempt in range(attempts):
        time.sleep(2 if attempt else 1)
        result = run_command(args, dry_run=dry_run)
        if not result:
            continue
        data = json.loads(result.stdout)
        refreshed = rows_from_lark_record_response(data)
        statuses = [str(record.get("审核状态") or "").strip() for record in refreshed]
        if statuses and all(status and status != "待审核" for status in statuses):
            break

    if not refreshed:
        print("[warn] 写入后未能回查 Base 公式结果，通知将使用写入前预审记录。", file=sys.stderr)
        return records

    merged: list[dict[str, Any]] = []
    for original, computed in zip(records, refreshed):
        merged.append(merge_precheck_result(original, computed))
    if len(records) > len(merged):
        merged.extend(records[len(merged) :])
    return merged


def collect_base_fields(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        fields = value.get("fields")
        if isinstance(fields, dict):
            found.append(fields)
        for child in value.values():
            found.extend(collect_base_fields(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(collect_base_fields(child))
    return found


def unwrap_cell(value: Any) -> Any:
    if isinstance(value, list):
        if not value:
            return ""
        return "; ".join(str(unwrap_cell(item)) for item in value if unwrap_cell(item) != "")
    if isinstance(value, dict):
        for key in ("text", "name", "value", "email", "id"):
            if key in value and value[key] not in (None, ""):
                return unwrap_cell(value[key])
        return json.dumps(value, ensure_ascii=False)
    return value


def rows_from_lark_record_response(data: dict[str, Any]) -> list[dict[str, Any]]:
    body = data.get("data", {}) if isinstance(data, dict) else {}
    rows = body.get("data", [])
    field_names = body.get("fields", [])
    if isinstance(rows, list) and isinstance(field_names, list) and field_names:
        return [
            {field: unwrap_cell(value) for field, value in zip(field_names, row)}
            for row in rows
            if isinstance(row, list)
        ]
    return [{key: unwrap_cell(value) for key, value in fields.items()} for fields in collect_base_fields(data)]


def list_reference_records(config: Config, table_id: str, *, dry_run: bool) -> list[dict[str, Any]]:
    if dry_run or is_placeholder(table_id):
        return []

    args = [
        config.lark_cli,
        "base",
        "+record-list",
        "--as",
        config.lark_identity,
        "--base-token",
        config.base_token,
        "--table-id",
        table_id,
        "--limit",
        "500",
        "--format",
        "json",
    ]
    result = run_command(args, dry_run=dry_run)
    if not result:
        return []
    data = json.loads(result.stdout)
    return rows_from_lark_record_response(data)


def parse_date_for_compare(value: Any) -> datetime | None:
    if isinstance(value, (int, float)) and value:
        return datetime.fromtimestamp(float(value) / 1000)
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit() and len(text) >= 12:
        return datetime.fromtimestamp(float(text) / 1000)
    text = text.replace("/", "-").replace(".", "-")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def latest_history(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        return {}
    return max(records, key=lambda record: parse_date_for_compare(record.get("订单日期")) or datetime.min)


def apply_auto_precheck(
    records: list[dict[str, Any]],
    code_records: list[dict[str, Any]],
    history_records: list[dict[str, Any]],
    config: Config,
) -> None:
    if not code_records and not history_records:
        return

    code_by_customer_material: dict[tuple[str, str], dict[str, Any]] = {}
    code_by_material: dict[str, dict[str, Any]] = {}
    for code in code_records:
        customer = str(code.get("客户名称") or "").strip()
        material = str(first_present(code, "客户订单商品号")).strip()
        if material:
            code_by_material.setdefault(material, code)
        if customer and material:
            code_by_customer_material[(customer, material)] = code

    for record in records:
        customer = str(record.get("买方/客户名称") or "").strip()
        material = str(first_present(record, "客户订单商品号")).strip()
        unit_price_value = parse_number(record.get("单价（含税）") if record.get("单价（含税）") is not None else record.get("单价含税"))
        unit_price = unit_price_value if unit_price_value is not None else 0
        currency = str(record.get("币种") or record.get("订单币种") or "").strip()
        order_date = parse_date_for_compare(record.get("订单日期")) or datetime.now()
        code = code_by_customer_material.get((customer, material)) or code_by_material.get(material)
        customer_history = [item for item in history_records if names_match(item.get("客户名称"), customer)]
        material_history = [item for item in customer_history if str(first_present(item, "客户订单商品号")).strip() == material]
        latest = latest_history(material_history)

        record["客户历史订单数"] = len(customer_history)
        record["人工审核动作"] = record.get("人工审核动作") or "待处理"
        record["流转状态"] = record.get("流转状态") or "待归档"
        if latest:
            record["上次成交价USD"] = to_number(latest.get("成交单价USD"), 0)

        problems: list[str] = []
        warnings: list[str] = []

        if not code:
            problems.append(f"客户订单商品号 {material or '未识别'} 没有匹配到来也 SKU，请确认商品匹配表是否已维护")
            record["审核状态"] = "⚠️ 需人工审核"
            record["审核说明"] = "；".join(problems)
            continue

        record["来也 SKU"] = first_present(code, "来也 SKU")
        standard_price = to_number(first_present(code, "标准售价 USD"), 0)
        if standard_price:
            record["标准售价 USD"] = standard_price
            record["价差百分比"] = round((unit_price - standard_price) / standard_price, 4)
        valid_until = first_present(code, "报价有效期")
        if valid_until not in (None, ""):
            record["报价有效期"] = valid_until

        code_currency = str(code.get("币种") or "").strip()
        if code_currency and currency and code_currency != currency:
            warnings.append(f"订单币种是 {currency}，商品匹配表维护币种是 {code_currency}，请确认是否需要换算或退回修改")

        if not customer_history:
            warnings.append(f"买方 {customer or '未识别'} 暂无历史订单记录，请人工确认客户资质和合作条款")
        if unit_price_value is None:
            warnings.append("客户订单单价未识别，请人工确认订单原文")

        expiry = parse_date_for_compare(valid_until)
        expired = bool(expiry and expiry.date() < order_date.date())
        price_abnormal = bool(
            unit_price_value is not None
            and standard_price
            and abs(unit_price - standard_price) / standard_price > config.price_variance_threshold
        )
        if expired:
            warnings.append(f"该商品报价有效期到 {format_date(valid_until)}，已过期，请确认是否仍按此价格接单")
        if price_abnormal:
            problems.append(
                f"客户订单单价 {format_number(unit_price)} USD，与标准售价 {format_number(standard_price)} USD 偏差 {abs(unit_price - standard_price) / standard_price:.1%}，请复核报价"
            )

        if expired and price_abnormal:
            record["审核状态"] = "⚠️ 需人工审核"
        elif price_abnormal:
            record["审核状态"] = "⚠️ 需人工审核"
        elif expired:
            record["审核状态"] = "⚠️ 需人工审核"
        elif not customer_history:
            record["审核状态"] = "⚠️ 需人工审核"
        elif warnings:
            record["审核状态"] = "⚠️ 需人工审核"
        else:
            record["审核状态"] = "✅ 通过"
            record["人工审核动作"] = "审核通过"

        record["审核说明"] = "；".join(problems + warnings) if problems or warnings else "客户、商品、币种、报价有效期和价格校验均通过"


def format_number(value: Any, precision: int = 4) -> str:
    number = to_number(value, 0)
    if abs(number - int(number)) < 0.0000001:
        return str(int(number))
    return f"{number:.{precision}f}".rstrip("0").rstrip(".")


def format_optional_number(value: Any, precision: int = 4) -> str:
    number = parse_number(value)
    if number is None:
        return "未识别"
    if abs(number - int(number)) < 0.0000001:
        return str(int(number))
    return f"{number:.{precision}f}".rstrip("0").rstrip(".")


def format_money(value: Any) -> str:
    return f"{to_number(value, 0):,.2f}"


def format_date(value: Any) -> str:
    if isinstance(value, (int, float)) and value:
        return datetime.fromtimestamp(float(value) / 1000).strftime("%Y-%m-%d")
    text = str(value or "").strip()
    if not text:
        return "未识别"
    if text.isdigit() and len(text) >= 12:
        return datetime.fromtimestamp(float(text) / 1000).strftime("%Y-%m-%d")
    for suffix in (" 00:00:00", " 00:00"):
        if text.endswith(suffix):
            return text[: -len(suffix)]
    return text


def summarize_precheck(records: list[dict[str, Any]]) -> tuple[str, list[str], int, int]:
    issue_lines: list[str] = []
    warning_lines: list[str] = []
    passed_count = 0

    for index, record in enumerate(records, start=1):
        status = str(record.get("审核状态") or "").strip()
        note = str(record.get("审核说明") or "").strip()
        description = str(first_present(record, "商品名称/规格") or first_present(record, "客户订单商品号") or "订单明细").strip()

        if status and "通过" in status:
            passed_count += 1
        elif status and status != "待审核":
            issue_markers = ("未匹配", "未识别", "相差", "过期", "低置信", "异常")
            target = issue_lines if any(marker in f"{status}{note}" for marker in issue_markers) else warning_lines
            target.append(f"第 {index} 行「{description}」{note or status}")
        elif is_blank_like(first_present(record, "客户订单商品号")):
            issue_lines.append(f"第 {index} 行「{description}」客户订单商品号未识别")

    if issue_lines:
        return "异常", issue_lines + warning_lines, len(issue_lines), len(warning_lines)
    if warning_lines:
        return "需复核", warning_lines, 0, len(warning_lines)
    if records and passed_count == len(records):
        return "通过", ["客户、商品、币种、报价有效期和价格校验均通过"], 0, 0
    return "待审核", ["已写入待审核订单表，等待参考数据预审或人工确认"], 0, 0


def build_reviewer_card(records: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    first = records[0] if records else {}
    order_no = str(first.get("订单编号") or summary.get("order_no") or "未识别")
    currency = str(first.get("币种") or first.get("订单币种") or "USD")
    header_total = to_number(first.get("订单总金额"), 0)
    total_amount = header_total or sum(to_number(record.get("总金额（含税）") or record.get("总金额"), 0) for record in records)
    result_text, precheck_lines, issue_count, warning_count = summarize_precheck(records)

    item_lines = []
    for index, record in enumerate(records[:8], start=1):
        material = str(first_present(record, "客户订单商品号") or "未识别客户订单商品号")
        item_name = str(first_present(record, "商品名称/规格") or "商品明细")
        quantity = format_optional_number(record.get("数量"))
        price = format_optional_number(record.get("单价（含税）") if record.get("单价（含税）") is not None else record.get("单价含税"))
        item_lines.append(f"{index}. `{material}` | {item_name} | 数量:{quantity} | 单价:{price}")
    if len(records) > 8:
        item_lines.append(f"... 还有 {len(records) - 8} 行，请在待审核订单表查看")

    precheck_icon = "🔴" if issue_count else ("🟡" if warning_count or result_text == "待审核" else "✅")
    precheck_detail = "\n".join(f"{precheck_icon} {line}" for line in precheck_lines[:5])
    if len(precheck_lines) > 5:
        precheck_detail += f"\n... 还有 {len(precheck_lines) - 5} 条，请在待审核订单表查看"

    record_links = summary.get("record_links") if isinstance(summary.get("record_links"), dict) else {}
    first_link = next(iter(record_links.values()), "")

    elements: list[dict[str, Any]] = [
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "✅ 通过订单自动识别",
            },
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"📝 **订单号：** {order_no}\n"
                    f"📅 **日期：** {format_date(first.get('订单日期'))}\n"
                    f"🏢 **卖方：** {first.get('卖方名称') or '未识别'}\n"
                    f"🏠 **买方：** {first.get('买方/客户名称') or '未识别'}\n"
                    f"💰 **明细行数：** {len(records)} 条\n"
                    f"💰 **总金额：** {format_money(total_amount)} {currency}"
                ),
            },
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": "📋 **商品明细：**\n" + "\n".join(item_lines),
            },
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"{precheck_icon} **预审结果：** {result_text}（异常 {issue_count} 项 / 警告 {warning_count} 项）\n"
                    f"{precheck_detail}"
                ),
            },
        },
        {"tag": "hr"},
        {
            "tag": "div",
            "text": {
                "tag": "lark_md",
                "content": (
                    f"📦 **来源：** {summary.get('source_label') or 'PDF 上传识别'}\n"
                    "🎧 **状态：** 已写入待审核订单表，请及时审核"
                ),
            },
        },
    ]

    if first_link:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "打开待审核记录"},
                        "url": first_link,
                        "type": "primary",
                    }
                ],
            }
        )

    return {
        "config": {"wide_screen_mode": True, "enable_forward": True},
        "header": {
            "template": "blue",
            "title": {"tag": "plain_text", "content": "📩 订单已自动录入"},
        },
        "elements": elements,
    }


def notify(records: list[dict[str, Any]], summary: dict[str, Any], config: Config, *, dry_run: bool) -> None:
    if not config.notify_on_success:
        return

    reviewer_user_id = str(summary.get("reviewer_user_id") or "").strip()
    if not reviewer_user_id:
        print("[warn] 未找到审核负责人 user open_id，已跳过私信通知。", file=sys.stderr)
        return

    card = build_reviewer_card(records, summary)
    args = [
        config.lark_cli,
        "im",
        "+messages-send",
        "--as",
        config.notify_identity,
        "--user-id",
        reviewer_user_id,
        "--msg-type",
        "interactive",
        "--content",
        json.dumps(card, ensure_ascii=False),
        "--format",
        "json",
    ]
    run_command(args, dry_run=dry_run)


def collect_dicts_with_key(value: Any, key: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if key in value:
            found.append(value)
        for child in value.values():
            found.extend(collect_dicts_with_key(child, key))
    elif isinstance(value, list):
        for child in value:
            found.extend(collect_dicts_with_key(child, key))
    return found


def mail_payload(message: dict[str, Any]) -> dict[str, Any]:
    data = message.get("data")
    return data if isinstance(data, dict) else message


def mail_sender_text(message: dict[str, Any], summary: dict[str, Any]) -> str:
    payload = mail_payload(message)
    sources = (payload, message, summary)
    for source in sources:
        head_from = source.get("head_from")
        if isinstance(head_from, dict):
            address = head_from.get("mail_address") or head_from.get("email") or head_from.get("address")
            name = head_from.get("name")
            if address and name:
                return f"{name} <{address}>"
            if address or name:
                return str(address or name)
        for key in ("from", "sender", "from_email", "sender_email"):
            value = source.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                return str(value.get("email") or value.get("address") or value.get("mail_address") or value.get("name") or "")
    return ""


def message_subject(message: dict[str, Any], summary: dict[str, Any]) -> str:
    for source in (mail_payload(message), message, summary):
        value = source.get("subject") or source.get("title")
        if isinstance(value, str):
            return value
    return ""


def attachment_filename(attachment: dict[str, Any]) -> str:
    for key in ("filename", "file_name", "name", "fileName"):
        value = attachment.get(key)
        if isinstance(value, str) and value:
            return value
    attachment_id = str(attachment.get("attachment_id") or attachment.get("id") or "attachment")
    return attachment_id


def attachment_id(attachment: dict[str, Any]) -> str:
    for key in ("attachment_id", "id", "attachmentId"):
        value = attachment.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def safe_filename(name: str) -> str:
    keep = []
    for char in name:
        keep.append(char if char.isalnum() or char in ".-_+()[] " else "_")
    cleaned = "".join(keep).strip()
    return cleaned or "attachment"


def short_token(value: str, limit: int = 12) -> str:
    cleaned = safe_filename(value)
    return cleaned[:limit] if len(cleaned) > limit else cleaned


def mail_attachment_key(message_id: str, attachment: dict[str, Any]) -> str:
    return f"{message_id}:{attachment_id(attachment)}"


def load_mail_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"processed": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"processed": {}}
    if not isinstance(data, dict):
        return {"processed": {}}
    processed = data.get("processed")
    if not isinstance(processed, dict):
        data["processed"] = {}
    return data


def save_mail_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def list_mail_summaries(config: Config, args: argparse.Namespace, *, dry_run: bool) -> list[dict[str, Any]]:
    mail_filter = json.loads(args.mail_filter) if args.mail_filter else {"folder": "inbox", "has_attachment": True}
    if args.mail_since_hours > 0 and "time_range" not in mail_filter:
        end_time = datetime.now().astimezone()
        start_time = end_time - timedelta(hours=args.mail_since_hours)
        mail_filter["time_range"] = {
            "start_time": start_time.isoformat(timespec="seconds"),
            "end_time": end_time.isoformat(timespec="seconds"),
        }
    command = [
        config.lark_cli,
        "mail",
        "+triage",
        "--as",
        config.mail_identity,
        "--mailbox",
        args.mailbox or config.mailbox,
        "--filter",
        json.dumps(mail_filter, ensure_ascii=False),
        "--max",
        str(args.mail_max),
        "--format",
        "json",
    ]
    if args.mail_query:
        command.extend(["--query", args.mail_query])
    result = run_command(command, dry_run=dry_run)
    if dry_run or not result:
        return []
    data = json.loads(result.stdout)
    return collect_dicts_with_key(data, "message_id")


def get_mail_message(config: Config, message_id: str, mailbox: str, *, dry_run: bool) -> dict[str, Any]:
    command = [
        config.lark_cli,
        "mail",
        "+message",
        "--as",
        config.mail_identity,
        "--mailbox",
        mailbox,
        "--message-id",
        message_id,
        "--format",
        "json",
    ]
    result = run_command(command, dry_run=dry_run)
    if dry_run or not result:
        return {}
    return json.loads(result.stdout)


def mail_order_attachments(message: dict[str, Any]) -> list[dict[str, Any]]:
    payload = mail_payload(message)
    raw_attachments = payload.get("attachments")
    candidates = raw_attachments if isinstance(raw_attachments, list) else collect_dicts_with_key(message, "attachment_id")
    attachments: list[dict[str, Any]] = []
    seen: set[str] = set()
    for attachment in candidates:
        if not isinstance(attachment, dict):
            continue
        aid = attachment_id(attachment)
        name = attachment_filename(attachment)
        if not aid or aid in seen:
            continue
        if attachment.get("is_inline") is True:
            continue
        if Path(name).suffix.lower() not in ORDER_ATTACHMENT_SUFFIXES:
            continue
        seen.add(aid)
        attachments.append(attachment)
    return attachments


def download_mail_attachment(
    config: Config,
    message_id: str,
    attachment: dict[str, Any],
    mailbox: str,
    output_dir: Path,
    *,
    dry_run: bool,
) -> Path | None:
    aid = attachment_id(attachment)
    filename = safe_filename(attachment_filename(attachment))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{short_token(message_id)}_{short_token(aid)}_{filename}"
    params = {
        "user_mailbox_id": mailbox,
        "message_id": message_id,
        "attachment_ids": [aid],
    }
    command = [
        config.lark_cli,
        "mail",
        "user_mailbox.message.attachments",
        "download_url",
        "--as",
        config.mail_identity,
        "--params",
        json.dumps(params, ensure_ascii=False),
        "--format",
        "json",
    ]
    result = run_command(command, dry_run=dry_run)
    if dry_run:
        return output_path
    if not result:
        return None
    data = json.loads(result.stdout)
    download_items = collect_dicts_with_key(data, "download_url")
    if not download_items:
        return None
    urllib.request.urlretrieve(str(download_items[0]["download_url"]), output_path)
    return output_path


def process_order_file(
    input_path: Path,
    config: Config,
    args: argparse.Namespace,
    *,
    dry_run: bool,
    source_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    all_records: list[dict[str, Any]] = []
    reviewer_user_id = resolve_reviewer_user_id(config, dry_run=dry_run)
    if args.from_adp_json:
        json_paths = [args.from_adp_json] if args.from_adp_json.is_file() else sorted(args.from_adp_json.glob("*.json"))
    else:
        output_dir = Path("work") / "adp-order-json" / datetime.now().strftime("%Y%m%d-%H%M%S")
        json_paths = extract_with_adp(input_path, config, output_dir, dry_run=dry_run)

    for json_path in json_paths:
        parsed = parse_adp_result(json_path)
        all_records.extend(
            build_audit_records(
                parsed["order"],
                parsed["items"],
                input_path.name,
                source_meta,
                reviewer_user_id=reviewer_user_id,
            )
        )

    if not all_records:
        raise SystemExit("ADP extraction completed, but no writable order lines were parsed; notification skipped.")

    code_records = list_reference_records(config, config.code_table_id, dry_run=dry_run)
    history_records = list_reference_records(config, config.history_table_id, dry_run=dry_run)
    apply_auto_precheck(all_records, code_records, history_records, config)

    print(json.dumps({"records_to_write": all_records}, ensure_ascii=False, indent=2))
    success, skipped, attached, record_ids = write_records(
        all_records,
        config,
        dry_run=dry_run,
        update_existing=args.update_existing,
        source_file=None if args.from_adp_json else input_path,
    )
    record_links = create_record_share_links(record_ids, config, dry_run=dry_run)
    notification_records = refresh_records_from_base(all_records, record_ids, config, dry_run=dry_run)

    first_record = all_records[0] if all_records else {}
    summary = {
        "order_no": first_record.get("订单编号", ""),
        "customer": first_record.get("买方/客户名称", ""),
        "line_count": len(all_records),
        "success_count": success,
        "skipped_count": skipped,
        "attached_count": attached,
        "record_ids": record_ids,
        "record_links": record_links,
        "reviewer_user_id": reviewer_user_id,
        "source_label": (
            "邮件附件识别"
            if source_meta and source_meta.get("来源邮件ID")
            else ("ADP JSON 结果导入" if args.from_adp_json else "PDF 上传识别")
        ),
    }
    notify(notification_records, summary, config, dry_run=dry_run)
    return summary


def run_mail_scan(config: Config, args: argparse.Namespace, *, dry_run: bool) -> list[dict[str, Any]]:
    mailbox = args.mailbox or config.mailbox
    state = load_mail_state(args.mail_state_file)
    processed_state = state.setdefault("processed", {})
    if not isinstance(processed_state, dict):
        processed_state = {}
        state["processed"] = processed_state

    print(
        f"[mail] 扫描飞书邮箱附件：mailbox={mailbox}, 最近 {args.mail_since_hours} 小时, 最多 {args.mail_max} 封。",
        file=sys.stderr,
    )
    summaries = list_mail_summaries(config, args, dry_run=dry_run)
    print(f"[mail] 命中附件邮件 {len(summaries)} 封。", file=sys.stderr)
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for summary in summaries:
        message_id = str(summary.get("message_id") or "")
        if not message_id:
            continue
        message = get_mail_message(config, message_id, mailbox, dry_run=dry_run)
        attachments = mail_order_attachments(message)
        if not attachments:
            skipped.append({"message_id": message_id, "reason": "no_supported_order_attachment"})
            continue
        source_meta = {
            "来源邮件ID": message_id,
            "来源邮箱": mail_sender_text(message, summary),
            "来源邮件主题": message_subject(message, summary),
        }
        print(
            f"[mail] 处理邮件：{source_meta.get('来源邮件主题') or '<无主题>'}，支持的订单附件 {len(attachments)} 个。",
            file=sys.stderr,
        )
        for attachment in attachments:
            filename = attachment_filename(attachment)
            attachment_key = mail_attachment_key(message_id, attachment)
            if not args.mail_reprocess and attachment_key in processed_state:
                skipped.append(
                    {
                        "message_id": message_id,
                        "attachment": filename,
                        "reason": "already_processed",
                    }
                )
                print(f"[mail] 跳过已处理附件：{filename}", file=sys.stderr)
                continue

            local_path = download_mail_attachment(
                config,
                message_id,
                attachment,
                mailbox,
                args.mail_download_dir,
                dry_run=dry_run,
            )
            if not local_path:
                failures.append(
                    {
                        "message_id": message_id,
                        "attachment": filename,
                        "error": "download_failed",
                    }
                )
                print(f"[mail] 附件下载失败：{filename}", file=sys.stderr)
                continue
            print(f"[mail] 已下载附件，开始 ADP 识别：{local_path}", file=sys.stderr)
            try:
                result = process_order_file(local_path, config, args, dry_run=dry_run, source_meta=source_meta)
            except SystemExit as exc:
                failures.append(
                    {
                        "message_id": message_id,
                        "attachment": filename,
                        "local_path": str(local_path),
                        "error": str(exc),
                    }
                )
                print(f"[mail] 附件处理失败：{filename} - {exc}", file=sys.stderr)
                continue
            except Exception as exc:
                failures.append(
                    {
                        "message_id": message_id,
                        "attachment": filename,
                        "local_path": str(local_path),
                        "error": repr(exc),
                    }
                )
                print(f"[mail] 附件处理异常：{filename} - {exc!r}", file=sys.stderr)
                continue

            processed_state[attachment_key] = {
                "processed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "message_id": message_id,
                "attachment_id": attachment_id(attachment),
                "filename": filename,
                "local_path": str(local_path),
                "order_no": result.get("order_no", ""),
                "record_ids": result.get("record_ids", []),
            }
            save_mail_state(args.mail_state_file, state)
            results.append(result)
    args.mail_scan_report = {
        "messages_scanned": len(summaries),
        "orders_processed": len(results),
        "skipped": skipped,
        "failures": failures,
        "state_file": str(args.mail_state_file),
    }
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ADP extraction and write procurement order audit records to Lark Base")
    parser.add_argument("input", nargs="?", type=Path, default=Path("demo.pdf"), help="采购订单 PDF 或文件夹路径")
    parser.add_argument("--config", type=Path, default=Path("config.json"), help="配置文件路径；不存在时使用内置演示配置")
    parser.add_argument("--from-adp-json", type=Path, default=None, help="使用已有 ADP JSON 结果写入 Base；用于字段映射验证，不重新调用 ADP")
    parser.add_argument("--from-mail", action="store_true", help="从飞书邮箱收件箱扫描订单附件并处理")
    parser.add_argument("--mailbox", default=None, help="要扫描的邮箱，默认 me")
    parser.add_argument("--mail-query", default="", help="邮件全文搜索关键词；默认只按附件过滤")
    parser.add_argument("--mail-filter", default='{"folder":"inbox","has_attachment":true}', help="mail +triage filter JSON")
    parser.add_argument("--mail-since-hours", type=int, default=24, help="默认扫描最近多少小时的附件邮件；传 0 表示不限制时间")
    parser.add_argument("--mail-max", type=int, default=20, help="每次最多扫描的邮件数")
    parser.add_argument("--mail-download-dir", type=Path, default=Path("work/mail-order-attachments"), help="邮件附件下载目录")
    parser.add_argument("--mail-state-file", type=Path, default=Path("work/mail-processed-attachments.json"), help="邮箱附件处理状态文件；用于轮询时避免重复调用 ADP")
    parser.add_argument("--mail-reprocess", action="store_true", help="重新处理已成功处理过的邮件附件")
    parser.add_argument("--poll-interval", type=int, default=0, help="大于 0 时按秒循环扫描邮箱")
    parser.add_argument("--update-existing", action="store_true", help="按去重字段找到已有记录后更新，而不是跳过")
    parser.add_argument("--no-notify", action="store_true", help="不发送审核人私信，适合字段回填")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dry_run = False
    config = load_config(args.config if args.config.exists() else None)
    if args.no_notify:
        config.notify_on_success = False

    ensure_adp_available(config, args)
    if base_config_incomplete(config):
        config = auto_init_lark_workspace(args.config)
        if args.no_notify:
            config.notify_on_success = False
    ensure_adp_available(config, args)
    validate_config_for_execute(config, args)
    if not args.from_mail and args.from_adp_json is None and not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")
    required_commands = [config.lark_cli]
    if config.adp_provider == "cli":
        required_commands.append(config.adp_cli)
    for command in required_commands:
        if not command_exists(command):
            raise SystemExit(f"Command not found: {command}")

    if args.from_mail:
        while True:
            summaries = run_mail_scan(config, args, dry_run=dry_run)
            report = getattr(args, "mail_scan_report", {})
            print(
                json.dumps(
                    {
                        "ok": True,
                        "mail_orders_processed": len(summaries),
                        "summaries": summaries,
                        **report,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            if args.poll_interval <= 0:
                break
            time.sleep(args.poll_interval)
    else:
        summary = process_order_file(args.input, config, args, dry_run=dry_run)
        print(json.dumps({"ok": True, **summary}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

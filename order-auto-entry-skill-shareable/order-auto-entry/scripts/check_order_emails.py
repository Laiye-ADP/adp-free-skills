#!/usr/bin/env python3
"""Compatibility wrapper for the mail-order intake flow.

This wrapper intentionally does not auto-reply, forward, delete, or move email.
Despite the historical filename, it runs the full mail intake path by delegating
to run_order_audit.py --from-mail: scan, download, ADP extraction, Base write,
source attachment upload, and reviewer notification.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    script = Path(__file__).with_name("run_order_audit.py")
    config = Path(__file__).resolve().parents[1] / "config.json"
    command = [sys.executable, str(script), "--from-mail", "--config", str(config), *sys.argv[1:]]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Compatibility wrapper retained only to redirect users to the real ADP path."""

from __future__ import annotations

def main() -> int:
    raise SystemExit(
        "This skill must call ADP for normal runs. Use scripts/run_order_audit.py with the original order PDF/image. "
        "Preferred setup: install ADP CLI with npm install -g @laiye-adp/agentic-doc-parse-and-extract-cli. "
        "Fallback setup: open https://adp.laiye.com/, get the API Key from personal center, then run: export ADP_API_KEY='<YOUR_ADP_API_KEY>'."
    )


if __name__ == "__main__":
    raise SystemExit(main())

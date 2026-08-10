#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from paperlib import validate_paper_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate one paper directory.")
    parser.add_argument("paper_dir", type=Path)
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    issues = validate_paper_dir(paper_dir, strict=args.strict)
    if issues:
        print(f"FAIL: {paper_dir}")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print(f"OK: {paper_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


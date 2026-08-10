#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from paperlib import dump_yaml, load_yaml, resolve_repo, slugify, today


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = SKILL_DIR / "assets" / "templates" / "search-request.yaml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a structured literature search request.")
    parser.add_argument("--repo", help="Paper Reader repository root; defaults to cwd")
    parser.add_argument("--question", required=True)
    parser.add_argument("--slug", help="Short ASCII identifier; defaults to the question")
    parser.add_argument(
        "--objective",
        default="literature-survey",
        choices=(
            "literature-survey",
            "baseline-selection",
            "novelty-check",
            "method-transfer",
            "evidence-gathering",
        ),
    )
    parser.add_argument("--task", default="")
    parser.add_argument("--setting", default="")
    parser.add_argument("--domain", default="")
    parser.add_argument("--time-range", default="")
    parser.add_argument("--prefer-code", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    request_slug = slugify(args.slug or args.question)
    request_id = f"{today()}-{request_slug}"
    target = repo / "inbox" / "search-requests" / f"{request_id}.yaml"
    if target.exists():
        raise SystemExit(f"Search request already exists: {target}")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    template = template.replace("{{REQUEST_ID}}", request_id)
    template = template.replace("{{DATE}}", today())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template, encoding="utf-8", newline="\n")

    data = load_yaml(target)
    data["research_question"] = args.question
    data["objective"] = args.objective
    data["scope"]["task"] = args.task
    data["scope"]["setting"] = args.setting
    data["scope"]["domain"] = args.domain
    data["scope"]["time_range"] = args.time_range
    data["preferences"]["code_available"] = args.prefer_code
    dump_yaml(target, data)
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


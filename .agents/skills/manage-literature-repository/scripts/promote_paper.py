#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil

from paperlib import dump_yaml, load_yaml, resolve_repo, today, validate_paper_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Promote a strictly validated paper.")
    parser.add_argument("--repo", help="Paper Reader repository root; defaults to cwd")
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--verified-by", default="coordinator")
    parser.add_argument("--verification-level", choices=("targeted", "full"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    source = repo / "inbox" / "papers" / args.paper_id
    target = repo / "papers" / args.paper_id
    if not source.is_dir():
        raise SystemExit(f"Staging paper does not exist: {source}")
    if target.exists():
        raise SystemExit(f"Canonical paper already exists: {target}")

    issues = validate_paper_dir(source, strict=True)
    if issues:
        print(f"Cannot promote {args.paper_id}:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    metadata = load_yaml(source / "metadata.yaml")
    metadata["workflow"]["status"] = "verified"
    metadata["workflow"]["translated_at"] = (
        metadata["workflow"].get("translated_at") or today()
    )
    metadata["workflow"]["reviewed_at"] = (
        metadata["workflow"].get("reviewed_at") or today()
    )
    metadata["workflow"]["verified_at"] = today()
    metadata["quality"]["evidence_verified"] = True
    metadata["quality"]["translation_verified"] = True
    metadata["quality"]["verification_level"] = args.verification_level or (
        metadata["quality"].get("verification_level")
        or ("targeted" if metadata["workflow"].get("reading_mode") == "fast" else "full")
    )
    metadata["provenance"]["last_updated"] = today()
    metadata["provenance"]["verified_by"] = args.verified_by
    dump_yaml(source / "metadata.yaml", metadata)

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    print(target)
    print("Run build_index.py to refresh index.yaml and generated collections.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

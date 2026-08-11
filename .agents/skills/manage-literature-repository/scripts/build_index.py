#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_obsidian import build_vault, classify_tracks
from paperlib import dump_yaml, load_yaml, resolve_repo, validate_paper_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the global paper index and collections.")
    parser.add_argument("--repo", help="Paper Reader repository root; defaults to cwd")
    return parser.parse_args()


def paper_record(repo: Path, paper_dir: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    record = {
        "id": metadata["id"],
        "title": metadata["title"],
        "title_zh": metadata.get("title_zh", ""),
        "authors": metadata.get("authors", []),
        "year": metadata["year"],
        "venue": metadata.get("publication", {}).get("venue", ""),
        "identifiers": metadata.get("identifiers", {}),
        "domains": metadata.get("research", {}).get("domains", []),
        "topics": metadata.get("research", {}).get("topics", []),
        "task": metadata.get("research", {}).get("task", ""),
        "method_family": metadata.get("research", {}).get("method_family", ""),
        "status": metadata.get("workflow", {}).get("status", ""),
        "code_url": metadata.get("artifacts", {}).get("code_url", ""),
        "path": paper_dir.relative_to(repo).as_posix(),
    }
    record["research_tracks"] = classify_tracks(record, metadata)
    return record


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    papers_root = repo / "papers"
    records: list[dict[str, Any]] = []
    failures: list[str] = []

    for paper_dir in sorted(path for path in papers_root.iterdir() if path.is_dir()):
        issues = validate_paper_dir(paper_dir, strict=True)
        if issues:
            failures.append(f"{paper_dir.name}: " + "; ".join(issues))
            continue
        metadata = load_yaml(paper_dir / "metadata.yaml")
        if metadata.get("workflow", {}).get("status") not in {"verified", "synthesized"}:
            failures.append(f"{paper_dir.name}: canonical paper is not verified")
            continue
        records.append(paper_record(repo, paper_dir, metadata))

    if failures:
        print("Index generation stopped because canonical papers are invalid:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    records.sort(key=lambda item: (-item["year"], item["id"]))
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "paper_count": len(records),
        "papers": records,
    }
    dump_yaml(repo / "index.yaml", index)

    obsidian = build_vault(repo, records)
    print(f"Indexed {len(records)} papers.")
    print(f"Refreshed {obsidian['paper_count']} Obsidian paper pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

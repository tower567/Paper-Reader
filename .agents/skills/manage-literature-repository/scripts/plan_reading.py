#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paperlib import atomic_write_text, dump_yaml, load_yaml, sha256_file, today


MODE_DEFAULTS = {
    "fast": {
        "time_budget_minutes": 30,
        "max_sections": 8,
        "max_characters": 30000,
        "max_characters_per_section": 6000,
        "max_tables": 2,
        "max_table_rows": 8,
        "max_figures_to_open": 1,
        "max_pdf_pages_to_check": 3,
        "max_evidence_claims": 6,
    },
    "deep": {
        "time_budget_minutes": 90,
        "max_sections": 20,
        "max_characters": 90000,
        "max_characters_per_section": 12000,
        "max_tables": 8,
        "max_table_rows": 20,
        "max_figures_to_open": 5,
        "max_pdf_pages_to_check": 15,
        "max_evidence_claims": 15,
    },
}

ROLE_PATTERNS = (
    ("abstract", re.compile(r"\babstract\b", re.IGNORECASE)),
    ("introduction", re.compile(r"\bintroduction\b", re.IGNORECASE)),
    (
        "conclusion",
        re.compile(r"\b(conclusions?|limitations?|discussion)\b", re.IGNORECASE),
    ),
    (
        "results",
        re.compile(r"\b(main\s+results?|results?|findings?)\b", re.IGNORECASE),
    ),
    (
        "experiments",
        re.compile(
            r"\b(experiments?|experimental\s+setup|evaluation|benchmarks?|datasets?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "method",
        re.compile(
            r"\b(methods?|methodology|approach|framework|architecture|algorithm|"
            r"training|learning|inference|retrieval|memory)\b",
            re.IGNORECASE,
        ),
    ),
)

FAST_SKIP_PATTERN = re.compile(
    r"\b(references?|acknowledg|related\s+work|broader\s+impacts?|"
    r"prompt\s+templates?|few-?shot\s+examples?|example\s+trajector|"
    r"computational\s+resources?|emergent\s+abilities\s+showcase)\b",
    re.IGNORECASE,
)
APPENDIX_PATTERN = re.compile(r"^(?:appendix\b|[A-Z](?:\.\d+)*\b)", re.IGNORECASE)
IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\([^\n)]+\)")
HTML_IMAGE_PATTERN = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
TABLE_ROW_PATTERN = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a bounded reading plan and image-light reading pack."
    )
    parser.add_argument("paper_dir", type=Path)
    parser.add_argument("--mode", choices=("fast", "deep"))
    parser.add_argument("--time-budget-minutes", type=int)
    parser.add_argument("--max-sections", type=int)
    parser.add_argument("--max-characters", type=int)
    parser.add_argument("--research-question", default="")
    parser.add_argument(
        "--focus",
        action="append",
        default=[],
        help="Repeat for a heading keyword that should receive priority.",
    )
    parser.add_argument(
        "--section-index",
        action="append",
        type=int,
        default=[],
        help="Repeat to select an exact one-based manifest section in the given read order.",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def section_role(title: str) -> str:
    for role, pattern in ROLE_PATTERNS:
        if pattern.search(title):
            return role
    return "other"


def focus_terms(question: str, focuses: list[str]) -> set[str]:
    text = " ".join([question, *focuses]).lower()
    terms = set(re.findall(r"[a-z0-9][a-z0-9-]{2,}|[\u4e00-\u9fff]{2,}", text))
    generic = {
        "paper",
        "llm",
        "agent",
        "agents",
        "论文",
        "研究",
        "方法",
        "结果",
        "实验",
        "模型",
    }
    terms -= generic
    if any(term.startswith("experient") for term in terms):
        terms.update({"experience", "experiences", "experiential"})
    return terms


def focus_match(title: str, terms: set[str]) -> bool:
    normalized = title.lower()
    return any(term in normalized for term in terms)


def should_skip_fast(title: str, terms: set[str]) -> bool:
    if focus_match(title, terms):
        return False
    return bool(FAST_SKIP_PATTERN.search(title) or APPENDIX_PATTERN.search(title.strip()))


def scored_sections(
    manifest: dict[str, Any], mode: str, terms: set[str], per_section_limit: int
) -> list[dict[str, Any]]:
    base_scores = {
        "abstract": 100,
        "introduction": 95,
        "conclusion": 92,
        "results": 90,
        "method": 82,
        "experiments": 78,
        "other": 20,
    }
    candidates: list[dict[str, Any]] = []
    for raw in manifest.get("sections", []):
        item = dict(raw)
        title = str(item.get("title", ""))
        role = section_role(title)
        characters = int(item.get("characters") or 0)
        matched_focus = focus_match(title, terms)
        skipped = mode == "fast" and should_skip_fast(title, terms)
        score = base_scores[role]
        if role == "method" and re.search(
            r"\b(learning\s+from|method|approach|framework|algorithm|architecture)\b",
            title,
            flags=re.IGNORECASE,
        ):
            score += 8
        if role == "results" and re.search(r"\bmain\b", title, flags=re.IGNORECASE):
            score += 8
        if matched_focus:
            score += 35
        if characters < 100:
            score -= 60
        item.update(
            {
                "role": role,
                "score": score,
                "focus_match": matched_focus,
                "skipped_by_default": skipped,
                "planned_characters": min(characters, per_section_limit),
            }
        )
        candidates.append(item)
    return candidates


def select_sections(
    candidates: list[dict[str, Any]], max_sections: int, max_characters: int
) -> list[dict[str, Any]]:
    selected: dict[int, dict[str, Any]] = {}
    planned_total = 0

    def add(item: dict[str, Any]) -> bool:
        nonlocal planned_total
        index = int(item["index"])
        if index in selected or len(selected) >= max_sections:
            return False
        planned = int(item["planned_characters"])
        if selected and planned_total + planned > max_characters:
            return False
        selected[index] = item
        planned_total += planned
        return True

    eligible = [item for item in candidates if not item["skipped_by_default"]]
    for role in ("abstract", "introduction", "method", "experiments", "results", "conclusion"):
        role_items = [item for item in eligible if item["role"] == role]
        if role_items:
            best = max(role_items, key=lambda item: (item["score"], -int(item["index"])))
            add(best)

    ranked = sorted(
        eligible,
        key=lambda item: (-int(item["score"]), int(item["index"])),
    )
    for item in ranked:
        add(item)

    return [selected[index] for index in sorted(selected)]


def select_sections_by_index(
    candidates: list[dict[str, Any]],
    indexes: list[int],
    max_sections: int,
    max_characters: int,
) -> list[dict[str, Any]]:
    if len(indexes) > max_sections:
        raise SystemExit(
            f"Explicit selection has {len(indexes)} sections, exceeding limit {max_sections}"
        )
    lookup = {int(item["index"]): item for item in candidates}
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    planned_total = 0
    for index in indexes:
        if index in seen:
            raise SystemExit(f"Duplicate explicit section index: {index}")
        item = lookup.get(index)
        if item is None:
            raise SystemExit(f"Unknown explicit section index: {index}")
        planned_total += int(item["planned_characters"])
        if planned_total > max_characters:
            raise SystemExit(
                f"Explicit selection exceeds character limit {max_characters}"
            )
        selected.append(item)
        seen.add(index)
    return selected


def truncate_section(text: str, limit: int) -> tuple[str, bool]:
    if len(text) <= limit:
        return text, False
    cutoff = text.rfind("\n\n", 0, limit)
    if cutoff < limit // 2:
        cutoff = limit
    return text[:cutoff].rstrip() + "\n\n[本节已按快速阅读预算截断；需要时回查原章节。]\n", True


def filter_tables(
    text: str,
    role: str,
    tables_kept: int,
    max_tables: int,
    max_rows: int,
) -> tuple[str, int, int, int]:
    lines = text.splitlines()
    output: list[str] = []
    index = 0
    kept = tables_kept
    omitted = 0
    truncated = 0
    while index < len(lines):
        if not TABLE_ROW_PATTERN.match(lines[index]):
            output.append(lines[index])
            index += 1
            continue
        end = index
        while end < len(lines) and TABLE_ROW_PATTERN.match(lines[end]):
            end += 1
        block = lines[index:end]
        is_table = len(block) >= 2 and TABLE_SEPARATOR_PATTERN.match(block[1])
        if not is_table:
            output.extend(block)
        elif role in {"results", "experiments"} and kept < max_tables:
            limit = min(len(block), max_rows + 2)
            output.extend(block[:limit])
            kept += 1
            if limit < len(block):
                output.append("\n[表格其余行已省略；仅保留快速核验所需行。]")
                truncated += 1
        else:
            output.append("[表格已省略；仅在关键结论缺少正文证据时回查。]")
            omitted += 1
        index = end
    return "\n".join(output), kept, omitted, truncated


def build_reading_pack(
    paper_dir: Path,
    selected: list[dict[str, Any]],
    limits: dict[str, int],
) -> tuple[str, dict[str, int]]:
    parts = [
        "# 限时阅读包",
        "",
        "本文件由 `plan_reading.py` 生成。默认省略图片，并限制表格和单节长度。",
        "需要额外证据时，只回查对应 source-section 或 PDF 页面。",
        "",
    ]
    images_omitted = 0
    tables_kept = 0
    tables_omitted = 0
    tables_truncated = 0
    sections_truncated = 0
    sections_root = paper_dir / "source-sections"

    for item in selected:
        section_path = sections_root / str(item["file"])
        text = section_path.read_text(encoding="utf-8")
        text, image_count = IMAGE_PATTERN.subn("[图像已省略；必要时回查原 PDF。]", text)
        text, html_image_count = HTML_IMAGE_PATTERN.subn(
            "[图像已省略；必要时回查原 PDF。]", text
        )
        images_omitted += image_count + html_image_count
        text, tables_kept, omitted, truncated = filter_tables(
            text,
            str(item["role"]),
            tables_kept,
            int(limits["max_tables"]),
            int(limits["max_table_rows"]),
        )
        tables_omitted += omitted
        tables_truncated += truncated
        text, was_truncated = truncate_section(
            text, int(limits["max_characters_per_section"])
        )
        sections_truncated += int(was_truncated)
        parts.extend(
            [
                f"## [{item['role']}] {item['title']}",
                "",
                f"来源：`source-sections/{item['file']}`",
                "",
                text.strip(),
                "",
            ]
        )

    pack = "\n".join(parts).strip() + "\n"
    stats = {
        "characters": len(pack),
        "images_omitted": images_omitted,
        "tables_kept": tables_kept,
        "tables_omitted": tables_omitted,
        "tables_truncated": tables_truncated,
        "sections_truncated": sections_truncated,
    }
    return pack, stats


def create_plan(
    paper_dir: Path,
    mode: str,
    research_question: str = "",
    focuses: list[str] | None = None,
    section_indexes: list[int] | None = None,
    overrides: dict[str, int | None] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    paper_dir = paper_dir.expanduser().resolve()
    metadata_path = paper_dir / "metadata.yaml"
    manifest_path = paper_dir / "source-sections" / "manifest.yaml"
    if not metadata_path.is_file() or not manifest_path.is_file():
        raise SystemExit("metadata.yaml and source-sections/manifest.yaml are required")

    metadata = load_yaml(metadata_path)
    manifest = load_yaml(manifest_path)
    limits = dict(MODE_DEFAULTS[mode])
    for key, value in (overrides or {}).items():
        if value is not None:
            if int(value) <= 0:
                raise SystemExit(f"{key} must be positive")
            limits[key] = int(value)

    terms = focus_terms(research_question, focuses or [])
    candidates = scored_sections(
        manifest,
        mode,
        terms,
        int(limits["max_characters_per_section"]),
    )
    if section_indexes:
        selected = select_sections_by_index(
            candidates,
            section_indexes,
            int(limits["max_sections"]),
            int(limits["max_characters"]),
        )
    else:
        selected = select_sections(
            candidates,
            int(limits["max_sections"]),
            int(limits["max_characters"]),
        )
    if not selected:
        raise SystemExit("No readable sections were selected")

    pack, pack_stats = build_reading_pack(paper_dir, selected, limits)
    selected_records = []
    for read_order, item in enumerate(selected, start=1):
        reason = f"core role: {item['role']}"
        if section_indexes:
            reason = "coordinator-curated core section for the focused research question"
        elif item["focus_match"]:
            reason += "; matched research focus"
        selected_records.append(
            {
                "read_order": read_order,
                "index": int(item["index"]),
                "title": item["title"],
                "file": item["file"],
                "role": item["role"],
                "source_characters": int(item.get("characters") or 0),
                "planned_characters": int(item["planned_characters"]),
                "reason": reason,
            }
        )

    plan = {
        "paper_id": metadata.get("id") or paper_dir.name,
        "mode": mode,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "research_question": research_question,
        "focus_terms": sorted(terms),
        "source_sha256": manifest.get("source_sha256", ""),
        "limits": limits,
        "selected_section_count": len(selected_records),
        "skipped_section_count": max(
            0, int(manifest.get("section_count") or 0) - len(selected_records)
        ),
        "selected_sections": selected_records,
        "reading_pack": {
            "file": "reading-pack.md",
            **pack_stats,
        },
        "default_omissions": [
            "references and unrelated work",
            "appendices unless matched by the research focus",
            "images and trajectory screenshots",
            "non-headline tables and excess table rows",
        ],
        "verification": {
            "level": "targeted" if mode == "fast" else "full",
            "verify_metadata": True,
            "max_claims": limits["max_evidence_claims"],
            "open_pdf_only_for_discrepancies": mode == "fast",
        },
        "escalation_triggers": [
            "a headline claim appears only in an omitted table or figure",
            "source text conflicts with metadata or contains broken formulas",
            "the research question depends on an omitted appendix or ablation",
            "the user explicitly requests full translation or exhaustive verification",
        ],
    }

    if dry_run:
        return plan

    pack_path = paper_dir / "reading-pack.md"
    atomic_write_text(pack_path, pack)
    plan["reading_pack"]["sha256"] = sha256_file(pack_path)
    dump_yaml(paper_dir / "reading-plan.yaml", plan)

    artifacts = metadata.setdefault("artifacts", {})
    artifacts["reading_plan"] = "reading-plan.yaml"
    artifacts["reading_pack"] = "reading-pack.md"
    workflow = metadata.setdefault("workflow", {})
    workflow["reading_mode"] = mode
    workflow["time_budget_minutes"] = limits["time_budget_minutes"]
    quality = metadata.setdefault("quality", {})
    quality["verification_level"] = "targeted" if mode == "fast" else "full"
    metadata.setdefault("provenance", {})["last_updated"] = today()
    dump_yaml(metadata_path, metadata)
    return plan


def main() -> int:
    args = parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    metadata = load_yaml(paper_dir / "metadata.yaml")
    mode = args.mode or metadata.get("workflow", {}).get("reading_mode") or "fast"
    plan = create_plan(
        paper_dir,
        mode,
        research_question=args.research_question,
        focuses=args.focus,
        section_indexes=args.section_index,
        overrides={
            "time_budget_minutes": args.time_budget_minutes,
            "max_sections": args.max_sections,
            "max_characters": args.max_characters,
        },
        dry_run=args.dry_run,
    )
    prefix = "DRY RUN" if args.dry_run else "CREATED"
    print(f"{prefix}: {paper_dir / 'reading-plan.yaml'}")
    print(
        "SELECTED: "
        f"{plan['selected_section_count']} sections; "
        f"{plan['reading_pack']['characters']} pack characters"
    )
    print(
        "OMITTED: "
        f"{plan['skipped_section_count']} sections; "
        f"{plan['reading_pack']['images_omitted']} images; "
        f"{plan['reading_pack']['tables_omitted']} tables"
    )
    for item in plan["selected_sections"]:
        print(f"- {item['read_order']}. {item['title']} ({item['role']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

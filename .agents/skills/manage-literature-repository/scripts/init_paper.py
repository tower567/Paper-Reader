#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from paperlib import dump_yaml, load_yaml, resolve_repo, sha256_file, slugify, today


SKILL_DIR = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = SKILL_DIR / "assets" / "templates"


def render_template(name: str, replacements: dict[str, str]) -> str:
    content = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize one staged paper record.")
    parser.add_argument("--repo", help="Paper Reader repository root; defaults to cwd")
    parser.add_argument("--id", dest="paper_id", help="Stable paper ID override")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--first-author", required=True)
    parser.add_argument("--short-title", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--title-zh", default="")
    parser.add_argument(
        "--authors",
        default="",
        help="Semicolon-separated full author list; defaults to first author",
    )
    parser.add_argument("--doi", default="")
    parser.add_argument("--arxiv", default="")
    parser.add_argument("--source-url", default="")
    parser.add_argument(
        "--translation-scope",
        choices=("structured-summary", "core-sections", "full", "custom"),
    )
    parser.add_argument("--reading-mode", choices=("fast", "deep"), default="fast")
    parser.add_argument("--time-budget-minutes", type=int)
    parser.add_argument("--pdf", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    translation_scope = args.translation_scope or (
        "structured-summary" if args.reading_mode == "fast" else "core-sections"
    )
    time_budget_minutes = args.time_budget_minutes or (
        30 if args.reading_mode == "fast" else 90
    )
    if time_budget_minutes <= 0:
        raise SystemExit("--time-budget-minutes must be positive")
    repo = resolve_repo(args.repo)
    paper_id = args.paper_id or (
        f"{args.year}-{slugify(args.first_author)}-{slugify(args.short_title)}"
    )
    if paper_id != slugify(paper_id):
        raise SystemExit("Paper ID must contain only lowercase ASCII letters, digits, and hyphens")

    target = repo / "inbox" / "papers" / paper_id
    if target.exists():
        raise SystemExit(f"Paper staging directory already exists: {target}")
    target.mkdir(parents=True)

    pdf_hash = ""
    status = "queued"
    if args.pdf:
        pdf_source = args.pdf.expanduser().resolve()
        if not pdf_source.is_file():
            raise SystemExit(f"PDF does not exist: {pdf_source}")
        with pdf_source.open("rb") as stream:
            if not stream.read(5).startswith(b"%PDF-"):
                raise SystemExit(f"Input file is not a PDF: {pdf_source}")
        shutil.copy2(pdf_source, target / "original.pdf")
        pdf_hash = sha256_file(target / "original.pdf")
        status = "downloaded"

    replacements = {
        "PAPER_ID": paper_id,
        "TITLE": args.title,
        "TITLE_ZH": args.title_zh,
        "YEAR": str(args.year),
        "DOI": args.doi,
        "ARXIV": args.arxiv,
        "SOURCE_URL": args.source_url,
        "STATUS": status,
        "PDF_SHA256": pdf_hash,
        "DATE": today(),
        "READING_MODE": args.reading_mode,
        "TIME_BUDGET_MINUTES": str(time_budget_minutes),
        "VERIFICATION_LEVEL": "targeted" if args.reading_mode == "fast" else "full",
        "TRANSLATION_SCOPE_ZH": {
            "structured-summary": "结构化中文导读（摘要全文翻译，方法、结果与局限压缩翻译）",
            "core-sections": "核心章节（摘要、引言、方法、实验、结论与局限）",
            "full": "全文",
            "custom": "自定义范围（请在此文件中说明）",
        }[translation_scope],
    }

    for template_name in ("translation.zh.md", "notes.md"):
        content = render_template(template_name, replacements)
        (target / template_name).write_text(content, encoding="utf-8", newline="\n")

    metadata_path = target / "metadata.yaml"
    metadata_path.write_text(
        render_template("metadata.yaml", replacements),
        encoding="utf-8",
        newline="\n",
    )
    metadata = load_yaml(metadata_path)
    authors = [item.strip() for item in args.authors.split(";") if item.strip()]
    metadata["authors"] = authors or [args.first_author]
    metadata["workflow"]["translation_scope"] = translation_scope
    metadata["workflow"]["reading_mode"] = args.reading_mode
    metadata["workflow"]["time_budget_minutes"] = time_budget_minutes
    metadata["quality"]["verification_level"] = (
        "targeted" if args.reading_mode == "fast" else "full"
    )
    dump_yaml(metadata_path, metadata)

    print(target)
    if not args.pdf:
        print("Add original.pdf and update provenance.pdf_sha256 before strict validation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

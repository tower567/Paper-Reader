#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mineru_client import MinerUClient, MinerUError
from paperlib import atomic_write_text, dump_yaml, load_yaml, sha256_file, today
from source_pipeline import (
    build_sections,
    copy_source_assets,
    count_pdf_pages,
    evaluate_source,
    safe_extract_zip,
    section_cache_valid,
    select_markdown_file,
    source_cache_valid,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create, cache, validate, and section a paper's source Markdown."
    )
    parser.add_argument("paper_dir", type=Path)
    parser.add_argument(
        "--backend",
        choices=("auto", "arxiv", "mineru", "local", "import"),
        default="auto",
    )
    parser.add_argument("--source-file", type=Path)
    parser.add_argument("--source-backend", default="arxiv-html")
    parser.add_argument("--arxiv-cache", type=Path)
    parser.add_argument("--model-version", default="vlm")
    parser.add_argument("--language", default="en")
    parser.add_argument("--page-ranges")
    parser.add_argument("--max-section-chars", type=int, default=18000)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--revalidate",
        action="store_true",
        help="Re-run quality checks and sectioning on existing source.md without parsing again.",
    )
    return parser.parse_args()


def find_repo(paper_dir: Path) -> Path:
    for parent in (paper_dir, *paper_dir.parents):
        if (parent / ".agents" / "skills" / "manage-literature-repository").is_dir():
            return parent
    raise SystemExit(f"Cannot locate Paper Reader repository from {paper_dir}")


def normalize_arxiv_id(value: str) -> str:
    return value.removeprefix("arXiv:").split("v", 1)[0].replace("/", "-").lower()


def find_arxiv_markdown(repo: Path, metadata: dict[str, Any], override: Path | None) -> Path | None:
    cache_root = (
        override.expanduser().resolve()
        if override
        else Path(os.environ.get("ARXIV_STORAGE_PATH", repo / ".cache" / "arxiv")).resolve()
    )
    if not cache_root.is_dir():
        return None
    arxiv_id = normalize_arxiv_id(str(metadata.get("identifiers", {}).get("arxiv", "")))
    title = str(metadata.get("title", "")).strip().lower()
    candidates = list(cache_root.rglob("*.md")) + list(cache_root.rglob("*.markdown"))
    ranked: list[tuple[int, int, Path]] = []
    for path in candidates:
        name = path.as_posix().lower()
        score = 0
        if arxiv_id and arxiv_id in name.replace("/", "-").replace("_", "-"):
            score += 10
        try:
            prefix = path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
        except OSError:
            continue
        if arxiv_id and arxiv_id in prefix.replace("/", "-"):
            score += 5
        if title and len(title) > 12 and title[:80] in prefix:
            score += 4
        if score:
            ranked.append((score, path.stat().st_size, path))
    return max(ranked, default=(0, 0, None))[2]


def parse_local(pdf_path: Path) -> str:
    try:
        import pymupdf4llm
    except ImportError as exc:
        raise RuntimeError(
            "Local PDF parsing requires pymupdf4llm. Install arxiv-mcp-server[pdf] "
            "in the paper-reader micromamba environment."
        ) from exc
    return str(pymupdf4llm.to_markdown(str(pdf_path)))


def import_markdown(source: Path) -> str:
    if not source.is_file():
        raise FileNotFoundError(source)
    text = source.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Source Markdown is empty: {source}")
    return text


def update_paper_metadata(
    paper_dir: Path,
    parse_metadata: dict[str, Any],
    manifest: dict[str, Any],
) -> None:
    metadata_path = paper_dir / "metadata.yaml"
    metadata = load_yaml(metadata_path)
    artifacts = metadata.setdefault("artifacts", {})
    artifacts["source"] = "source.md"
    artifacts["source_manifest"] = "source-sections/manifest.yaml"
    artifacts["parse"] = "parse.yaml"
    workflow = metadata.setdefault("workflow", {})
    if workflow.get("status") in {"queued", "downloaded", "screened"}:
        workflow["status"] = "parsed"
    workflow.setdefault("source_required", True)
    quality = metadata.setdefault("quality", {})
    quality["source_verified"] = parse_metadata["quality"]["status"] == "passed"
    provenance = metadata.setdefault("provenance", {})
    provenance["last_updated"] = today()
    provenance["source_sha256"] = parse_metadata["source_sha256"]
    metadata["source_sections"] = manifest["section_count"]
    dump_yaml(metadata_path, metadata)


def main() -> int:
    args = parse_args()
    paper_dir = args.paper_dir.expanduser().resolve()
    repo = find_repo(paper_dir)
    pdf_path = paper_dir / "original.pdf"
    metadata_path = paper_dir / "metadata.yaml"
    if not pdf_path.is_file():
        raise SystemExit(f"Missing original.pdf: {pdf_path}")
    if not metadata_path.is_file():
        raise SystemExit(f"Missing metadata.yaml: {metadata_path}")

    metadata = load_yaml(metadata_path)
    pdf_hash = sha256_file(pdf_path)
    source_path = paper_dir / "source.md"
    if args.revalidate:
        parse_path = paper_dir / "parse.yaml"
        if not source_path.is_file() or not parse_path.is_file():
            raise SystemExit("--revalidate requires existing source.md and parse.yaml")
        markdown = source_path.read_text(encoding="utf-8")
        page_count = count_pdf_pages(pdf_path)
        quality = evaluate_source(markdown, page_count=page_count)
        manifest = build_sections(
            paper_dir,
            markdown,
            max_chars=args.max_section_chars,
        )
        parse_metadata = load_yaml(parse_path)
        parse_metadata["status"] = "ready" if quality.status == "passed" else "needs-review"
        parse_metadata["pdf_sha256"] = pdf_hash
        parse_metadata["source_sha256"] = sha256_file(source_path)
        parse_metadata["page_count"] = page_count
        parse_metadata["source_characters"] = quality.characters
        parse_metadata["section_count"] = manifest["section_count"]
        parse_metadata["quality"] = {
            "status": quality.status,
            "issues": quality.issues,
            "headings": quality.headings,
            "replacement_characters": quality.replacement_characters,
        }
        parse_metadata["revalidated_at"] = datetime.now(timezone.utc).isoformat()
        dump_yaml(parse_path, parse_metadata)
        update_paper_metadata(paper_dir, parse_metadata, manifest)
        print(f"REVALIDATED: {source_path}")
        print(f"SECTIONS: {manifest['section_count']}")
        print(f"QUALITY: {quality.status}")
        for issue in quality.issues:
            print(f"- {issue}")
        return 0 if quality.status == "passed" else 2

    if not args.force and source_cache_valid(paper_dir, pdf_hash):
        markdown = source_path.read_text(encoding="utf-8")
        source_hash = sha256_file(source_path)
        if section_cache_valid(paper_dir, source_hash, args.max_section_chars):
            manifest = load_yaml(paper_dir / "source-sections" / "manifest.yaml")
            sections_status = "REUSED"
        else:
            manifest = build_sections(paper_dir, markdown, max_chars=args.max_section_chars)
            parse_metadata = load_yaml(paper_dir / "parse.yaml")
            parse_metadata["section_count"] = manifest["section_count"]
            dump_yaml(paper_dir / "parse.yaml", parse_metadata)
            update_paper_metadata(paper_dir, parse_metadata, manifest)
            sections_status = "REBUILT"
        print(f"CACHED: {source_path}")
        print(f"SECTIONS: {manifest['section_count']}")
        print(f"SECTION_CACHE: {sections_status}")
        return 0

    backend = args.backend
    source_origin = ""
    provider_result: dict[str, Any] = {}
    asset_count = 0

    if args.source_file:
        backend = "import"
    elif backend in {"auto", "arxiv"}:
        cached_arxiv = find_arxiv_markdown(repo, metadata, args.arxiv_cache)
        if cached_arxiv:
            args.source_file = cached_arxiv
            args.source_backend = "arxiv-mcp"
            backend = "import"
        elif backend == "arxiv":
            raise SystemExit(
                "No cached arXiv Markdown found. Run the arxiv MCP download_paper tool first "
                "or pass --source-file."
            )
        else:
            backend = "local"

    if backend == "import":
        if not args.source_file:
            raise SystemExit("--source-file is required for import backend")
        imported_source = args.source_file.expanduser().resolve()
        markdown = import_markdown(imported_source)
        try:
            source_origin = imported_source.relative_to(repo).as_posix()
        except ValueError:
            source_origin = str(imported_source)
        backend_name = args.source_backend
    elif backend == "local":
        markdown = parse_local(pdf_path)
        source_origin = "original.pdf"
        backend_name = "pymupdf4llm"
    elif backend == "mineru":
        backend_name = f"mineru-{args.model_version}"
        with tempfile.TemporaryDirectory(prefix="paper-reader-mineru-") as temporary:
            temp_root = Path(temporary)
            zip_path = temp_root / "result.zip"
            extracted = temp_root / "result"
            try:
                client = MinerUClient()
                provider_result = client.extract_local_pdf(
                    pdf_path,
                    zip_path,
                    data_id=str(metadata.get("id") or paper_dir.name),
                    model_version=args.model_version,
                    language=args.language,
                    page_ranges=args.page_ranges,
                    timeout_seconds=args.timeout,
                    poll_interval=args.poll_interval,
                )
            except MinerUError as exc:
                raise SystemExit(str(exc)) from exc
            safe_extract_zip(zip_path, extracted)
            selected = select_markdown_file(extracted)
            markdown = selected.read_text(encoding="utf-8")
            asset_count = copy_source_assets(extracted, paper_dir, selected)
            content_lists = list(extracted.rglob("content_list.json"))
            if content_lists:
                shutil.copy2(content_lists[0], paper_dir / "source.content_list.json")
            source_origin = str(provider_result.get("full_zip_url", ""))
    else:
        raise SystemExit(f"Unsupported backend: {backend}")

    markdown = markdown.replace("\r\n", "\n").strip() + "\n"
    atomic_write_text(source_path, markdown)
    page_count = count_pdf_pages(pdf_path)
    quality = evaluate_source(markdown, page_count=page_count)
    manifest = build_sections(paper_dir, markdown, max_chars=args.max_section_chars)
    parse_metadata = {
        "status": "ready" if quality.status == "passed" else "needs-review",
        "backend": backend_name,
        "model_version": args.model_version if backend == "mineru" else "",
        "source_origin": source_origin,
        "task_id": provider_result.get("task_id", ""),
        "batch_id": provider_result.get("batch_id", ""),
        "pdf_sha256": pdf_hash,
        "source_sha256": sha256_file(source_path),
        "page_count": page_count,
        "source_characters": quality.characters,
        "section_count": manifest["section_count"],
        "asset_count": asset_count,
        "quality": {
            "status": quality.status,
            "issues": quality.issues,
            "headings": quality.headings,
            "replacement_characters": quality.replacement_characters,
        },
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }
    dump_yaml(paper_dir / "parse.yaml", parse_metadata)
    update_paper_metadata(paper_dir, parse_metadata, manifest)

    print(f"BACKEND: {backend_name}")
    print(f"SOURCE: {source_path}")
    print(f"SECTIONS: {manifest['section_count']}")
    print(f"QUALITY: {quality.status}")
    for issue in quality.issues:
        print(f"- {issue}")
    return 0 if quality.status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())

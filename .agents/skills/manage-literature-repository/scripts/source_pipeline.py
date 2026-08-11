#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import shutil
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paperlib import atomic_write_text, dump_yaml, load_yaml, sha256_file, slugify


HEADING_PATTERN = re.compile(
    r"(?mi)^(?:"
    r"(?P<markdown>#{1,3})\s+(?P<markdown_title>.+?)"
    r"|\*\*(?P<bold_title>"
    r"(?:(?:\d+(?:\.\d+)*|[A-Z]\.\d+(?:\.\d+)*)\s+.+?)"
    r"|(?:abstract|introduction|background|related work|methods?|approach|framework|"
    r"experiments?|evaluation|results?|discussion|conclusions?|limitations?|references|appendix)"
    r")\*\*"
    r")\s*$"
)

CORE_HEADING_PATTERN = re.compile(
    r"\b(abstract|introduction|methods?|methodology|approach|framework|"
    r"experiments?|evaluation|results?|discussion|conclusions?|limitations?)\b",
    flags=re.IGNORECASE,
)

# PDF-to-Markdown parsers sometimes promote appendix labels or long example
# trajectories to headings.  Terms such as "results", "experiments", or
# "workflow" inside those labels should not make them core-section quality
# gates.
NON_CORE_HEADING_PATTERN = re.compile(
    r"^(?:(?i:appendix)\b|[A-Z](?:\.\d+)*\.?\s+"
    r"(?i:experiment|details|additional|supplementary|implementation|proof|"
    r"prompts?|datasets?|hyperparameters?|ablations?|case studies?)\b|"
    r"[B-Z](?:\.\d+)*\.?\s+(?i:methods?|methodology|approach|framework|"
    r"experiments?|evaluation|benchmarks?|extended\s+results?|results?|discussion|"
    r"conclusions?|limitations?)\b)",
)

NUMBERED_HEADING_PATTERN = re.compile(
    r"^(?P<number>\d+(?:\.\d+)*|[A-Z](?:\.\d+)+)\b",
    flags=re.IGNORECASE,
)

BACK_MATTER_BOUNDARY_PATTERN = re.compile(
    r"^(?:references?|appendix|supplementary(?:\s+material)?)\b",
    flags=re.IGNORECASE,
)

LETTERED_HEADING_PATTERN = re.compile(r"^[A-Z](?:\.\d+)*\.?\s+", flags=re.IGNORECASE)


def heading_title(match: re.Match[str]) -> str:
    title = match.group("markdown_title") or match.group("bold_title") or ""
    return title.strip().strip("*_ ")


def heading_level(match: re.Match[str]) -> int:
    title = heading_title(match)
    numbered = NUMBERED_HEADING_PATTERN.match(title)
    if numbered:
        return numbered.group("number").count(".") + 1
    markdown = match.group("markdown")
    if markdown:
        return len(markdown)
    return 1


@dataclass(frozen=True)
class SourceQuality:
    status: str
    issues: list[str]
    characters: int
    headings: int
    replacement_characters: int


def count_pdf_pages(pdf_path: Path) -> int | None:
    try:
        from pypdf import PdfReader

        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def evaluate_source(markdown: str, page_count: int | None = None) -> SourceQuality:
    stripped = markdown.strip()
    headings = len(list(HEADING_PATTERN.finditer(stripped)))
    replacements = stripped.count("\ufffd")
    issues: list[str] = []

    minimum = max(1000, (page_count or 0) * 80)
    if len(stripped) < minimum:
        issues.append(f"source text is too short: {len(stripped)} chars, expected at least {minimum}")
    if headings < 2:
        issues.append("source text has fewer than two Markdown headings")
    if replacements > max(10, len(stripped) // 1000):
        issues.append("source text contains many Unicode replacement characters")
    natural_language_characters = len(re.findall(r"[A-Za-z\u4e00-\u9fff]", stripped))
    if natural_language_characters < 100:
        issues.append("source text does not contain a substantial natural-language passage")

    heading_matches = list(HEADING_PATTERN.finditer(stripped))
    in_back_matter = False
    for index, match in enumerate(heading_matches):
        normalized_title = heading_title(match)
        if BACK_MATTER_BOUNDARY_PATTERN.search(normalized_title):
            in_back_matter = True
        if not CORE_HEADING_PATTERN.search(normalized_title):
            continue
        if in_back_matter and LETTERED_HEADING_PATTERN.search(normalized_title):
            continue
        if NON_CORE_HEADING_PATTERN.search(normalized_title) or len(normalized_title) > 180:
            continue
        current_level = heading_level(match)
        end = len(stripped)
        for following in heading_matches[index + 1 :]:
            if heading_level(following) <= current_level:
                end = following.start()
                break
        body = stripped[match.end() : end]
        body_characters = len(re.findall(r"[A-Za-z\u4e00-\u9fff]", body))
        if body_characters < 40:
            issues.append(
                f"core section has too little body text: {normalized_title} "
                f"({body_characters} natural-language chars)"
            )

    critical = any("too short" in item or "substantial" in item for item in issues)
    status = "failed" if critical else ("warning" if issues else "passed")
    return SourceQuality(status, issues, len(stripped), headings, replacements)


def safe_extract_zip(zip_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    root = output_dir.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (output_dir / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"Unsafe ZIP entry: {member.filename}")
        archive.extractall(output_dir)


def select_markdown_file(root: Path) -> Path:
    candidates = list(root.rglob("*.md")) + list(root.rglob("*.markdown"))
    if not candidates:
        raise FileNotFoundError(f"No Markdown file found under {root}")
    preferred = [path for path in candidates if path.name.lower() == "full.md"]
    return max(preferred or candidates, key=lambda path: path.stat().st_size)


def copy_source_assets(extracted_root: Path, paper_dir: Path, selected_markdown: Path) -> int:
    destination = paper_dir / "source-assets"
    if destination.exists():
        shutil.rmtree(destination)
    copied = 0
    for path in extracted_root.rglob("*"):
        if not path.is_file() or path == selected_markdown:
            continue
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
            continue
        relative = path.relative_to(extracted_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def _split_large_block(block: str, max_chars: int) -> list[str]:
    if len(block) <= max_chars:
        return [block]
    paragraphs = re.split(r"(\n\s*\n)", block)
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(current) + len(paragraph) <= max_chars:
            current += paragraph
            continue
        if current.strip():
            chunks.append(current.strip() + "\n")
        while len(paragraph) > max_chars:
            cut = paragraph.rfind("\n", 0, max_chars)
            if cut < max_chars // 2:
                cut = paragraph.rfind(" ", 0, max_chars)
            if cut < max_chars // 2:
                cut = max_chars
            chunks.append(paragraph[:cut].strip() + "\n")
            paragraph = paragraph[cut:].lstrip()
        current = paragraph
    if current.strip():
        chunks.append(current.strip() + "\n")
    return chunks


def split_markdown(markdown: str, max_chars: int = 18000) -> list[tuple[str, str]]:
    matches = list(HEADING_PATTERN.finditer(markdown))
    blocks: list[tuple[str, str]] = []
    if not matches:
        blocks = [("Document", markdown)]
    else:
        if matches[0].start() > 0 and markdown[: matches[0].start()].strip():
            blocks.append(("Preamble", markdown[: matches[0].start()]))
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
            title = heading_title(match) or "Section"
            blocks.append((title, markdown[match.start() : end]))

    output: list[tuple[str, str]] = []
    for title, block in blocks:
        pieces = _split_large_block(block, max_chars)
        for piece_index, piece in enumerate(pieces, start=1):
            label = title if len(pieces) == 1 else f"{title} ({piece_index}/{len(pieces)})"
            output.append((label, piece))
    return output


def build_sections(paper_dir: Path, markdown: str, max_chars: int = 18000) -> dict[str, Any]:
    sections_dir = paper_dir / "source-sections"
    if sections_dir.exists():
        shutil.rmtree(sections_dir)
    sections_dir.mkdir(parents=True)

    chunks = split_markdown(markdown, max_chars=max_chars)
    manifest_items: list[dict[str, Any]] = []
    used_names: set[str] = set()
    for index, (title, content) in enumerate(chunks, start=1):
        try:
            base = slugify(title)[:50]
        except ValueError:
            base = "section"
        filename = f"{index:03d}-{base}.md"
        while filename in used_names:
            filename = f"{index:03d}-{base}-{len(used_names)}.md"
        used_names.add(filename)
        stored_content = content.rstrip() + "\n"
        atomic_write_text(sections_dir / filename, stored_content)
        manifest_items.append(
            {
                "index": index,
                "title": title,
                "file": filename,
                "characters": len(stored_content),
                "sha256": hashlib.sha256(stored_content.encode("utf-8")).hexdigest(),
            }
        )

    manifest = {
        "source": "../source.md",
        "source_sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        "max_characters_per_section": max_chars,
        "section_count": len(manifest_items),
        "sections": manifest_items,
    }
    dump_yaml(sections_dir / "manifest.yaml", manifest)
    return manifest


def source_cache_valid(paper_dir: Path, pdf_hash: str) -> bool:
    source_path = paper_dir / "source.md"
    parse_path = paper_dir / "parse.yaml"
    if not source_path.is_file() or not parse_path.is_file():
        return False
    try:
        import yaml

        metadata = yaml.safe_load(parse_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    return (
        metadata.get("pdf_sha256") == pdf_hash
        and metadata.get("source_sha256") == sha256_file(source_path)
        and metadata.get("status") == "ready"
        and (metadata.get("quality") or {}).get("status") == "passed"
    )


def section_cache_valid(paper_dir: Path, source_hash: str, max_chars: int) -> bool:
    manifest_path = paper_dir / "source-sections" / "manifest.yaml"
    if not manifest_path.is_file():
        return False
    try:
        manifest = load_yaml(manifest_path)
    except ValueError:
        return False
    sections = manifest.get("sections")
    if (
        manifest.get("source_sha256") != source_hash
        or manifest.get("max_characters_per_section") != max_chars
        or not isinstance(sections, list)
        or manifest.get("section_count") != len(sections)
    ):
        return False
    root = manifest_path.parent.resolve()
    for item in sections:
        if not isinstance(item, dict) or not str(item.get("file", "")).strip():
            return False
        section_path = (root / str(item["file"])).resolve()
        if root not in section_path.parents or not section_path.is_file():
            return False
        if item.get("sha256") != sha256_file(section_path):
            return False
    return True

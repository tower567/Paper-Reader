#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import re
import tempfile
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

import yaml


ALLOWED_STATUSES = {
    "discovered",
    "screened",
    "queued",
    "downloaded",
    "parsed",
    "translating",
    "reading",
    "verification-required",
    "verified",
    "synthesized",
}

REQUIRED_TOP_LEVEL = (
    "id",
    "title",
    "title_zh",
    "authors",
    "year",
    "identifiers",
    "publication",
    "research",
    "artifacts",
    "workflow",
    "quality",
    "provenance",
)

REQUIRED_NOTE_HEADINGS = (
    "## 一句话总结",
    "## 核心贡献",
    "## 方法与实验",
    "## 局限性",
    "## 与当前研究的关系",
    "## 关键证据索引",
)

PLACEHOLDER_MARKERS = (
    "{{",
    "[待填写]",
    "[待翻译]",
    "[按原文章节调整]",
)


def today() -> str:
    return date.today().isoformat()


def resolve_repo(value: str | Path | None) -> Path:
    repo = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    skill = repo / ".agents" / "skills" / "manage-literature-repository"
    if not skill.is_dir():
        raise SystemExit(f"Not a Paper Reader repository: {repo}")
    return repo


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if not slug:
        raise ValueError(f"Cannot create an ASCII slug from: {value!r}")
    return slug


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return data


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        dir=path.parent,
        delete=False,
    )
    try:
        with handle:
            handle.write(content)
        os.replace(handle.name, path)
    except Exception:
        Path(handle.name).unlink(missing_ok=True)
        raise


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    content = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    )
    atomic_write_text(path, content)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def validate_paper_dir(paper_dir: Path, strict: bool = False) -> list[str]:
    issues: list[str] = []
    paper_dir = paper_dir.resolve()
    required_files = ["original.pdf", "translation.zh.md", "notes.md", "metadata.yaml"]
    for name in required_files:
        if not (paper_dir / name).is_file():
            issues.append(f"missing required file: {name}")

    metadata_path = paper_dir / "metadata.yaml"
    metadata: dict[str, Any] = {}
    if metadata_path.is_file():
        try:
            metadata = load_yaml(metadata_path)
        except ValueError as exc:
            issues.append(str(exc))

    if metadata:
        for key in REQUIRED_TOP_LEVEL:
            if key not in metadata:
                issues.append(f"metadata missing top-level key: {key}")

        paper_id = metadata.get("id")
        if paper_id != paper_dir.name:
            issues.append(
                f"metadata id {paper_id!r} does not match directory {paper_dir.name!r}"
            )
        if not metadata.get("title"):
            issues.append("metadata title is empty")
        if not isinstance(metadata.get("authors"), list) or not metadata.get("authors"):
            issues.append("metadata authors must contain at least one author")
        if not isinstance(metadata.get("year"), int):
            issues.append("metadata year must be an integer")

        status = nested(metadata, "workflow", "status")
        if status not in ALLOWED_STATUSES:
            issues.append(f"unsupported workflow status: {status!r}")

        translation_scope = nested(metadata, "workflow", "translation_scope")
        if translation_scope not in {
            "structured-summary",
            "full",
            "core-sections",
            "custom",
        }:
            issues.append(f"unsupported translation scope: {translation_scope!r}")

        reading_mode = nested(metadata, "workflow", "reading_mode")
        if reading_mode is not None and reading_mode not in {"fast", "deep"}:
            issues.append(f"unsupported reading mode: {reading_mode!r}")
        time_budget = nested(metadata, "workflow", "time_budget_minutes")
        if reading_mode is not None:
            if not isinstance(time_budget, int) or time_budget <= 0:
                issues.append("workflow.time_budget_minutes must be a positive integer")
            elif reading_mode == "fast" and time_budget > 30:
                issues.append("fast reading mode must use a time budget of 30 minutes or less")

        if strict and nested(metadata, "workflow", "source_required") is True:
            required_files.extend(
                ("source.md", "parse.yaml", "source-sections/manifest.yaml")
            )
        if strict and reading_mode is not None:
            required_files.extend(("reading-plan.yaml", "reading-pack.md"))

        reproducibility = nested(metadata, "quality", "reproducibility")
        if reproducibility not in {"unknown", "low", "medium", "high"}:
            issues.append(f"unsupported reproducibility value: {reproducibility!r}")

        verification_level = nested(metadata, "quality", "verification_level")
        if verification_level is not None and verification_level not in {
            "targeted",
            "full",
        }:
            issues.append(f"unsupported verification level: {verification_level!r}")

        identifiers = metadata.get("identifiers")
        if strict and isinstance(identifiers, dict):
            if not any(
                str(identifiers.get(key, "")).strip()
                for key in ("doi", "arxiv", "source_url")
            ):
                issues.append("strict mode requires DOI, arXiv ID, or source URL")

        if "{{" in metadata_path.read_text(encoding="utf-8"):
            issues.append("metadata contains unresolved template placeholders")

    for name in required_files:
        if not (paper_dir / name).is_file() and f"missing required file: {name}" not in issues:
            issues.append(f"missing required file: {name}")

    pdf_path = paper_dir / "original.pdf"
    if pdf_path.is_file():
        header = pdf_path.read_bytes()[:120]
        if header.startswith(b"version https://git-lfs.github.com/spec/v1"):
            issues.append("original.pdf is a Git LFS pointer; run git lfs pull")
        elif not header.startswith(b"%PDF-"):
            issues.append("original.pdf does not have a PDF header")
        elif strict and pdf_path.stat().st_size < 500:
            issues.append("original.pdf is unexpectedly small")

        expected_hash = nested(metadata, "provenance", "pdf_sha256") if metadata else None
        if strict and not expected_hash:
            issues.append("strict mode requires provenance.pdf_sha256")
        elif expected_hash and expected_hash != sha256_file(pdf_path):
            issues.append("provenance.pdf_sha256 does not match original.pdf")

    translation_path = paper_dir / "translation.zh.md"
    if translation_path.is_file():
        translation = translation_path.read_text(encoding="utf-8")
        if "# 中文翻译" not in translation:
            issues.append("translation.zh.md is missing its title")
        if "## 翻译信息" not in translation:
            issues.append("translation.zh.md is missing translation metadata")
        if len(re.findall(r"^#{2,3} ", translation, flags=re.MULTILINE)) < 4:
            issues.append("translation.zh.md has too few structured sections")
        if strict:
            scope = nested(metadata, "workflow", "translation_scope") or "full"
            minimum_translation = {
                "structured-summary": 600,
                "full": 1200,
                "core-sections": 700,
                "custom": 400,
            }[scope]
            if len(translation.strip()) < minimum_translation:
                issues.append(
                    "translation.zh.md is too short for "
                    f"{scope} strict validation ({len(translation.strip())} < {minimum_translation})"
                )
        if strict:
            for marker in PLACEHOLDER_MARKERS:
                if marker in translation:
                    issues.append(f"translation.zh.md contains placeholder: {marker}")

    notes_path = paper_dir / "notes.md"
    if notes_path.is_file():
        notes = notes_path.read_text(encoding="utf-8")
        for heading in REQUIRED_NOTE_HEADINGS:
            if heading not in notes:
                issues.append(f"notes.md is missing heading: {heading}")
        minimum_notes = (
            650 if nested(metadata, "workflow", "reading_mode") == "fast" else 900
        )
        if strict and len(notes.strip()) < minimum_notes:
            issues.append(
                "notes.md is too short for strict validation "
                f"({len(notes.strip())} < {minimum_notes})"
            )
        if strict:
            for marker in PLACEHOLDER_MARKERS:
                if marker in notes:
                    issues.append(f"notes.md contains placeholder: {marker}")
            if not re.search(
                r"(PDF\s*p\.|第\s*\d+\s*页|Sec\.|Fig\.|Table|Eq\.)",
                notes,
                flags=re.IGNORECASE,
            ):
                issues.append("notes.md lacks recognizable evidence locations")

    source_path = paper_dir / "source.md"
    parse_path = paper_dir / "parse.yaml"
    manifest_path = paper_dir / "source-sections" / "manifest.yaml"
    parse_metadata: dict[str, Any] = {}
    if source_path.is_file() and parse_path.is_file():
        try:
            parse_metadata = load_yaml(parse_path)
        except ValueError as exc:
            issues.append(str(exc))
        else:
            if parse_metadata.get("pdf_sha256") and pdf_path.is_file():
                if parse_metadata["pdf_sha256"] != sha256_file(pdf_path):
                    issues.append("parse.yaml pdf_sha256 does not match original.pdf")
            if parse_metadata.get("source_sha256"):
                if parse_metadata["source_sha256"] != sha256_file(source_path):
                    issues.append("parse.yaml source_sha256 does not match source.md")
            if strict and nested(metadata, "workflow", "source_required") is True:
                if parse_metadata.get("status") != "ready":
                    issues.append("parse.yaml status must be ready")
                if nested(parse_metadata, "quality", "status") != "passed":
                    issues.append("strict mode requires source parsing quality to pass")

    if source_path.is_file() and manifest_path.is_file():
        try:
            manifest = load_yaml(manifest_path)
        except ValueError as exc:
            issues.append(str(exc))
        else:
            source_hash = sha256_file(source_path)
            if manifest.get("source_sha256") != source_hash:
                issues.append("source-sections manifest source_sha256 does not match source.md")
            sections = manifest.get("sections")
            if not isinstance(sections, list) or not sections:
                issues.append("source-sections manifest must contain at least one section")
            else:
                if manifest.get("section_count") != len(sections):
                    issues.append("source-sections manifest section_count is inconsistent")
                if parse_metadata and parse_metadata.get("section_count") != len(sections):
                    issues.append("parse.yaml section_count does not match source-sections manifest")
                sections_root = manifest_path.parent.resolve()
                for item in sections:
                    if not isinstance(item, dict) or not str(item.get("file", "")).strip():
                        issues.append("source-sections manifest contains an invalid section entry")
                        continue
                    section_path = (sections_root / str(item["file"])).resolve()
                    if sections_root not in section_path.parents:
                        issues.append("source-sections manifest contains an unsafe section path")
                        continue
                    if not section_path.is_file():
                        issues.append(f"missing source section: {item['file']}")
                        continue
                    if item.get("sha256") != sha256_file(section_path):
                        issues.append(f"source section hash mismatch: {item['file']}")

    reading_plan_path = paper_dir / "reading-plan.yaml"
    reading_pack_path = paper_dir / "reading-pack.md"
    if reading_plan_path.is_file():
        try:
            reading_plan = load_yaml(reading_plan_path)
        except ValueError as exc:
            issues.append(str(exc))
        else:
            reading_mode = nested(metadata, "workflow", "reading_mode")
            if reading_mode and reading_plan.get("mode") != reading_mode:
                issues.append("reading-plan.yaml mode does not match metadata")
            if manifest_path.is_file():
                try:
                    manifest_for_plan = load_yaml(manifest_path)
                except ValueError:
                    manifest_for_plan = {}
                if reading_plan.get("source_sha256") != manifest_for_plan.get(
                    "source_sha256"
                ):
                    issues.append("reading-plan.yaml source_sha256 does not match manifest")
            selected = reading_plan.get("selected_sections")
            if not isinstance(selected, list) or not selected:
                issues.append("reading-plan.yaml must select at least one section")
            pack_metadata = reading_plan.get("reading_pack")
            if not isinstance(pack_metadata, dict):
                issues.append("reading-plan.yaml is missing reading_pack metadata")
            elif reading_pack_path.is_file() and pack_metadata.get("sha256"):
                if pack_metadata["sha256"] != sha256_file(reading_pack_path):
                    issues.append("reading-pack.md hash does not match reading-plan.yaml")

    if reading_pack_path.is_file():
        pack_text = reading_pack_path.read_text(encoding="utf-8")
        if "# 限时阅读包" not in pack_text:
            issues.append("reading-pack.md is missing its generated title")
        if strict and len(pack_text.strip()) < 500:
            issues.append("reading-pack.md is unexpectedly short")
        if (
            strict
            and nested(metadata, "workflow", "reading_mode") == "fast"
            and len(pack_text) > 40000
        ):
            issues.append("fast reading-pack.md exceeds the 40000 character hard limit")

    return issues

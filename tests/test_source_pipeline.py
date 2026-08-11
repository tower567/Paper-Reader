from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".agents" / "skills" / "manage-literature-repository" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from paperlib import validate_paper_dir
from source_pipeline import (
    build_sections,
    evaluate_source,
    section_cache_valid,
    source_cache_valid,
    split_markdown,
)


def test_build_sections_creates_bounded_manifest(tmp_path: Path) -> None:
    markdown = (
        "# Paper\n\n"
        + "Opening text. " * 200
        + "\n\n## Method\n\n"
        + "Method text. " * 300
        + "\n\n## Experiments\n\n"
        + "Experiment text. " * 300
    )
    manifest = build_sections(tmp_path, markdown, max_chars=1200)
    assert manifest["section_count"] >= 3
    assert all(item["characters"] <= 1300 for item in manifest["sections"])
    assert (tmp_path / "source-sections" / "manifest.yaml").is_file()


def test_split_markdown_recognizes_numbered_bold_headings() -> None:
    markdown = (
        "# Paper\n\nAbstract.\n\n"
        "**1 Introduction**\n\nIntro text.\n\n"
        "## **2 Related Work**\n\nPrior work.\n\n"
        "**H.2 ALFWorld, World Model Belief Update**\n\nAppendix text.\n"
    )
    titles = [title for title, _ in split_markdown(markdown)]
    assert "1 Introduction" in titles
    assert "2 Related Work" in titles
    assert "H.2 ALFWorld, World Model Belief Update" in titles


def test_source_quality_rejects_short_text() -> None:
    result = evaluate_source("# Title\n\nshort", page_count=10)
    assert result.status == "failed"
    assert result.issues


def test_source_quality_warns_on_empty_core_section() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n**1 Introduction**\n\n"
        + "## 2 Related Work\n\n"
        + "Related work content. " * 100
        + "\n\n## 3 Conclusion\n\n"
        + "Conclusion content. " * 100
    )
    result = evaluate_source(markdown, page_count=4)
    assert result.status == "warning"
    assert any("1 Introduction" in issue for issue in result.issues)


def test_source_quality_accepts_core_parent_with_subsection_body() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n## 5 Experiments\n\n"
        + "### 5.1 Experimental Setup\n\n"
        + "Experimental setup content. " * 100
        + "\n\n### 5.2 Results\n\n"
        + "Results content. " * 100
        + "\n\n## 6 Conclusion\n\n"
        + "Conclusion content. " * 100
    )
    result = evaluate_source(markdown, page_count=5)
    assert result.status == "passed"


def test_source_quality_ignores_appendix_and_long_example_headings() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n## 1 Method\n\n"
        + "Method content. " * 100
        + "\n\n## B Experiment Details\n\n"
        + "\n\n## B. Details for Experiment Settings\n\n"
        + "\n\n## B Method Details\n\n"
        + "\n\n## E Extended Results\n\n"
        + "\n\n## E. Evaluation Metrics\n\n"
        + "\n\n## D Benchmark Specifications and Evaluation Protocols\n\n"
        + "\n\n## shopping: search and sort Given that you are on the Amazon search "
        + "results page, this workflow searches for a product and sorts the results "
        + "using a sequence of interface actions that is represented as an example.\n\n"
        + "\n\n## 6 Conclusion\n\n"
        + "Conclusion content. " * 100
    )
    result = evaluate_source(markdown, page_count=5)
    assert result.status == "passed"


def test_source_quality_ignores_lettered_core_heading_after_references() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n## 1 Method\n\n"
        + "Method content. " * 100
        + "\n\n## References\n\n"
        + "Reference content. " * 100
        + "\n\n## A Method\n\n"
    )
    result = evaluate_source(markdown, page_count=5)
    assert result.status == "passed"


def test_source_quality_checks_lettered_core_heading_before_references() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n## A Method\n\n"
        + "\n\n## References\n\n"
        + "Reference content. " * 100
    )
    result = evaluate_source(markdown, page_count=5)
    assert result.status == "warning"
    assert "core section has too little body text: A Method" in result.issues[0]


def test_source_quality_keeps_regular_a_prefixed_core_heading() -> None:
    markdown = (
        "# Paper\n\n"
        + "Abstract content. " * 100
        + "\n\n## A Method for Memory Evolution\n\n"
        + "\n\n## 6 Conclusion\n\n"
        + "Conclusion content. " * 100
    )
    result = evaluate_source(markdown, page_count=5)
    assert result.status == "warning"
    assert any("A Method for Memory Evolution" in issue for issue in result.issues)


def test_prepare_source_import_and_cache(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    paper = repo / "inbox" / "papers" / "2026-test-source"
    paper.mkdir(parents=True)
    (repo / ".agents" / "skills" / "manage-literature-repository").mkdir(parents=True)
    pdf = paper / "original.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"0" * 700 + b"\n%%EOF\n")
    metadata = {
        "id": paper.name,
        "title": "Source Test",
        "title_zh": "",
        "authors": ["Test"],
        "year": 2026,
        "identifiers": {"doi": "", "arxiv": "2608.00001", "source_url": ""},
        "publication": {"venue": "", "type": "", "status": "preprint"},
        "research": {"domains": [], "topics": [], "task": "", "method_family": ""},
        "artifacts": {
            "pdf": "original.pdf",
            "translation": "translation.zh.md",
            "notes": "notes.md",
            "source": "source.md",
        },
        "workflow": {
            "status": "downloaded",
            "translation_scope": "core-sections",
            "source_required": True,
        },
        "quality": {
            "relevance": None,
            "source_verified": False,
            "evidence_verified": False,
            "translation_verified": False,
            "reproducibility": "unknown",
        },
        "provenance": {
            "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "last_updated": "2026-08-09",
        },
    }
    (paper / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    source = tmp_path / "arxiv.md"
    source.write_text(
        "# Source Test\n\n"
        + "Abstract content. " * 100
        + "\n\n## Introduction\n\n"
        + "Introduction content. " * 100
        + "\n\n## Method\n\n"
        + "Method content. " * 100,
        encoding="utf-8",
    )

    command = [
        sys.executable,
        str(SCRIPTS / "prepare_source.py"),
        str(paper),
        "--backend",
        "import",
        "--source-file",
        str(source),
        "--source-backend",
        "arxiv-mcp",
    ]
    first = subprocess.run(command, check=True, text=True, capture_output=True)
    assert "QUALITY: passed" in first.stdout
    assert (paper / "source.md").is_file()
    assert (paper / "parse.yaml").is_file()
    assert (paper / "source-sections" / "manifest.yaml").is_file()
    assert source_cache_valid(paper, hashlib.sha256(pdf.read_bytes()).hexdigest())
    assert section_cache_valid(
        paper,
        hashlib.sha256((paper / "source.md").read_bytes()).hexdigest(),
        18000,
    )

    second = subprocess.run(command, check=True, text=True, capture_output=True)
    assert "CACHED:" in second.stdout
    assert "SECTION_CACHE: REUSED" in second.stdout

    rebuilt = subprocess.run(
        [*command, "--max-section-chars", "1000"],
        check=True,
        text=True,
        capture_output=True,
    )
    assert "SECTION_CACHE: REBUILT" in rebuilt.stdout
    parse_metadata = yaml.safe_load((paper / "parse.yaml").read_text(encoding="utf-8"))
    manifest = yaml.safe_load(
        (paper / "source-sections" / "manifest.yaml").read_text(encoding="utf-8")
    )
    assert parse_metadata["section_count"] == manifest["section_count"]


def test_strict_validation_detects_tampered_source_section(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    paper = repo / "inbox" / "papers" / "2026-test-integrity"
    paper.mkdir(parents=True)
    (repo / ".agents" / "skills" / "manage-literature-repository").mkdir(parents=True)
    pdf = paper / "original.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"0" * 700 + b"\n%%EOF\n")
    (paper / "translation.zh.md").write_text(
        "# 中文翻译\n\n## 翻译信息\n\n已完成。\n\n## 摘要\n\n"
        + "翻译内容。" * 150
        + "\n\n## 方法\n\n"
        + "方法内容。" * 100
        + "\n\n## 结论\n\n"
        + "结论内容。" * 100,
        encoding="utf-8",
    )
    (paper / "notes.md").write_text(
        "# 阅读笔记\n\n## 一句话总结\n\n总结，见 PDF p. 1。\n\n"
        "## 核心贡献\n\n贡献，见 PDF p. 1。\n\n"
        "## 方法与实验\n\n方法，见 PDF p. 1。\n\n"
        "## 局限性\n\n局限，见 PDF p. 1。\n\n"
        "## 与当前研究的关系\n\n关系，见 PDF p. 1。\n\n"
        "## 关键证据索引\n\n证据，见 PDF p. 1。\n\n"
        + "补充分析。" * 200,
        encoding="utf-8",
    )
    metadata = {
        "id": paper.name,
        "title": "Integrity Test",
        "title_zh": "",
        "authors": ["Test"],
        "year": 2026,
        "identifiers": {"doi": "", "arxiv": "2608.00002", "source_url": ""},
        "publication": {},
        "research": {},
        "artifacts": {},
        "workflow": {
            "status": "parsed",
            "translation_scope": "core-sections",
            "source_required": True,
        },
        "quality": {"reproducibility": "unknown"},
        "provenance": {"pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()},
    }
    (paper / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    source = tmp_path / "source.md"
    source.write_text(
        "# Integrity Test\n\n"
        + "Abstract content. " * 100
        + "\n\n## Method\n\n"
        + "Method content. " * 100,
        encoding="utf-8",
    )
    command = [
        sys.executable,
        str(SCRIPTS / "prepare_source.py"),
        str(paper),
        "--backend",
        "import",
        "--source-file",
        str(source),
    ]
    subprocess.run(command, check=True, text=True, capture_output=True)
    manifest = yaml.safe_load(
        (paper / "source-sections" / "manifest.yaml").read_text(encoding="utf-8")
    )
    section = paper / "source-sections" / manifest["sections"][0]["file"]
    section.write_text(section.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")

    issues = validate_paper_dir(paper, strict=True)
    assert any("source section hash mismatch" in issue for issue in issues)

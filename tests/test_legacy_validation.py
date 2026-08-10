from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".agents" / "skills" / "manage-literature-repository" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from paperlib import validate_paper_dir


def test_legacy_record_does_not_require_source_files(tmp_path: Path) -> None:
    paper = tmp_path / "2025-test-legacy"
    paper.mkdir()
    pdf = paper / "original.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"0" * 700 + b"\n%%EOF\n")
    translation = (
        "# 中文翻译\n\n## 翻译信息\n\n已校验\n\n## 摘要\n\n"
        + "中文翻译内容。" * 100
        + "\n\n## 方法\n\n"
        + "方法内容。" * 100
        + "\n\n## 结论\n\n"
        + "结论内容。" * 100
    )
    notes = (
        "# 阅读笔记\n\n## 一句话总结\n\n总结，见 PDF p. 1。\n\n"
        "## 核心贡献\n\n贡献，见 PDF p. 1。\n\n"
        "## 方法与实验\n\n方法，见 PDF p. 1。\n\n"
        "## 局限性\n\n局限，见 PDF p. 1。\n\n"
        "## 与当前研究的关系\n\n关系，见 PDF p. 1。\n\n"
        "## 关键证据索引\n\n证据，见 PDF p. 1。\n\n"
        + "补充分析。" * 200
    )
    (paper / "translation.zh.md").write_text(translation, encoding="utf-8")
    (paper / "notes.md").write_text(notes, encoding="utf-8")
    metadata = {
        "id": paper.name,
        "title": "Legacy",
        "title_zh": "",
        "authors": ["Test"],
        "year": 2025,
        "identifiers": {"doi": "", "arxiv": "2501.00001", "source_url": ""},
        "publication": {},
        "research": {},
        "artifacts": {},
        "workflow": {"status": "verification-required", "translation_scope": "full"},
        "quality": {"reproducibility": "unknown"},
        "provenance": {"pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()},
    }
    (paper / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    issues = validate_paper_dir(paper, strict=True)
    assert not [issue for issue in issues if "source.md" in issue or "parse.yaml" in issue]


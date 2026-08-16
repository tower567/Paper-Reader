from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = (
    REPO / ".agents" / "skills" / "manage-literature-repository" / "scripts"
)
sys.path.insert(0, str(SKILL_SCRIPTS))

from build_obsidian import build_vault, classify_tracks, safe_paper_dir  # noqa: E402


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_classify_tracks_supports_multiple_research_views() -> None:
    tracks = classify_tracks(
        {
            "title": "Skill-Pro",
            "topics": ["procedural memory", "experience reuse"],
        },
        {},
    )
    assert tracks == ["skill-evolution", "memory-evolution"]

    assert classify_tracks(
        {"title": "OpenVLA", "domains": ["robotics"]}, {}
    ) == ["vla-embodied-ai"]


def test_explicit_tracks_override_keyword_classification() -> None:
    metadata = {"research": {"tracks": ["vla-embodied-ai"]}}
    assert classify_tracks({"title": "Agent Memory"}, metadata) == [
        "vla-embodied-ai"
    ]


def test_build_vault_generates_paper_page_bases_and_research_folders(
    tmp_path: Path,
) -> None:
    paper = tmp_path / "papers" / "2026-example"
    paper.mkdir(parents=True)
    metadata = {
        "id": "2026-example",
        "title": "Example Skill Memory",
        "title_zh": "示例技能记忆论文",
        "authors": ["A. Researcher"],
        "year": 2026,
        "identifiers": {"source_url": "https://example.test/paper"},
        "publication": {"venue": "ExampleConf"},
        "research": {
            "domains": ["LLM agents"],
            "topics": ["reusable skills", "agent memory"],
            "task": "experience reuse",
            "method_family": "external procedural memory",
        },
        "artifacts": {
            "pdf": "original.pdf",
            "translation": "translation.zh.md",
            "notes": "notes.md",
            "reading_pack": "reading-pack.md",
        },
        "workflow": {
            "status": "verified",
            "reading_mode": "fast",
            "translation_scope": "structured-summary",
        },
        "quality": {"reproducibility": "medium"},
        "provenance": {"last_updated": "2026-08-11"},
    }
    write_yaml(paper / "metadata.yaml", metadata)
    for name in ("original.pdf", "translation.zh.md", "notes.md", "reading-pack.md"):
        (paper / name).write_text("placeholder", encoding="utf-8")

    record = {
        "id": "2026-example",
        "title": metadata["title"],
        "title_zh": metadata["title_zh"],
        "authors": metadata["authors"],
        "year": 2026,
        "venue": "ExampleConf",
        "domains": ["LLM agents"],
        "topics": ["reusable skills", "agent memory"],
        "task": "experience reuse",
        "method_family": "external procedural memory",
        "status": "verified",
        "path": "papers/2026-example",
    }

    summary = build_vault(tmp_path, [record])

    assert summary["paper_count"] == 1
    page = (paper / "paper.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(page.split("---", 2)[1])
    assert frontmatter["display_title"] == "示例技能记忆论文"
    assert frontmatter["read"] is False
    assert frontmatter["research_tracks"] == ["Skill 自进化", "Memory 自进化"]
    assert "research/skill-evolution" in frontmatter["tags"]
    assert "![[papers/2026-example/original.pdf#height=850]]" in page
    assert "![[papers/2026-example/translation.zh.md]]" in page

    all_base = yaml.safe_load((tmp_path / "library" / "全部论文.base").read_text())
    assert 'file.hasTag("paper")' in all_base["filters"]["and"]
    assert "note.read" in all_base["views"][0]["order"]
    assert "✅ " in all_base["formulas"]["paper_link"]

    page_path = paper / "paper.md"
    page_path.write_text(page.replace("read: false", "read: true"), encoding="utf-8")
    build_vault(tmp_path, [record])
    rebuilt = yaml.safe_load(page_path.read_text(encoding="utf-8").split("---", 2)[1])
    assert rebuilt["read"] is True
    skill_base = yaml.safe_load(
        (tmp_path / "library" / "研究分类" / "Skill 自进化" / "论文.base").read_text()
    )
    assert 'file.hasTag("research/skill-evolution")' in skill_base["filters"]["and"]
    assert (tmp_path / "00-论文库.md").is_file()
    assert (
        tmp_path / "library" / "研究分类" / "VLA 具身智能" / "研究主页.md"
    ).is_file()


def test_safe_paper_dir_rejects_escape(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsafe paper path"):
        safe_paper_dir(tmp_path, "../outside")

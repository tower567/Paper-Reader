from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / ".agents" / "skills" / "manage-literature-repository" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from plan_reading import create_plan
from paperlib import validate_paper_dir


def make_paper(tmp_path: Path) -> Path:
    paper = tmp_path / "2026-test-fast-reader"
    sections_root = paper / "source-sections"
    sections_root.mkdir(parents=True)
    metadata = {
        "id": paper.name,
        "title": "Fast Reader Test",
        "title_zh": "",
        "authors": ["Test"],
        "year": 2026,
        "identifiers": {"doi": "", "arxiv": "2608.00003", "source_url": ""},
        "publication": {},
        "research": {},
        "artifacts": {},
        "workflow": {
            "status": "parsed",
            "reading_mode": "fast",
            "time_budget_minutes": 30,
            "translation_scope": "structured-summary",
            "source_required": True,
        },
        "quality": {"reproducibility": "unknown"},
        "provenance": {"last_updated": "2026-08-10"},
    }
    (paper / "metadata.yaml").write_text(
        yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    sections = [
        ("Paper Title", "Title information. " * 20),
        ("Abstract", "Abstract evidence. " * 80),
        ("1 Introduction", "Introduction evidence. " * 80),
        ("2 Related Work", "Prior work. " * 80),
        (
            "3 Method",
            "Method evidence. " * 80 + "\n\n![diagram](images/method.png)\n",
        ),
        (
            "4 Main Results",
            "Result prose. " * 50
            + "\n\n| Model | Score |\n|---|---|\n| A | 1 |\n"
            + "\n\n| Model | Cost |\n|---|---|\n| A | 2 |\n"
            + "\n\n| Model | Extra |\n|---|---|\n| A | 3 |\n",
        ),
        ("5 Conclusion and Limitations", "Conclusion evidence. " * 80),
        ("References", "Citation. " * 200),
        ("A.1 Prompt Templates", "Prompt text. " * 200),
        ("A.2 Ablation Details", "Ablation evidence. " * 80),
    ]
    manifest_sections = []
    for index, (title, content) in enumerate(sections, start=1):
        filename = f"{index:03d}-section.md"
        path = sections_root / filename
        path.write_text(f"## {title}\n\n{content}\n", encoding="utf-8")
        manifest_sections.append(
            {
                "index": index,
                "title": title,
                "file": filename,
                "characters": len(path.read_text(encoding="utf-8")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "source": "../source.md",
        "source_sha256": "source-hash",
        "max_characters_per_section": 18000,
        "section_count": len(manifest_sections),
        "sections": manifest_sections,
    }
    (sections_root / "manifest.yaml").write_text(
        yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return paper


def test_fast_plan_selects_core_sections_and_filters_visual_noise(tmp_path: Path) -> None:
    paper = make_paper(tmp_path)
    plan = create_plan(paper, "fast")

    titles = {item["title"] for item in plan["selected_sections"]}
    assert {"Abstract", "1 Introduction", "3 Method", "4 Main Results"}.issubset(titles)
    assert "5 Conclusion and Limitations" in titles
    assert "2 Related Work" not in titles
    assert "References" not in titles
    assert "A.1 Prompt Templates" not in titles
    assert plan["selected_section_count"] <= 8

    pack = (paper / "reading-pack.md").read_text(encoding="utf-8")
    assert "![diagram]" not in pack
    assert "图像已省略" in pack
    assert plan["reading_pack"]["tables_kept"] == 2
    assert plan["reading_pack"]["tables_omitted"] == 1
    assert plan["reading_pack"]["characters"] < 40000
    assert plan["reading_pack"]["sha256"] == hashlib.sha256(
        (paper / "reading-pack.md").read_bytes()
    ).hexdigest()

    metadata = yaml.safe_load((paper / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["artifacts"]["reading_plan"] == "reading-plan.yaml"
    assert metadata["workflow"]["reading_mode"] == "fast"
    assert metadata["quality"]["verification_level"] == "targeted"


def test_fast_plan_can_include_focused_appendix(tmp_path: Path) -> None:
    paper = make_paper(tmp_path)
    plan = create_plan(paper, "fast", focuses=["ablation"])

    titles = {item["title"] for item in plan["selected_sections"]}
    assert "A.2 Ablation Details" in titles


def test_fast_plan_can_use_exact_coordinator_section_order(tmp_path: Path) -> None:
    paper = make_paper(tmp_path)
    plan = create_plan(paper, "fast", section_indexes=[2, 5, 10])

    assert [item["index"] for item in plan["selected_sections"]] == [2, 5, 10]
    assert plan["selected_section_count"] == 3
    assert all(
        item["reason"].startswith("coordinator-curated")
        for item in plan["selected_sections"]
    )
    pack = (paper / "reading-pack.md").read_text(encoding="utf-8")
    assert pack.index("Abstract evidence") < pack.index("Method evidence")
    assert "Ablation evidence" in pack


def test_init_paper_defaults_to_fast_structured_summary(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".agents" / "skills" / "manage-literature-repository").mkdir(
        parents=True
    )
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4\n" + b"0" * 700 + b"\n%%EOF\n")
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "init_paper.py"),
            "--repo",
            str(repo),
            "--year",
            "2026",
            "--first-author",
            "Test",
            "--short-title",
            "fast-mode",
            "--title",
            "Fast Mode",
            "--arxiv",
            "2608.00004",
            "--pdf",
            str(pdf),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    paper = repo / "inbox" / "papers" / "2026-test-fast-mode"
    metadata = yaml.safe_load((paper / "metadata.yaml").read_text(encoding="utf-8"))
    assert metadata["workflow"]["reading_mode"] == "fast"
    assert metadata["workflow"]["time_budget_minutes"] == 30
    assert metadata["workflow"]["translation_scope"] == "structured-summary"
    assert metadata["quality"]["verification_level"] == "targeted"
    assert "结构化中文导读" in (paper / "translation.zh.md").read_text(
        encoding="utf-8"
    )
    assert "阅读模式：fast" in (paper / "notes.md").read_text(encoding="utf-8")

    strict_issues = validate_paper_dir(paper, strict=True)
    assert "missing required file: reading-plan.yaml" in strict_issues
    assert "missing required file: reading-pack.md" in strict_issues

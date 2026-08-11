#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from paperlib import atomic_write_text, dump_yaml, load_yaml, resolve_repo


TRACKS: dict[str, dict[str, Any]] = {
    "skill-evolution": {
        "label": "Skill 自进化",
        "tag": "research/skill-evolution",
        "folder": "Skill 自进化",
        "description": "技能生成、抽取、检索、组合、策展、验证、维护与持续演化。",
        "terms": (
            "skill",
            "技能",
            "tool creation",
            "tool acquisition",
            "toolset",
            "workflow",
            "procedural",
            "procedure graph",
            "action learning",
        ),
    },
    "memory-evolution": {
        "label": "Memory 自进化",
        "tag": "research/memory-evolution",
        "folder": "Memory 自进化",
        "description": "智能体长期记忆、经验复用、检索、巩固、更新、治理与自适应演化。",
        "terms": (
            "memory",
            "记忆",
            "experience replay",
            "experience reuse",
            "experiential learning",
            "episodic",
            "retrieval",
            "long-term",
            "经验回放",
            "经验复用",
        ),
    },
    "vla-embodied-ai": {
        "label": "VLA 具身智能",
        "tag": "research/vla-embodied-ai",
        "folder": "VLA 具身智能",
        "description": "视觉—语言—动作模型、机器人学习、具身智能、操作策略、数据与评测。",
        "terms": (
            "vision-language-action",
            "vision language action",
            "robotics",
            "robot learning",
            "robot-learning",
            "robot manipulation",
            "visuomotor",
            "embodied-ai",
            "embodied artificial intelligence",
            "机器人",
            "具身",
            "视觉—语言—动作",
        ),
    },
    "other": {
        "label": "其他论文",
        "tag": "research/other",
        "folder": "其他论文",
        "description": "尚未归入 Skill、Memory 或 VLA 主线的论文。",
        "terms": (),
    },
}

TRACK_ALIASES = {
    "skill": "skill-evolution",
    "skill-evolution": "skill-evolution",
    "skill 自进化": "skill-evolution",
    "memory": "memory-evolution",
    "memory-evolution": "memory-evolution",
    "memory 自进化": "memory-evolution",
    "vla": "vla-embodied-ai",
    "vla-embodied-ai": "vla-embodied-ai",
    "vla 具身智能": "vla-embodied-ai",
    "embodied-ai": "vla-embodied-ai",
    "other": "other",
    "其他": "other",
    "其他论文": "other",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Obsidian paper landing pages, Bases, and research folders."
    )
    parser.add_argument("--repo", help="Paper Reader repository root; defaults to cwd")
    return parser.parse_args()


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def normalize_track(value: Any) -> str | None:
    label = str(value).strip().casefold().replace("_", "-")
    return TRACK_ALIASES.get(label)


def classify_tracks(record: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    research = metadata.get("research") or {}
    explicit = (
        research.get("tracks")
        or research.get("research_tracks")
        or record.get("research_tracks")
        or record.get("research_group")
    )
    explicit_tracks = [
        normalized
        for value in as_list(explicit)
        if (normalized := normalize_track(value)) is not None
    ]
    if explicit_tracks:
        return list(dict.fromkeys(explicit_tracks))

    values = [
        record.get("title"),
        record.get("title_zh"),
        metadata.get("title"),
        metadata.get("title_zh"),
        *(record.get("domains") or []),
        *(record.get("topics") or []),
        *(research.get("domains") or []),
        *(research.get("topics") or []),
        record.get("task"),
        record.get("method_family"),
        research.get("task"),
        research.get("method_family"),
    ]
    text = " ".join(str(value) for value in values if value).casefold()
    matched = [
        key
        for key, config in TRACKS.items()
        if key != "other" and any(term in text for term in config["terms"])
    ]
    return matched or ["other"]


def safe_paper_dir(repo: Path, relative: str) -> Path:
    root = repo.resolve()
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"unsafe paper path: {relative}")
    return target


def clean_mapping(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if value not in (None, "", [], {})
    }


def unique_strings(values: list[Any]) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))


def wiki_label(value: Any) -> str:
    return str(value).replace("|", "｜").replace("]", "］")


def paper_frontmatter(
    record: dict[str, Any], metadata: dict[str, Any], tracks: list[str]
) -> dict[str, Any]:
    research = metadata.get("research") or {}
    publication = metadata.get("publication") or {}
    workflow = metadata.get("workflow") or {}
    quality = metadata.get("quality") or {}
    provenance = metadata.get("provenance") or {}
    artifacts = metadata.get("artifacts") or {}
    identifiers = record.get("identifiers") or metadata.get("identifiers") or {}
    title = record.get("title") or metadata.get("title") or record.get("id")
    title_zh = record.get("title_zh") or metadata.get("title_zh") or ""
    display_title = title_zh or title
    aliases = unique_strings([title, title_zh])
    source_url = identifiers.get("source_url") if isinstance(identifiers, dict) else ""
    return clean_mapping(
        {
            "type": "paper",
            "paper_id": record.get("id") or metadata.get("id"),
            "display_title": display_title,
            "title": title,
            "title_zh": title_zh,
            "aliases": aliases,
            "authors": record.get("authors") or metadata.get("authors") or [],
            "year": record.get("year") or metadata.get("year"),
            "venue": record.get("venue") or publication.get("venue") or "",
            "status": record.get("status") or workflow.get("status") or "",
            "research_tracks": [TRACKS[key]["label"] for key in tracks],
            "domains": record.get("domains") or research.get("domains") or [],
            "topics": record.get("topics") or research.get("topics") or [],
            "task": record.get("task") or research.get("task") or "",
            "method_family": record.get("method_family")
            or research.get("method_family")
            or "",
            "reading_mode": workflow.get("reading_mode") or "legacy",
            "translation_scope": workflow.get("translation_scope") or "",
            "reproducibility": quality.get("reproducibility") or "unknown",
            "source_url": source_url,
            "code_url": record.get("code_url") or artifacts.get("code_url") or "",
            "updated": provenance.get("last_updated") or "",
            "tags": ["paper", *(TRACKS[key]["tag"] for key in tracks)],
        }
    )


def paper_page(
    repo: Path,
    record: dict[str, Any],
    metadata: dict[str, Any],
    tracks: list[str],
) -> str:
    frontmatter = paper_frontmatter(record, metadata, tracks)
    artifacts = metadata.get("artifacts") or {}
    relative = str(record["path"]).strip("/")
    pdf_name = str(artifacts.get("pdf") or "original.pdf")
    translation_name = str(artifacts.get("translation") or "translation.zh.md")
    notes_name = str(artifacts.get("notes") or "notes.md")
    reading_pack_name = str(artifacts.get("reading_pack") or "reading-pack.md")
    title = wiki_label(frontmatter["display_title"])
    meta = " · ".join(
        str(value)
        for value in (frontmatter.get("year"), frontmatter.get("venue"))
        if value
    )
    track_links = " · ".join(
        f"[[library/研究分类/{TRACKS[key]['folder']}/研究主页|{TRACKS[key]['label']}]]"
        for key in tracks
    )
    entry_links = [
        f"[[{relative}/{pdf_name}|原文 PDF]]",
        f"[[{relative}/{translation_name}|中文整理]]",
        f"[[{relative}/{notes_name}|阅读笔记]]",
    ]
    if (repo / relative / reading_pack_name).is_file():
        entry_links.append(f"[[{relative}/{reading_pack_name}|限时阅读包]]")

    yaml_text = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        width=100,
    ).rstrip()
    return "\n".join(
        [
            "---",
            yaml_text,
            "---",
            "<!-- Generated by build_obsidian.py. Edit metadata.yaml, translation.zh.md, or notes.md instead. -->",
            "",
            f"# {title}",
            "",
            meta,
            "",
            f"> [!info] 研究分类\n> {track_links}",
            "",
            "## 阅读入口",
            "",
            " · ".join(entry_links),
            "",
            "> [!tip] 并排阅读\n> 在新标签页打开原文 PDF，再将中文整理或阅读笔记拖到另一侧窗格。",
            "",
            "## 原文 PDF",
            "",
            f"![[{relative}/{pdf_name}#height=850]]",
            "",
            "## 中文整理",
            "",
            f"![[{relative}/{translation_name}]]",
            "",
            "## 阅读笔记",
            "",
            f"![[{relative}/{notes_name}]]",
            "",
        ]
    )


def base_config(name: str, tag: str | None = None) -> dict[str, Any]:
    filters = ['file.hasTag("paper")']
    if tag:
        filters.append(f'file.hasTag("{tag}")')
    return {
        "filters": {"and": filters},
        "formulas": {"paper_link": "file.asLink(display_title)"},
        "properties": {
            "formula.paper_link": {"displayName": "论文"},
            "note.year": {"displayName": "年份"},
            "note.venue": {"displayName": "会议/期刊"},
            "note.research_tracks": {"displayName": "研究方向"},
            "note.status": {"displayName": "状态"},
            "note.reproducibility": {"displayName": "复现性"},
        },
        "views": [
            {
                "type": "table",
                "name": name,
                "order": [
                    "formula.paper_link",
                    "note.year",
                    "note.venue",
                    "note.research_tracks",
                    "note.status",
                    "note.reproducibility",
                ],
                "columnSize": {
                    "formula.paper_link": 420,
                    "note.year": 75,
                    "note.venue": 180,
                    "note.research_tracks": 180,
                    "note.status": 95,
                    "note.reproducibility": 90,
                },
            }
        ],
    }


def research_home(key: str, count: int) -> str:
    config = TRACKS[key]
    return "\n".join(
        [
            f"# {config['label']}",
            "",
            f"> {config['description']}",
            "",
            f"当前收录：**{count}** 篇。",
            "",
            "![[论文.base]]",
            "",
            "## 跨论文综合",
            "",
            "- [[synthesis/literature-map|文献地图]]",
            "- [[synthesis/comparison-matrix|比较矩阵]]",
            "- [[synthesis/baseline-candidates|Baseline 候选]]",
            "- [[synthesis/research-gaps|研究空白]]",
            "",
        ]
    )


def vault_home(total: int, counts: Counter[str]) -> str:
    lines = [
        "# Paper Reader 论文库",
        "",
        f"当前收录 **{total}** 篇已验证论文。",
        "",
        "## 研究分类",
        "",
    ]
    for key, config in TRACKS.items():
        lines.append(
            f"- [[library/研究分类/{config['folder']}/研究主页|{config['label']}]] — {counts[key]} 篇"
        )
    lines.extend(
        [
            "",
            "## 全部论文",
            "",
            "![[library/全部论文.base]]",
            "",
            "## 研究综合",
            "",
            "- [[synthesis/literature-map|文献地图]]",
            "- [[synthesis/comparison-matrix|比较矩阵]]",
            "- [[synthesis/baseline-candidates|Baseline 候选]]",
            "- [[synthesis/research-gaps|研究空白]]",
            "",
        ]
    )
    return "\n".join(lines)


def build_vault(
    repo: Path, records: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    repo = repo.expanduser().resolve()
    if records is None:
        records = (load_yaml(repo / "index.yaml").get("papers") or [])

    counts: Counter[str] = Counter()
    generated = 0
    for record in records:
        relative = str(record.get("path") or "")
        paper_dir = safe_paper_dir(repo, relative)
        metadata = load_yaml(paper_dir / "metadata.yaml")
        tracks = classify_tracks(record, metadata)
        record["research_tracks"] = tracks
        for key in tracks:
            counts[key] += 1
        atomic_write_text(
            paper_dir / "paper.md",
            paper_page(repo, record, metadata, tracks),
        )
        generated += 1

    library = repo / "library"
    dump_yaml(library / "全部论文.base", base_config("全部论文"))
    research_root = library / "研究分类"
    for key, config in TRACKS.items():
        folder = research_root / config["folder"]
        dump_yaml(folder / "论文.base", base_config(config["label"], config["tag"]))
        atomic_write_text(folder / "研究主页.md", research_home(key, counts[key]))
    atomic_write_text(repo / "00-论文库.md", vault_home(generated, counts))
    return {"paper_count": generated, "track_counts": dict(counts)}


def main() -> int:
    args = parse_args()
    repo = resolve_repo(args.repo)
    summary = build_vault(repo)
    print(f"Built Obsidian vault pages for {summary['paper_count']} papers.")
    for key, config in TRACKS.items():
        print(f"- {config['label']}: {summary['track_counts'].get(key, 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

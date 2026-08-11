from __future__ import annotations

import re
import tomllib
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / ".agents" / "skills" / "manage-literature-repository"


def skill_frontmatter() -> dict:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "SKILL.md must start with YAML frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict)
    return data


def test_skill_metadata_and_interface_are_consistent() -> None:
    metadata = skill_frontmatter()
    assert metadata["name"] == "manage-literature-repository"
    assert "30-minute" in metadata["description"]

    interface = yaml.safe_load(
        (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    )["interface"]
    assert "$manage-literature-repository" in interface["default_prompt"]
    assert 25 <= len(interface["short_description"]) <= 64


def test_codex_configuration_is_portable() -> None:
    config = tomllib.loads((REPO / ".codex" / "config.toml").read_text(encoding="utf-8"))
    arxiv = config["mcp_servers"]["arxiv"]
    assert arxiv["command"] == "micromamba"
    storage_path = arxiv["args"][arxiv["args"].index("--storage-path") + 1]
    assert storage_path == ".cache/arxiv"
    assert not Path(storage_path).is_absolute()


def test_public_template_protects_personal_literature() -> None:
    ignored = (REPO / ".gitignore").read_text(encoding="utf-8")
    for pattern in (
        ".local/",
        "papers/*",
        "inbox/papers/*",
        "inbox/candidates/*",
        "inbox/search-requests/*",
    ):
        assert pattern in ignored

    attributes = (REPO / ".gitattributes").read_text(encoding="utf-8")
    assert "*.pdf filter=lfs" in attributes


def test_public_documentation_exists() -> None:
    for path in (
        REPO / "README.md",
        REPO / "docs" / "DEPLOYMENT.md",
        REPO / "docs" / "USAGE.md",
        REPO / "SECURITY.md",
        REPO / ".github" / "workflows" / "ci.yml",
        SKILL / "scripts" / "build_obsidian.py",
        REPO / "00-论文库.md",
        REPO / "library" / "全部论文.base",
    ):
        assert path.is_file(), f"missing public project file: {path.relative_to(REPO)}"


def test_agent_configs_parse_and_use_fast_reading_pack() -> None:
    reader = tomllib.loads(
        (REPO / ".codex" / "agents" / "paper-reader.toml").read_text(
            encoding="utf-8"
        )
    )
    verifier = tomllib.loads(
        (REPO / ".codex" / "agents" / "evidence-verifier.toml").read_text(
            encoding="utf-8"
        )
    )
    scout = tomllib.loads(
        (REPO / ".codex" / "agents" / "literature-scout.toml").read_text(
            encoding="utf-8"
        )
    )
    assert "reading-pack.md" in reader["developer_instructions"]
    assert "six load-bearing claims" in verifier["developer_instructions"]
    assert scout["sandbox_mode"] == "workspace-write"

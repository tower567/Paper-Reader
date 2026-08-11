# Metadata schema

## Required top-level keys

- id, title, title_zh, authors, year
- identifiers, publication, research, artifacts
- workflow, quality, provenance

## Research classification

Use `research.tracks` for stable Obsidian research views. Supported canonical values are
`skill-evolution`, `memory-evolution`, and `vla-embodied-ai`. A paper may belong to multiple
tracks. Leave the list empty to use keyword-based classification during Obsidian generation.

## Identifiers

Store DOI without a resolver URL, arXiv ID with a version only when version-specific, and an authoritative source URL. A verified record needs at least one identifier or source URL.

## Workflow

Use the existing status lifecycle from discovered through verified and synthesized. Only the coordinator sets verified or synthesized.

Translation scope:

- structured-summary: fast default;
- core-sections: deep reading;
- full: explicit complete translation;
- custom: document inclusions and omissions in translation.zh.md.

Reading mode:

- fast: default; time_budget_minutes must be 30 or less and reading-plan/pack are required;
- deep: explicit upgrade for exhaustive reading, full translation, or high-stakes verification.

## Quality

- relevance: 1–5 or null;
- source_verified, evidence_verified, translation_verified: booleans;
- reproducibility: unknown, low, medium, or high;
- verification_level: targeted or full.

Targeted verification checks metadata, the abstract translation, and the limited evidence set defined in reading-plan.yaml.

## Provenance

Store PDF/source SHA-256 values, discovered_by, last_updated, and verified_by when promoted.

---
name: manage-literature-repository
description: Search, screen, download, parse, time-box, translate, read, verify, classify, and synthesize academic papers in a structured literature repository. Use for literature research, arXiv discovery, fast paper ingestion with a default 30-minute reading budget, HTML/local/MinerU parsing, bounded reading packs that omit unnecessary figures and tables, Chinese structured translations, evidence-linked notes, baseline selection, research gaps, and repository indexes.
---

# Manage Literature Repository

## Operating contract

- Treat the repository as the canonical literature store.
- Default to `fast` mode and target 30 minutes for an ordinary machine-readable paper.
- Store every paper once and preserve original.pdf without modification.
- Require source.md, parse.yaml, source-sections/manifest.yaml, reading-plan.yaml, reading-pack.md, translation.zh.md, notes.md, and metadata.yaml for new records.
- Classify papers through metadata and generated collections; never duplicate a PDF.
- Read reading-pack.md only. Open a source section or PDF page only to resolve a specific gap.
- Label Paper claim, Reported result, Reader inference, and Open question separately.
- Let only the coordinator update index.yaml, collections/generated, bibliography, and synthesis files.

## Choose a mode

### Fast mode: default

- Target 30 minutes after an accessible PDF or cached source is available.
- Read at most 8 selected sections and 30,000 packed characters.
- Translate the abstract fully, then faithfully compress the problem, method, headline results, conclusion, and limitations.
- Keep at most 2 result tables with at most 8 data rows each. Omit images from the reading pack.
- Verify metadata and at most 6 load-bearing claims. Check at most 3 PDF pages, only when source text is insufficient or conflicting.
- Skip related work, references, appendices, prompt dumps, example trajectories, exhaustive ablations, and figure OCR by default.
- Rebuild the index after promotion. Defer bibliography cleanup and cross-paper synthesis until requested or batched.

### Deep mode: opt in

Use `deep` only when the user requests full translation or exhaustive verification, the paper is a core baseline or novelty anchor, a high-stakes claim depends on omitted material, or the PDF is image-heavy/scanned. Read references/reading-protocol.md and references/translation-rules.md before deep work.

## Fast workflow

1. Inspect AGENTS.md and deduplicate against index.yaml by DOI, arXiv ID, and normalized title.
2. Initialize with scripts/init_paper.py. Keep the default `--reading-mode fast` and `structured-summary` translation scope.
3. Run scripts/prepare_source.py --backend auto. Auto reuses cache or arXiv Markdown, then uses fast local parsing. Run MinerU explicitly only when source quality fails.
4. Run scripts/plan_reading.py with the research question or a few `--focus` terms.
5. Read only reading-pack.md. Do not preload source.md, the full PDF, source-assets, or omitted sections.
6. Write translation.zh.md and notes.md within references/reading-protocol.md and references/translation-rules.md limits.
7. Perform targeted verification sequentially. Start a separate evidence-verifier only for deep mode, high-stakes claims, or unresolved discrepancies.
8. Run strict validation, promote, and rebuild the index. Do not perform open-ended synthesis unless requested.

Use this time allocation as a hard prioritization rule:

- source preparation and plan: 7 minutes;
- reading and artifact writing: 13 minutes;
- targeted verification and correction: 5 minutes;
- validation, promotion, and index: 5 minutes.

If parsing alone exceeds 8 minutes, finish or cache parsing, report that the paper is an exception, and do not compensate by dropping evidence quality. MinerU-only, scanned, unusually long, or image-centric papers are not guaranteed to fit the 30-minute target.

## Escalation rules

- Read a table only if a headline result is unavailable in prose, and read only relevant rows.
- Open a figure only if the method cannot be reconstructed from text. Never OCR appendix figures or trajectory screenshots in fast mode.
- Read an appendix only when required for the research question, reproducibility judgment, or a disputed claim.
- Expand beyond 6 claims only for a core paper or explicit user request.
- Upgrade to deep mode instead of silently exceeding the fast budget.

## Agent boundaries

- Use one reader/coordinator sequentially for a single fast paper; handoffs add overhead.
- Use scout agents for broad discovery and separate readers only when several papers can run in parallel.
- Keep one writer per staging directory.
- Keep verifiers read-only and let the coordinator apply findings.
- Only the coordinator changes global indexes, bibliography, and synthesis.

## Required paper artifacts

- original.pdf: immutable source.
- source.md, parse.yaml, source-sections/manifest.yaml: reusable parsed source.
- reading-plan.yaml: selected sections, limits, omissions, and escalation triggers.
- reading-pack.md: bounded, image-light reader input.
- translation.zh.md: Chinese output with explicit scope.
- notes.md: concise analytical notes and evidence index.
- metadata.yaml: identity, classification, mode, provenance, and quality flags.

## Quality gates

- Confirm identity and at least one authoritative identifier or URL.
- Confirm PDF/source hashes, parser quality, reading-pack hash, and strict validation.
- In fast mode, verify the abstract translation and up to 6 load-bearing claims against selected source sections; use PDF pages only for discrepancies.
- Confirm omitted material is disclosed and no inference is presented as a paper conclusion.
- Do not use an unverified paper for a formal novelty, research-gap, or baseline claim.

Read references/parsing-protocol.md for source preparation, references/reading-protocol.md for output limits, references/translation-rules.md for scope, and references/orchestration.md for multi-paper work.

## Repository commands

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/init_paper.py \
      --repo . --year 2025 --first-author Smith --short-title example-method \
      --title "Example Method" --pdf /path/to/paper.pdf

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/prepare_source.py \
      inbox/papers/2025-smith-example-method --backend auto

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/plan_reading.py \
      inbox/papers/2025-smith-example-method \
      --research-question "your focused question"

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/validate_paper.py \
      inbox/papers/2025-smith-example-method --strict

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/promote_paper.py \
      --repo . --paper-id 2025-smith-example-method

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/build_index.py --repo .

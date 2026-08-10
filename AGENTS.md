# Paper Reader project rules

- Use the manage-literature-repository Skill for literature search, ingestion, translation, reading, verification, classification, and synthesis.
- Use the `paper-reader` micromamba environment for all repository scripts in WSL and Windows.
- Default to fast reading mode with a 30-minute budget for ordinary machine-readable papers.
- Keep one canonical directory per paper and preserve original.pdf without modification.
- New records require source.md, parse.yaml, source-sections/manifest.yaml, reading-plan.yaml, reading-pack.md, translation.zh.md, notes.md, and metadata.yaml before promotion.
- Use cached arXiv HTML-first content first, then fast local parsing; run MinerU explicitly only when quality fails.
- Read only reading-pack.md by default. Never preload the complete PDF, source.md, source-assets, or omitted sections.
- Fast mode reads at most 8 sections and 30,000 packed characters, keeps at most 2 short result tables, and omits images.
- Do not OCR figures, read appendices, or transcribe full tables unless a headline claim depends on them.
- Use structured-summary Chinese output by default; use core-sections or full translation only in deep mode or when explicitly requested.
- For one fast paper, avoid reader/verifier handoffs; verify metadata, the abstract, and at most 6 major claims sequentially.
- Scouts write only candidate reports. Readers write only their assigned inbox/papers/<paper-id>. Verifiers report without editing.
- Only the coordinator modifies index.yaml, collections/generated, bibliography, and synthesis.
- Do not cite an unverified paper as evidence for novelty, research gaps, or baseline selection.
- Run strict validation before promotion and rebuild generated indexes afterward.
- Batch bibliography cleanup and synthesis instead of expanding them after every fast-paper run.

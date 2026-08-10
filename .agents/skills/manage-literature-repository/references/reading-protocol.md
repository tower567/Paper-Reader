# Reading protocol

## Fast mode

1. Require parse quality `passed`, reading-plan.yaml, and reading-pack.md.
2. Read only reading-pack.md. Do not preload source.md, source-assets, omitted sections, or the full PDF.
3. Extract the research problem, up to 3 contributions, the method mechanism, experimental setting, up to 3 headline results, limitations, reproducibility, and relevance.
4. Keep notes between roughly 1,200 and 2,500 Chinese characters. Prefer omission over encyclopedic coverage.
5. Use at most 6 evidence rows. Section and table identifiers are sufficient; add PDF pages only when checked.
6. Do not read related work, references, appendices, prompt dumps, example trajectories, or exhaustive ablations unless the research question requires them.

## Figure and table policy

- Images are omitted from the generated pack. Open at most one central figure only when prose cannot explain the method.
- Keep at most two headline result tables and only the relevant rows. Do not transcribe full tables.
- Never OCR appendix figures, qualitative trajectories, or decorative diagrams in fast mode.
- Preserve a clear note when evidence was skipped or could not be verified.

## Targeted verification

- Verify title, authors, year, identifier, and source URL.
- Verify the abstract translation and at most 6 load-bearing claims against selected source sections.
- Open at most 3 PDF pages to resolve pagination, formula, table, or wording conflicts.
- Use Paper claim, Reported result, Reader inference, and Open question labels.
- Upgrade to deep mode if a central conclusion depends on omitted content.

## Deep mode

Read additional method, ablation, efficiency, failure-case, and appendix sections only after an explicit upgrade. Full verification may use more tables, figures, and PDF pages, but still reuse cached source sections.

## Completion

Complete translation.zh.md, notes.md, metadata.yaml, strict validation, promotion, and index generation. A separate verifier is optional in fast mode and required only for high-stakes, disputed, or deep work.

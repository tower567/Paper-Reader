# Multi-agent orchestration

## Discovery

Use one literature scout for one focused search brief. The scout writes only a candidate report and keeps tool responses bounded.

## Reading

Prepare source.md, source-sections, reading-plan.yaml, and reading-pack.md before assigning a reader.

For one fast paper, keep reading and targeted verification in the coordinator or one reader; a reader/verifier handoff is usually slower than the work saved. Use separate readers when several papers can run in parallel or when deep mode is required.

Give a reader one paper ID, one staging directory, reading-plan.yaml, reading-pack.md, the research question, translation scope, and deadline. Do not assign two writers to one directory.

## Verification

In fast mode, verify metadata, the abstract translation, and up to 6 major claims sequentially. Start evidence-verifier only for high-stakes claims, unresolved discrepancies, full translation, or deep mode. The verifier remains read-only.

## Global writes

Run promotion and index generation sequentially. Only the coordinator modifies index.yaml, collections/generated, bibliography, and synthesis.

Batch bibliography cleanup and synthesis after several papers or when the user asks; do not spend the final minutes of every fast-paper run expanding global prose.

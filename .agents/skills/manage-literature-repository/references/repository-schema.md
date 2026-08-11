# Repository schema

## Canonical layout

    .
    ├── inbox/{search-requests,candidates,papers}/
    ├── papers/
    ├── collections/manual/
    ├── synthesis/
    ├── bibliography/
    ├── logs/search-history/
    └── index.yaml

## Ownership

- Scouts write candidate reports.
- One reader writes one inbox/papers/<paper-id> directory.
- The coordinator promotes papers and owns global indexes, bibliography, and synthesis.

## Paper identity and classification

Use `<year>-<first-author>-<short-title>` with lowercase ASCII letters, digits, and hyphens. Store each paper once. Put domains, topics, and research tracks in metadata.yaml; `build_index.py` generates the global index and Obsidian views.

## Staging and promotion

New records require original.pdf, source.md, parse.yaml, source-sections/manifest.yaml, reading-plan.yaml, reading-pack.md, translation.zh.md, notes.md, and metadata.yaml. Promote only after strict validation and targeted or full evidence verification. Record later corrections as reviewed project changes.

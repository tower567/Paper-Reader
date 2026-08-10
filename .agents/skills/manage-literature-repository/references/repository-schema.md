# Repository schema

## Canonical layout

    .
    ├── inbox/{search-requests,candidates,papers}/
    ├── papers/
    ├── collections/{generated,manual}/
    ├── synthesis/
    ├── bibliography/
    ├── logs/search-history/
    └── index.yaml

## Ownership

- Scouts write candidate reports.
- One reader writes one inbox/papers/<paper-id> directory.
- The coordinator promotes papers and owns global indexes, bibliography, and synthesis.
- build_index.py owns collections/generated.

## Paper identity and classification

Use `<year>-<first-author>-<short-title>` with lowercase ASCII letters, digits, and hyphens. Store each paper once. Put domains and topics in metadata.yaml and generate topical collections.

## Staging and promotion

New records require original.pdf, source.md, parse.yaml, source-sections/manifest.yaml, reading-plan.yaml, reading-pack.md, translation.zh.md, notes.md, and metadata.yaml. Promote only after strict validation and targeted or full evidence verification. Record later corrections as reviewed project changes.

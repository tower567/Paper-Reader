# Parsing protocol

## Objective

Materialize source.md once, validate it, split it into bounded sections, then generate an even smaller reading pack. Never repeatedly parse or load the same PDF.

## Backend order

1. Reuse source.md when parse.yaml hashes match.
2. For arXiv papers, use bounded arXiv MCP HTML-first Markdown and import the cache.
3. In fast mode, use local PyMuPDF4LLM when cached arXiv Markdown is unavailable.
4. Use MinerU VLM explicitly only when HTML/local extraction fails quality checks or the paper is scanned/image-centric.

`prepare_source.py --backend auto` follows the fast path. Use `--backend mineru` for an explicit quality upgrade.

## MinerU

Configure MINERU_API_TOKEN once at the WSL user level and never store it in the project:

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/configure_mineru_token.py

Use MinerU only after the fast parser fails:

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/prepare_source.py \
      inbox/papers/<paper-id> --backend mineru

## Quality gate

Require matching PDF/source hashes, ready status, passed quality, readable core sections, and a source-sections manifest. Do not require perfect table layout, image extraction, appendix OCR, or figure-caption recovery in fast mode when the abstract, main method, results, and conclusion are readable.

After changing local quality rules, re-check cached content without uploading again:

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/prepare_source.py \
      inbox/papers/<paper-id> --revalidate

## Reading-pack step

After source preparation, run:

    micromamba run -n paper-reader python \
      .agents/skills/manage-literature-repository/scripts/plan_reading.py \
      inbox/papers/<paper-id> --research-question "focused question"

Read reading-pack.md instead of selecting sections manually. It removes images, caps tables and rows, truncates oversized sections, and records every omission in reading-plan.yaml.

# Search protocol

## Input

Create the request as inbox/search-requests/<request-id>.yaml with
scripts/init_search_request.py. Complete the generated YAML with:

- research question;
- target task, setting, modality, population, or domain;
- desired time range;
- known seed papers;
- expected role: survey, baseline selection, novelty check, method transfer, or evidence gathering;
- inclusion and exclusion criteria;
- preferred venues or code availability when relevant.

## Search angles

Search from several independent angles:

1. Direct problem and task terminology.
2. Common synonyms and historical terminology.
3. Representative methods and benchmark names.
4. Adjacent fields with transferable methods.
5. Recent citing and cited-by chains from strong seed papers.
6. Targeted novelty searches for the proposed mechanism.

## Verification

Require at least one authoritative paper page or stable identifier for every candidate. Verify rather than infer:

- exact title and author list;
- year and publication status;
- DOI or arXiv ID;
- venue;
- official PDF or landing page;
- code repository ownership and linkage.

Treat search snippets, generated citations, and unofficial mirrors as leads rather than evidence.

## Deduplication

Merge records in this order:

1. Same DOI.
2. Same arXiv ID.
3. Normalized title and matching first author.
4. Preprint and published version confirmed as the same work.

Prefer the published bibliographic record while preserving the accessible preprint URL when useful.

## Ranking

Rank candidates using:

- direct relevance to the research question;
- setting and evaluation match;
- usefulness as baseline, related work, or methodological inspiration;
- evidence quality;
- availability of code, data, and reproducibility details;
- recency only when the task calls for recent work.

Do not use venue prestige as a substitute for relevance.

## Output

Write a YAML candidate report under inbox/candidates by following
assets/templates/candidate-report.yaml. For every paper include:

- title;
- authors;
- year;
- DOI and arXiv ID;
- venue and publication status;
- source URL;
- code URL;
- relevance reason;
- likely role;
- search angle;
- confidence;
- verification notes.

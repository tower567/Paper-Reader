# Chinese translation rules

## Default scope

In fast mode, use `structured-summary`: translate the abstract fully, then faithfully compress the problem, contribution, method, up to three headline results, conclusion, and limitations. Do not translate related work, references, appendices, non-key tables, figure text, prompts, or example trajectories. Record every omission at the top or end of translation.zh.md.

Use `core-sections` only in deep mode. Use `full` only when the user explicitly requests a complete translation.

## Fidelity

- Preserve the selected sections' logical order.
- Preserve equations, symbols, citations, footnotes, algorithm references, and cross-references when they are material to the selected content.
- Preserve figure and table numbers only when cited in the selected translation.
- Do not silently simplify technical claims or add criticism to the translation body.
- Keep the original English term at first occurrence when Chinese terminology is ambiguous or field-specific.

## Names and terms

- Keep author names, dataset names, model names, benchmark names, and code identifiers in their established form.
- Maintain a consistent term mapping.
- Put uncertain choices in the terminology and uncertainty section.

## Uncertainty

Mark uncertain passages explicitly:

    <!-- REVIEW: explain the ambiguity and retain the source phrase -->

Do not guess missing text, unreadable formulas, or cropped captions. Do not start OCR merely to fill a non-central figure or table; disclose the omission and upgrade only when it controls a major conclusion.

## Separation of artifacts

Keep translation faithful and descriptive. Put criticism, comparison, implications, and research ideas in notes.md.

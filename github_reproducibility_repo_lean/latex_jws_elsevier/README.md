# JWS / Elsevier LaTeX Manuscript Folder

Target journal: Journal of Web Semantics (Elsevier)

Special issue: Knowledge Engineering Automation

Main file: `main.tex`

## Contents

- `main.tex`: full LaTeX manuscript draft using `elsarticle`.
- `references.bib`: numbered-reference bibliography restricted to scholarly publications in Scopus indexed venues.
- `highlights.tex`: Elsevier-style highlights, 5 bullets under 85 characters each.
- `cover_letter.md`: draft cover letter for the special issue.
- `reference_screening.md`: reference-screening note for the Scopus-only requirement.
- `submission_checklist.md`: remaining pre-submission items.
- `tables/`: copies of generated manuscript CSV tables.

## Build

A TeX distribution with Elsevier `elsarticle` is required. This environment does not currently provide `pdflatex`, `xelatex`, `latexmk`, or `tectonic`, so PDF compilation was not run locally.

Recommended command on a machine with TeX Live / Overleaf:

```bash
pdflatex main
bibtex main
pdflatex main
pdflatex main
```

The manuscript uses:

```tex
\documentclass[final,5p,times,twocolumn]{elsarticle}
\bibliographystyle{elsarticle-num}
```

This follows the Elsevier/JWS guidance to provide editable LaTeX source files and numbered references.

## Required TODOs Before Submission

- Replace placeholder author names, affiliations, and corresponding-author email.
- Insert repository/archive DOI or permanent URL in the Data and code availability section.
- Confirm funding and competing-interest statements for all authors.
- Complete CRediT roles after final author order is fixed.
- Complete the external domain/ontology review or keep it explicitly as a limitation.
- Run final Scopus source-list verification for every bibliography entry.
- Compile the PDF and inspect tables/figures in double-column layout.

## Sources Used for Formatting Decisions

- Journal of Web Semantics Guide for Authors, ScienceDirect / Elsevier.
- Elsevier LaTeX instructions for `elsarticle`.
- Elsevier article-structure guidance by Angel Borja, "11 steps to structuring a science paper editors will take seriously".

These formatting sources are not included in the manuscript bibliography because the user requested bibliographic references to be limited to Scopus indexed scholarly publications.

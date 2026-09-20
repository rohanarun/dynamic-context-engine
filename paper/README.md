# Dynamic Context Engine white paper

Author: **Rohan Arun, Super Powers AI**.

This is a pre-submission technical manuscript, not an arXiv publication. It includes the original 32-question accuracy result, the post-selected 29-question rerun, website-prompt replay, selector cost, and parallel/end-to-end timing.

- [Read the PDF](../output/pdf/dynamic-context-engine-white-paper.pdf)
- [LaTeX source](main.tex)
- [arXiv source archive](../output/dynamic-context-engine-arxiv-source.tar.gz)
- [Evidence manifest](evidence-manifest.json)
- [Submission metadata](submission-metadata.json)

## Build

From the repository root:

```sh
python3 paper/build_figures.py
cd paper
tectonic --keep-logs --outdir ../output/pdf main.tex
cp ../output/pdf/main.pdf ../output/pdf/dynamic-context-engine-white-paper.pdf
```

Alternatively, use a standard LaTeX installation and run `pdflatex main.tex` twice from `paper/`. The source uses standard packages, PNG figures, and an inline bibliography; no private data, external commands, custom fonts, or API credentials are required to compile it. Local compilation was verified with Tectonic. arXiv server compilation still needs verification during submission.

## Submission status

No arXiv identifier or submission receipt has been issued. The inspected arXiv account page requires login. The author must review the manuscript and confirm the submission license and arXiv agreement. The suggested subject is `cs.CL` (Computation and Language), with `cs.IR` (Information Retrieval) as a possible cross-list subject to arXiv moderation. Endorsement may be required by the account/category.

The source archive contains only `main.tex` and the three used figures. Do not upload the generated PDF in place of the LaTeX source. After arXiv compiles the source, inspect that PDF before final submission.

Official instructions: [submission](https://info.arxiv.org/help/submit/index.html), [TeX source](https://info.arxiv.org/help/submit_tex.html), [licenses](https://info.arxiv.org/help/license/index.html).

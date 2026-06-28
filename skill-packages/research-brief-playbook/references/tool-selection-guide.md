# Tool Selection Guide

Use this guide to decide which tool should handle the next part of the workflow.

## Start with the smallest useful step

Prefer the narrowest tool that can answer the question. Do not start with a crawl if one page can answer it.

## Tool choices

### `@zack/web-page-extract`

Use it when:
- you already know the exact page you need
- the question depends on the content of one article or report
- you want cleaned page content plus metadata before doing any broader exploration

### `@zack/robots-aware-crawl`

Use it when:
- the answer depends on several related pages
- you need bounded exploration of a docs section, newsroom page, or small site area
- you want discovery plus extraction together

Do not use it as the first move when the user already gave one clearly relevant page.

### `@zack/document-convert`

Use it when:
- a useful source is a local document rather than a web page
- a downloaded file needs to be normalized into text or markdown before review

### `@zack/table-extract`

Use it when:
- the evidence lives in a table
- structured rows matter more than narrative prose
- the brief needs counts, comparisons, or tabular facts

### `@zack/markdown-chunk`

Use it when:
- the notes or extracted content are too long to reason over cleanly
- the final summary should preserve section boundaries or heading context

### `@zack/summarize-text`

Use it when:
- the useful evidence has already been assembled
- the task is now synthesis, not discovery

Do not use it as a substitute for reading weak or incomplete source material.

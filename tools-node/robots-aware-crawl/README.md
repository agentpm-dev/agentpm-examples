# robots-aware-crawl

Crawl a small set of pages with depth/page limits, optional robots.txt handling, and normalized page output.

## Why install it

Research and ingestion agents often need more than a single fetch. This tool packages the basic crawl loop, link normalization, and robots-aware filtering into one reusable primitive.

## Inputs

- `start_urls`: seed URLs to begin crawling from
- `allowed_domains`: optional list of domains the crawler may visit
- `max_pages`: maximum number of pages to fetch
- `max_depth`: maximum crawl depth from the start URLs
- `same_origin_only`: restrict links to the same origin as the seed URL
- `respect_robots`: whether to consult `robots.txt`
- `include_patterns`: optional regex patterns a URL must match to be crawled
- `exclude_patterns`: optional regex patterns that disqualify a URL

## Outputs

- `pages`: fetched pages with title, excerpt, depth, and discovered links
- `visited_count`: number of pages actually fetched
- `skipped`: skipped URLs with reasons
- `errors`: fetch or parse failures encountered during the crawl
- `metadata`: crawl summary information

## Local development

The source code for this tool can be found [here](https://github.com/agentpm-dev/agentpm-examples/tree/main/tools-node/robots-aware-crawl)

Test:

```bash
npm test
```

Build:

```bash
npm run build
```

## Example invocation

```bash
printf '%s' '{"start_urls":["https://example.com/docs"],"max_pages":5,"max_depth":1,"respect_robots":true}' | node dist/index.js
```

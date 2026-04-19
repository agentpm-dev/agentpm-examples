# web-page-extract

Fetch a web page and return cleaned page content, metadata, and normalized links.

## Why install it

Most agent systems need a reliable first-step web ingestion primitive. This tool gives you one packageable contract for page fetch + cleaning instead of rebuilding the same fetch/parse glue inside every agent.

## Inputs

- `url`: page URL to fetch
- `format`: `markdown` or `text`
- `include_links`: include extracted links
- `timeout_ms`: request timeout
- `max_chars`: output content cap

## Outputs

- `url`: original requested URL
- `final_url`: final fetched URL after redirects
- `title`
- `canonical_url`
- `published_at`
- `byline`
- `excerpt`
- `format`
- `content`
- `links`
- `metadata`

## Local development

```bash
node --test
```

To build the packaged entrypoint:

```bash
npm run build
```

## Example invocation

```bash
printf '%s' '{"url":"https://example.com","format":"markdown"}' | node dist/index.js
```

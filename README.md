pnpm -r install

pnpm -C tools-node/wikipedia-scrape build

pnpm -C tools-node/wikipedia-scrape add -D @types/node@^22 typescript@^5

echo '{"url":"https://en.wikipedia.org/wiki/Alan_Turing"}' | node tools-node/wikipedia-scrape/dist/index.js

pnpm -C tools-node/translate-text add -D dotenv-cli

pnpm -C tools-node/translate-text build

pnpm --dir tools-node/translate-text exec dotenv -e .env.local -- node dist/index.js <<'JSON'
{"text":"Hello world","target_language":"Spanish"}}
JSON

uv sync --directory tools-python/summarize-text

uv add --directory tools-python/summarize-text python-dotenv
uv add --directory tools-python/summarize-text "python-dotenv[cli]"

uv run --directory tools-python/summarize-text \
python -m dotenv -f .env.local run -- \
python -m summarize_text <<'JSON'
{"text":"Alan Turing was a computer scientist","max_words":60}
JSON

uv pip install --target tools-python/summarize-text/summarize_text/_vendor "openai>=1.51.0"



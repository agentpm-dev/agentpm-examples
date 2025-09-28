pnpm -r install

pnpm -C tools-node/wikipedia-scrape build

pnpm -C tools-node/wikipedia-scrape add -D @types/node@^22 typescript@^5

echo '{"url":"https://en.wikipedia.org/wiki/Alan_Turing"}' | node tools-node/wikipedia-scrape/dist/index.js

pnpm -C tools-node/translate-text add -D dotenv-cli

pnpm -C tools-node/translate-text build

pnpm --dir tools-node/translate-text exec dotenv -e .env.local -- node dist/index.js <<'JSON'
{"text":"Hello world","target_language":"Spanish"}}
JSON

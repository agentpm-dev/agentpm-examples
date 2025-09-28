pnpm -r install

pnpm -C tools-node/wikipedia-scrape build

echo '{"url":"https://en.wikipedia.org/wiki/Alan_Turing"}' | node tools-node/wikipedia-scrape/dist/index.js
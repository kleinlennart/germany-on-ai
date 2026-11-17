# Germany on AI: site

The situation report on German AI policy, built as a static Astro site and published on
GitHub Pages by `.github/workflows/pages.yml`.

```sh
uv run germany-on-ai build   # in the repo root: exports the site reads from build/
pnpm install
pnpm dev                     # http://localhost:4321/germany-on-ai/
pnpm build                   # static site in dist/
```

Pages: the situation report (`/`), method and sources (`/method/`), about (`/about/`), and one
page per proceeding (`/vorgang/<id>/`). `scripts/prepare-data.mjs` turns the committed records
(`../data/records`) and the build exports (`../build`) into JSON under `src/data/`.

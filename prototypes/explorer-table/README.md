# PROTOTYPE: Germany on AI (throwaway)

A situation report on German AI policy, built on real data (DIP proceedings) to work out
what the site should be before the real one is written.

```sh
pnpm install
pnpm dev            # http://localhost:4321
pnpm exec svelte-check --workspace .
```

Pages: the situation report (`/`), method and sources (`/method/`), about (`/about/`), and one
static page per proceeding (`/vorgang/<id>/`). Data comes from `../../data/records/dip` and
`../../build/catalogue.json` (run `uv run germany-on-ai build` in the repo root first).

Not production code: once the direction is settled, this moves to a throwaway branch and the
real site is written properly.

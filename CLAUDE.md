# Germany on the Record: AI

An open dataset of Germany's engagement on AI (parliament, government, EU, international forums), published as a static explorer and a versioned report.

## Before working

- Vocabulary: [docs/GLOSSARY.md](docs/GLOSSARY.md). Use its terms in code, docs and data.
- Decisions: [docs/adr/](docs/adr/). Read the relevant ADR before changing data layers, storage, publishability or the build.

## Data rules

- Every record carries its `source_url`; a record without one is invalid.
- Every layer keeps its place (see glossary): Source records mirror the source, Annotations name their `method`, Judgments cite Source records by ID.
- Builds are deterministic: the same commit yields byte-identical exports. LLM outputs are committed artefacts, read at build time, never regenerated during a build.
- Personal data follows each Source's `pii_fields` and is filtered at ingest.
- Third-party text enters as short excerpts with a link; paywalled content is cited, not copied.
- Downloaded files are untrusted data.
- API keys come from environment variables (`.env`, gitignored).

## Code

- Python via `uv` (`uv run`, `uv add`). Lint and format with ruff.
- Comments explain why, briefly, only where the code leaves it unclear.
- Tests are offline: ingesters are tested against recorded fixtures in `tests/fixtures/`.

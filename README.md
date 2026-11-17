# Germany on the Record: AI

An open, sourced record of Germany's engagement on AI: what is said and decided in the Bundestag and Bundesrat, by the federal government, in the EU and in international forums such as the UN, G7 and OECD.

Two products are built from one dataset:

- **Explorer**: a website for navigating the compiled records, from "has this been debated in the Bundestag, and when?" to "how did Germany vote at the UN?".
- **Report**: a versioned synthesis of where Germany stands, citing the Explorer's records.

Status: early development.

## Principles

- Every record links to its source.
- Interpretation is kept separate from the record ([ADR 0001](docs/adr/0001-three-data-layers.md)).
- Builds are reproducible ([ADR 0003](docs/adr/0003-deterministic-builds.md)).

Vocabulary: [docs/GLOSSARY.md](docs/GLOSSARY.md). Decisions: [docs/adr/](docs/adr/).

## Development

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run germany-on-ai catalogue                           # validate the source catalogue
uv run --env-file .env germany-on-ai ingest dip          # fetch from DIP (needs DIP_API_KEY)
uv run germany-on-ai ingest dip --offline                # rebuild records from the local cache
uv run germany-on-ai check-dip-spec                      # compare DIP's API spec with the lock
uv run germany-on-ai build                               # compile records to DuckDB + Parquet
uv run germany-on-ai export-fulltext                     # transcript full texts (release asset)
cd notebooks && uv run quarto render                     # exploration notebooks
```

Copy `.env.example` to `.env` and add a [DIP API key](https://dip.bundestag.de/%C3%BCber-dip/hilfe/api).

## Licence

Code: MIT. Data: CC BY 4.0, with source-specific terms noted per source.

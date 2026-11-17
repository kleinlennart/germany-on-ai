# Germany on AI

An open, sourced record of Germany's engagement on AI: what is said and decided in the Bundestag and Bundesrat, by the federal government, in the EU and in international forums such as the UN, G7 and OECD.

Status: early development.

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

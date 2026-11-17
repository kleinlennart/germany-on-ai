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
```

## Licence

Code: MIT. Data: CC BY 4.0, with source-specific terms noted per source.

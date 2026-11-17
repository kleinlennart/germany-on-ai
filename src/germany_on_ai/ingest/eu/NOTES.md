# EU sources: data facts

## European Parliament Open Data API v2

- `GET /api/v2/procedures/{yyyy-nnnn}?format=application/ld+json` returns `{"data": [procedure]}`. The procedure's `label` is the reference (`2025/0359(COD)`); its id is `eli/dl/proc/2025-0359`.
- `consists_of` lists dated events: `activity_date`, `activity_id` (stable), `had_activity_type` (e.g. `def/ep-activities/PLENARY_VOTE`, `SIGNATURE`, `PUBLICATION_OFFICIAL_JOURNAL`, `TABLING_PLENARY`), `occured_at_stage`.
- Events are Parliament-side only: the Commission proposal date can be missing, and there are no forecast dates.
- `process_title` is keyed by language code (`en`, `de`, …).
- The linked-data URI returns RDF, not a page. The human page is the Legislative Observatory: `https://oeil.secure.europarl.europa.eu/oeil/en/procedure-file?reference=2025/0359(COD)` (server-rendered).
- `GET /api/v2/meetings?year=` lists plenary sitting days (upcoming included).

## Cellar SPARQL (Publications Office)

- Endpoint `https://publications.europa.eu/webapi/rdf/sparql`, unauthenticated GET, `Accept: application/sparql-results+json`.
- Works are found by `cdm:resource_legal_id_celex`. `cdm:resource_legal_date_entry-into-force` holds several values for acts with staged application (AI Act 32024R1689: 2024-08-01, 2025-02-02, 2025-08-02, 2026-08-02, 2027-08-02). The query returns one row per combination, so dates must be deduplicated.
- EuroVoc concept `http://eurovoc.europa.eu/3030` is "artificial intelligence"; results include merger and court cases, so filter by CELEX sector and type.
- EUR-Lex's own website refuses automated requests; Cellar does not. Human links use `https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}`.

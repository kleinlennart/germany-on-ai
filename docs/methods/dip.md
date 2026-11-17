# Method: Bundestag and Bundesrat (DIP)

Source: [DIP](https://dip.bundestag.de), the Bundestag's documentation and information system for parliamentary materials, read through its [API](https://dip.bundestag.de/%C3%BCber-dip/hilfe/api).

## Coverage

All electoral terms from the 19th Bundestag (24 October 2017) onwards. The 19th term is the one in which the federal AI strategy (November 2018) was adopted and the Bundestag's Enquete Commission on Artificial Intelligence was set up. Whole electoral terms are used because DIP and the Bundestag organise their records by term.

## What is downloaded

The fetch filter in [`data/fetch/dip.yaml`](../../data/fetch/dip.yaml) decides what is downloaded. It does not decide what counts as AI-related; that is a later, separately documented step.

1. **Proceedings** (Vorgänge) carrying one of the DIP thesaurus descriptors listed in the filter, or whose title contains one of its title terms. Descriptors cover indexed items; titles catch items not yet indexed. DIP expands some descriptors to broader terms. "Autonomes Waffensystem", for example, also matches military robots and drones. This is deliberate: nothing relevant is lost, and off-topic items are handled when records are labelled.
2. Everything linked to those proceedings: their **steps** (Vorgangspositionen), the **printed papers** (Drucksachen) and **activities** (speeches, questions, motions by named members) of those steps, and the **persons** behind the activities.
3. **All plenary transcripts** (Plenarprotokolle) of the Bundestag and Bundesrat in these terms. DIP has no full-text search, so speeches that no descriptor flags can only be found in the text itself.

## Passages

Each transcript paragraph (DIP's text has one paragraph per line) that matches one of the filter's passage terms is kept as a passage. Passages are copied verbatim. Each carries its character offsets in the full text and the full text's SHA-256, so it can be checked against the published full text. Full texts are too large for the repository and are published as a release file.

## How the data is kept faithful

- Each record stores DIP's own JSON unchanged, inside an envelope with our ID, a public link, the retrieval time and a content hash.
- The content hash leaves out DIP's `aktualisiert` timestamp. DIP updates that timestamp whenever a linked record changes. A record is rewritten, and its retrieval time updated, only when its own content changes.
- Every query is paged to the end and its result is checked against the total DIP reports. A mismatch stops the run.
- Our requests are checked against DIP's OpenAPI specification, its authoritative documentation. A lock file records the specification's version and hash and the parameters we use.
- Requests run one at a time, at most one every two seconds. DIP asks for no more than 25 concurrent requests and does not publish rate limits; its bot protection throttled us at a faster pace.

## Updates

After the first full download, daily runs ask DIP only for records updated since the last run. The window overlaps by 30 minutes, because DIP needs about 15 minutes before a change appears in the API.

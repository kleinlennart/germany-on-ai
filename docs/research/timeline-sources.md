# Timeline sources: machine-readable feeds for dated AI-policy events

Research note for the timeline lanes outside DIP. Written 2026-11-17. The scope is deliberately narrow: only machine-readable primary sources (API, RSS, iCal, SPARQL) that I could confirm with a live request, at most three per lane. Everything else is listed under "Later". DIP was not contacted.

## Shortlist

| Source                                                      | Lane          | Endpoint                                                                                                                                                                                             | Past / upcoming                                      | AI selection                                                      | Terms                                                             | Effort     |
| ----------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------- | ---------- |
| Federal Government RSS (BPA), plus Foreign Office press RSS | Germany       | `https://www.bundesregierung.de/service/rss/breg-de/1151244/feed.xml` (press releases), `.../2318648/feed.xml` (Bulletin); `https://www.auswaertiges-amt.de/static/includes/rss/Presse-RSS-Feed.xml` | Past only, last 10–20 items                          | Keyword match on title and description                            | No reuse licence stated (imprints)                                | Low        |
| Rechtsinformationsportal API (trial)                        | Germany       | `https://testphase.rechtsinformationen.bund.de/v1/legislation?searchTerm=...`                                                                                                                        | Past (promulgation)                                  | `searchTerm`, then a curated list of ELIs                         | No licence stated; 600 req/min                                    | Low        |
| Bundestag and Bundesrat calendars                           | Germany       | Bundestag sitting weeks iCal; Bundestag committee agendas RSS; Bundesrat `RSSGenerator_Event.xml`                                                                                                    | Upcoming                                             | None by topic: calendar anchors, plus committee name in the title | Bundestag/Bundesrat imprints                                      | Low        |
| European Parliament Open Data API v2                        | EU            | `https://data.europarl.europa.eu/api/v2/procedures/{yyyy-nnnn}`, `.../api/v2/meetings?year=`                                                                                                         | Past events per procedure; upcoming plenary sittings | Follow procedure numbers                                          | EP legal notice                                                   | Low        |
| Cellar SPARQL (Publications Office)                         | EU            | `https://publications.europa.eu/webapi/rdf/sparql`                                                                                                                                                   | Past, plus future application dates of acts          | EuroVoc concept `3030` "artificial intelligence"; CELEX lists     | Commission reuse policy (CC BY 4.0); EUR-Lex notice not confirmed | Medium     |
| UN Digital Library, voting data                             | International | `https://digitallibrary.un.org/search?p=...&cc=Voting%20Data&of=xm`                                                                                                                                  | Past only                                            | Full-text query, e.g. `"artificial intelligence"`                 | Not confirmed                                                     | Low–medium |

The International lane has only one confirmed machine-readable source. Its upcoming dates (CCW sessions, UN Global Dialogue, summits, G7/G20) have to be curated for now.

## Shortlisted sources

### Federal Government RSS (BPA) and Foreign Office press RSS

The BPA lists four RSS 2.0 feeds on its RSS page: Bundesregierung kompakt (1151242), Pressemitteilungen (1151244), Artikel (1151246) and Bulletin (2318648). The Bulletin carries speeches by the Chancellor and ministers ([RSS page](https://www.bundesregierung.de/breg-de/service/newsletter-und-abos/rss-newsfeed)). Each item has `title`, `link`, `description`, `pubDate` and `guid` (the item URL). A fetch of the press-release feed returned 20 items, with `<ttl>60</ttl>` and `<copyright>Presse- und Informationsamt der Bundesregierung</copyright>`. The Foreign Office feed "Pressemitteilungen und Reden" returned 10 items, with full HTML text in `description` ([RSS page](https://www.auswaertiges-amt.de/de/newsroom/presse/newsletter/rss/-/199382)). Neither feed has history, so the ingester must poll (daily is enough) and keep what it sees. AI selection is a keyword filter (KI, künstliche Intelligenz, AI Act, KI-Verordnung) followed by human review. The [BPA imprint](https://www.bundesregierung.de/breg-de/impressum) states only "© 2026 Presse- und Informationsamt der Bundesregierung" and gives no reuse licence. The [Foreign Office imprint](https://www.auswaertiges-amt.de/de/impressum-node) says content is "urheberrechtlich geschützt. Alle Rechte vorbehalten." Store title, date, link and a short excerpt only.

### Rechtsinformationsportal API (NeuRIS, trial)

This is the federal legal information service of the Federal Ministry of Justice and the Federal Office of Justice ([docs](https://docs.rechtsinformationen.bund.de/)). It needs no API key, and its [rate limit](https://docs.rechtsinformationen.bund.de/guides/rate-limiting/) is "600 requests per minute per client IP". A live search for `Künstliche Intelligenz` returned the KI-Marktüberwachungs- und Innovationsförderungsgesetz (KI-MIG) with these fields:

- `legislationIdentifier`: `eli/bund/bgbl-1/2026/223/2026-07-22/1/deu`
- `legislationDate`: `2026-07-22`
- `datePublished`: `2026-07-28`
- `isPartOf.name`: `BGBl I, 2026 223`
- `legislationLegalForce`: `InForce`

That gives the promulgation date and the BGBl citation for the Germany lane. The docs say "This is a trial service" and the dataset "is not yet complete". No licence is stated, though federal laws are official works without copyright under [§ 5 UrhG](https://www.gesetze-im-internet.de/urhg/__5.html). Follow a small curated list of ELIs, and use `searchTerm` only to find new candidates.

### Bundestag and Bundesrat calendars

These are calendar anchors for upcoming dates. DIP already covers the proceedings themselves.

- **Bundestag sitting weeks.** The [Sitzungskalender](https://www.bundestag.de/parlament/plenum/sitzungskalender) links iCal files. `https://www.bundestag.de/resource/blob/1103938/Parlamentstermine_2026_ics.ics` holds the 2026 weeks. `.../1193892/Parlamentstermine_2026_ics-1-.ics` is, despite its filename, the 2027 file (21 all-day events, `SUMMARY:Sitzungswoche Deutscher Bundestag`). Its UIDs come from a third-party iCal generator, so key records on the dates, not the UIDs.
- **Bundestag committee agendas.** The feed `https://www.bundestag.de/static/appdata/includes/rss/tagesordnungen.rss` announces upcoming committee meetings. Titles follow the form "Committee: Nth sitting on date, time, public/non-public", and each links to an agenda PDF. Filter by committee prefix, e.g. Digitales und Staatsmodernisierung. Only that prefix is machine-readable: the AI items themselves sit in the PDFs.
- **Bundesrat.** The feed `https://www.bundesrat.de/SiteGlobals/Functions/RSSFeed/RSSGenerator_Event.xml` returned 19 upcoming items, including "20.11.2026 09:30 Uhr | 1070. Plenarsitzung". The date and time are in the title text, and `pubDate` is the posting date. The Bundesrat lists its feeds on its [RSS page](https://www.bundesrat.de/DE/service-navi/rss/rss-node.html).

Terms: both [Bundestag](https://www.bundestag.de/services/impressum) and [Bundesrat](https://www.bundesrat.de/DE/service-navi/impressum/impressum-node.html) state that site content is copyrighted, and that Drucksachen and Plenarprotokolle are official works under § 5 UrhG. Dates and titles are facts; store them with a link.

### European Parliament Open Data API v2

`GET /api/v2/procedures/2021-0106?format=application/ld+json` returned procedure `2021/0106(COD)` with 26 events in `consists_of`. Each event has `activity_date`, `had_activity_type` (e.g. `PLENARY_VOTE`, `SIGNATURE`, `PUBLICATION_OFFICIAL_JOURNAL`) and a stable `activity_id`. I confirmed both Digital Omnibus files the same way:

- **`2025/0359(COD)`, Digital Omnibus on AI:** plenary position adopted 2026-06-16, signed 2026-07-08, published in the Official Journal 2026-07-24.
- **`2025/0360(COD)`, broader Digital Omnibus:** committee opinions adopted 2026-11-04 and 2026-11-10.

`GET /api/v2/meetings?year=2026` returned 54 plenary sitting days, through `MTG-PL-2026-12-17`, so it supplies upcoming sittings. Two gaps: the per-procedure events are Parliament-side (the Commission proposal date is missing for 2025/0359), and they contain no forecast dates. The [EP legal notice](https://www.europarl.europa.eu/legal-notice/en/) authorises reuse "provided that the entire item is reproduced and the source is acknowledged".

### Cellar SPARQL (Publications Office)

The endpoint answered unauthenticated GET queries with JSON results. Useful properties are `cdm:resource_legal_id_celex`, `cdm:work_date_document`, `cdm:resource_legal_date_signature`, `cdm:official-journal-act_date_publication`, `cdm:resource_legal_date_entry-into-force`, `cdm:work_is_about_concept_eurovoc` and `cdm:work_part_of_dossier`.

For the AI Act (CELEX `32024R1689`), the entry-into-force dates included 2024-08-01, 2025-02-02, 2025-08-02, 2026-08-02 and 2027-08-02, which are the act's staged application dates. These are upcoming events that can be sourced. Regulation `32026R1744`, which amends Regulation (EU) 2024/1689, was signed 2026-07-08, published 2026-07-24 and entered into force 2026-07-27.

EuroVoc concept `http://eurovoc.europa.eu/3030` ("artificial intelligence") returned 40+ documents from 2026. These include noise (merger cases `M`, court cases `6…`), so filter by CELEX sector and type. Reuse: the [Commission legal notice](https://commission.europa.eu/legal-notice_en) licenses EU-owned content under CC BY 4.0 per Decision 2011/833/EU. The EUR-Lex legal notice itself could not be retrieved (see Unconfirmed).

### UN Digital Library, voting data

The search `https://digitallibrary.un.org/search?p=%22artificial%20intelligence%22&cc=Voting%20Data&of=xm&rg=3&so=d` returned MARCXML. Fields:

- `791`: resolution symbol (A/RES/80/302, A/RES/80/23, A/RES/80/58)
- `245`: title
- `269`: vote date (2025-12-01; absent on one record)
- `996`: tallies (yes, no, abstain, non-voting, total)
- `967`: per-country votes (`$c DEU`, `$d Y`/`A`, `$e GERMANY`)

This yields "Germany voted X on resolution Y on date Z" with an official record URL (`https://digitallibrary.un.org/record/{001}`). Past only. Keep requests few (`rg` small); no documented rate limit found.

## Later

- **Bundesregierung cabinet results and Regierungspressekonferenz transcripts:** listings render client-side, so scrape only.
- **BMDS press:** the RSS feed (`https://bmds.bund.de/feed/rss.xml`) was empty when checked. The HTML list is paginated, and texts are CC BY-ND 4.0 per the [imprint](https://bmds.bund.de/impressum).
- **Foreign Office Open Data API:** only travel advice, missions and country names; no news. Drop.
- **Bundestag plenary agendas:** HTML/PDF; no structured endpoint confirmed.
- **recht.bund.de (BGBl):** returned HTTP 503 to automated requests; use the Rechtsinformationsportal instead.
- **EUR-Lex website, RSS and webservice:** the site returned an empty 202 (bot challenge), so use Cellar instead.
- **OEIL procedure pages:** HTML/PDF; the EP API covers the same events.
- **Council (calendar, press, voting results):** `consilium.europa.eu` returned 403 to automated requests.
- **Commission Have Your Say and press corner:** not checked.
- **UN Journal:** JavaScript app; no API found.
- **UN press, UNODA CCW meetings, Council of Europe Treaty Office (CETS 225), OECD legal instruments and OECD.AI, G7/G20 presidency sites, AI summit sites:** HTML only or not checked. Treat as curated records, each with its official URL.

## Unconfirmed

- Reuse terms for the UN Digital Library (un.org terms page returned 403) and for the EUR-Lex legal notice (bot challenge).
- The EP Open Data API rate limit (a search summary of the developer corner reported 500 requests per 5 minutes; the page itself did not render for me). Also the dataset-level licence on the EP open data portal.
- The licence of the Rechtsinformationsportal API.
- Whether the Bundestag committee-agenda feed uses the title prefix "Digitales und Staatsmodernisierung" (inferred from other committees' titles).
- How far back any of the RSS feeds reach (observed: 10–20 items).

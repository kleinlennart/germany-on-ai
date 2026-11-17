# Records as files in git, published as a static site

Source records, Annotations and Judgments live as plain files in the repository; a build step compiles them into DuckDB and Parquet/JSON exports, and the Explorer is a static site that queries those exports in the browser. Git gives every record a reviewable history, which a public, citable dataset needs, and a static site needs no server to run or secure. We considered a hosted database, but nothing in scope needs writes from visitors or server-side queries. Scheduled updates arrive as a pull request, so every data change is reviewed before it is published.

## Consequences

Large full texts (e.g. plenary transcripts) are shipped as release assets rather than committed, to keep the repository small.

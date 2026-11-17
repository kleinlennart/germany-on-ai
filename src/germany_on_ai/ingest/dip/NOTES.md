# DIP: data facts

Durable facts about DIP's data and API that the code depends on. Authoritative docs: the OpenAPI spec (locked in `data/fetch/dip-openapi.lock.json`) and DIP's API info sheet.

## Fields

- `vorgang.datum` is the date of the proceeding's **latest** document, not its start. Counting proceedings by `datum` places old proceedings in recent periods. A start date has to come from the earliest step (Vorgangsposition).
- `aktualisiert` changes when a linked entity changes, even if the record's own fields did not. It is excluded from content hashes.
- Linked lists (`vorgangsbezug`, `vorgang_verlinkung`, …) are previews and may be incomplete. Query the linked endpoint for the full list.
- Written and oral questions (`Schriftliche Frage`, `Mündliche Frage`) carry no `initiative` on the proceeding. The asking MP is on the activity (`aktivitaet.person_id`). Party breakdowns need activities.
- Activity titles follow "Name, role, affiliation": for members of the Bundestag, `…, MdB, <parliamentary group>` (e.g. `Dr. Petra Sitte, MdB, DIE LINKE`); for answers, `…, Staatssekr., <ministry>`; for Bundesrat members, `…, MdBR (<office>), <Land>`. Group names vary by term (`DIE LINKE`, `Die Linke (Gruppe)`, `fraktionslos`); normalise before counting. `aktivitaetsart` distinguishes `Frage`, `Kleine Anfrage`, `Antwort`, `Rede`, `Zwischenfrage`, etc.
- A proceeding's activities include later steps by others (e.g. an opposition `Entschließungsantrag` on a government bill). To find who *started* it, count only the activity type that starts that proceeding type: `Schriftliche/Mündliche Frage` ← `Frage`, `Kleine Anfrage` ← `Kleine Anfrage`, `Große Anfrage` ← `Große Anfrage`, `Antrag` ← `Antrag`, `Entschließungsantrag BT` ← `Entschließungsantrag`, `Gesetzgebung` ← `Gesetzentwurf`.
- Timestamps are German local time (`+01:00` / `+02:00`); `f.aktualisiert.start` is sent in Europe/Berlin time.
- Interpellations (`Kleine Anfrage`, `Große Anfrage`) have a step `vorgangsposition: "Antwort"` (rarely `"Ergänzende Antwort"`) whose `fundstelle` is the government's answer as a printed paper (`drucksachetyp: "Antwort"`, `urheber: ["Bundesregierung"]`). The lead ministry is on the step: `ressort[].titel` with `federfuehrend: true`. Full text: `drucksache-text/{fundstelle.id}`.
- Printed papers have no structured text: `drucksache-text` gives `text`, a plain extraction of the PDF with its line breaks, hyphenation and running page headers, and no `xml_url` (only transcripts have one). Question-answer structure has to be read from the text.
- An answer repeats each numbered question, then answers it. Numbers 1–9 are padded: an en space (U+2002) in answers, a figure space (U+2007) in the question paper; some papers use a plain space or none. The government may answer jointly and out of order ("Die Fragen 1, 3 und 8 werden gemeinsam beantwortet.", then 2), leaving earlier questions with no text, and answers contain numbered lists of their own. Locating each question by its wording from the interpellation's own paper (step `vorgangsposition: "Kleine Anfrage"`, `drucksachetyp` the same) finds all 1,688 questions in the 21st term's 76 AI answers; one paper prints a number twice ("17 17 Ist …").
- An answer can be on record before its text: in November 2026, 21/9223 had an `Antwort` step but no `text` yet.
- Plenary transcript text (`plenarprotokoll-text`) has one paragraph per line. Bundestag transcripts also link structured XML (`fundstelle.xml_url`) with speeches and speakers.

## Filters

- Thesaurus descriptors expand synonyms: `Maschinelles Lernen` returns the same set as `Künstliche Intelligenz`. `Autonomes Waffensystem` resolves to broader terms (`Militärroboter`, `Unbemanntes Fluggerät`), so results include drone and procurement items.
- OR-repeatable: `f.id`, `f.wahlperiode`, `f.vorgangsposition_id`, `f.person_id`, `f.titel`. Not repeatable: `f.vorgang`, `f.zuordnung` (one value per query). `f.deskriptor` repeats as AND.
- `numFound` is exact; paging with `cursor` to the end yields exactly that many unique ids.

## Paging and limits

- 100 entities per page; full-text endpoints about 10. Results are sorted by date and id, descending. Paging ends when the cursor stops changing.
- Lists of several full texts can arrive cut off: fetch transcripts one id at a time.
- Bot protection: after about 580 requests in two minutes, DIP answered with `303` to `/.enodia/challenge` for more than eight minutes. The client paces at one request per two seconds.

## Links

- Web pages need a slug segment, whose value is ignored: `https://dip.bundestag.de/vorgang/-/{id}` (checked by hand). The person page pattern is unchecked.
- Documents link PDFs with a page anchor: `fundstelle.pdf_url` (e.g. `…/21041.pdf#P.4805`).

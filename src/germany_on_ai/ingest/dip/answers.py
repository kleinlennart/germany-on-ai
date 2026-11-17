"""Government answers to interpellations, split into verbatim question-answer pairs.

An answer's full text repeats each numbered question ("N. ...?") followed by the
government's answer. The government may answer questions jointly and out of order
(1, 3 and 8 together, then 2), so each question is found in the answer by its own
wording, taken from the interpellation's printed paper. Each pair keeps its exact
text and its character offsets into the full text, plus the full text's SHA-256, so
every quote can be checked against the published document.
"""

import re
from typing import Any

from germany_on_ai.ingest.dip.transcripts import text_sha256

# A numbered line: the number and a full stop, after optional padding (answers use an
# en space, U+2002, question papers a figure space, U+2007, before single digits).
QUESTION_START = re.compile(r"(?m)^[^\S\n]*(\d{1,2})\.\s")
# Lines that continue a question: sub-questions ("a) ...") or a lower-case continuation.
CONTINUES = re.compile(r"^\s*([a-z]\)|[a-zäöüß])")
# Running headers and footers of printed papers, and the printer's colophon on the
# last page (an annex may follow it), removed only when showing text.
PAGE_FURNITURE = re.compile(
    r"(?m)^(Drucksache \d+/\d+ – \d+ – Deutscher Bundestag – \d+\. Wahlperiode|"
    r"Deutscher Bundestag – \d+\. Wahlperiode – \d+ – Drucksache \d+/\d+|"
    r"Gesamtherstellung: .*\nVertrieb: .*\nISSN [\d-]+X?\]?)\s*$\n?"
)
# How many letters and digits of a question's opening are compared, and the fewest
# that count as a match.
OPENING = 60
MIN_OPENING = 20


def question_starts(text: str) -> list[re.Match[str]]:
    """Numbered lines kept only while numbering runs 1, 2, 3, ... This reads an
    interpellation's paper reliably, where questions come in order with nothing between
    them, and keeps out lines such as "21. Wahlperiode"."""
    starts, expected = [], 1
    for m in QUESTION_START.finditer(text):
        if int(m.group(1)) == expected:
            starts.append(m)
            expected += 1
    return starts


def question_end(text: str, start: int, limit: int) -> int:
    """End of the question text: the first line ending in '?' that is not followed by a
    sub-question or a continuation. Falls back to the first '?' line."""
    first_q = None
    pos = start
    while pos < limit:
        line_end = text.find("\n", pos, limit)
        line_end = limit if line_end == -1 else line_end
        if text[pos:line_end].rstrip().endswith("?"):
            first_q = first_q or line_end
            next_end = text.find("\n", line_end + 1, limit)
            next_line = text[line_end + 1 : limit if next_end == -1 else next_end]
            if not CONTINUES.match(next_line):
                return line_end
        pos = line_end + 1
    return first_q or limit


def opening(text: str) -> str:
    """A question's first letters and digits after its number, lower-cased: equal in
    the question paper and the answer whatever the line breaks, hyphenation and page
    furniture. Some papers print the number twice ("17 17 Ist ..."), so all leading
    digits go."""
    letters = re.sub(r"\W", "", PAGE_FURNITURE.sub("", text)).lower()
    return letters.lstrip("0123456789")[:OPENING]


def same_question(asked: str, candidate: str) -> bool:
    """A short question's whole text can be shorter than OPENING; then the answer's
    window runs on into the next question, so compare the shorter length."""
    shorter = min(len(asked), len(candidate))
    return shorter >= MIN_OPENING and asked[:shorter] == candidate[:shorter]


def questions(paper: str) -> dict[int, str]:
    """Number to opening of each question in an interpellation's printed paper."""
    starts = question_starts(paper)
    found = {}
    for i, m in enumerate(starts):
        limit = starts[i + 1].start() if i + 1 < len(starts) else len(paper)
        found[int(m.group(1))] = opening(paper[m.start() : limit])
    return found


def located_questions(text: str, paper: str | None) -> list[re.Match[str]]:
    """Question starts in an answer, in text order. With the question paper, a numbered
    line counts only if it opens like that question (so numbered lists inside answers
    are skipped); without it, numbering must run 1, 2, 3, ..."""
    asked = questions(paper) if paper else {}
    if not asked:
        return question_starts(text)
    found: dict[int, re.Match[str]] = {}
    for m in QUESTION_START.finditer(text):
        number = int(m.group(1))
        window = text[m.start() : m.start() + 4 * OPENING]
        if (
            number in asked
            and number not in found
            and same_question(asked[number], opening(window))
        ):
            found[number] = m
    return sorted(found.values(), key=lambda m: m.start())


def extract_pairs(text: str, paper: str | None = None) -> list[dict[str, Any]]:
    starts = located_questions(text, paper)
    digest = text_sha256(text)
    pairs, answered = [], []
    for i, m in enumerate(starts):
        limit = starts[i + 1].start() if i + 1 < len(starts) else len(text)
        q_end = question_end(text, m.start(), limit)
        a_start = min(q_end + 1, limit)
        answered.append(bool(readable(text[a_start:limit])))
        pairs.append(
            {
                "number": int(m.group(1)),
                "question_start": m.start(),
                "question_end": q_end,
                "question": text[m.start() : q_end],
                "answer_start": a_start,
                "answer_end": limit,
                "answer": text[a_start:limit],
                "answered_with": None,
                "fulltext_sha256": digest,
            }
        )
    # Questions answered together ("Die Fragen 1, 3 und 8 werden gemeinsam
    # beantwortet.") leave all but the last empty; point them to the pair whose answer
    # covers them, the next one in the text.
    for i, pair in enumerate(pairs):
        if not answered[i]:
            later = next((j for j in range(i + 1, len(pairs)) if answered[j]), None)
            pair["answered_with"] = (
                pairs[later]["number"] if later is not None else None
            )
    return sorted(pairs, key=lambda p: p["number"])


def readable(verbatim: str) -> str:
    """For display only: drop page headers and footers, join wrapped lines."""
    text = PAGE_FURNITURE.sub("", verbatim)
    text = text.replace(" ", " ")
    text = re.sub(r"-\n(?=[a-zäöüß])", "", text)  # words hyphenated across lines
    text = re.sub(r"-\n(?=[A-ZÄÖÜ])", "-", text)  # compounds such as IT-Sicherheit
    return " ".join(text.split())


def lead_ministry(document: dict[str, Any]) -> str | None:
    lead = [r["titel"] for r in document.get("ressort", []) if r.get("federfuehrend")]
    return lead[0] if lead else None


def answer_pairs(
    document: dict[str, Any], paper: str | None = None
) -> list[dict[str, Any]]:
    """Pair records for one answer (a `drucksache-text` response), each carrying what a
    reader needs without the full text: the paper, the proceeding, the lead ministry.
    `paper` is the full text of the interpellation's own printed paper."""
    vorgang = (document.get("vorgangsbezug") or [{}])[0]
    meta = {
        "drucksache_id": document["id"],
        "dokumentnummer": document["dokumentnummer"],
        "datum": document["datum"],
        "wahlperiode": document["wahlperiode"],
        "vorgang_id": vorgang.get("id"),
        "vorgang_titel": vorgang.get("titel"),
        "vorgangstyp": vorgang.get("vorgangstyp"),
        "ressort": lead_ministry(document),
        "pdf_url": document["fundstelle"]["pdf_url"],
    }
    return [
        {"id": f"{document['id']}-{pair['number']}", **meta, **pair}
        for pair in extract_pairs(document["text"], paper)
    ]


def for_display(pair: dict[str, Any]) -> dict[str, Any]:
    """A stored pair with its question and answer made readable, for the site."""
    offsets = ("question_start", "question_end", "answer_start", "answer_end")
    shown = {k: v for k, v in pair.items() if k not in offsets}
    return shown | {
        "question": readable(pair["question"]),
        "answer": readable(pair["answer"]),
    }

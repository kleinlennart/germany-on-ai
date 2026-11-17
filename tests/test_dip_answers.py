from germany_on_ai.ingest.dip.answers import answer_pairs, extract_pairs, readable

# Shaped like DIP's answer texts: an en space before each question number, wrapped
# questions with sub-questions, page furniture, two questions answered jointly.
TEXT = (
    "Antwort\nder Bundesregierung\n\nVorbemerkung der Bundesregierung\n"
    "Die Bundesregierung fördert 21. Jahrhundert-Technologien.\n"
    " 1. In welchen Bundesministerien werden KI-gestützte Systeme \n"
    "eingesetzt?\n"
    " 2. Ist ein solcher Einsatz geplant,\n"
    "a) in welchen Behörden, und\n"
    "b) bis wann?\n"
    "Die Fragen 1 und 2 werden zusammen beantwortet.\n"
    "Der Einsatz wird in der IT-\nSicherheit geprüft und weiter-\nentwickelt.\n"
    "Drucksache 21/7323 – 4 – Deutscher Bundestag – 21. Wahlperiode\n"
    " 3. Welche Pläne gibt es?\n"
    "Keine.\n"
)


def test_pairs_are_verbatim_slices_in_order():
    pairs = extract_pairs(TEXT)
    assert [p["number"] for p in pairs] == [1, 2, 3]
    for p in pairs:
        assert TEXT[p["question_start"] : p["question_end"]] == p["question"]
        assert TEXT[p["answer_start"] : p["answer_end"]] == p["answer"]
        assert p["question"].endswith("?")


def test_sub_questions_stay_with_their_question():
    assert extract_pairs(TEXT)[1]["question"].endswith("b) bis wann?")


def test_joint_answers_point_to_the_answer_that_covers_them():
    first, second, third = extract_pairs(TEXT)
    assert (first["answer"], first["answered_with"]) == ("", 2)
    assert second["answered_with"] is None
    assert readable(second["answer"]).startswith("Die Fragen 1 und 2")
    assert readable(third["answer"]) == "Keine."


def test_readable_joins_lines_and_drops_page_furniture():
    text = readable(extract_pairs(TEXT)[1]["answer"])
    assert "IT-Sicherheit geprüft und weiterentwickelt." in text
    assert "Wahlperiode" not in text


def test_numbering_with_a_plain_space():
    pairs = extract_pairs(" 1. Was?\nJa.\n 2. Wie?\nSo.\n")
    assert [readable(p["answer"]) for p in pairs] == ["Ja.", "So."]


def test_answer_pairs_carry_the_paper_and_lead_ministry():
    document = {
        "id": "290001",
        "dokumentnummer": "21/7323",
        "datum": "2026-07-01",
        "wahlperiode": 21,
        "vorgangsbezug": [
            {"id": "330001", "titel": "KI", "vorgangstyp": "Kleine Anfrage"}
        ],
        "ressort": [
            {"federfuehrend": False, "titel": "Auswärtiges Amt"},
            {"federfuehrend": True, "titel": "Bundesministerium der Verteidigung"},
        ],
        "fundstelle": {
            "pdf_url": "https://dserver.bundestag.de/btd/21/073/2107323.pdf"
        },
        "text": TEXT,
    }
    pairs = answer_pairs(document)
    assert [p["id"] for p in pairs] == ["290001-1", "290001-2", "290001-3"]
    assert pairs[0]["ressort"] == "Bundesministerium der Verteidigung"
    assert pairs[0]["vorgang_id"] == "330001"


def test_question_paper_finds_questions_answered_out_of_order():
    paper = (
        "Wir fragen die Bundesregierung:\n"
        " 1. Welche Maßstäbe legt die Bundesregierung beim Einsatz an?\n"
        " 2. Wird im Rahmen der Prüfung neuer Waffen geprüft?\n"
        " 3. Welche Merkmale einer Kapitulation werden zugrunde gelegt?\n"
    )
    answer = (
        " 1. Welche Maßstäbe legt die Bundesregierung beim Einsatz an?\n"
        " 3. Welche Merkmale einer Kapitulation werden zugrunde gelegt?\n"
        "Die Fragen 1 und 3 werden gemeinsam beantwortet.\n"
        "Es gelten folgende Grundsätze:\n"
        " 2. Das geltende Recht.\n"  # a numbered list inside the answer
        " 2. Wird im Rahmen der Prüfung neuer Waffen geprüft?\n"
        "Ja.\n"
    )
    pairs = extract_pairs(answer, paper)
    assert [p["number"] for p in pairs] == [1, 2, 3]
    assert pairs[0]["answered_with"] == 3
    assert readable(pairs[1]["answer"]) == "Ja."
    assert readable(pairs[2]["answer"]).endswith("2. Das geltende Recht.")


def test_readable_drops_the_printers_colophon():
    last = (
        "Keine.\n"
        "Gesamtherstellung: H. Heenemann GmbH & Co. KG, Buch- und Offsetdruckerei\n"
        "Vertrieb: Bundesanzeiger Verlag GmbH, Postfach 10 05 34, 50445 Köln\n"
        "ISSN 0722-8333]\n"
        "Anlage 1\n"
    )
    assert readable(last) == "Keine. Anlage 1"

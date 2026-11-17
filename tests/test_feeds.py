from germany_on_ai.ingest.feeds import EXCERPT_CHARS, parse_ical, parse_rss

RSS = (
    """<?xml version="1.0"?>
<rss version="2.0"><channel><title>Feed</title>
<item>
  <title>Bundeskanzler eröffnet   Digital-Gipfel</title>
  <link>https://example.org/a</link>
  <guid>https://example.org/a</guid>
  <pubDate>Tue, 17 Nov 2026 10:00:00 +0100</pubDate>
  <description>&lt;p&gt;KI &amp; Rechenzentren&lt;/p&gt;</description>
</item>
<item>
  <title>Long</title><link>https://example.org/b</link>
  <description>"""
    + "x " * 400
    + """</description>
</item>
</channel></rss>"""
)

ICAL = (
    "BEGIN:VCALENDAR\r\nBEGIN:VEVENT\r\nUID:abc\r\nDTSTART;VALUE=DATE:20260112\r\n"
    "DTEND;VALUE=DATE:20260117\r\nSUMMARY:Sitzungswoche Deutscher\r\n  Bundestag\r\n"
    "END:VEVENT\r\nEND:VCALENDAR\r\n"
)


def test_rss_items_keep_title_date_link_and_a_plain_excerpt():
    first, long = parse_rss(RSS, "https://example.org/feed.xml")
    assert first["title"] == "Bundeskanzler eröffnet Digital-Gipfel"
    assert first["excerpt"] == "KI & Rechenzentren"
    assert first["published"] == "2026-11-17T10:00:00+01:00"
    assert len(long["excerpt"]) <= EXCERPT_CHARS
    assert first["id"] == parse_rss(RSS, "other")[0]["id"]  # id comes from the item


def test_ical_unfolds_lines_and_makes_the_end_date_inclusive():
    (event,) = parse_ical(ICAL)
    assert event == {
        "id": "2026-01-12",
        "start": "2026-01-12",
        "end": "2026-01-16",
        "summary": "Sitzungswoche Deutscher Bundestag",
    }

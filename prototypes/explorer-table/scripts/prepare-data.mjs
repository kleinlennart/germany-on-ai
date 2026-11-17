// PROTOTYPE: flatten stored DIP proceedings into one small JSON file for the UI.
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const dir = "../../data/records/dip/vorgang";
const records = readdirSync(dir)
  .filter((f) => f.endsWith(".jsonl"))
  .flatMap((f) => readFileSync(join(dir, f), "utf8").trim().split("\n").map(JSON.parse));

const names = (d, typ) => (d.deskriptor ?? []).filter((x) => !typ || x.typ === typ).map((x) => x.name);

const rows = records.map(({ data: d, source_url, retrieved_at, content_sha256 }) => ({
  id: d.id,
  title: d.titel,
  type: d.vorgangstyp,
  term: d.wahlperiode,
  date: d.datum ?? null,
  status: d.beratungsstand ?? "–",
  initiators: d.initiative ?? [],
  subjects: d.sachgebiet ?? [],
  descriptors: names(d, "Sachbegriffe"),
  laws: names(d, "Rechtsmaterialien"),
  institutions: names(d, "Institutionen"),
  abstract: d.abstract ?? null,
  linked: (d.vorgang_verlinkung ?? []).map((v) => ({ id: v.id, title: v.titel, relation: v.verweisung })),
  url: source_url,
  retrievedAt: retrieved_at,
  hash: content_sha256,
}));
rows.sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""));

mkdirSync("src/data", { recursive: true });
writeFileSync("src/data/vorgaenge.json", JSON.stringify(rows));
// The catalogue export comes from `uv run germany-on-ai build` in the repo root.
writeFileSync("src/data/catalogue.json", readFileSync("../../build/catalogue.json", "utf8"));
console.log(`prepared ${rows.length} proceedings and the source catalogue`);

// EU lane: Parliament procedure milestones and legal dates of adopted acts.
const readJsonl = (path) => readFileSync(path, "utf8").trim().split("\n").map(JSON.parse);
const euFilter = readFileSync("../../data/fetch/eu.yaml", "utf8");
const shortOf = (key) => {
  const m = euFilter.match(new RegExp(`(?:reference|celex): ${key.replace(/[()/]/g, "\\$&")}\\s+short: (.+)`));
  return m ? m[1].trim() : key;
};
const MILESTONES = {
  COMMITTEE_ADOPTING_REPORT: "Parliament committee adopts its report",
  COMMITTEE_ADOPTING_OPINION: "Parliament committee adopts an opinion",
  PLENARY_ADOPT_POSITION: "Parliament adopts its position",
  INTERINSTITUTIONAL_NEGOTIATION: "Trilogue with Council and Commission",
  COMMITTEE_APPROVE_PROVISIONAL_AGREEMENT: "Parliament committee approves the provisional agreement",
  SIGNATURE: "Signed by Parliament and Council",
  PUBLICATION_OFFICIAL_JOURNAL: "Published in the Official Journal",
};
const euEvents = [];
for (const { data: p, source_url } of readJsonl("../../data/records/ep/procedure/all.jsonl")) {
  const seen = new Set();
  for (const e of p.consists_of ?? []) {
    const type = (e.had_activity_type ?? "").split("/").pop();
    const label = MILESTONES[type];
    if (!label || seen.has(`${e.activity_date}|${label}`)) continue;
    seen.add(`${e.activity_date}|${label}`);
    euEvents.push({ date: e.activity_date, kind: "Parliament", title: `${shortOf(p.label)}: ${label}`, url: source_url, source: "European Parliament open data" });
  }
}
// An act amended by a later tracked act (`amended_by` in eu.yaml) keeps only the dates up
// to the amendment's entry into force; its changed dates come from the curated events.
const amendedBy = Object.fromEntries(
  [...euFilter.matchAll(/celex: (\S+)\s+short: .+\s+(?:#.*\s+)?amended_by: (\S+)/g)].map((m) => [m[1], m[2]]),
);
const acts = Object.fromEntries(readJsonl("../../data/records/cellar/act/all.jsonl").map((r) => [r.data.celex, r]));
for (const { data: a, source_url } of Object.values(acts)) {
  const amender = acts[amendedBy[a.celex]]?.data;
  const cutoff = amender?.date_entry_into_force?.[0];
  (a.date_entry_into_force ?? []).filter((date) => !cutoff || date <= cutoff).forEach((date, i) =>
    euEvents.push({
      date,
      kind: "EU law",
      title: `${shortOf(a.celex)}: ${i === 0 ? "enters into force" : "further provisions start to apply"}`,
      url: source_url,
      source: "EU Publications Office",
    }),
  );
}
euEvents.sort((a, b) => a.date.localeCompare(b.date));
writeFileSync("src/data/eu-events.json", JSON.stringify(euEvents));
console.log(`prepared ${euEvents.length} EU events`);

// Germany calendar: Bundestag sitting weeks (context bands), Bundesrat plenary sessions and
// digital-committee meetings, and government press items that meet the AI rule.
const ordinal = (n) => {
  const s = n % 100 >= 11 && n % 100 <= 13 ? "th" : { 1: "st", 2: "nd", 3: "rd" }[n % 10] ?? "th";
  return `${n}${s}`;
};
const AI_RULE = /\bKI\b|[Kk]ünstliche[nrs]? Intelligenz|AI Act|KI-Verordnung/;
const sittingWeeks = readJsonl("../../data/records/bundestag_sitting_weeks/sitting_week/all.jsonl")
  .map(({ data }) => ({ start: data.start, end: data.end }));
const germanyEvents = [];
for (const { data: e, source_url } of readJsonl("../../data/records/bundesrat_events/event/all.jsonl")) {
  const m = e.title.match(/^(\d{2})\.(\d{2})\.(\d{4})(?: (\d{2}:\d{2}) Uhr)? \| ([^|]+)/);
  if (!m) continue;
  const [, d, mo, y, , name] = m;
  if (!/Plenarsitzung|Digitales/.test(name)) continue;
  if (/entfällt|abgesagt/i.test(e.title)) continue; // cancelled meetings are not events
  const plenary = name.match(/(\d+)\.\s*Plenarsitzung/);
  const title = /Plenarsitzung/.test(name)
    ? `Bundesrat plenary session${plenary ? ` (${ordinal(Number(plenary[1]))})` : ""}`
    : "Bundesrat Committee on Digital Affairs and State Modernisation meets";
  germanyEvents.push({ date: `${y}-${mo}-${d}`, kind: "Bundesrat", title, url: source_url });
}
for (const { data: g, source_url } of readJsonl("../../data/records/bundesregierung_feeds/item/all.jsonl")) {
  if (!AI_RULE.test(`${g.title} ${g.excerpt}`) || !g.published) continue;
  germanyEvents.push({ date: g.published.slice(0, 10), kind: "Federal Government", title: g.title, url: source_url });
}
writeFileSync("src/data/germany-calendar.json", JSON.stringify({ sittingWeeks, events: germanyEvents }));
console.log(`prepared ${sittingWeeks.length} sitting weeks and ${germanyEvents.length} Germany calendar events`);

// Curated events (validated by the Python build, each with an official source).
writeFileSync("src/data/curated-events.json", readFileSync("../../build/curated_events.json", "utf8"));

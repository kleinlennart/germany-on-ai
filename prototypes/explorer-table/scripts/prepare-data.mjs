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
for (const { data: a, source_url } of readJsonl("../../data/records/cellar/act/all.jsonl")) {
  (a.date_entry_into_force ?? []).forEach((date, i) =>
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

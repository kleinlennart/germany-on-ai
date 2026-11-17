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

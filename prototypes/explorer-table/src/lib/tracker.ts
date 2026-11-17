// PROTOTYPE: the descriptive analysis behind the tracker page. Every number on the page
// comes from here, computed at build time from the stored records.
import catalogue from "../data/catalogue.json";
import { type Level, type Seed, seeds } from "../data/seeds";
import data from "../data/vorgaenge.json";
import { formatDate, type Proceeding, recordHref } from "./proceedings";

const all = data as Proceeding[];

// What counts as AI for this page (stated on the page as well). Deterministic and
// provisional until the annotation layer replaces it.
const AI_DESCRIPTORS = ["Künstliche Intelligenz", "Generative KI"];
const AI_TITLE = /\bKI\b|[Kk]ünstliche[nrs]? Intelligenz/;
export const RULE =
  'the Bundestag\'s documentalists have tagged it "Künstliche Intelligenz" or "Generative KI", or if its title contains "KI" or "Künstliche Intelligenz"';

export const isAi = (p: Proceeding) =>
  p.descriptors.some((d) => AI_DESCRIPTORS.includes(d)) || AI_TITLE.test(p.title);

export const TERMS = [
  { term: 19, start: "2017-10-24", end: "2021-10-26" },
  { term: 20, start: "2021-10-26", end: "2025-03-25" },
  { term: 21, start: "2025-03-25", end: null as string | null },
];
export const CURRENT = 21;

const ai = all.filter(isAi);
export const asOf = ai.reduce((max, p) => (p.date > max ? p.date : max), "");
const current = ai.filter((p) => p.term === CURRENT);

const months = (start: string, end: string) =>
  (new Date(end).getTime() - new Date(start).getTime()) / (1000 * 60 * 60 * 24 * 30.44);

export const rates = TERMS.map(({ term, start, end }) => {
  const n = ai.filter((p) => p.term === term).length;
  return { term, n, perMonth: n / months(start, end ?? asOf) };
});
export const currentRate = rates.find((r) => r.term === CURRENT)!;
export const previousRate = Math.max(...rates.filter((r) => r.term !== CURRENT).map((r) => r.perMonth));

export const quarterOf = (iso: string) => `${iso.slice(0, 4)} Q${Math.floor((Number(iso.slice(5, 7)) - 1) / 3) + 1}`;
export const quarters = (() => {
  const counts = new Map<string, number>();
  for (const p of ai) counts.set(quarterOf(p.date), (counts.get(quarterOf(p.date)) ?? 0) + 1);
  const keys = [...counts.keys()].sort();
  const first = keys[0], last = quarterOf(asOf);
  const out: { key: string; n: number; term: number; partial: boolean }[] = [];
  for (let y = Number(first.slice(0, 4)); y <= Number(last.slice(0, 4)); y++) {
    for (let q = 1; q <= 4; q++) {
      const key = `${y} Q${q}`;
      if (key < first || key > last) continue;
      const startMonth = String((q - 1) * 3 + 1).padStart(2, "0");
      const term = [...TERMS].reverse().find((t) => `${y}-${startMonth}-01` >= t.start.slice(0, 7) + "-01")!.term;
      out.push({ key, n: counts.get(key) ?? 0, term, partial: key === last });
    }
  }
  return out;
})();

// How parliament engages: instruments, grouped into readable English categories.
const INSTRUMENTS: Record<string, string> = {
  "Schriftliche Frage": "Written questions",
  "Mündliche Frage": "Oral questions",
  "Kleine Anfrage": "Minor interpellations",
  "Große Anfrage": "Major interpellations",
  "Befragung der Bundesregierung": "Government question time",
  Antrag: "Motions",
  "Entschließungsantrag BT": "Motions",
  "Selbständiger Antrag von Ländern auf Entschließung": "Motions",
  Gesetzgebung: "Legislation",
  "EU-Vorlage": "EU documents",
  "Unterrichtung durch das Europäische Parlament": "EU documents",
  "Bericht, Gutachten, Programm": "Reports and programmes",
};
const QUESTIONS = ["Written questions", "Oral questions", "Minor interpellations", "Major interpellations", "Government question time"];
export const instrumentOf = (p: Proceeding) => INSTRUMENTS[p.type] ?? "Other";

export const instruments = countBy(current, (p) => [instrumentOf(p)]);
export const questionShare = current.filter((p) => QUESTIONS.includes(instrumentOf(p))).length / current.length;

// Who initiates: only proceedings that name an initiator (individual MPs' written and
// oral questions do not, in proceedings data).
const INITIATORS: Record<string, string> = {
  "Fraktion der AfD": "AfD",
  "Fraktion BÜNDNIS 90/DIE GRÜNEN": "Greens",
  "Fraktion DIE LINKE": "Die Linke",
  "Fraktion der CDU/CSU": "CDU/CSU",
  "Fraktion der SPD": "SPD",
  Bundesregierung: "Federal Government",
  Bundestag: "Bundestag (committees and plenary)",
  "Europäische Kommission": "European Commission",
};
const named = current.filter((p) => p.initiators.length);
const unnamed = current.filter((p) => !p.initiators.length);
const MEMBER_QUESTIONS = ["Schriftliche Frage", "Mündliche Frage"];
export const initiatorBase = {
  named: named.length,
  // Written and oral questions are filed by individual members; other items without an
  // initiator (question time, topical hours, statements) are counted separately.
  memberQuestions: unnamed.filter((p) => MEMBER_QUESTIONS.includes(p.type)).length,
  otherUnnamed: unnamed.filter((p) => !MEMBER_QUESTIONS.includes(p.type)).length,
};
// Opposition in the 21st Bundestag (coalition of CDU/CSU and SPD since May 2025).
const OPPOSITION = ["Fraktion der AfD", "Fraktion BÜNDNIS 90/DIE GRÜNEN", "Fraktion DIE LINKE"];
export const byOpposition = named.filter((p) => p.initiators.some((i) => OPPOSITION.includes(i))).length;
export const initiators = countBy(named, (p) => p.initiators.map((i) => INITIATORS[i] ?? i)).slice(0, 8);

// What AI is discussed with: the documentalists' other subject keywords.
const GENERIC = new Set(["Künstliche Intelligenz", "Gesetzgebung", "Bundesmittel", "Digitalisierung"]);
export const topics = countBy(current, (p) => p.descriptors.filter((d) => !GENERIC.has(d))).slice(0, 10);
export const recordsWith = (descriptor: string) => current.filter((p) => p.descriptors.includes(descriptor));

// What is moving: legislation this term, newest first, with status in English.
const STATUS: Record<string, { label: string; order: number }> = {
  Verkündet: { label: "In force", order: 4 },
  Verabschiedet: { label: "Passed", order: 3 },
  Überwiesen: { label: "In committee", order: 2 },
  "Dem Bundestag zugeleitet - Noch nicht beraten": { label: "Submitted, not yet debated", order: 1 },
};
export const statusOf = (p: Proceeding) => STATUS[p.status]?.label ?? p.status;
export const legislation = current.filter((p) => p.type === "Gesetzgebung").sort((a, b) => b.date.localeCompare(a.date));

export const latest = [...current].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 6);

// Timeline: what happened and what is coming, across levels. Parliament items come from
// records; other levels from the brief's seeds until their sources are ingested.
export type TimelineItem = {
  sortKey: string;
  when: string;
  level: Level;
  kind: string;
  title: string;
  status?: string;
  href?: string;
  fromBrief: boolean;
  held?: boolean;
  start: string; // ISO day; with end, the period a coarse date covers
  end: string;
  short?: string;
};
const DEBATES: Record<string, string> = {
  "Aktuelle Stunde": "Topical hour",
  Regierungserklärung: "Government statement",
  "Vereinbarte Debatte": "Debate",
  "Befragung der Bundesregierung": "Government question time",
  "Große Anfrage": "Major interpellation",
  "Enquete-Kommission": "Commission of inquiry",
  Gesetzgebung: "Bill",
};
const monthName = (iso: string) =>
  new Date(`${iso.slice(0, 7)}-01`).toLocaleDateString("en-GB", { month: "long", year: "numeric" });
const lastDay = (y: number, m: number) => new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10);
const period = (s: Seed): [string, string] => {
  const y = Number(s.date.slice(0, 4)), m = Number(s.date.slice(5, 7));
  if (s.precision === "day") return [s.date, s.date];
  if (s.precision === "month") return [`${s.date}-01`, lastDay(y, m)];
  if (s.precision === "season") return [`${s.date}-01`, lastDay(y, m + 2)];
  return [`${y}-01-01`, `${y}-12-31`];
};
const seedItem = (s: Seed): TimelineItem => ({
  sortKey: s.precision === "day" ? s.date : s.precision === "year" ? `${s.date}-12-31` : `${s.date}-15`,
  when: s.label ?? (s.precision === "day" ? formatDate(s.date) : s.precision === "month" ? monthName(s.date) : s.date),
  level: s.level,
  kind: s.kind,
  title: s.title,
  fromBrief: true,
  held: s.held,
  start: period(s)[0],
  end: period(s)[1],
  short: s.short,
});
const recordItem = (p: Proceeding): TimelineItem => ({
  sortKey: p.date,
  when: formatDate(p.date),
  level: "Germany",
  kind: DEBATES[p.type],
  title: p.title,
  status: p.type === "Gesetzgebung" ? statusOf(p) : undefined,
  href: recordHref(p.id),
  fromBrief: false,
  start: p.date,
  end: p.date,
});

export const today = new Date().toISOString().slice(0, 10);
export const yearAgo = `${Number(today.slice(0, 4)) - 1}${today.slice(4)}`;
const dated = [
  ...current.filter((p) => p.type in DEBATES && p.type !== "Gesetzgebung").map(recordItem),
  ...legislation.filter((p) => STATUS[p.status]?.order >= 3).map(recordItem),
  ...seeds.map(seedItem),
];
const isPast = (i: TimelineItem) => i.held ?? i.sortKey <= today;
export const timeline = {
  upcoming: dated.filter((i) => !isPast(i)).sort((a, b) => a.sortKey.localeCompare(b.sortKey)),
  pending: legislation.filter((p) => STATUS[p.status]?.order <= 2 || !STATUS[p.status]).map(recordItem),
  past: dated.filter((i) => isPast(i) && i.sortKey >= yearAgo).sort((a, b) => b.sortKey.localeCompare(a.sortKey)),
};
export const totals = { current: current.length, all: ai.length };

// Coverage: which levels have live sources and which are planned, from the catalogue.
type Source = { id: string; name: string; arenas: string[]; status: string; kind: string };
// Ordered from the highest level of governance down, matching the timeline lanes.
const LEVELS = [
  { id: "international", label: "International" },
  { id: "eu", label: "European Union" },
  { id: "domestic", label: "Germany" },
];
export const coverage = LEVELS.map(({ id, label }) => {
  const sources = (catalogue as Source[]).filter((s) => s.arenas.includes(id) && s.kind === "primary");
  return {
    label,
    live: sources.filter((s) => ["ingested", "partial"].includes(s.status) || s.id === "dip"),
    planned: sources.filter((s) => s.status === "planned" && s.id !== "dip"),
  };
});

function countBy(items: Proceeding[], keys: (p: Proceeding) => string[]): [string, number][] {
  const counts = new Map<string, number>();
  for (const p of items) for (const k of new Set(keys(p))) counts.set(k, (counts.get(k) ?? 0) + 1);
  return [...counts].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}

/** Stable anchor for an event, shared by the timeline line and the list below it. */
export const eventId = (i: TimelineItem) =>
  `ev-${i.start}-${i.title.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").slice(0, 32).replace(/-+$/, "")}`;

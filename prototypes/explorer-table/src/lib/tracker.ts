// PROTOTYPE: the descriptive analysis behind the tracker page. Every number on the page
// comes from here, computed at build time from the stored records.
import catalogue from "../data/catalogue.json";
import { type Level, type Seed, seeds } from "../data/seeds";
import curatedEvents from "../data/curated-events.json";
import euEvents from "../data/eu-events.json";
import germanyCalendar from "../data/germany-calendar.json";
import answerData from "../data/answers.json";
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
export const recordsByInstrument = (instrument: string) => current.filter((p) => instrumentOf(p) === instrument);
export const questionShare = current.filter((p) => QUESTIONS.includes(instrumentOf(p))).length / current.length;

// Who initiates: the parliamentary groups of the members who started a proceeding (from
// activities); otherwise its institutional initiator (government, Bundesrat, EU, committees).
const INSTITUTIONS: Record<string, string> = {
  Bundesregierung: "Federal Government",
  Bundesrat: "Bundesrat",
  Bundestag: "Bundestag (committees and plenary)",
  "Europäische Kommission": "European Commission",
  "Europäisches Parlament": "European Parliament",
  "Ausschuss für Forschung, Technologie, Raumfahrt und Technikfolgenabschätzung": "Bundestag research committee",
  "Bundesbeauftragter für den Datenschutz und die Informationsfreiheit": "Federal Data Protection Commissioner",
};
const memberStarted = current.filter((p) => p.memberParties.length);
const whoStarted = (p: Proceeding) =>
  p.memberParties.length ? p.memberParties : p.initiators.map((i) => INSTITUTIONS[i] ?? i);
export const initiators = countBy(current, whoStarted).slice(0, 8);
export const recordsStartedBy = (who: string) => current.filter((p) => whoStarted(p).includes(who));
export const initiatorBase = { members: memberStarted.length, others: current.length - memberStarted.length };
// Opposition in the 21st Bundestag (coalition of CDU/CSU and SPD since May 2025).
const OPPOSITION = ["AfD", "Greens", "Die Linke"];
export const byOpposition = memberStarted.filter((p) => p.memberParties.some((g) => OPPOSITION.includes(g))).length;

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
  external?: boolean; // href points to the source outside this site
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
// Debates and settled bills from parliament; for the line, from every term.
const parliamentItems = (ps: Proceeding[]) => [
  ...ps.filter((p) => p.type in DEBATES && p.type !== "Gesetzgebung").map(recordItem),
  ...ps.filter((p) => p.type === "Gesetzgebung" && STATUS[p.status]?.order >= 3).map(recordItem),
];
const otherItems: TimelineItem[] = [
  ...seeds.map(seedItem),
  ...euEvents.map(
    (e): TimelineItem => ({
      sortKey: e.date,
      when: formatDate(e.date),
      level: "European Union",
      kind: e.kind,
      title: e.title,
      href: e.url,
      external: true,
      fromBrief: false,
      start: e.date,
      end: e.date,
    }),
  ),
];
const sourcedItem = (level: Level) => (e: { date: string; kind: string; title: string; url: string }): TimelineItem => ({
  sortKey: e.date,
  when: formatDate(e.date),
  level,
  kind: e.kind,
  title: e.title,
  href: e.url,
  external: true,
  fromBrief: false,
  start: e.date,
  end: e.date,
});
otherItems.push(...germanyCalendar.events.map(sourcedItem("Germany")));

// Curated events: each verified against an official source; coarse dates become periods.
const CURATED_LEVEL: Record<string, Level> = {
  international: "International",
  eu: "European Union",
  national: "Germany",
};
type Curated = {
  date: string; precision: Seed["precision"]; end: string | null; level: string; kind: string;
  title: string; source_url: string; held: boolean;
};
otherItems.push(
  ...(curatedEvents as Curated[]).map((c): TimelineItem => {
    const asSeed: Seed = { date: c.date, precision: c.precision, level: CURATED_LEVEL[c.level], kind: c.kind, title: c.title, held: c.held };
    const [start, end] = period(asSeed);
    return {
      sortKey: start,
      when: c.end ? `${formatDate(c.date)} to ${formatDate(c.end)}` : seedItem(asSeed).when,
      level: CURATED_LEVEL[c.level],
      kind: c.kind,
      title: c.title,
      href: c.source_url,
      external: true,
      fromBrief: false,
      held: c.held,
      start,
      end: c.end ?? end,
    };
  }),
);
/** Bundestag sitting weeks: context bands on the Germany lane, not events. */
export const sittingWeeks = germanyCalendar.sittingWeeks;
const dated = [...parliamentItems(current), ...otherItems];
/** Everything with a date, across all terms: the timeline line can zoom out to 2017. */
export const lineItems = [...parliamentItems(ai), ...otherItems].sort((a, b) => a.start.localeCompare(b.start));

const shiftMonths = (iso: string, months: number) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCMonth(d.getUTCMonth() + months);
  return d.toISOString().slice(0, 10);
};
/** Zoom presets for the line, all anchored on today. The first-listed default is "1y". */
export const RANGES = [
  { key: "3m", label: "±3 months", from: "", to: "" },
  { key: "1y", label: "±1 year", from: "", to: "" },
  { key: "all", label: "Since 2017", from: "", to: "" },
].map((r) => ({
  ...r,
  from: r.key === "3m" ? shiftMonths(today, -3) : r.key === "1y" ? shiftMonths(today, -12) : TERMS[0].start,
  to: r.key === "3m" ? shiftMonths(today, 3) : shiftMonths(today, 12),
}));
export const DEFAULT_RANGE = "1y";
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

// What the government says: its answers to interpellations on AI this term, split into
// the numbered questions and the answer to each (quoted in German as published).
export type AnswerPair = { n: number; q: string; a: string; with: number | null };
export type Answer = {
  id: string; number: string; date: string; ministry: string | null; vorgangId: string;
  title: string; type: string; pdf: string; pairs: AnswerPair[];
};
// Short English names for the lead ministries (21st term; the 20th-term names that
// still occur are kept).
const MINISTRIES: Record<string, string> = {
  "Bundesministerium für Digitales und Staatsmodernisierung": "Digital Ministry",
  "Bundesministerium des Innern": "Interior Ministry",
  "Bundesministerium für Arbeit und Soziales": "Labour Ministry",
  "Bundesministerium der Verteidigung": "Defence Ministry",
  "Bundesministerium für Forschung, Technologie und Raumfahrt": "Research Ministry",
  "Bundesministerium der Justiz und für Verbraucherschutz": "Justice Ministry",
  "Bundesministerium für Bildung, Familie, Senioren, Frauen und Jugend": "Education and Family Ministry",
  "Bundesministerium für Landwirtschaft, Ernährung und Heimat": "Agriculture Ministry",
  "Bundesministerium für Verkehr": "Transport Ministry",
  "Auswärtiges Amt": "Foreign Office",
  "Bundesministerium für Wirtschaft und Energie": "Economy Ministry",
  "Bundesministerium für Wirtschaft und Klimaschutz": "Economy Ministry (until May 2025)",
  "Bundesministerium der Finanzen": "Finance Ministry",
  "Bundesministerium für Gesundheit": "Health Ministry",
  "Beauftr. der Bundesregierung für Kultur und Medien": "Culture Commissioner",
  "Bundesministerium für Wohnen, Stadtentwicklung und Bauwesen": "Housing Ministry",
};
export const ministryName = (m: string | null) => (m ? MINISTRIES[m] ?? m : "Ministry not stated");
const byId = new Map(current.map((p) => [p.id, p]));
export const answers = (answerData as Answer[]).filter((a) => byId.has(a.vorgangId));
export const answersFor = (vorgangId: string) => (answerData as Answer[]).filter((a) => a.vorgangId === vorgangId);
export const answerAskedBy = (a: Answer) => byId.get(a.vorgangId)?.memberParties ?? [];
const interpellations = current.filter((p) => ["Kleine Anfrage", "Große Anfrage"].includes(p.type));
const hasAnswer = (p: Proceeding) => p.steps.some((s) => s.step === "Antwort" || s.step === "Ergänzende Antwort");
export const answerTotals = {
  asked: interpellations.length,
  answered: interpellations.filter(hasAnswer).length,
  withText: new Set(answers.map((a) => a.vorgangId)).size,
  pairs: answers.reduce((n, a) => n + a.pairs.length, 0),
};
export const answeringMinistries = countBy(
  answers.map((a) => byId.get(a.vorgangId)!).filter(Boolean),
  (p) => [...new Set(answers.filter((a) => a.vorgangId === p.id).map((a) => ministryName(a.ministry)))],
);
export const recordsAnsweredBy = (ministry: string) =>
  [...new Set(answers.filter((a) => ministryName(a.ministry) === ministry).map((a) => a.vorgangId))].map((id) => byId.get(id)!);

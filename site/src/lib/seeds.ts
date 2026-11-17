// Dated events from research notes that no ingested or curated source covers yet.
// Each is marked on the page "Source not yet linked"; one moves to
// data/curated/events.yaml once its official source is found.
export type Level = "Germany" | "European Union" | "International";
export type Precision = "day" | "month" | "season" | "year";

export type Seed = {
  date: string; // ISO day, month (YYYY-MM) or year (YYYY)
  precision: Precision;
  label?: string; // display date when precision is coarse
  level: Level;
  kind: string;
  title: string;
  short?: string; // label on the timeline line, for upcoming events
  // Month- or season-level dates can't tell past from future, so each seed says.
  held: boolean;
};

export const seeds: Seed[] = [
  { date: "2025-12-01", precision: "day", level: "International", kind: "UN vote", title: "UN General Assembly adopts resolution A/RES/80/57 on autonomous weapons, 164 to 6 with 7 abstentions", held: true },
  { date: "2026-02-11", precision: "day", level: "Germany", kind: "Cabinet", title: "Cabinet approves the AI Act implementation law", held: true },
  { date: "2026-03-23", precision: "day", level: "Germany", kind: "Hearing", title: "Bundestag Digital committee hearing on the AI Act implementation law", held: true },
  { date: "2026-04", precision: "month", level: "Germany", kind: "Advisory body", title: "Expert commission ‘Competition and AI’ (Economy Ministry) delivers final recommendations", held: true },
  { date: "2026-06", precision: "month", level: "Germany", kind: "Government", title: "National Security Council decides to set up an AI safety institute", held: true },
  { date: "2026-08", precision: "month", level: "Germany", kind: "Government", title: "Interior and Digital ministries launch the AI safety institute", held: true },
];

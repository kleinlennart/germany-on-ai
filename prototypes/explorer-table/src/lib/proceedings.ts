// PROTOTYPE: the shape of a proceeding as prepared for the pages, and small formatting helpers.

export type Proceeding = {
  id: string;
  title: string;
  type: string;
  term: number;
  date: string;
  status: string;
  initiators: string[];
  subjects: string[];
  descriptors: string[];
  laws: string[];
  institutions: string[];
  abstract: string | null;
  linked: { id: string; title: string; relation: string }[];
  url: string;
  retrievedAt: string;
  hash: string;
};

export const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });

export const recordHref = (id: string) => `${import.meta.env.BASE_URL}vorgang/${id}/`;

/** 19 -> "19th", 21 -> "21st", 22 -> "22nd". */
export const ordinal = (n: number | string) => {
  const v = Number(n);
  const suffix = v % 100 >= 11 && v % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[v % 10] ?? "th";
  return `${v}${suffix}`;
};

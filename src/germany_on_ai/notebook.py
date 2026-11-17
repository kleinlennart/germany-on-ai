"""Notebook helpers: DataFrames shown as Markdown tables, so rendered output stays
readable as plain text (for agents and diffs) as well as in HTML."""

import pandas as pd
from IPython.core.getipython import get_ipython

MAX_ROWS = 60
MAX_CELL = 120


def _cell(value: object) -> str:
    text = "" if value is None or value is pd.NA else str(value)
    text = text.replace("|", "\\|").replace("\n", " ")
    return text if len(text) <= MAX_CELL else text[: MAX_CELL - 1] + "…"


def to_markdown(df: pd.DataFrame) -> str:
    shown = df.head(MAX_ROWS)
    columns = [str(c) for c in shown.columns]
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += [
        "| " + " | ".join(_cell(v) for v in row) + " |"
        for row in shown.itertuples(index=False)
    ]
    if len(df) > MAX_ROWS:
        lines.append(f"\n_{len(df) - MAX_ROWS} more rows not shown._")
    return "\n".join(lines)


def setup() -> None:
    shell = get_ipython()
    formatter = shell.display_formatter if shell else None
    if formatter is None:
        return
    formatter.formatters["text/markdown"].for_type(pd.DataFrame, to_markdown)
    formatter.formatters["text/html"].for_type(pd.DataFrame, lambda df: None)

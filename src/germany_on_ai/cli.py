import argparse
import os
import sys
from datetime import timedelta
from pathlib import Path

from pydantic import ValidationError

from germany_on_ai import build, catalogue, store
from germany_on_ai.ingest.dip import ingest as dip
from germany_on_ai.ingest.dip import spec as dip_spec
from germany_on_ai.ingest.dip import transcripts
from germany_on_ai.ingest.dip.client import DipClient, DipError

FULLTEXT_PATH = build.BUILD_DIR / "release" / "dip_plenarprotokoll_text.parquet"


def _catalogue(args: argparse.Namespace) -> int:
    try:
        sources = catalogue.load(args.path)
    except (ValidationError, ValueError) as error:
        print(f"Catalogue invalid: {error}", file=sys.stderr)
        return 1
    questions = catalogue.open_questions(sources)
    print(f"{len(sources)} sources valid; {len(questions)} open questions")
    for question in questions:
        print(f"  - {question}")
    if args.export:
        catalogue.export(sources, args.export)
        print(f"Exported to {args.export}")
    return 0


def _ingest_dip(args: argparse.Namespace) -> int:
    try:
        client = DipClient(
            os.environ.get("DIP_API_KEY"),
            offline=args.offline,
            reuse_cache_younger_than=timedelta(hours=12) if args.resume else None,
        )
        stats = dip.run(client, full=args.full)
    except DipError as error:
        print(f"DIP ingest failed: {error}", file=sys.stderr)
        return 1
    for entity, s in stats.items():
        print(
            f"{entity}: {s.added} added, {s.changed} changed, {s.unchanged} unchanged"
        )
    return 0


def _check_dip_spec(args: argparse.Namespace) -> int:
    problems = dip_spec.check()
    for problem in problems:
        print(f"  - {problem}")
    print(
        "DIP spec matches the lock"
        if not problems
        else "DIP spec drifted from the lock"
    )
    return 1 if problems else 0


def _build(args: argparse.Namespace) -> int:
    for table, count in build.build().items():
        print(f"{table}: {count}")
    return 0


def _export_fulltext(args: argparse.Namespace) -> int:
    protokolle = [
        r.data
        for path in sorted((dip.RECORDS_DIR / "plenarprotokoll").glob("*.jsonl"))
        for r in store.read(path)
    ]
    try:
        count = transcripts.export_fulltext(
            DipClient(None, offline=True), protokolle, FULLTEXT_PATH
        )
    except DipError as error:
        print(f"Full-text export failed: {error}", file=sys.stderr)
        return 1
    print(f"{count} transcripts written to {FULLTEXT_PATH}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="germany-on-ai")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalogue", help="validate the Source catalogue")
    check.add_argument("--path", type=Path, default=catalogue.CATALOGUE_PATH)
    check.add_argument(
        "--export", type=Path, metavar="JSON", help="also write the catalogue as JSON"
    )
    check.set_defaults(run=_catalogue)

    ingest = commands.add_parser("ingest", help="fetch Source records")
    sources = ingest.add_subparsers(dest="source", required=True)
    dip_parser = sources.add_parser("dip", help="Bundestag and Bundesrat (DIP API)")
    dip_parser.add_argument(
        "--full", action="store_true", help="ignore the last-run state"
    )
    dip_parser.add_argument(
        "--offline", action="store_true", help="read cached responses only"
    )
    dip_parser.add_argument(
        "--resume",
        action="store_true",
        help="reuse responses cached in the last 12 hours",
    )
    dip_parser.set_defaults(run=_ingest_dip)

    spec = commands.add_parser(
        "check-dip-spec", help="compare DIP's live API spec with the lock"
    )
    spec.set_defaults(run=_check_dip_spec)

    commands.add_parser(
        "build", help="compile records into DuckDB and Parquet"
    ).set_defaults(run=_build)

    commands.add_parser(
        "export-fulltext",
        help="write cached plenary transcript texts to Parquet (release asset)",
    ).set_defaults(run=_export_fulltext)

    args = parser.parse_args(argv)
    return args.run(args)

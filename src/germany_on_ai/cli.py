import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from germany_on_ai import catalogue


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="germany-on-ai")
    commands = parser.add_subparsers(dest="command", required=True)

    check = commands.add_parser("catalogue", help="validate the Source catalogue")
    check.add_argument("--path", type=Path, default=catalogue.CATALOGUE_PATH)
    check.add_argument(
        "--export", type=Path, metavar="JSON", help="also write the catalogue as JSON"
    )
    check.set_defaults(run=_catalogue)

    args = parser.parse_args(argv)
    return args.run(args)

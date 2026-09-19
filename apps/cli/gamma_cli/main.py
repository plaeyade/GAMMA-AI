from __future__ import annotations

import argparse
import json
from pathlib import Path

from gamma_config import load_settings
from gamma_persistence import SQLiteRepository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gamma")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("config-check")
    migrate = subcommands.add_parser("migrate")
    migrate.add_argument("--database", default="data/gamma-dev.db")
    migrate.add_argument("--migrations", default="migrations/versions")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "config-check":
        settings = load_settings()
        print(json.dumps({"status": "ok", "environment": settings.environment}, sort_keys=True))
        return 0
    if args.command == "migrate":
        Path(args.database).parent.mkdir(parents=True, exist_ok=True)
        repository = SQLiteRepository(args.database)
        repository.apply_migrations(Path(args.migrations))
        print(json.dumps({"status": "ok", "database": args.database}, sort_keys=True))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


def verify_database(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {path}")
    with closing(sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()
    if result is None or result[0] != "ok":
        raise RuntimeError(f"SQLite integrity check failed: {result}")


def copy_database(source: Path, target: Path) -> None:
    verify_database(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
    try:
        with (
            closing(
                sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True),
            ) as source_db,
            closing(sqlite3.connect(temporary)) as target_db,
        ):
            source_db.backup(target_db)
        verify_database(temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup, restore, or verify a SQLite database.")
    parser.add_argument("mode", choices=("backup", "restore", "verify"))
    parser.add_argument("source", type=Path)
    parser.add_argument("target", nargs="?", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    if args.mode == "verify":
        verify_database(source)
        print(f"SQLite integrity check passed: {source}")
        return
    if args.target is None:
        parser.error("target is required for backup and restore")
    target = args.target.resolve()
    copy_database(source, target)
    verb = "Backup" if args.mode == "backup" else "Restore"
    print(f"{verb} completed and verified: {source} -> {target}")


if __name__ == "__main__":
    main()

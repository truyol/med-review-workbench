import sqlite3
from pathlib import Path

from app.ops.sqlite_backup import copy_database, verify_database


def test_sqlite_backup_and_restore_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"

    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE evidence (value TEXT NOT NULL)")
        connection.execute("INSERT INTO evidence VALUES ('p7')")

    copy_database(source, backup)
    copy_database(backup, restored)
    verify_database(restored)

    with sqlite3.connect(restored) as connection:
        value = connection.execute("SELECT value FROM evidence").fetchone()
    assert value == ("p7",)

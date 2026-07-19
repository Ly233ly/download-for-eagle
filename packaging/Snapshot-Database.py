from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a consistent SQLite backup and redacted inventory.")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    source = args.source.resolve()
    destination = args.destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source) as connection, sqlite3.connect(destination) as backup:
        connection.backup(backup)
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        counts = {
            table: int(
                connection.execute(
                    'SELECT COUNT(*) FROM "' + table.replace('"', '""') + '"'
                ).fetchone()[0]
            )
            for table in tables
        }
        paired = bool(
            connection.execute(
                "SELECT COUNT(*) FROM settings "
                "WHERE key = 'extension_token_hash' AND length(value) > 0"
            ).fetchone()[0]
        )
        result = {
            "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            "userVersion": int(connection.execute("PRAGMA user_version").fetchone()[0]),
            "counts": counts,
            "paired": paired,
        }
    result["backupSha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

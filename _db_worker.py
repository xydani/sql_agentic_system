"""
_db_worker.py

Standalone script invoked by db_executor.py as a subprocess:
    python _db_worker.py <db_path> <sql> [max_rows] [ro|rw]

Deliberately NOT imported anywhere - it is only ever run via
`sys.executable _db_worker.py ...` so a hanging/misbehaving query can be
killed with a subprocess timeout without touching the main process.

Kept as its own file (rather than a triple-quoted string passed to
`python -c`) so it can't get its indentation mangled by an editor/
autoformatter reflowing a string literal.
"""

import json
import sqlite3
import sys
from pathlib import Path


def _connect(db_path: str, read_only: bool) -> sqlite3.Connection:
    if not read_only:
        return sqlite3.connect(db_path)
    uri = Path(db_path).resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def main():
    db_path, sql = sys.argv[1], sys.argv[2]
    max_rows = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    read_only = sys.argv[4] != "rw" if len(sys.argv) > 4 else True
    conn = None
    try:
        conn = _connect(db_path, read_only)
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        if max_rows > 0:
            rows = cur.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            rows = rows[:max_rows]
        else:
            rows = cur.fetchall()
            truncated = False
        if not read_only:
            conn.commit()
        print(json.dumps({"success": True, "columns": columns, "rows": rows, "truncated": truncated}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()

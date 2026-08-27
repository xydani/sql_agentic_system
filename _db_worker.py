"""
_db_worker.py

Standalone script invoked by db_executor.py as a subprocess:
    python _db_worker.py <db_path> <sql>

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


def main():
    db_path, sql = sys.argv[1], sys.argv[2]
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(sql)
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall()
        print(json.dumps({"success": True, "columns": columns, "rows": rows}))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    main()

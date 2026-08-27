"""
schema_utils.py

Introspects a SQLite database and produces a compact textual description
of its schema, suitable for injecting into an LLM prompt as context.

Swap out `get_schema_description` if you move to Postgres/MySQL/etc:
just point it at your driver's information_schema / catalog tables and
keep the same output format (CREATE TABLE-ish text works well for LLMs).
"""

import sqlite3


def get_schema_description(db_path: str) -> str:
    #Return a human/LLM-readable description of every table in the DB.
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cur.fetchall()]

    chunks = []
    for table in tables:
        cur.execute(f"PRAGMA table_info({table});")
        columns = cur.fetchall()  # cid, name, type, notnull, dflt_value, pk

        cur.execute(f"PRAGMA foreign_key_list({table});")
        fks = cur.fetchall()

        col_lines = []
        for col in columns:
            _, name, ctype, notnull, default, pk = col
            flags = []
            if pk:
                flags.append("PRIMARY KEY")
            if notnull:
                flags.append("NOT NULL")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            col_lines.append(f"  - {name}: {ctype}{flag_str}")

        fk_lines = []
        for fk in fks:
            # id, seq, table, from, to, on_update, on_delete, match
            fk_lines.append(f"  - {fk[3]} -> {fk[2]}({fk[4]})")

        table_desc = f"TABLE {table}\n" + "\n".join(col_lines)
        if fk_lines:
            table_desc += "\n  Foreign keys:\n" + "\n".join(fk_lines)
        chunks.append(table_desc)

    conn.close()
    return "\n\n".join(chunks)


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "example.db"
    print(get_schema_description(path))

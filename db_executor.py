"""
db_executor.py

Runs a SQL string against the target database and returns a structured
result: either the rows produced, or the exact error message the DB
engine raised (which is what we feed back to the LLM for self-correction).

Executed in a subprocess (not just an in-process sqlite3 call) so that:
  - a query that hangs or misbehaves doesn't take down the agent loop
  - this file is the single point where you'd swap in a different DB
    engine, add a read-only connection, a query timeout, a row limit,
    or a permission check (e.g. block DROP/DELETE) before going further.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass

_WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_db_worker.py")

DEFAULT_MAX_ROWS = 50


@dataclass
class ExecutionResult:
    success: bool
    columns: list | None = None
    rows: list | None = None
    error: str | None = None
    truncated: bool = False


_ALLOWED_FIRST_KEYWORDS = ("SELECT", "WITH")

_TOP_LEVEL_WRITE_VERBS = re.compile(r"\b(DELETE|UPDATE|INSERT|REPLACE)\b", re.IGNORECASE)


def _skeleton(sql: str) -> str:
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < n else ""
        if ch == "-" and nxt == "-":
            j = sql.find("\n", i)
            i = n if j == -1 else j
        elif ch == "/" and nxt == "*":
            j = sql.find("*/", i + 2)
            out.append(" ")
            i = n if j == -1 else j + 2
        elif ch in ("'", '"', "`"):
            j = i + 1
            while j < n:
                if sql[j] == ch:
                    if j + 1 < n and sql[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            out.append(ch + ch)
            i = j + 1
        elif ch == "[":
            j = sql.find("]", i)
            out.append("[]")
            i = n if j == -1 else j + 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _top_level(skeleton: str) -> str:
    out: list[str] = []
    depth = 0
    for ch in skeleton:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def validate_read_only(sql: str) -> str | None:
    skeleton = _skeleton(sql)

    body, sep, rest = skeleton.partition(";")
    if sep and rest.strip():
        return "multiple statements are not allowed; send exactly one SELECT."

    match = re.match(r"[\s(]*([A-Za-z_]+)", body)
    if not match:
        return "the query is empty or does not start with a SQL keyword."

    first = match.group(1).upper()
    if first not in _ALLOWED_FIRST_KEYWORDS:
        return (f"only read-only queries are allowed; the statement must start "
                f"with SELECT or WITH, but it starts with {first}.")

    verb = _TOP_LEVEL_WRITE_VERBS.search(_top_level(body))
    if verb:
        return f"{verb.group(1).upper()} is not allowed, even after a WITH clause."

    return None


def execute_sql(
    db_path: str,
    sql: str,
    allow_writes: bool = False,
    timeout: int = 10,
    max_rows: int = DEFAULT_MAX_ROWS,
) -> ExecutionResult:
    """
    Runs `sql` against `db_path` in an isolated subprocess.
    Returns an ExecutionResult describing success/failure.
    """
    if not allow_writes:
        reason = validate_read_only(sql)
        if reason:
            return ExecutionResult(success=False, error=f"Refused: {reason}")

    # We shell out to a tiny worker script (_db_worker.py) so a runaway
    # query can be killed cleanly via subprocess timeout without touching
    # the main process.
    mode = "rw" if allow_writes else "ro"
    try:
        proc = subprocess.run(
            [sys.executable, _WORKER_PATH, db_path, sql, str(max_rows), mode],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return ExecutionResult(success=False, error=f"Query timed out after {timeout}s.")

    if proc.returncode != 0 and not proc.stdout.strip():
        return ExecutionResult(success=False, error=proc.stderr.strip() or "Unknown execution error.")

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return ExecutionResult(success=False, error=proc.stderr.strip() or proc.stdout.strip())

    if payload["success"]:
        return ExecutionResult(
            success=True,
            columns=payload["columns"],
            rows=payload["rows"],
            truncated=payload.get("truncated", False),
        )
    return ExecutionResult(success=False, error=payload["error"])

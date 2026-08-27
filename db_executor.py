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
import subprocess
import sys
from dataclasses import dataclass

_WORKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_db_worker.py")


@dataclass
class ExecutionResult:
    success: bool
    columns: list | None = None
    rows: list | None = None
    error: str | None = None


# Statement types we refuse to run automatically. Expand as needed, or
# replace with a proper allow-list / read-only DB user in production.
_FORBIDDEN_PREFIXES = ("DROP", "DELETE", "UPDATE", "ALTER", "INSERT", "TRUNCATE")


def _is_write_statement(sql: str) -> bool:
    first_word = sql.strip().split(None, 1)[0].upper() if sql.strip() else ""
    return first_word in _FORBIDDEN_PREFIXES


def execute_sql(db_path: str, sql: str, allow_writes: bool = False, timeout: int = 10) -> ExecutionResult:
    """
    Runs `sql` against `db_path` in an isolated subprocess.
    Returns an ExecutionResult describing success/failure.
    """
    if not allow_writes and _is_write_statement(sql):
        return ExecutionResult(
            success=False,
            error=f"Refused to execute a write statement ('{sql.strip().split()[0]}'). "
                  f"This agent is configured for read-only SELECT queries.",
        )

    # We shell out to a tiny worker script (_db_worker.py) so a runaway
    # query can be killed cleanly via subprocess timeout without touching
    # the main process.
    try:
        proc = subprocess.run(
            [sys.executable, _WORKER_PATH, db_path, sql],
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
        return ExecutionResult(success=True, columns=payload["columns"], rows=payload["rows"])
    else:
        return ExecutionResult(success=False, error=payload["error"])

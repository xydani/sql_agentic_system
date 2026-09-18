"""
main.py

Orchestration loop:

    user NL query
        -> agent generates SQL (given schema context)
        -> executor runs SQL against the DB
        -> if it fails: feed the exact error back to the agent, retry
        -> repeat until success or MAX_RETRIES exhausted

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python main.py "Which customers placed more than one order?"
    python main.py            # interactive mode, one query per line
"""

import sys

from sql_agent.db_executor import ExecutionResult, execute_sql
from legacy.nl2sql_agent import NL2SQLAgent
from sql_agent.schema_utils import get_schema_description

DB_PATH = "data/example.db"
MAX_RETRIES = 4


def run_query(nl_query: str, db_path: str = DB_PATH, verbose: bool = True) -> ExecutionResult:
    schema = get_schema_description(db_path)
    agent = NL2SQLAgent()

    print(f"\nDatabase schema:\n{schema}\n")
    sql = agent.start_query(schema, nl_query)

    # test with a wrong hardcoded SQL query for demonstration purposes
    # sql = "SELECT c.name FROM customer c JOIN orders o ON c.id = o.customer_id GROUP BY c.id HAVING COUNT(o.id) > 1"

    for attempt in range(1, MAX_RETRIES + 1):
        if verbose:
            print(f"\n[attempt {attempt}] generated SQL:\n{sql}\n")

        result = execute_sql(db_path, sql)

        if result.success:
            if verbose:
                print(f"Success after {attempt} attempt(s).")
            return result

        if verbose:
            print(f"Execution error: {result.error}")

        if attempt == MAX_RETRIES:
            if verbose:
                print("Max retries reached, giving up.")
            return result

        sql = agent.retry_with_error(sql, result.error)

    return result  # unreachable, kept for clarity


def print_result(result: ExecutionResult):
    if not result.success:
        print(f"\nFinal state: FAILED - {result.error}")
        return
    print("\nColumns:", result.columns)
    for row in result.rows:
        print(row)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        result = run_query(query)
        print_result(result)
    else:
        print("Interactive mode. Type a question, or 'exit' to quit.")
        while True:
            query = input("\n> ").strip()
            if query.lower() in ("exit", "quit"):
                break
            if not query:
                continue
            result = run_query(query)
            print_result(result)

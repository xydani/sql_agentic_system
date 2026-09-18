import re

from langchain.tools import tool

from sql_agent.db_executor import execute_sql
from sql_agent.schema_utils import describe_single_table, list_table_names, quote_identifier

SAMPLE_SIZE = 5

LIST_TABLES_DESCRIPTION = (
    "List the names of every table in the database. "
    "Call this first when you do not yet know what the database contains."
)

DESCRIBE_TABLE_DESCRIPTION = (
    "Show the columns, types, primary keys and foreign keys of one table. "
    "Use this to learn the exact column names before writing a query, "
    "instead of guessing them."
)

SAMPLE_ROWS_DESCRIPTION = (
    "Show a few real rows from a table. Use this before filtering on a column "
    "to see how its values are actually written: a country column may hold "
    "'IT' rather than 'Italy', and a status column may hold 'A' rather than 'active'. "
    "A query that filters on a guessed value runs without error and silently "
    "returns nothing."
)

RUN_SELECT_DESCRIPTION = (
    "Run a read-only SELECT query and return the resulting rows. "
    "Only SELECT and WITH statements are allowed. "
    "If the query fails, the exact database error is returned, so you can "
    "correct the query and try again."
)


STRING_LITERAL = re.compile(r"'((?:[^']|'')*)'")


def find_string_literals(sql: str) -> list[str]:
    return [match.group(1).replace("''", "'") for match in STRING_LITERAL.finditer(sql)]


def describe_empty_result(sql: str) -> str:
    literals = sorted(set(find_string_literals(sql)))
    if not literals:
        return "No rows returned."
    values = ", ".join(repr(value) for value in literals)
    return (
        f"No rows returned. This query filters on the literal value(s) {values}. "
        "An empty result looks the same whether nothing matches or the filter value "
        "is simply not written that way in the data. Use sample_rows to check how the "
        "column is actually written before reporting this as a finding."
    )


def format_table(columns: list[str], rows: list, truncated: bool = False) -> str:
    if not rows:
        return "No rows returned."

    header = " | ".join(columns)
    body = "\n".join(
        " | ".join("NULL" if value is None else str(value) for value in row)
        for row in rows
    )
    footer = (
        f"({len(rows)} rows shown; more rows exist, so this is a sample "
        f"and must not be used to count or total anything)"
        if truncated
        else f"({len(rows)} rows)"
    )
    return f"{header}\n{body}\n{footer}"


def build_tools(db_path: str) -> list:

    @tool(description=LIST_TABLES_DESCRIPTION)
    def list_tables() -> str:
        names = list_table_names(db_path)
        return "\n".join(names) if names else "The database has no tables."

    @tool(description=DESCRIBE_TABLE_DESCRIPTION)
    def describe_table(table: str) -> str:
        try:
            return describe_single_table(db_path, table)
        except ValueError as unknown_table:
            return str(unknown_table)

    @tool(description=SAMPLE_ROWS_DESCRIPTION)
    def sample_rows(table: str) -> str:
        known_tables = list_table_names(db_path)
        if table not in known_tables:
            return f"No such table: {table}. Available tables: {', '.join(known_tables)}"

        result = execute_sql(
            db_path,
            f"SELECT * FROM {quote_identifier(table)}",
            max_rows=SAMPLE_SIZE,
        )
        if not result.success:
            return f"Could not read {table}: {result.error}"
        return format_table(result.columns, result.rows, result.truncated)

    @tool(description=RUN_SELECT_DESCRIPTION)
    def run_select(sql: str) -> str:
        result = execute_sql(db_path, sql)
        if not result.success:
            return f"Query failed: {result.error}"
        if not result.rows:
            return describe_empty_result(sql)
        return format_table(result.columns, result.rows, result.truncated)

    return [list_tables, describe_table, sample_rows, run_select]

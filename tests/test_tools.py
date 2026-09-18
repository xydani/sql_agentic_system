import pytest

from sql_agent.tools import build_tools, describe_empty_result, find_string_literals, format_table

EXAMPLE_DB = "data/example.db"


@pytest.fixture
def tools():
    return {tool.name: tool for tool in build_tools(EXAMPLE_DB)}


def test_every_tool_has_a_description(tools):
    assert set(tools) == {"list_tables", "describe_table", "sample_rows", "run_select"}
    for tool in tools.values():
        assert len(tool.description) > 40


def test_list_tables(tools):
    assert tools["list_tables"].invoke({}) == "customers\norders"


def test_describe_table(tools):
    output = tools["describe_table"].invoke({"table": "orders"})
    assert "TABLE orders" in output
    assert "customer_id -> customers(id)" in output


def test_describe_unknown_table_suggests_real_ones(tools):
    output = tools["describe_table"].invoke({"table": "customer"})
    assert "No such table" in output
    assert "customers" in output


def test_sample_rows_reveals_actual_values(tools):
    output = tools["sample_rows"].invoke({"table": "customers"})
    assert "IT" in output
    assert "Alice Rossi" in output


def test_sample_rows_unknown_table_suggests_real_ones(tools):
    output = tools["sample_rows"].invoke({"table": "nope"})
    assert "No such table" in output
    assert "customers, orders" in output


def test_run_select_returns_rows(tools):
    output = tools["run_select"].invoke({"sql": "SELECT name FROM customers ORDER BY id"})
    assert "Alice Rossi" in output
    assert "(3 rows)" in output


def test_run_select_reports_the_database_error(tools):
    output = tools["run_select"].invoke({"sql": "SELECT * FROM customer"})
    assert output.startswith("Query failed:")
    assert "no such table: customer" in output


def test_run_select_refuses_writes(tools):
    output = tools["run_select"].invoke({"sql": "DROP TABLE customers"})
    assert "Refused" in output
    assert tools["list_tables"].invoke({}) == "customers\norders"


def test_empty_result_from_a_guessed_literal_is_flagged(tools):
    output = tools["run_select"].invoke({"sql": "SELECT * FROM customers WHERE country = 'Italy'"})
    assert "No rows returned" in output
    assert "'Italy'" in output
    assert "sample_rows" in output


def test_empty_result_without_literals_is_plain(tools):
    output = tools["run_select"].invoke({"sql": "SELECT * FROM orders WHERE amount > 9999"})
    assert output == "No rows returned."


@pytest.mark.parametrize("sql,expected", [
    ("SELECT * FROM t WHERE c = 'IT'", ["IT"]),
    ("SELECT * FROM t WHERE a = 'x' AND b = 'y'", ["x", "y"]),
    ("SELECT * FROM t WHERE c = 'it''s'", ["it's"]),
    ("SELECT * FROM t WHERE n > 5", []),
])
def test_find_string_literals(sql, expected):
    assert find_string_literals(sql) == expected


def test_empty_result_lists_each_literal_once():
    output = describe_empty_result("SELECT * FROM t WHERE a = 'IT' OR b = 'IT'")
    assert output.count("'IT'") == 1


def test_format_table_warns_when_truncated():
    output = format_table(["id"], [(1,), (2,)], truncated=True)
    assert "sample" in output
    assert "must not be used to count" in output


def test_format_table_renders_null():
    assert "NULL" in format_table(["a"], [(None,)])

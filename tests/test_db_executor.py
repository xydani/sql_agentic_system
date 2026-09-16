import sqlite3

import pytest

from db_executor import execute_sql, validate_read_only

ACCEPTED = [
    "SELECT * FROM customers",
    "select name from customers",
    "  \n\tSELECT 1",
    "SELECT * FROM customers;",
    "WITH t AS (SELECT 1 AS x) SELECT x FROM t",
    "(SELECT 1) UNION (SELECT 2)",
    "SELECT * FROM orders WHERE product = 'DROP'",
    "SELECT * FROM orders WHERE product = 'a;b'",
    "SELECT * FROM orders WHERE product = 'it''s'",
    "SELECT * FROM orders -- most recent",
    "SELECT /* inline */ * FROM orders",
    "SELECT updated_at, deleted_flag FROM t",
    'SELECT "delete" FROM t',
    "SELECT * FROM (SELECT * FROM orders WHERE product = ';')",
]

REJECTED = [
    "",
    "   ",
    "DROP TABLE customers",
    "DELETE FROM customers",
    "UPDATE customers SET name = 'x'",
    "INSERT INTO customers VALUES (9, 'x', 'x', 'x', 'x')",
    "CREATE TABLE evil (x INT)",
    "REPLACE INTO customers VALUES (9, 'x', 'x', 'x', 'x')",
    "ALTER TABLE customers ADD COLUMN x INT",
    "ATTACH DATABASE '/etc/passwd' AS p",
    "DETACH DATABASE p",
    "PRAGMA table_info(customers)",
    "VACUUM",
    "-- harmless comment\nDROP TABLE customers",
    "/* harmless */ DROP TABLE customers",
    "SELECT 1; DROP TABLE customers",
    "SELECT 1;;",
    "WITH x AS (SELECT 1) DELETE FROM customers",
    "WITH x AS (SELECT 1) INSERT INTO customers SELECT * FROM x",
    "'just a string'",
]


@pytest.mark.parametrize("sql", ACCEPTED)
def test_accepts_read_only(sql):
    assert validate_read_only(sql) is None


@pytest.mark.parametrize("sql", REJECTED)
def test_rejects_writes_and_tricks(sql):
    assert validate_read_only(sql) is not None


def test_rejection_reason_tells_the_llm_what_to_do():
    reason = validate_read_only("DROP TABLE customers")
    assert "DROP" in reason and "SELECT" in reason


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "t.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    conn.executemany("INSERT INTO t (v) VALUES (?)", [(f"row{i}",) for i in range(10)])
    conn.commit()
    conn.close()
    return str(path)


def _count(db):
    return execute_sql(db, "SELECT COUNT(*) FROM t").rows[0][0]


def test_select_returns_rows(db):
    r = execute_sql(db, "SELECT * FROM t ORDER BY id")
    assert r.success
    assert r.columns == ["id", "v"]
    assert len(r.rows) == 10
    assert not r.truncated


def test_max_rows_truncates_and_flags(db):
    r = execute_sql(db, "SELECT * FROM t", max_rows=3)
    assert r.success and len(r.rows) == 3 and r.truncated


def test_max_rows_exact_fit_is_not_truncated(db):
    r = execute_sql(db, "SELECT * FROM t", max_rows=10)
    assert r.success and len(r.rows) == 10 and not r.truncated


def test_write_refused_by_guard(db):
    r = execute_sql(db, "DELETE FROM t")
    assert not r.success and r.error.startswith("Refused")
    assert _count(db) == 10


def test_engine_blocks_write_even_if_guard_is_bypassed(db, monkeypatch):
    monkeypatch.setattr("db_executor.validate_read_only", lambda sql: None)
    r = execute_sql(db, "DELETE FROM t")
    assert not r.success and "readonly" in r.error.lower()
    assert _count(db) == 10


def test_allow_writes_persists(db):
    r = execute_sql(db, "DELETE FROM t WHERE id = 1", allow_writes=True)
    assert r.success
    assert _count(db) == 9


def test_sql_error_is_reported_verbatim(db):
    r = execute_sql(db, "SELECT nope FROM t")
    assert not r.success and "no such column: nope" in r.error


def test_missing_database_is_not_silently_created(tmp_path):
    missing = tmp_path / "missing.db"
    r = execute_sql(str(missing), "SELECT 1")
    assert not r.success
    assert not missing.exists()

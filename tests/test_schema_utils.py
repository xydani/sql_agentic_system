import sqlite3

import pytest

from schema_utils import describe_single_table, get_schema_description, list_table_names


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "t.db"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE books (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            author_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors(id)
        );
        CREATE TABLE "order" (id INTEGER PRIMARY KEY);
    """)
    conn.commit()
    conn.close()
    return str(path)


def test_list_table_names(db):
    assert list_table_names(db) == ["authors", "books", "order"]


def test_describe_columns_and_flags(db):
    assert describe_single_table(db, "authors") == (
        "TABLE authors\n"
        "  - id: INTEGER (PRIMARY KEY)\n"
        "  - name: TEXT (NOT NULL)"
    )


def test_describe_includes_foreign_keys(db):
    desc = describe_single_table(db, "books")
    assert desc.endswith("  Foreign keys:\n  - author_id -> authors(id)")


def test_describe_handles_reserved_word_table_name(db):
    assert describe_single_table(db, "order").startswith("TABLE order\n")


def test_describe_unknown_table_lists_available(db):
    with pytest.raises(ValueError) as exc:
        describe_single_table(db, "nope")
    assert "nope" in str(exc.value)
    assert "authors, books, order" in str(exc.value)


def test_describe_rejects_injection_in_table_name(db):
    with pytest.raises(ValueError):
        describe_single_table(db, 'authors"); DROP TABLE authors; --')
    assert "authors" in list_table_names(db)


def test_full_schema_is_join_of_single_tables(db):
    expected = "\n\n".join(describe_single_table(db, t) for t in list_table_names(db))
    assert get_schema_description(db) == expected


def test_example_db_schema_unchanged():
    assert get_schema_description("example.db") == (
        "TABLE customers\n"
        "  - id: INTEGER (PRIMARY KEY)\n"
        "  - name: TEXT (NOT NULL)\n"
        "  - email: TEXT\n"
        "  - country: TEXT\n"
        "  - signup_date: DATE\n"
        "\n"
        "TABLE orders\n"
        "  - id: INTEGER (PRIMARY KEY)\n"
        "  - customer_id: INTEGER (NOT NULL)\n"
        "  - product: TEXT (NOT NULL)\n"
        "  - amount: REAL (NOT NULL)\n"
        "  - order_date: DATE\n"
        "  Foreign keys:\n"
        "  - customer_id -> customers(id)"
    )

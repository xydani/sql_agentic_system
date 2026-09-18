import sqlite3

import pytest

from sql_agent.schema_utils import get_schema_description, list_table_names

SHOP_DB = "data/shop.db"


@pytest.fixture
def db():
    connection = sqlite3.connect(f"file:{SHOP_DB}?mode=ro", uri=True)
    yield connection
    connection.close()


def count(db, sql):
    return db.execute(sql).fetchone()[0]


def test_tables():
    assert list_table_names(SHOP_DB) == ["customers", "products", "orders", "order_items"]


def test_volume_exceeds_the_row_cap(db):
    assert count(db, "SELECT COUNT(*) FROM customers") == 150
    assert count(db, "SELECT COUNT(*) FROM orders") == 400
    assert count(db, "SELECT COUNT(*) FROM order_items") == 977


def test_countries_are_codes_not_names(db):
    countries = [row[0] for row in db.execute("SELECT DISTINCT country FROM customers")]
    assert "IT" in countries
    assert "Italy" not in countries


def test_order_status_is_a_code(db):
    statuses = {row[0] for row in db.execute("SELECT DISTINCT status FROM orders")}
    assert statuses == {"D", "S", "P", "X"}


def test_nullable_columns_contain_nulls(db):
    assert count(db, "SELECT COUNT(*) FROM customers WHERE email IS NULL") > 0
    assert count(db, "SELECT COUNT(*) FROM orders WHERE shipped_date IS NULL") > 0


def test_name_is_ambiguous_between_tables():
    schema = get_schema_description(SHOP_DB)
    assert "TABLE customers" in schema and "TABLE products" in schema
    assert schema.count("  - name: TEXT") == 2


def test_order_items_keep_a_historical_price(db):
    drifted = count(db, """
        SELECT COUNT(*) FROM order_items i
        JOIN products p ON p.id = i.product_id
        WHERE i.unit_price != p.unit_price
    """)
    assert drifted > 0


def test_foreign_keys_resolve(db):
    assert count(db, "SELECT COUNT(*) FROM orders WHERE customer_id NOT IN (SELECT id FROM customers)") == 0
    assert count(db, "SELECT COUNT(*) FROM order_items WHERE order_id NOT IN (SELECT id FROM orders)") == 0

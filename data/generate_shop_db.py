import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

SEED = 42
OUTPUT = Path(__file__).with_name("shop.db")

COUNTRIES = ["IT", "UK", "DE", "FR", "ES", "US", "CN", "JP"]
COUNTRY_WEIGHTS = [26, 18, 14, 11, 8, 12, 7, 4]

ORDER_STATUS = ["D", "S", "P", "X"]
ORDER_STATUS_WEIGHTS = [58, 20, 15, 7]

CATEGORIES = ["Hardware", "Accessories", "Software", "Services"]

FIRST_NAMES = [
    "Alice", "Bob", "Chen", "Dana", "Elena", "Farid", "Giulia", "Hans", "Ingrid", "Jonas",
    "Karim", "Laura", "Marco", "Nadia", "Oscar", "Paula", "Quentin", "Rosa", "Stefan", "Tara",
    "Ulrich", "Vera", "Wei", "Xavier", "Yuki", "Zara",
]
LAST_NAMES = [
    "Rossi", "Smith", "Wei", "Novak", "Moreau", "Schmidt", "Garcia", "Johnson", "Bianchi",
    "Dubois", "Muller", "Lopez", "Tanaka", "Andersson", "Kowalski", "Ferrari", "Nguyen",
    "Okafor", "Petrov", "Silva",
]

PRODUCT_WORDS = [
    "Widget", "Gadget", "Gizmo", "Adapter", "Cable", "Dock", "Hub", "Mount", "Sleeve",
    "Charger", "Battery", "Keyboard", "Mouse", "Monitor", "Stand", "Case", "Filter",
    "Sensor", "Router", "Switch",
]
PRODUCT_QUALIFIERS = ["Pro", "Mini", "Plus", "Lite", "Max", "Basic"]

SCHEMA = """
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    country TEXT NOT NULL,
    signup_date DATE NOT NULL,
    is_active INTEGER NOT NULL
);

CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    discontinued INTEGER NOT NULL
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    shipped_date DATE,
    status TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""

START = date(2023, 1, 1)
END = date(2025, 12, 31)


def random_date(rng, start=START, end=END):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def build_products(rng):
    names = set()
    rows = []
    while len(rows) < 40:
        name = f"{rng.choice(PRODUCT_WORDS)} {rng.choice(PRODUCT_QUALIFIERS)}"
        if name in names:
            continue
        names.add(name)
        rows.append((
            len(rows) + 1,
            name,
            rng.choice(CATEGORIES),
            round(rng.uniform(4.5, 480.0), 2),
            1 if rng.random() < 0.15 else 0,
        ))
    return rows


def build_customers(rng):
    rows = []
    for customer_id in range(1, 151):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        email = None if rng.random() < 0.12 else f"{first.lower()}.{last.lower()}{customer_id}@example.com"
        rows.append((
            customer_id,
            f"{first} {last}",
            email,
            rng.choices(COUNTRIES, weights=COUNTRY_WEIGHTS)[0],
            random_date(rng, START, date(2025, 6, 30)).isoformat(),
            0 if rng.random() < 0.18 else 1,
        ))
    return rows


def build_orders(rng, customers):
    rows = []
    for order_id in range(1, 401):
        customer = rng.choice(customers)
        ordered = random_date(rng, date.fromisoformat(customer[4]), END)
        status = rng.choices(ORDER_STATUS, weights=ORDER_STATUS_WEIGHTS)[0]
        shipped = None
        if status in ("S", "D"):
            shipped = (ordered + timedelta(days=rng.randint(1, 12))).isoformat()
        rows.append((order_id, customer[0], ordered.isoformat(), shipped, status))
    return rows


def build_order_items(rng, orders, products):
    rows = []
    for order in orders:
        for product in rng.sample(products, rng.randint(1, 4)):
            drift = rng.uniform(0.82, 1.05) if rng.random() < 0.4 else 1.0
            rows.append((
                len(rows) + 1,
                order[0],
                product[0],
                rng.randint(1, 5),
                round(product[3] * drift, 2),
            ))
    return rows


def main():
    rng = random.Random(SEED)
    if OUTPUT.exists():
        OUTPUT.unlink()

    products = build_products(rng)
    customers = build_customers(rng)
    orders = build_orders(rng, customers)
    order_items = build_order_items(rng, orders, products)

    conn = sqlite3.connect(OUTPUT)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", customers)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", orders)
    conn.executemany("INSERT INTO order_items VALUES (?,?,?,?,?)", order_items)
    conn.commit()

    for table in ("customers", "products", "orders", "order_items"):
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:14s} {count:>5}")
    conn.close()
    print(f"\nwritten to {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main())

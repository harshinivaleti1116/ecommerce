import sqlite3
import hashlib
import os
from datetime import datetime


# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "products.db")


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# =========================================================
# PASSWORD HASH
# =========================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # -------------------------
    # USERS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    """)

    # -------------------------
    # PRODUCTS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)

    # -------------------------
    # ORDERS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'PLACED',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # -------------------------
    # ORDER ITEMS
    # -------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    # -------------------------
    # DEFAULT ADMIN
    # -------------------------

    admin_password = hash_password("Admin@123")

    cursor.execute("""
        INSERT INTO users
        (username, password, role)
        VALUES (?, ?, ?)
        ON CONFLICT(username)
        DO UPDATE SET
            password = excluded.password,
            role = excluded.role
    """, (
        "admin",
        admin_password,
        "admin"
    ))

    conn.commit()
    conn.close()


# =========================================================
# USER / SIGNUP
# =========================================================

def create_user(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO users
            (username, password, role)
            VALUES (?, ?, ?)
        """, (
            username,
            hash_password(password),
            "user"
        ))

        conn.commit()

        user_id = cursor.lastrowid

        conn.close()

        return user_id

    except sqlite3.IntegrityError:

        conn.close()

        return None


# =========================================================
# LOGIN
# =========================================================

def get_user(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, role
        FROM users
        WHERE username = ?
        AND password = ?
    """, (
        username,
        hash_password(password)
    ))

    user = cursor.fetchone()

    conn.close()

    return user


# =========================================================
# PRODUCTS
# =========================================================

def get_all_products():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, stock
        FROM products
        ORDER BY id
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3]
        }
        for row in rows
    ]


def search_products(name):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, price, stock
        FROM products
        WHERE name LIKE ?
        ORDER BY name
    """, (
        "%" + name + "%",
    ))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3]
        }
        for row in rows
    ]


def add_product(name, price, stock):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO products
        (name, price, stock)
        VALUES (?, ?, ?)
    """, (
        name,
        price,
        stock
    ))

    conn.commit()

    product_id = cursor.lastrowid

    conn.close()

    return product_id


def update_product(product_id, name, price, stock):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE products
        SET name = ?,
            price = ?,
            stock = ?
        WHERE id = ?
    """, (
        name,
        price,
        stock,
        product_id
    ))

    conn.commit()

    updated = cursor.rowcount

    conn.close()

    return updated


def delete_product(product_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (
        product_id,
    ))

    conn.commit()

    deleted = cursor.rowcount

    conn.close()

    return deleted


# =========================================================
# CHECKOUT
# =========================================================

def create_order(user_id, cart_items):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("BEGIN IMMEDIATE")

        combined_items = {}

        for item in cart_items:

            product_id = int(item["product_id"])
            quantity = int(item["quantity"])

            if quantity <= 0:
                raise ValueError(
                    "Quantity must be greater than zero."
                )

            combined_items[product_id] = (
                combined_items.get(product_id, 0)
                + quantity
            )

        order_items = []
        total_amount = 0.0

        for product_id, quantity in combined_items.items():

            cursor.execute("""
                SELECT id, name, price, stock
                FROM products
                WHERE id = ?
            """, (
                product_id,
            ))

            product = cursor.fetchone()

            if product is None:
                raise ValueError(
                    f"Product with ID {product_id} does not exist."
                )

            current_stock = product[3]
            current_price = product[2]

            if current_stock < quantity:
                raise ValueError(
                    f"Insufficient stock for {product[1]}. "
                    f"Available: {current_stock}"
                )

            item_total = current_price * quantity

            total_amount += item_total

            order_items.append({
                "product_id": product_id,
                "quantity": quantity,
                "price": current_price,
                "total": item_total
            })

        created_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor.execute("""
            INSERT INTO orders
            (user_id, total_amount, status, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            round(total_amount, 2),
            "PLACED",
            created_at
        ))

        order_id = cursor.lastrowid

        for item in order_items:

            cursor.execute("""
                INSERT INTO order_items
                (order_id, product_id, quantity, price, total)
                VALUES (?, ?, ?, ?, ?)
            """, (
                order_id,
                item["product_id"],
                item["quantity"],
                item["price"],
                item["total"]
            ))

            cursor.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (
                item["quantity"],
                item["product_id"]
            ))

        conn.commit()

        return {
            "order_id": order_id,
            "total": round(total_amount, 2)
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================================================
# USER ORDERS
# =========================================================

def get_user_orders(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, total_amount, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
    """, (
        user_id,
    ))

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "total": row[1],
            "status": row[2],
            "created_at": row[3]
        }
        for row in rows
    ]


# =========================================================
# ADMIN DASHBOARD
# =========================================================

def get_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(stock), 0)
        FROM products
    """)
    total_stock = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(price * stock), 0)
        FROM products
    """)
    inventory_value = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE status = 'PLACED'
    """)
    total_sales = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, name, price, stock
        FROM products
        WHERE stock <= 5
        ORDER BY stock
    """)

    rows = cursor.fetchall()

    conn.close()

    low_stock = [
        {
            "id": row[0],
            "name": row[1],
            "price": row[2],
            "stock": row[3]
        }
        for row in rows
    ]

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "inventory_value": inventory_value,
        "total_orders": total_orders,
        "total_sales": total_sales,
        "low_stock": low_stock
    }


# =========================================================
# ADMIN ALL ORDERS
# =========================================================

def get_all_orders():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            orders.id,
            users.username,
            orders.total_amount,
            orders.status,
            orders.created_at
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "username": row[1],
            "total": row[2],
            "status": row[3],
            "created_at": row[4]
        }
        for row in rows
    ]

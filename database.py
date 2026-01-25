import os
import sqlite3
from datetime import datetime
from typing import Optional

# 檢查是否使用 Cloud SQL (透過環境變數)
USE_CLOUD_SQL = os.environ.get("USE_CLOUD_SQL", "false").lower() == "true"
DB_NAME = "group_buying.db"

if USE_CLOUD_SQL:
    import pg8000
    import pg8000.native

def get_connection():
    """取得資料庫連線"""
    if USE_CLOUD_SQL:
        # Cloud SQL PostgreSQL 連線
        conn = pg8000.connect(
            host=os.environ.get("DB_HOST", "127.0.0.1"),
            port=int(os.environ.get("DB_PORT", "5432")),
            database=os.environ.get("DB_NAME", "buying_system"),
            user=os.environ.get("DB_USER", "postgres"),
            password=os.environ.get("DB_PASSWORD", "")
        )
        return conn
    else:
        # 本地 SQLite 連線
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


def dict_row(cursor, row):
    """將 PostgreSQL 結果轉換為類字典物件"""
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def init_db():
    """初始化資料庫表格"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if USE_CLOUD_SQL:
        # PostgreSQL 語法
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_orders (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id SERIAL PRIMARY KEY,
                group_order_id INTEGER NOT NULL REFERENCES group_orders(id),
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_orders (
                id SERIAL PRIMARY KEY,
                group_order_id INTEGER NOT NULL REFERENCES group_orders(id),
                customer_name TEXT NOT NULL,
                note TEXT,
                is_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                id SERIAL PRIMARY KEY,
                customer_order_id INTEGER NOT NULL REFERENCES customer_orders(id),
                item_id INTEGER NOT NULL REFERENCES items(id),
                quantity INTEGER NOT NULL
            )
        """)
    else:
        # SQLite 語法
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'open',
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 檢查是否需要新增欄位 (相容舊資料庫)
        cursor.execute("PRAGMA table_info(group_orders)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'start_time' not in columns:
            cursor.execute("ALTER TABLE group_orders ADD COLUMN start_time TIMESTAMP")
        if 'end_time' not in columns:
            cursor.execute("ALTER TABLE group_orders ADD COLUMN end_time TIMESTAMP")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_order_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (group_order_id) REFERENCES group_orders(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customer_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_order_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                note TEXT,
                is_paid INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_order_id) REFERENCES group_orders(id)
            )
        """)
        
        # 檢查是否需要新增欄位 (相容舊資料庫)
        cursor.execute("PRAGMA table_info(customer_orders)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'note' not in columns:
            cursor.execute("ALTER TABLE customer_orders ADD COLUMN note TEXT")
        if 'is_paid' not in columns:
            cursor.execute("ALTER TABLE customer_orders ADD COLUMN is_paid INTEGER DEFAULT 0")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_order_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (customer_order_id) REFERENCES customer_orders(id),
                FOREIGN KEY (item_id) REFERENCES items(id)
            )
        """)
    
    conn.commit()
    conn.close()


def _sql(query: str) -> str:
    """將 SQLite 的 ? 佔位符轉換為 PostgreSQL 的 %s"""
    if USE_CLOUD_SQL:
        return query.replace("?", "%s")
    return query


def _fetch_all(cursor, rows):
    """處理 fetchall 結果，PostgreSQL 需要轉換為字典"""
    if USE_CLOUD_SQL:
        if not rows:
            return []
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    return rows


def _fetch_one(cursor, row):
    """處理 fetchone 結果，PostgreSQL 需要轉換為字典"""
    if USE_CLOUD_SQL:
        if row is None:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return row


def _get_last_id(cursor, conn, table_name: str) -> int:
    """取得最後插入的 ID"""
    if USE_CLOUD_SQL:
        cursor.execute(f"SELECT currval(pg_get_serial_sequence('{table_name}', 'id'))")
        return cursor.fetchone()[0]
    return cursor.lastrowid


# ============ 團購單相關 ============

def create_group_order(title: str, description: str = "", start_time: str = None, end_time: str = None) -> int:
    """建立新團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _sql("INSERT INTO group_orders (title, description, start_time, end_time) VALUES (?, ?, ?, ?)"),
        (title, description, start_time, end_time)
    )
    order_id = _get_last_id(cursor, conn, "group_orders")
    conn.commit()
    conn.close()
    return order_id


def get_all_group_orders():
    """取得所有團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_orders ORDER BY created_at DESC")
    orders = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return orders


def get_open_group_orders():
    """取得開放中的團購單 (根據時間和狀態)"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(_sql("""
        SELECT * FROM group_orders 
        WHERE status = 'open' 
        AND (start_time IS NULL OR start_time <= ?)
        AND (end_time IS NULL OR end_time >= ?)
        ORDER BY created_at DESC
    """), (now, now))
    orders = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return orders


def update_group_order_status(order_id: int, status: str):
    """更新團購單狀態"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("UPDATE group_orders SET status = ? WHERE id = ?"), (status, order_id))
    conn.commit()
    conn.close()


def get_group_order_by_id(order_id: int):
    """取得單一團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("SELECT * FROM group_orders WHERE id = ?"), (order_id,))
    order = _fetch_one(cursor, cursor.fetchone())
    conn.close()
    return order


def update_group_order(order_id: int, title: str, description: str, start_time: str, end_time: str):
    """更新團購單資訊"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        UPDATE group_orders 
        SET title = ?, description = ?, start_time = ?, end_time = ?
        WHERE id = ?
    """), (title, description, start_time, end_time, order_id))
    conn.commit()
    conn.close()


def delete_group_order(order_id: int):
    """刪除團購單及相關資料"""
    conn = get_connection()
    cursor = conn.cursor()
    # 刪除訂單明細
    cursor.execute(_sql("""
        DELETE FROM order_details WHERE customer_order_id IN 
        (SELECT id FROM customer_orders WHERE group_order_id = ?)
    """), (order_id,))
    # 刪除顧客訂單
    cursor.execute(_sql("DELETE FROM customer_orders WHERE group_order_id = ?"), (order_id,))
    # 刪除品項
    cursor.execute(_sql("DELETE FROM items WHERE group_order_id = ?"), (order_id,))
    # 刪除團購單
    cursor.execute(_sql("DELETE FROM group_orders WHERE id = ?"), (order_id,))
    conn.commit()
    conn.close()


# ============ 品項相關 ============

def add_item(group_order_id: int, name: str, price: float) -> int:
    """新增品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        _sql("INSERT INTO items (group_order_id, name, price) VALUES (?, ?, ?)"),
        (group_order_id, name, price)
    )
    item_id = _get_last_id(cursor, conn, "items")
    conn.commit()
    conn.close()
    return item_id


def get_items_by_group_order(group_order_id: int):
    """取得團購單的所有品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("SELECT * FROM items WHERE group_order_id = ?"), (group_order_id,))
    items = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return items


def delete_item(item_id: int):
    """刪除品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("DELETE FROM order_details WHERE item_id = ?"), (item_id,))
    cursor.execute(_sql("DELETE FROM items WHERE id = ?"), (item_id,))
    conn.commit()
    conn.close()


# ============ 顧客訂單相關 ============

def create_customer_order(group_order_id: int, customer_name: str, items_qty: dict, note: str = "") -> int:
    """建立顧客訂單
    items_qty: {item_id: quantity}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        _sql("INSERT INTO customer_orders (group_order_id, customer_name, note) VALUES (?, ?, ?)"),
        (group_order_id, customer_name, note)
    )
    customer_order_id = _get_last_id(cursor, conn, "customer_orders")
    
    for item_id, qty in items_qty.items():
        if qty > 0:
            cursor.execute(
                _sql("INSERT INTO order_details (customer_order_id, item_id, quantity) VALUES (?, ?, ?)"),
                (customer_order_id, item_id, qty)
            )
    
    conn.commit()
    conn.close()
    return customer_order_id


def get_customer_orders_by_group(group_order_id: int):
    """取得團購單的所有顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        SELECT co.*, 
               SUM(od.quantity * i.price) as total_amount
        FROM customer_orders co
        LEFT JOIN order_details od ON co.id = od.customer_order_id
        LEFT JOIN items i ON od.item_id = i.id
        WHERE co.group_order_id = ?
        GROUP BY co.id, co.group_order_id, co.customer_name, co.created_at
        ORDER BY co.created_at DESC
    """), (group_order_id,))
    orders = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return orders


def get_order_details(customer_order_id: int):
    """取得訂單明細"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        SELECT od.*, i.name, i.price, (od.quantity * i.price) as subtotal
        FROM order_details od
        JOIN items i ON od.item_id = i.id
        WHERE od.customer_order_id = ?
    """), (customer_order_id,))
    details = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return details


def get_group_order_summary(group_order_id: int):
    """取得團購單彙總統計"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        SELECT i.id, i.name, i.price, 
               COALESCE(SUM(od.quantity), 0) as total_qty,
               COALESCE(SUM(od.quantity * i.price), 0) as total_amount
        FROM items i
        LEFT JOIN order_details od ON i.id = od.item_id
        WHERE i.group_order_id = ?
        GROUP BY i.id, i.name, i.price
    """), (group_order_id,))
    summary = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return summary


def get_item_buyers(item_id: int):
    """取得購買某品項的顧客列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        SELECT co.customer_name, od.quantity, (od.quantity * i.price) as subtotal
        FROM order_details od
        JOIN customer_orders co ON od.customer_order_id = co.id
        JOIN items i ON od.item_id = i.id
        WHERE od.item_id = ? AND od.quantity > 0
        ORDER BY co.customer_name
    """), (item_id,))
    buyers = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return buyers


def delete_customer_order(customer_order_id: int):
    """刪除顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("DELETE FROM order_details WHERE customer_order_id = ?"), (customer_order_id,))
    cursor.execute(_sql("DELETE FROM customer_orders WHERE id = ?"), (customer_order_id,))
    conn.commit()
    conn.close()


def get_customer_order_by_id(customer_order_id: int):
    """取得單一顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("SELECT * FROM customer_orders WHERE id = ?"), (customer_order_id,))
    order = _fetch_one(cursor, cursor.fetchone())
    conn.close()
    return order


def get_customer_orders_by_name(group_order_id: int, customer_name: str):
    """根據姓名取得顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("""
        SELECT co.*, SUM(od.quantity * i.price) as total_amount
        FROM customer_orders co
        LEFT JOIN order_details od ON co.id = od.customer_order_id
        LEFT JOIN items i ON od.item_id = i.id
        WHERE co.group_order_id = ? AND co.customer_name = ?
        GROUP BY co.id, co.group_order_id, co.customer_name, co.created_at
        ORDER BY co.created_at DESC
    """), (group_order_id, customer_name))
    orders = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    return orders


def update_customer_order(customer_order_id: int, items_qty: dict):
    """更新顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 刪除舊的明細
    cursor.execute(_sql("DELETE FROM order_details WHERE customer_order_id = ?"), (customer_order_id,))
    
    # 新增新的明細
    for item_id, qty in items_qty.items():
        if qty > 0:
            cursor.execute(
                _sql("INSERT INTO order_details (customer_order_id, item_id, quantity) VALUES (?, ?, ?)"),
                (customer_order_id, item_id, qty)
            )
    
    conn.commit()
    conn.close()


def get_order_details_as_dict(customer_order_id: int):
    """取得訂單明細為字典格式 {item_id: quantity}"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("SELECT item_id, quantity FROM order_details WHERE customer_order_id = ?"), (customer_order_id,))
    details = _fetch_all(cursor, cursor.fetchall())
    conn.close()
    if USE_CLOUD_SQL:
        return {d['item_id']: d['quantity'] for d in details}
    return {d['item_id']: d['quantity'] for d in details}


def update_customer_order_paid_status(customer_order_id: int, is_paid: int):
    """更新顧客訂單的付款狀態"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(_sql("UPDATE customer_orders SET is_paid = ? WHERE id = ?"), (is_paid, customer_order_id))
    conn.commit()
    conn.close()

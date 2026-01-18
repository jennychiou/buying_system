import sqlite3
from datetime import datetime
from typing import Optional

DB_NAME = "group_buying.db"


def get_connection():
    """取得資料庫連線"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化資料庫表格"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 團購單主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'open',  -- open, closed
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
    
    # 團購品項表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_order_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (group_order_id) REFERENCES group_orders(id)
        )
    """)
    
    # 顧客訂單表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customer_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_order_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_order_id) REFERENCES group_orders(id)
        )
    """)
    
    # 訂單明細表
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


# ============ 團購單相關 ============

def create_group_order(title: str, description: str = "", start_time: str = None, end_time: str = None) -> int:
    """建立新團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO group_orders (title, description, start_time, end_time) VALUES (?, ?, ?, ?)",
        (title, description, start_time, end_time)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_all_group_orders():
    """取得所有團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_orders ORDER BY created_at DESC")
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_open_group_orders():
    """取得開放中的團購單 (根據時間和狀態)"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM group_orders 
        WHERE status = 'open' 
        AND (start_time IS NULL OR start_time <= ?)
        AND (end_time IS NULL OR end_time >= ?)
        ORDER BY created_at DESC
    """, (now, now))
    orders = cursor.fetchall()
    conn.close()
    return orders


def update_group_order_status(order_id: int, status: str):
    """更新團購單狀態"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE group_orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


def get_group_order_by_id(order_id: int):
    """取得單一團購單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    conn.close()
    return order


def update_group_order(order_id: int, title: str, description: str, start_time: str, end_time: str):
    """更新團購單資訊"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE group_orders 
        SET title = ?, description = ?, start_time = ?, end_time = ?
        WHERE id = ?
    """, (title, description, start_time, end_time, order_id))
    conn.commit()
    conn.close()


def delete_group_order(order_id: int):
    """刪除團購單及相關資料"""
    conn = get_connection()
    cursor = conn.cursor()
    # 刪除訂單明細
    cursor.execute("""
        DELETE FROM order_details WHERE customer_order_id IN 
        (SELECT id FROM customer_orders WHERE group_order_id = ?)
    """, (order_id,))
    # 刪除顧客訂單
    cursor.execute("DELETE FROM customer_orders WHERE group_order_id = ?", (order_id,))
    # 刪除品項
    cursor.execute("DELETE FROM items WHERE group_order_id = ?", (order_id,))
    # 刪除團購單
    cursor.execute("DELETE FROM group_orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


# ============ 品項相關 ============

def add_item(group_order_id: int, name: str, price: float) -> int:
    """新增品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (group_order_id, name, price) VALUES (?, ?, ?)",
        (group_order_id, name, price)
    )
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id


def get_items_by_group_order(group_order_id: int):
    """取得團購單的所有品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE group_order_id = ?", (group_order_id,))
    items = cursor.fetchall()
    conn.close()
    return items


def delete_item(item_id: int):
    """刪除品項"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM order_details WHERE item_id = ?", (item_id,))
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


# ============ 顧客訂單相關 ============

def create_customer_order(group_order_id: int, customer_name: str, items_qty: dict) -> int:
    """建立顧客訂單
    items_qty: {item_id: quantity}
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO customer_orders (group_order_id, customer_name) VALUES (?, ?)",
        (group_order_id, customer_name)
    )
    customer_order_id = cursor.lastrowid
    
    for item_id, qty in items_qty.items():
        if qty > 0:
            cursor.execute(
                "INSERT INTO order_details (customer_order_id, item_id, quantity) VALUES (?, ?, ?)",
                (customer_order_id, item_id, qty)
            )
    
    conn.commit()
    conn.close()
    return customer_order_id


def get_customer_orders_by_group(group_order_id: int):
    """取得團購單的所有顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT co.*, 
               SUM(od.quantity * i.price) as total_amount
        FROM customer_orders co
        LEFT JOIN order_details od ON co.id = od.customer_order_id
        LEFT JOIN items i ON od.item_id = i.id
        WHERE co.group_order_id = ?
        GROUP BY co.id
        ORDER BY co.created_at DESC
    """, (group_order_id,))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_order_details(customer_order_id: int):
    """取得訂單明細"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT od.*, i.name, i.price, (od.quantity * i.price) as subtotal
        FROM order_details od
        JOIN items i ON od.item_id = i.id
        WHERE od.customer_order_id = ?
    """, (customer_order_id,))
    details = cursor.fetchall()
    conn.close()
    return details


def get_group_order_summary(group_order_id: int):
    """取得團購單彙總統計"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.name, i.price, 
               COALESCE(SUM(od.quantity), 0) as total_qty,
               COALESCE(SUM(od.quantity * i.price), 0) as total_amount
        FROM items i
        LEFT JOIN order_details od ON i.id = od.item_id
        WHERE i.group_order_id = ?
        GROUP BY i.id
    """, (group_order_id,))
    summary = cursor.fetchall()
    conn.close()
    return summary


def get_item_buyers(item_id: int):
    """取得購買某品項的顧客列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT co.customer_name, od.quantity, (od.quantity * i.price) as subtotal
        FROM order_details od
        JOIN customer_orders co ON od.customer_order_id = co.id
        JOIN items i ON od.item_id = i.id
        WHERE od.item_id = ? AND od.quantity > 0
        ORDER BY co.customer_name
    """, (item_id,))
    buyers = cursor.fetchall()
    conn.close()
    return buyers


def delete_customer_order(customer_order_id: int):
    """刪除顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM order_details WHERE customer_order_id = ?", (customer_order_id,))
    cursor.execute("DELETE FROM customer_orders WHERE id = ?", (customer_order_id,))
    conn.commit()
    conn.close()


def get_customer_order_by_id(customer_order_id: int):
    """取得單一顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customer_orders WHERE id = ?", (customer_order_id,))
    order = cursor.fetchone()
    conn.close()
    return order


def get_customer_orders_by_name(group_order_id: int, customer_name: str):
    """根據姓名取得顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT co.*, SUM(od.quantity * i.price) as total_amount
        FROM customer_orders co
        LEFT JOIN order_details od ON co.id = od.customer_order_id
        LEFT JOIN items i ON od.item_id = i.id
        WHERE co.group_order_id = ? AND co.customer_name = ?
        GROUP BY co.id
        ORDER BY co.created_at DESC
    """, (group_order_id, customer_name))
    orders = cursor.fetchall()
    conn.close()
    return orders


def update_customer_order(customer_order_id: int, items_qty: dict):
    """更新顧客訂單"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 刪除舊的明細
    cursor.execute("DELETE FROM order_details WHERE customer_order_id = ?", (customer_order_id,))
    
    # 新增新的明細
    for item_id, qty in items_qty.items():
        if qty > 0:
            cursor.execute(
                "INSERT INTO order_details (customer_order_id, item_id, quantity) VALUES (?, ?, ?)",
                (customer_order_id, item_id, qty)
            )
    
    conn.commit()
    conn.close()


def get_order_details_as_dict(customer_order_id: int):
    """取得訂單明細為字典格式 {item_id: quantity}"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, quantity FROM order_details WHERE customer_order_id = ?", (customer_order_id,))
    details = cursor.fetchall()
    conn.close()
    return {d['item_id']: d['quantity'] for d in details}

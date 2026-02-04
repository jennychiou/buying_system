# -*- coding: utf-8 -*-
"""
查詢所有團購單 ID 和品項資訊
執行方法: python show_group_orders.py
"""

import sys
sys.path.insert(0, r'D:\Jenny\buying_system')
import database as db

# 初始化資料庫
db.init_db()

print("=" * 70)
print("資料庫中的所有團購單")
print("=" * 70)

# 取得所有團購單
orders = db.get_all_group_orders()

if not orders:
    print("目前沒有任何團購單")
else:
    for order in orders:
        print(f"\n【團購單 ID: {order['id']}】")
        print(f"  名稱: {order['title']}")
        print(f"  說明: {order['description'] or '(無)'}")
        print(f"  狀態: {'開放中' if order['status'] == 'open' else '已關閉'}")
        print(f"  時間: {order['start_time'] or '(無)'} ~ {order['end_time'] or '(無)'}")
        
        # 顯示品項
        items = db.get_items_by_group_order(order['id'])
        if items:
            print(f"  品項 (共 {len(items)} 項):")
            for i, item in enumerate(items, 1):
                print(f"    {i}. {item['name']} - ${item['price']} (品項ID: {item['id']})")
        else:
            print("  品項: (無)")
        
        # 顯示訂單統計
        summary = db.get_group_order_summary(order['id'])
        if summary:
            total_orders = len(db.get_customer_orders_by_group(order['id']))
            total_amount = sum(s['total_amount'] for s in summary)
            print(f"  訂單統計: {total_orders} 筆訂單，總金額 ${total_amount:,.0f}")
        
        print("-" * 70)

print("\n" + "=" * 70)
print(f"共 {len(orders)} 個團購單")
print("=" * 70)

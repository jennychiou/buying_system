import pandas as pd
import sys
import os

# 添加專案路徑
sys.path.insert(0, r'D:\Jenny\buying_system')
import database as db

# 讀取 Excel 檔案
excel_path = r'C:\Users\OFFICE\Downloads\年菜115年2.xlsx'

try:
    df = pd.read_excel(excel_path, engine='openpyxl')
except Exception as e:
    print(f"讀取 Excel 錯誤: {e}")
    sys.exit(1)

print("=" * 60)
print("Excel 檔案資訊")
print("=" * 60)
print(f"工作表大小: {df.shape[0]} 列 x {df.shape[1]} 欄")
print(f"\n欄位名稱:")
for i, col in enumerate(df.columns.tolist(), 1):
    print(f"  {i}. {col}")

print("\n" + "=" * 60)
print("前 10 行資料預覽")
print("=" * 60)
print(df.head(10).to_string())

print("\n" + "=" * 60)
print("資料庫現有團購單")
print("=" * 60)
db.init_db()
group_orders = db.get_all_group_orders()
if group_orders:
    for i, order in enumerate(group_orders, 1):
        print(f"{i}. ID={order['id']}: {order['title']}")
        items = db.get_items_by_group_order(order['id'])
        print(f"   品項數: {len(items)}")
        if items:
            for j, item in enumerate(items, 1):
                print(f"   {j}. {item['name']} - ${item['price']}")
else:
    print("尚無團購單")

print("\n" + "=" * 60)

# -*- coding: utf-8 -*-
"""
步驟 2: 將 Excel 資料匯入資料庫
使用方法:
1. 先執行 step1_analyze_excel.py 確認資料結構
2. 確認團購單 ID (在下方設定)
3. 執行此腳本: python step2_import_to_db.py
"""

import pandas as pd
import sys
sys.path.insert(0, r'D:\Jenny\buying_system')
import database as db

# ========== 設定區 ==========
EXCEL_PATH = r'C:\Users\OFFICE\Downloads\年菜115年2.xlsx'
GROUP_ORDER_ID = 3  # 請填入要匯入的團購單 ID，例如: 1

# 欄位對應 - 根據 Excel 欄位順序對應到資料庫品項
# 例如: 第1欄是姓名，第2欄之後是各品項數量，最後一欄是備註
CUSTOMER_NAME_COLUMN = 0  # 姓名在第幾欄 (0 = 第1欄)
ITEMS_START_COLUMN = 1     # 品項數量從第幾欄開始 (1 = 第2欄)
NOTE_COLUMN = -1           # 備註在第幾欄 (-1 = 最後一欄, None = 沒有備註欄)

# 匯入模式
UPDATE_MODE = True  # True = 更新現有訂單（不重複建立）, False = 新增訂單
# ============================

def main():
    # 初始化資料庫
    db.init_db()
    
    # 檢查團購單 ID
    if GROUP_ORDER_ID is None:
        print("錯誤: 請先設定 GROUP_ORDER_ID")
        print("\n目前資料庫中的團購單:")
        orders = db.get_all_group_orders()
        if orders:
            for order in orders:
                print(f"  ID={order['id']}: {order['title']}")
                items = db.get_items_by_group_order(order['id'])
                print(f"    品項數: {len(items)}")
                for i, item in enumerate(items, 1):
                    print(f"      {i}. {item['name']} (${item['price']})")
        else:
            print("  尚無團購單")
        return
    
    # 讀取 Excel
    print(f"正在讀取 Excel: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    
    # 取得團購單品項
    items = db.get_items_by_group_order(GROUP_ORDER_ID)
    if not items:
        print(f"錯誤: 團購單 ID={GROUP_ORDER_ID} 沒有品項")
        return
    
    print(f"\n團購單品項 (共 {len(items)} 項):")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item['name']} (${item['price']})")
    
    # 計算預期欄位數
    if NOTE_COLUMN is not None:
        # 有備註欄: 姓名 + 品項數量 + 備註
        expected_columns = ITEMS_START_COLUMN + len(items) + 1
        print(f"\n欄位配置: 姓名 + {len(items)}個品項 + 備註")
    else:
        # 沒有備註欄: 姓名 + 品項數量
        expected_columns = ITEMS_START_COLUMN + len(items)
        print(f"\n欄位配置: 姓名 + {len(items)}個品項")
    
    # 檢查欄位數量
    if len(df.columns) < expected_columns:
        print(f"\n警告: Excel 欄位數 ({len(df.columns)}) 少於預期 ({expected_columns})")
        print("Excel 欄位:")
        for i, col in enumerate(df.columns):
            print(f"  第 {i} 欄: {col}")
        response = input("\n是否繼續? (y/n): ")
        if response.lower() != 'y':
            return
    
    # 開始匯入
    if UPDATE_MODE:
        print(f"\n【更新模式】開始更新現有訂單...")
    else:
        print(f"\n【新增模式】開始匯入資料...")
    
    success_count = 0
    error_count = 0
    update_count = 0
    create_count = 0
    
    for idx, row in df.iterrows():
        try:
            # 取得顧客姓名
            customer_name = str(row.iloc[CUSTOMER_NAME_COLUMN]).strip()
            
            # 跳過空白姓名
            if not customer_name or customer_name == 'nan':
                continue
            
            # 收集品項數量
            items_qty = {}
            total_qty = 0
            
            for i, item in enumerate(items):
                col_idx = ITEMS_START_COLUMN + i
                if col_idx < len(row):
                    qty = row.iloc[col_idx]
                    # 轉換為數字
                    try:
                        qty = int(float(qty)) if pd.notna(qty) else 0
                    except:
                        qty = 0
                    
                    items_qty[item['id']] = qty
                    total_qty += qty
                else:
                    items_qty[item['id']] = 0
            
            # 取得備註
            note = ""
            if NOTE_COLUMN is not None:
                if NOTE_COLUMN == -1:
                    # 最後一欄
                    note_value = row.iloc[-1]
                else:
                    # 指定欄位
                    if NOTE_COLUMN < len(row):
                        note_value = row.iloc[NOTE_COLUMN]
                    else:
                        note_value = None
                
                if pd.notna(note_value):
                    note = str(note_value).strip()
            
            # 跳過沒有訂購任何品項的訂單
            if total_qty == 0:
                continue
            
            if UPDATE_MODE:
                # 更新模式：檢查是否已存在此姓名的訂單
                existing_orders = db.get_customer_orders_by_name(GROUP_ORDER_ID, customer_name)
                
                if existing_orders:
                    # 更新第一筆訂單（如果有多筆，只更新第一筆）
                    existing_order = existing_orders[0]
                    order_id = existing_order['id']
                    
                    # 更新訂單內容
                    db.update_customer_order(order_id, items_qty)
                    
                    # 更新備註
                    if note:
                        conn = db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute(db._sql("UPDATE customer_orders SET note = ? WHERE id = ?"), (note, order_id))
                        conn.commit()
                        conn.close()
                    
                    update_count += 1
                    success_count += 1
                    if note:
                        print(f"  ↻ {customer_name}: 已更新，總數量 {total_qty}, 備註: {note[:20]}... (訂單 ID={order_id})")
                    else:
                        print(f"  ↻ {customer_name}: 已更新，總數量 {total_qty} (訂單 ID={order_id})")
                else:
                    # 不存在則建立新訂單
                    order_id = db.create_customer_order(GROUP_ORDER_ID, customer_name, items_qty, note=note)
                    create_count += 1
                    success_count += 1
                    if note:
                        print(f"  ✓ {customer_name}: 新增訂單，總數量 {total_qty}, 備註: {note[:20]}... (訂單 ID={order_id})")
                    else:
                        print(f"  ✓ {customer_name}: 新增訂單，總數量 {total_qty} (訂單 ID={order_id})")
            else:
                # 新增模式：直接建立訂單
                order_id = db.create_customer_order(GROUP_ORDER_ID, customer_name, items_qty, note=note)
                create_count += 1
                success_count += 1
                if note:
                    print(f"  ✓ {customer_name}: 總數量 {total_qty}, 備註: {note[:20]}... (訂單 ID={order_id})")
                else:
                    print(f"  ✓ {customer_name}: 總數量 {total_qty} (訂單 ID={order_id})")
            
        except Exception as e:
            error_count += 1
            print(f"  ✗ 第 {idx + 1} 列錯誤: {e}")
    
    print("\n" + "=" * 70)
    print(f"匯入完成!")
    if UPDATE_MODE:
        print(f"  更新: {update_count} 筆")
        print(f"  新增: {create_count} 筆")
    else:
        print(f"  新增: {create_count} 筆")
    print(f"  失敗: {error_count} 筆")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError:
        print(f"錯誤: 找不到檔案 {EXCEL_PATH}")
    except Exception as e:
        print(f"錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

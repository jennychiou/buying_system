# -*- coding: utf-8 -*-
"""
步驟 1: 分析 Excel 檔案結構
請在命令提示字元執行: python step1_analyze_excel.py
"""

import pandas as pd

print("正在讀取 Excel 檔案...")
excel_path = r'C:\Users\OFFICE\Downloads\年菜115年2.xlsx'

try:
    # 嘗試讀取 Excel
    df = pd.read_excel(excel_path)
    
    print("\n" + "=" * 70)
    print("Excel 檔案分析結果")
    print("=" * 70)
    
    print(f"\n總列數: {len(df)}")
    print(f"總欄數: {len(df.columns)}")
    
    print("\n欄位名稱 (共 {} 欄):".format(len(df.columns)))
    for i, col in enumerate(df.columns, 1):
        print(f"  第 {i} 欄: {col}")
    
    print("\n" + "=" * 70)
    print("前 10 列資料預覽:")
    print("=" * 70)
    print(df.head(10).to_string(index=False))
    
    print("\n" + "=" * 70)
    print("資料類型:")
    print("=" * 70)
    print(df.dtypes)
    
    print("\n" + "=" * 70)
    print("完成分析!")
    print("=" * 70)
    
except FileNotFoundError:
    print(f"錯誤: 找不到檔案 {excel_path}")
    print("請確認檔案路徑是否正確")
except Exception as e:
    print(f"錯誤: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

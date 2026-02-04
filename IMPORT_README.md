# Excel 匯入資料庫操作說明

## 步驟說明

### 步驟 1: 分析 Excel 檔案結構
在命令提示字元 (CMD) 執行:
```
cd D:\Jenny\buying_system
python step1_analyze_excel.py
```

這會顯示:
- Excel 有幾列、幾欄
- 每一欄的名稱
- 前 10 列的資料預覽

### 步驟 2: 設定匯入參數
1. 用記事本或編輯器開啟 `step2_import_to_db.py`
2. 找到「設定區」，設定以下參數:

```python
# ========== 設定區 ==========
GROUP_ORDER_ID = 1  # 填入要匯入的團購單 ID

# 欄位對應
CUSTOMER_NAME_COLUMN = 0  # 姓名在第幾欄 (0=第1欄, 1=第2欄...)
ITEMS_START_COLUMN = 1     # 品項數量從第幾欄開始
# ============================
```

說明:
- `GROUP_ORDER_ID`: 要匯入到哪個團購單 (先執行一次 step2 會列出所有團購單)
- `CUSTOMER_NAME_COLUMN`: 顧客姓名在 Excel 的第幾欄 (從 0 開始計算)
- `ITEMS_START_COLUMN`: 品項數量從第幾欄開始

例如，如果 Excel 格式是:
```
| 姓名 | 品項1 | 品項2 | 品項3 | ... |
```
那麼:
- `CUSTOMER_NAME_COLUMN = 0` (第1欄是姓名)
- `ITEMS_START_COLUMN = 1` (從第2欄開始是品項數量)

### 步驟 3: 執行匯入
在命令提示字元執行:
```
cd D:\Jenny\buying_system
python step2_import_to_db.py
```

第一次執行時，如果沒有設定 GROUP_ORDER_ID，會顯示所有團購單供你選擇。

## 注意事項

1. **品項順序對應**: Excel 中品項數量的欄位順序，會依序對應到資料庫中該團購單的品項順序
2. **空白資料**: 姓名為空或數量為 0 的訂單會被跳過
3. **備份建議**: 匯入前建議先備份資料庫 `group_buying.db`

## 範例

假設資料庫中團購單 ID=1 有以下品項 (依序):
1. 海帶
2. 豆干
3. 米血

Excel 格式為:
```
| 姓名   | 海帶 | 豆干 | 米血 |
| 小明   |  2   |  1   |  0   |
| 小華   |  1   |  1   |  2   |
```

設定:
```python
GROUP_ORDER_ID = 1
CUSTOMER_NAME_COLUMN = 0  # 姓名在第1欄 (index 0)
ITEMS_START_COLUMN = 1     # 品項從第2欄開始 (index 1)
```

執行結果:
- 小明: 海帶 x2, 豆干 x1
- 小華: 海帶 x1, 豆干 x1, 米血 x2

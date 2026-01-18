# 團購訂單系統

一個基於 Streamlit 的團購訂單管理系統，讓團主輕鬆建立團購單、管理商品，讓顧客方便下單。

## 功能特色

### 管理後台
- 建立團購單（設定名稱、說明、開放時間）
- 新增/管理團購品項及價格
- 查看訂單統計與彙總
- 管理顧客訂單

### 商品訂購
- 顧客可瀏覽開放中的團購單
- 選擇品項數量並下單
- 查詢/修改自己的訂單

## 系統需求

- Python 3.8 以上
- Windows 作業系統（含 .bat 安裝腳本）

## 安裝方式

### 方法一：使用安裝腳本（推薦）

雙擊執行 `install.bat`，會自動：
1. 建立 Python 虛擬環境
2. 安裝所需套件

### 方法二：手動安裝

```bash
# 建立虛擬環境
python -m venv venv

# 啟動虛擬環境
venv\Scripts\activate

# 安裝套件
pip install -r requirements.txt
```

## 啟動系統

### 方法一：使用啟動腳本

雙擊執行 `run.bat`

### 方法二：手動啟動

```bash
# 啟動虛擬環境
venv\Scripts\activate

# 執行程式
streamlit run app.py
```

啟動後，瀏覽器會自動開啟 http://localhost:8501

## 使用說明

### 管理後台
1. 點選側邊欄「管理後台」
2. 輸入管理密碼（預設：`123456`）
3. 可建立團購單、管理品項、查看統計

### 商品訂購
1. 點選側邊欄「商品訂購」
2. 選擇要參加的團購單
3. 輸入姓名、選擇品項數量
4. 確認送出訂單

## 專案結構

```
buying_system/
├── app.py           # 主程式（Streamlit 應用）
├── database.py      # 資料庫操作模組
├── group_buying.db  # SQLite 資料庫
├── requirements.txt # Python 套件需求
├── install.bat      # 安裝腳本
├── run.bat          # 啟動腳本
└── venv/            # Python 虛擬環境
```

## 技術架構

- **前端框架**：Streamlit
- **資料庫**：SQLite
- **資料處理**：Pandas

## 授權

此專案僅供個人使用。

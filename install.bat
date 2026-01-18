@echo off
echo ========================================
echo   團購訂單系統 - 環境安裝
echo ========================================
echo.

REM 建立虛擬環境
echo [1/3] 建立虛擬環境...
python -m venv venv

REM 啟動虛擬環境並安裝套件
echo [2/3] 安裝套件...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo [3/3] 安裝完成！
echo ========================================
echo.
echo 使用方式：
echo   1. 啟動虛擬環境: venv\Scripts\activate
echo   2. 執行程式: streamlit run app.py
echo.
pause

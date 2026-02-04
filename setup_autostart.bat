@echo off
REM 使用 Windows 排程器讓 Streamlit 在系統啟動時自動執行

cd /d "%~dp0"

echo ====================================================================
echo 設定 Streamlit 開機自動啟動
echo ====================================================================
echo.
echo 此腳本會建立 Windows 排程工作，讓 Streamlit 在開機時自動啟動
echo.
echo 專案路徑: %~dp0
echo.

set TASK_NAME=StreamlitBuyingSystem
set SCRIPT_PATH=%~dp0run_background.bat

REM 檢查是否已存在排程工作
schtasks /query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 發現已存在的排程工作，將先刪除...
    schtasks /delete /TN "%TASK_NAME%" /F >nul 2>&1
)

echo.
echo 正在建立排程工作...
echo.

REM 建立排程工作（開機時執行）
schtasks /create /TN "%TASK_NAME%" /TR "\"%SCRIPT_PATH%\"" /SC ONLOGON /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================================================
    echo 設定成功！
    echo ====================================================================
    echo.
    echo 排程工作名稱: %TASK_NAME%
    echo 執行腳本: %SCRIPT_PATH%
    echo 觸發條件: 使用者登入時
    echo.
    echo Streamlit 將在下次登入時自動啟動
    echo 網址: http://localhost:8501
    echo.
    echo 如要立即啟動，請執行 run_background.bat
    echo 如要取消開機自動啟動，請執行 remove_autostart.bat
    echo.
) else (
    echo.
    echo ====================================================================
    echo 設定失敗！
    echo ====================================================================
    echo.
    echo 請以系統管理員身分執行此批次檔
    echo （右鍵點擊 → 以系統管理員身分執行）
    echo.
)

pause

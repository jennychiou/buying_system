@echo off
REM 移除 Streamlit 開機自動啟動設定

echo ====================================================================
echo 移除 Streamlit 開機自動啟動
echo ====================================================================
echo.

set TASK_NAME=StreamlitBuyingSystem

REM 檢查排程工作是否存在
schtasks /query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo 正在刪除排程工作...
    schtasks /delete /TN "%TASK_NAME%" /F
    
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo 已成功移除開機自動啟動設定
        echo.
    ) else (
        echo.
        echo 移除失敗，請以系統管理員身分執行此批次檔
        echo.
    )
) else (
    echo.
    echo 找不到排程工作「%TASK_NAME%」
    echo 可能尚未設定開機自動啟動
    echo.
)

pause

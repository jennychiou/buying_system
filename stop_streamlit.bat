@echo off
REM 停止背景運行的 Streamlit 應用程式

echo 正在停止 Streamlit 應用程式...

REM 找出所有 streamlit 相關的 Python 程序並停止
for /f "tokens=2" %%a in ('tasklist ^| findstr /i "python"') do (
    wmic process where "ProcessId=%%a AND CommandLine like '%%streamlit%%'" delete >nul 2>&1
)

echo.
echo Streamlit 應用程式已停止
echo.
pause

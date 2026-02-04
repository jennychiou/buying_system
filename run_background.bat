@echo off
REM 在背景啟動 Streamlit 應用程式
REM 此視窗可以關閉，應用程式會繼續在背景執行

cd /d "%~dp0"

echo 正在啟動 Streamlit 應用程式...
echo.
echo 應用程式將在背景執行
echo 網址: http://localhost:8501
echo.
echo 關閉此視窗不會停止應用程式
echo 要停止應用程式，請使用 stop_streamlit.bat
echo.

start /B python -m streamlit run app.py

echo.
echo 應用程式已在背景啟動！
echo 請開啟瀏覽器，前往 http://localhost:8501
echo.
pause

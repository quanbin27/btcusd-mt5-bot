@echo off
echo ============================================
echo   Building BTC Sell Bot EXE
echo ============================================
echo.

pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --noconsole --onefile --name "BTC_Sell_Bot" main.py

echo.
echo ============================================
echo   Build complete!
echo   EXE location: dist\BTC_Sell_Bot.exe
echo ============================================
pause

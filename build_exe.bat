@echo off
echo ============================================
echo   Building BTC Sell Bot EXE
echo ============================================
echo.

pip install -r requirements.txt

echo.
echo Building executable...
pyinstaller --noconsole --onefile --name "BTC_Sell_Bot" ^
    --icon=app_icon.ico ^
    --add-data "app_icon.ico;." ^
    --add-data ".env;." ^
    --hidden-import=numpy ^
    --hidden-import=numpy._core ^
    --hidden-import=numpy._core.multiarray ^
    --hidden-import=numpy._core._multiarray_umath ^
    --hidden-import=numpy.core ^
    --hidden-import=numpy.core.multiarray ^
    --hidden-import=requests ^
    --hidden-import=dotenv ^
    --collect-all numpy ^
    --collect-all MetaTrader5 ^
    main.py

echo.
echo ============================================
echo   Build complete!
echo   EXE: dist\BTC_Sell_Bot.exe
echo ============================================
pause

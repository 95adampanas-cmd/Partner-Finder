@echo off
REM ===== Partner Finder - uruchamianie jednym klikiem =====
cd /d "%~dp0backend"

echo.
echo   ============================================
echo    Partner Finder - serwer startuje...
echo.
echo    Otworz w przegladarce:  http://localhost:8000
echo    Zatrzymanie serwera:    Ctrl + C
echo   ============================================
echo.

REM otworz przegladarke po 3 sekundach (gdy serwer wstanie)
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8000"

REM uruchom serwer (blokuje okno - tak ma byc)
python -m uvicorn app:app --port 8000

echo.
echo Serwer zatrzymany.
pause

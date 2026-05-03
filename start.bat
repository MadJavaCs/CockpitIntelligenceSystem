@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Das Projekt wurde mit einem Fehler beendet.
)
pause

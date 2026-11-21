@echo off
where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0pdf-library.py"
) else (
    py -3 "%~dp0pdf-library.py"
)
if errorlevel 1 pause


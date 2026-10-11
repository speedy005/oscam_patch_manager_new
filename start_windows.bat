@echo off
cd /d "%~dp0"

echo ========================================
echo OSCam Patch Manager - Windows Start
echo ========================================
echo.

set "PYTHON_EXE="

for /f "delims=" %%P in ('py -3.11 -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"

if not defined PYTHON_EXE (
    echo FEHLER: Python 3.11 wurde nicht gefunden.
    pause
    exit /b 1
)

echo Verwendetes Python:
echo "%PYTHON_EXE%"
echo.

echo Pruefe Syntax ...
"%PYTHON_EXE%" -m py_compile main.py startup.py gui.py
if errorlevel 1 (
    echo FEHLER: Syntaxpruefung fehlgeschlagen.
    pause
    exit /b 1
)

echo.
echo Starte OSCam Patch Manager ...
"%PYTHON_EXE%" main.py

if errorlevel 1 (
    echo.
    echo FEHLER beim Start. Siehe Fehlermeldung oben.
    pause
)

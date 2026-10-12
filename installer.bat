@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 installer.py
    exit /b %errorlevel%
)
where python >nul 2>nul
if %errorlevel%==0 (
    python installer.py
    exit /b %errorlevel%
)
echo Python 3 was not found. Install Python 3 and enable it in PATH, then try again.
pause
exit /b 1

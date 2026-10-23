@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
rem always run from the folder this file lives in

echo.
echo ===========================================================
echo   academy-ops : Payroll Automation MVP
echo ===========================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [STOP] Python not found.
  echo        Install from https://www.python.org/downloads/
  echo        Check "Add python.exe to PATH" during setup.
  echo.
  pause
  exit /b 1
)

echo [0/3] checking packages
python -c "import openpyxl, yaml, reportlab" >nul 2>&1
if errorlevel 1 (
  echo       installing missing packages ...
  python -m pip install --quiet openpyxl PyYAML reportlab
)

echo.
echo [1/3] build sample data
python tools\make_samples.py samples\2026-09
if errorlevel 1 goto failed

echo.
echo [2/3] run payroll  (normal input + exception input)
python -m app.cli run --month 2026-09 --input samples\2026-09 --output out\2026-09
rem exit code 2 means a staff member was blocked - intended behaviour, not an error.
if errorlevel 3 goto failed

echo.
echo [3/3] build result dashboard
python tools\make_dashboard.py out\2026-09 docs\index.html

echo.
echo ===========================================================
echo   DONE - results are in  out\2026-09
echo ===========================================================
echo.
start "" "%~dp0out\2026-09"
pause
exit /b 0

:failed
echo.
echo [STOP] something failed above. Please read the message.
pause
exit /b 1

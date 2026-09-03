@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo ERROR: Project Python was not found at .venv\Scripts\python.exe
  echo Create the repository virtual environment and install requirements-visualization.txt.
  pause
  exit /b 1
)

if not exist "apps\mindboggle101_3d_viewer.py" (
  echo ERROR: Viewer entry point is missing: apps\mindboggle101_3d_viewer.py
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -c "import streamlit" >nul 2>nul
if errorlevel 1 (
  echo ERROR: Streamlit is unavailable in the repository virtual environment.
  echo Install requirements-visualization.txt and try again.
  pause
  exit /b 1
)

if "%BRAIN_DEMO_VALIDATE_ONLY%"=="1" (
  echo LAUNCHER_VALIDATION_PASSED
  echo .venv\Scripts\python.exe -m streamlit run apps\mindboggle101_3d_viewer.py --server.address 127.0.0.1
  exit /b 0
)

echo Starting the local Mindboggle-101 manual-DKT31 viewer...
echo Close this window or press Ctrl+C to stop the server.
".venv\Scripts\python.exe" -m streamlit run "apps\mindboggle101_3d_viewer.py" --server.address 127.0.0.1 --server.headless false
if errorlevel 1 (
  echo.
  echo ERROR: The viewer exited with an error.
  pause
  exit /b 1
)
endlocal


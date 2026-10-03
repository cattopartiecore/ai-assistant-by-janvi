@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto novenv
".venv\Scripts\python.exe" -m streamlit run app/app.py --server.headless false
pause
exit /b

:novenv
echo .venv folder not found.
echo Create it first with: python -m venv .venv
pause
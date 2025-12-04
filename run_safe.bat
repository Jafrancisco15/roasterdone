
@echo off
setlocal
if not exist .venv (
  py -3.12 -m venv .venv
)
call .venv\Scripts\python -m pip install --upgrade pip wheel setuptools
call .venv\Scripts\pip install -r requirements.txt
REM Light theme safest
set ROASTLAB_THEME=light
call .venv\Scripts\python main.py
endlocal
pause

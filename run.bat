@echo off
setlocal
title RoastLab Python (py312-friendly)
py -3 -V
py -3 -V >NUL 2>&1
if errorlevel 1 (
  echo No se encontro 'py'. Instala Python 3.x desde python.org y vuelve a intentar.
  pause
  exit /b 1
)
if not exist .venv (
  py -3 -m venv .venv
)
set "PYVENV=.venv\Scripts\python.exe"
"%PYVENV%" -m ensurepip --upgrade
"%PYVENV%" -m pip install --upgrade pip wheel setuptools
echo == Instalando requirements (puede tardar unos minutos) ==
"%PYVENV%" -m pip install -r requirements.txt
set MPLBACKEND=TkAgg
echo ================== LAUNCH ==================
"%PYVENV%" -u main.py
echo ================== EXIT ==================
pause

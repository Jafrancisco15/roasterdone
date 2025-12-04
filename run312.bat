@echo off
setlocal
title RoastLab v7 (Py 3.12)

set "PY312=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PY312%" (
  echo No encuentro Python 3.12 en: %PY312%
  echo Ejecuta 'py -0p' para ver rutas y pega aqui la correcta del 3.12.
  pause
  exit /b 1
)

if not exist .venv (
  "%PY312%" -m venv .venv
  set "PYVENV=.venv\Scripts\python.exe"
  "%PYVENV%" -m ensurepip --upgrade
  "%PYVENV%" -m pip install --upgrade pip wheel setuptools
  "%PYVENV%" -m pip install --only-binary :all: -r requirements.txt
) else (
  set "PYVENV=.venv\Scripts\python.exe"
  "%PYVENV%" -m pip install --upgrade pip wheel setuptools >NUL
)

set MPLBACKEND=TkAgg
"%PYVENV%" -u main.py
pause

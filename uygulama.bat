@echo off
REM Masaustu uygulamasi: uygulama.bat [baslangic.json]
set PYTHONPATH=%~dp0
python -m arayuz %*

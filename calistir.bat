@echo off
REM Kullanim: calistir.bat baslangic.json komutlar.jsonl > sonuclar.jsonl
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8
python -m rezervasyon %*

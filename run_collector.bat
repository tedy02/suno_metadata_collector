@echo off
REM Suno Metatag Collector v2.0.2 quick runner for Windows users
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python suno_metadata_collector.py
pause

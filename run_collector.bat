@echo off
REM Suno Metatag Collector v2.0.1 quick runner for Windows users
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt
py -3.11 suno_metadata_collector.py
pause

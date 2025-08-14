#!/bin/bash
# Suno Metatag Collector v2.0.2 quick runner for Linux/Mac users

set -e

# Check Python version
PYTHON_BIN="${PYTHON_BIN:-python3}"

# Upgrade pip and install requirements
$PYTHON_BIN -m pip install --upgrade pip
$PYTHON_BIN -m pip install -r requirements.txt

# Run the script
$PYTHON_BIN suno_metadata_collector.py

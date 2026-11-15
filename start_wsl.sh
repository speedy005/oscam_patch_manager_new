#!/bin/bash
cd "$(dirname "$0")"
source .venv/bin/activate
python3 -m py_compile main.py startup.py gui.py license_center.py || exit 1
python3 main.py

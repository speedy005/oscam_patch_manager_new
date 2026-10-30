#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Public launcher for OSCam Patch Manager. Run: python main.py"""
import os
import platform
import faulthandler
import signal
import sys

if hasattr(signal, "SIGUSR1"):
    faulthandler.register(signal.SIGUSR1, file=sys.stderr, all_threads=True)

if platform.system() == "Windows":
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ.setdefault("QT_OPENGL", "software")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "0")

# PyQt-Fehler aus Signal- und Event-Callbacks sichtbar machen
import traceback

def _qt_exception_hook(exc_type, exc_value, exc_tb):
    print(
        "\\n========== UNBEHANDELTE PYTHON-AUSNAHME IN QT ==========\\n",
        file=sys.__stderr__,
        flush=True,
    )
    traceback.print_exception(
        exc_type, exc_value, exc_tb, file=sys.__stderr__
    )
    print(
        "\\n========== ENDE DES FEHLERBERICHTS ==========\\n",
        file=sys.__stderr__,
        flush=True,
    )

sys.excepthook = _qt_exception_hook

from startup import main

if __name__ == "__main__":
    main()

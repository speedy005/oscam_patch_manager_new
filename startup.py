"""OSCam Patch Manager module fragment: Application entry point."""

# Explicit module imports (kept broad for compatibility with legacy callbacks).
import ctypes
import glob
import importlib.util
import io
import json
import locale
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from PyQt6.QtCore import QDateTime, QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect, QSize, QThread, QTime, QTimer, QUrl, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPolygon, QTextCursor
from PyQt6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGraphicsColorizeEffect, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSizePolicy, QSlider, QTextEdit, QVBoxLayout, QWidget, QWidgetItem
from datetime import datetime, timezone

from bootstrap import auto_install_emoji_font
from dialogs_splash import CinematicMatrixSplash
from gui import PatchManagerGUI

def main():
    import os, sys, platform, traceback, threading, ctypes, subprocess, shutil
    from pathlib import Path
    from PyQt6.QtCore import Qt, QTimer, QLibraryInfo
    from PyQt6.QtWidgets import QApplication, QMessageBox

        # ---------------- 0. ADMIN / ROOT ELEVATION (VM & WINDOWS FIX) ----------------
    def elevate_privileges():
        """Prüft auf Admin/Root und fordert diese grafisch an, falls nötig."""
        # Verhindert Endlosschleife, falls Elevation fehlschlägt
        if "--elevated" in sys.argv:
            return

        system = platform.system()
        try:
            if system == "Windows":
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    print("[SYSTEM] Fordere Windows-Admin-Rechte an...")

                    script = os.path.abspath(sys.argv[0])

                    params = subprocess.list2cmdline(
                        [script] + sys.argv[1:] + ["--elevated"]
                    )

                    result = ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",
                        sys.executable,
                        params,
                        os.path.dirname(script),
                        1
                    )

                    if result <= 32:
                        print(f"[FEHLER] Windows konnte den Prozess nicht erhöhen. Fehlercode: {result}")
                        input("ENTER zum Beenden...")
                        sys.exit(1)

                    print("[SYSTEM] Administrator-Prozess wurde gestartet.")
                    sys.exit(0)
            
            elif system == "Linux":
                if os.geteuid() != 0:
                    print("[SYSTEM] Root-Rechte erforderlich für VM-Operationen...")
                    
                    # 1. Ermittle den echten, unprivilegierten Benutzer hinter der aktuellen Session
                    real_user = os.getenv("USER") or os.getenv("LOGNAME")
                    if not real_user or real_user == "root":
                        # Versuche den Besitzer der grafischen X11-Session zu ermitteln
                        try:
                            real_user = subprocess.check_output(["id", "-un"], text=True).strip()
                        except Exception:
                            real_user = "root"
                    
                    # 2. Hole die kritischen Display- und Sitzungsvariablen des aktuellen Users
                    display = os.getenv("DISPLAY", ":0")
                    xauth = os.getenv("XAUTHORITY")
                    xdg_runtime = os.getenv("XDG_RUNTIME_DIR")
                    wayland_display = os.getenv("WAYLAND_DISPLAY")

                    # Fallback für XAUTHORITY, falls leer
                    if not xauth and real_user and real_user != "root":
                        possible_xauth = Path(f"/home/{real_user}/.Xauthority")
                        if possible_xauth.exists():
                            xauth = str(possible_xauth)

                    # Fallback für XDG_RUNTIME_DIR (wichtig für Wayland & Qt6)
                    if not xdg_runtime and real_user and real_user != "root":
                        try:
                            import pwd
                            uid = pwd.getpwnam(real_user).pw_uid
                            possible_xdg = Path(f"/run/user/{uid}")
                            if possible_xdg.exists():
                                xdg_runtime = str(possible_xdg)
                        except Exception:
                            pass

                    # 3. X11-Berechtigung für Root freigeben (Erlaubt Root den Zugriff auf das User-Display)
                    try:
                        subprocess.run(["xhost", "+SI:localuser:root"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass

                    # 4. Elevation-Tool wählen und Umgebungsvariablen über die Shell erzwingen
                    # Grund: pkexec/sudo löschen os.environ vor dem Start. Wir müssen sie per env mitgeben!
                    launcher = shutil.which("pkexec") or shutil.which("sudo")
                    if launcher:
                        # Baue die Zuweisungen für die Umgebungsvariablen zusammen
                        env_args = [f"DISPLAY={display}"]
                        if xauth:
                            env_args.append(f"XAUTHORITY={xauth}")
                        if xdg_runtime:
                            env_args.append(f"XDG_RUNTIME_DIR={xdg_runtime}")
                        if wayland_display:
                            env_args.append(f"WAYLAND_DISPLAY={wayland_display}")

                        # Erstelle das Python-Kommando
                        python_cmd = [sys.executable] + sys.argv + ["--elevated"]

                        if "sudo" in launcher:
                            # Bei sudo nutzen wir 'env', um gefilterte Variablen zu erzwingen
                            os.execv(launcher, [launcher, "env"] + env_args + python_cmd)
                        else:
                            # pkexec erlaubt keine direkte Nutzung von env als Argument.
                            # Wir kapseln den Aufruf in einer Root-Bash, um die Variablen sicher zu injizieren.
                            bash_script = " ".join(env_args) + " " + " ".join(f'"{a}"' for a in python_cmd)
                            os.execv(launcher, [launcher, "bash", "-c", bash_script])
                    
                    sys.exit(1)
        except Exception as e:
            print(f"[!] Elevation-Error: {e}")

    # Rechte prüfen, bevor die GUI geladen wird
    elevate_privileges()

    # ---------------- 1. SYSTEM ENV & HIGH-DPI FIX ----------------
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["NO_AT_BRIDGE"] = "1"

    system = platform.system()
    if system == "Linux":
        # Qt akzeptiert hier einen einzelnen Plattform-Plugin-Namen.
        # Wenn der Benutzer bereits QT_QPA_PLATFORM gesetzt hat, bleibt
        # diese Auswahl unangetastet.
        if not os.environ.get("QT_QPA_PLATFORM"):
            if os.environ.get("WAYLAND_DISPLAY"):
                os.environ["QT_QPA_PLATFORM"] = "wayland"
            elif os.environ.get("DISPLAY"):
                os.environ["QT_QPA_PLATFORM"] = "xcb"

    elif system == "Windows":
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")


    # ---------------- 2. DPI POLICY & QAPPLICATION START ----------------
    try:
        if hasattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )
    except Exception:
        pass

    # Plugin-Pfad für Qt vor QApplication setzen.
    plugin_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    if plugin_path:
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_path)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    # ---------------- 3. DISPLAY / RESOLUTION DETECTION ----------------
    screen_geo = app.primaryScreen().availableGeometry()
    width, height = screen_geo.width(), screen_geo.height()
    try:
        import getpass
        current_user = getpass.getuser()
    except Exception:
        current_user = (
            os.environ.get("USERNAME")
            or os.environ.get("USER")
            or "unknown"
        )

    print(
        f"[SYSTEM] Display erkannt: {width}x{height} | User: {current_user}"
    )

    # ---------------- 4. FONT-FIX ASYNC START ----------------
    if 'auto_install_emoji_font' in globals():
        auto_install_emoji_font()
    else:
        print("[!] auto_install_emoji_font() Funktion wurde nicht gefunden.")

        # ---------------- 5. GLOBAL STATE & GUI START LOGIK ----------------
    main_window = None

    def _actually_start():
        """Hauptinstanz der GUI laden und Auflösung anpassen."""
        global main_window
        try:
            # GUI laden (Stelle sicher, dass PatchManagerGUI definiert ist)
            if 'PatchManagerGUI' in globals():
                main_window = PatchManagerGUI()
            else:
                raise NameError("Klasse 'PatchManagerGUI' nicht im globalen Scope gefunden.")

            # Optionaler globaler Style
            if 'CYBER_STYLE' in globals():
                main_window.setStyleSheet(CYBER_STYLE)

            main_window.setWindowTitle("OSCam Emu Patch Manager v4.0 - by speedy005")

            main_window.showMaximized()
            main_window.raise_()
            # ERZWUNGENER NEUSTART-FIX: 
            # Sobald das Fenster nach dem Cinematic Splash erscheint, geben wir 
            # PyQt 100ms Zeit, die Buttons im Grafikspeicher zu verankern.
            # Dann feuern wir das Festplatten-Auslesen ab, damit alle Buttons grün werden!
            # =================================================================
            if hasattr(main_window, "update_ui_texts"):
                QTimer.singleShot(100, main_window.update_ui_texts)
            # =================================================================

            # Akustische Rückmeldung beim Start
            if platform.system() == "Windows":
                try:
                    import winsound
                    winsound.Beep(1500, 100)
                except: 
                    pass

        except Exception:
            error_details = traceback.format_exc()
            print(f"FATAL ERROR:\n{error_details}")
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("SYSTEM FAILURE")
            msg.setText("Kritischer Fehler beim Laden des Kern-Moduls.")
            msg.setDetailedText(error_details)
            msg.setStyleSheet("background-color: #050505; color: #00ff41; font-family: 'Consolas';")
            msg.exec()
            sys.exit(1)

    def launch_main_gui():
        """Wird getriggert, wenn Splash-Screen endet."""
        QTimer.singleShot(200, _actually_start)

    # ---------------- 6. CINEMATIC SPLASH ----------------
    try:
        # Falls CinematicMatrixSplash nicht definiert ist, direkt starten
        if 'CinematicMatrixSplash' in globals():
            splash = CinematicMatrixSplash(duration=5000)
            splash.finished.connect(launch_main_gui)
            splash.show()
        else:
            _actually_start()
    except Exception as e:
        print(f"[!] Splash-Error: {e}. Starte direkt...")
        _actually_start()

    # ---------------- 7. MAIN EXECUTION LOOP ----------------
    try:
        sys.exit(app.exec())
    except Exception:
        traceback.print_exc()
        sys.exit(1)

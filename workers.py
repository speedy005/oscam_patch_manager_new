"""OSCam Patch Manager module fragment: Background workers and installation helpers."""

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

class OSCamUpdateWorker(QThread):
    """Prüft im Hintergrund, ob im Streamboard-Git neue Commits vorliegen."""

    status_signal = pyqtSignal(bool, str)  # (Update verfügbar?, Neuer Hash)

    def __init__(self, remote_url, local_path):
        super().__init__()
        self.remote_url = remote_url
        self.local_path = local_path

    def run(self):
        try:
            # 1. Remote HEAD Hash abrufen
            cmd_remote = ["git", "ls-remote", self.remote_url, "HEAD"]
            remote_out = subprocess.check_output(
                cmd_remote, text=True, stderr=subprocess.DEVNULL
            ).split()
            if not remote_out:
                return
            remote_hash = remote_out[0]

            # 2. Lokalen Hash prüfen
            local_hash = ""
            # Prüfen ob Pfad existiert UND ein Git-Repo ist
            if os.path.exists(self.local_path) and os.path.exists(
                os.path.join(self.local_path, ".git")
            ):
                cmd_local = ["git", "-C", self.local_path, "rev-parse", "HEAD"]
                local_hash = subprocess.check_output(
                    cmd_local, text=True, stderr=subprocess.DEVNULL
                ).strip()
            else:
                # Falls Ordner nicht existiert -> Update (Installation) ist definitiv nötig
                local_hash = "NOT_INSTALLED"

            # 3. Vergleich & Signal senden
            update_available = remote_hash != local_hash
            self.status_signal.emit(update_available, remote_hash)
        except Exception as e:
            print(f"Update-Check Fehler: {e}")
            self.status_signal.emit(False, "")

def check_and_install_dependencies(required_packages):
    missing_packages = []
    for pkg in required_packages:
        if importlib.util.find_spec(pkg) is None:
            missing_packages.append(pkg)

    if missing_packages:
        # Falls PyQt6 fehlt, können wir keine MessageBox zeigen!
        if "PyQt6" in missing_packages:
            print(f"\n⚠️ Fehlende Komponenten: {', '.join(missing_packages)}")
            choice = input("Möchten Sie diese jetzt via pip installieren? (j/n): ")
            if choice.lower() == "j":
                for pkg in missing_packages:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                # Neustart des Skripts
                os.execv(sys.executable, [sys.executable] + sys.argv)
                return True
            return False

        # Wenn PyQt6 vorhanden ist, aber andere (wie requests) fehlen:
        from PyQt6.QtWidgets import QApplication, QMessageBox

        temp_app = QApplication.instance() or QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Fehlende Komponenten")
        msg.setText(f"Folgende Bibliotheken fehlen: {', '.join(missing_packages)}")
        msg.setInformativeText("Möchten Sie diese jetzt installieren?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if msg.exec() == QMessageBox.StandardButton.Yes:
            for pkg in missing_packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
            # Neustart des Skripts nach Installation
            os.execv(sys.executable, [sys.executable] + sys.argv)
            return True
    return False

# ===================== GLOBALE SOUND-SICHERHEIT=====================
import glob
import os
import platform
import shutil
import subprocess

# 'pwd' nur unter Linux importieren, um den Windows-Fehler zu verhindern
if platform.system() == "Linux":
    import pwd
else:
    pwd = None

HAS_PAPLAY = shutil.which("paplay") is not None


def safe_play(sound_name):
    if platform.system() != "Linux" or pwd is None:
        return

    s_path = f"/usr/share/sounds/freedesktop/stereo/{sound_name}"

    if not (HAS_PAPLAY and os.path.exists(s_path)):
        return

    try:
        # Normaler Benutzer
        if os.geteuid() != 0:
            subprocess.Popen(["paplay", s_path])
            return

        # Als Root -> aktiven Desktop-Benutzer suchen
        for runtime in glob.glob("/run/user/*"):
            uid_str = os.path.basename(runtime)
            if not uid_str.isdigit():
                continue

            uid = int(uid_str)

            # Systembenutzer überspringen
            if uid < 1000:
                continue

            try:
                # Holt den Benutzernamen (fängt KeyError ab, falls UID ungültig ist)
                user = pwd.getpwuid(uid).pw_name
            except KeyError:
                continue  # Überspringen, falls der Benutzer nicht (mehr) existiert

            env = os.environ.copy()
            env["XDG_RUNTIME_DIR"] = runtime

            subprocess.Popen(
                ["runuser", "-u", user, "--", "paplay", s_path],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

    except Exception as e:
        print("safe_play:", e)

import os
import shutil
import platform
import subprocess
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal

class S3InstallWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, base_target_dir):
        super().__init__()
        self.base_target_dir = os.path.normpath(base_target_dir)

    def run(self):
        temp_clone = None
        proj_name = "S3 Standard"
        sub_folder = "s3"
        repo_url = "https://github.com/gorgone/s3_releases"
        
        try:
            final_destination = os.path.join(self.base_target_dir, sub_folder)
            temp_clone = tempfile.mkdtemp(prefix="s3_standard_clone_")

            # 1. Git Clone
            is_win = platform.system() == "Windows"
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, temp_clone],
                shell=False
            )

            # 2. .git Ordner bereinigen (Windows Fix)
            git_dir = os.path.join(temp_clone, ".git")
            if os.path.exists(git_dir):
                if is_win:
                    subprocess.run(['attrib', '-R', os.path.join(git_dir, '*'), '/S', '/D'], 
                                   shell=False, capture_output=True)
                shutil.rmtree(git_dir, ignore_errors=True)

            # 3. Zielordner erstellen und kopieren
            os.makedirs(final_destination, exist_ok=True)
            for item in os.listdir(temp_clone):
                s = os.path.join(temp_clone, item)
                d = os.path.join(final_destination, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # 4. Linux Rechte setzen
            if platform.system() == "Linux":
                try:
                    subprocess.call(["chmod", "-R", "755", final_destination])
                except:
                    pass

            self.finished_signal.emit(True, f"{proj_name} erfolgreich in '{sub_folder}' installiert!")

        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg or "[Errno 13]" in error_msg:
                error_msg += "\n\nTipp: Starten Sie das Programm als Admin oder wählen Sie einen anderen Installationsort."
            self.finished_signal.emit(False, f"{proj_name} Fehler: {error_msg}")

        finally:
            if temp_clone and os.path.exists(temp_clone):
                shutil.rmtree(temp_clone, ignore_errors=True)

import os
import shutil
import platform
import subprocess
import tempfile
import time
from PyQt6.QtCore import QThread, pyqtSignal

class NcamBonecrewInstallWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, base_target_dir):
        super().__init__()
        self.base_target_dir = os.path.normpath(base_target_dir)

    def run(self):
        temp_clone = None
        proj_name = "NCam Bonecrew"
        sub_folder = "s3_ncam_bonecrew"
        repo_url = "https://github.com/speedy005/s3_ncam_bonecrew_test"
        
        try:
            final_destination = os.path.join(self.base_target_dir, sub_folder)
            temp_clone = tempfile.mkdtemp(prefix="s3_ncam_clone_")
            
            time.sleep(0.5)
            is_win = platform.system() == "Windows"
            
            # WINDOWS-FIX: Wir deaktivieren den NTFS-Pfadschutz für diesen Klon-Vorgang.
            # Dadurch ignoriert Git die Logdateien mit ":" im Namen, anstatt abzubrechen.
            cmd = [
                "git", 
                "-c", "credential.helper=", 
                "-c", "core.protectNTFS=false", 
                "clone", 
                "--depth", "1", 
                repo_url, 
                temp_clone
            ]
            
            result = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                text=True
            )
            
            # Ein Rückkehrwert von 0 ist Erfolg. Unter Windows kann Git hier 
            # trotz der Warnung "Clone succeeded" mit Code 128 (oder ungleich 0) abbrechen.
            # Deshalb prüfen wir, ob die wichtige Hauptdatei 's3' trotzdem erzeugt wurde.
            if result.returncode != 0 and not os.path.exists(os.path.join(temp_clone, "s3")):
                git_err = result.stderr.strip() if result.stderr else f"Exit-Code {result.returncode}"
                raise Exception(f"Git-Fehler: {git_err}")

            # 2. .git Ordner bereinigen (Windows Fix)
            git_dir = os.path.join(temp_clone, ".git")
            if os.path.exists(git_dir):
                if is_win:
                    subprocess.run(['attrib', '-R', os.path.join(git_dir, '*'), '/S', '/D'], 
                                   shell=False, capture_output=True)
                shutil.rmtree(git_dir, ignore_errors=True)

            # 3. Zielordner erstellen und kopieren
            os.makedirs(final_destination, exist_ok=True)
            for item in os.listdir(temp_clone):
                s = os.path.join(temp_clone, item)
                d = os.path.join(final_destination, item)
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # 4. Linux Rechte setzen
            if platform.system() == "Linux":
                try:
                    subprocess.call(["chmod", "-R", "755", final_destination])
                except:
                    pass

            self.finished_signal.emit(True, f"{proj_name} erfolgreich in '{sub_folder}' installiert!")

        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg or "[Errno 13]" in error_msg:
                error_msg += "\n\nTipp: Starten Sie das Programm als Admin oder wählen Sie einen anderen Installationsort."
            
            self.finished_signal.emit(False, f"{proj_name} Fehler:\n{error_msg}")

        finally:
            if temp_clone and os.path.exists(temp_clone):
                shutil.rmtree(temp_clone, ignore_errors=True)

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QApplication
import os, platform, shutil, subprocess, tempfile
import os, shutil, platform, subprocess, tempfile, re
from PyQt6.QtCore import QThread, pyqtSignal
import os, shutil, platform, subprocess, tempfile, re

class S4InstallWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, base_target_dir):
        super().__init__()
        # Das ist der vom User gewählte Basis-Pfad (z.B. C:\opt oder /opt)
        self.base_target_dir = os.path.normpath(base_target_dir)

    def run(self):
        temp_clone = None
        proj_name = "SimpleBuild 4"
        sub_folder = "simplebuild4"
        repo_url = "https://git.streamboard.tv/common/simplebuild4.git"
        
        try:
            # 1. Zielverzeichnis festlegen
            final_destination = os.path.join(self.base_target_dir, sub_folder)

            # 2. Temporärer Clone im Benutzer-TEMP
            temp_clone = tempfile.mkdtemp(prefix="s4_clone_gen_")

            # 3. Git Clone mit --depth 1
            is_win = platform.system() == "Windows"
            subprocess.check_call(
                ["git", "clone", "--depth", "1", repo_url, temp_clone],
                shell=False
            )

            # 4. FIX FÜR PERMISSION DENIED (Windows):
            git_dir = os.path.join(temp_clone, ".git")
            if os.path.exists(git_dir):
                if is_win:
                    subprocess.run(['attrib', '-R', os.path.join(git_dir, '*'), '/S', '/D'], 
                                   shell=False, capture_output=True)
                shutil.rmtree(git_dir, ignore_errors=True)

            # 5. Ziel-Unterordner erstellen
            os.makedirs(final_destination, exist_ok=True)

            # 6. Inhalte aus dem Temp-Clone kopieren
            for item in os.listdir(temp_clone):
                s = os.path.join(temp_clone, item)
                d = os.path.join(final_destination, item)
                
                if os.path.isdir(s):
                    shutil.copytree(s, d, dirs_exist_ok=True)
                else:
                    shutil.copy2(s, d)

            # 7. Linux Rechte setzen
            if platform.system() == "Linux":
                try:
                    subprocess.call(["chmod", "-R", "755", final_destination])
                except:
                    pass

            self.finished_signal.emit(True, f"{proj_name} erfolgreich in '{sub_folder}' installiert!")

        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg or "[Errno 13]" in error_msg:
                error_msg += "\n\nTipp: Starten Sie das Programm als Admin oder wählen Sie einen anderen Installationsort."
            
            self.finished_signal.emit(False, f"{proj_name} Fehler: {error_msg}")

        finally:
            if temp_clone and os.path.exists(temp_clone):
                shutil.rmtree(temp_clone, ignore_errors=True)
# ===================== VERSION HANDLING (Optimiert) =====================
try:
    from packaging.version import Version, InvalidVersion
except (ImportError, ModuleNotFoundError):
    class Version:
        def __init__(self, vstring):
            # Extrahiert Versionen wie 'v1.2.3' -> [1, 2, 3]
            cleaned = "".join(re.findall(r'[0-9.]', str(vstring)))
            self.v = [int(x) for x in cleaned.split(".") if x.isdigit()]

        def __gt__(self, other): return self.v > other.v
        def __lt__(self, other): return self.v < other.v
        def __ge__(self, other): return self.v >= other.v
        def __le__(self, other): return self.v <= other.v
        def __eq__(self, other): return self.v == other.v

    class InvalidVersion(Exception):
        pass

# ===================== ENV SETUP =====================
# Git Fehler unterdrücken
if platform.system() == "Windows":
    os.environ["GIT_REDIRECT_STDERR"] = "2>nul"
else:
    os.environ["GIT_REDIRECT_STDERR"] = "2>/dev/null"
# ===================== SCRIPT DIR =====================
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

def ensure_executable_self():
    """Setzt Ausführungsrechte für das eigene Skript (Linux/Unix)."""
    try:
        st = os.stat(__file__)
        if not (st.st_mode & stat.S_IXUSR):
            os.chmod(__file__, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except Exception as e:
        print(f"[WARN] Konnte Rechte nicht setzen: {e}")

# ===================== ZEIT =====================

"""OSCam Patch Manager module fragment: Dialogs, task helpers, clock, and splash screen."""

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

from bootstrap import fix_windows_path
from patch_format import load_github_config, save_github_config
from translations import TEXTS

class GithubConfigDialog(QDialog):
    """Dialog for entering GitHub credentials - Absturzsicher"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Sprache sicher ermitteln
        self.lang = getattr(parent, "LANG", globals().get("LANG", "de"))

        # Titel sicher setzen (Fallback falls Key fehlt)
        title = TEXTS.get(self.lang, {}).get("github_dialog_title", "GitHub Config")
        self.setMinimumWidth(1100)  # Erhöht die Breite, damit Deutsch reinpasst
        self.resize(1200, 800)

        layout = QFormLayout(self)

        # Eingabefelder initialisieren
        self.patch_repo = QLineEdit()
        self.patch_branch = QLineEdit("master")
        self.emu_repo = QLineEdit()
        self.emu_branch = QLineEdit("master")
        self.username = QLineEdit()
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.user_name = QLineEdit("speedy005")
        self.user_email = QLineEdit("patch@oscam.local")

        # Bestehende Konfiguration laden
        try:
            cfg = load_github_config()
            self.patch_repo.setText(cfg.get("repo_url", ""))
            self.patch_branch.setText(cfg.get("branch", "master"))
            self.emu_repo.setText(cfg.get("emu_repo_url", ""))
            self.emu_branch.setText(cfg.get("emu_branch", "master"))
            self.username.setText(cfg.get("username", ""))
            self.token.setText(cfg.get("token", ""))
            self.user_name.setText(cfg.get("user_name", "speedy005"))
            self.user_email.setText(cfg.get("user_email", "patch@oscam.local"))
        except Exception as e:
            print(f"Fehler beim Laden der GitHub-Config: {e}")

        # Hilfsfunktion für sichere Texte
        def get_t(key, default):
            return TEXTS.get(self.lang, {}).get(key, default)

        # Layout Labels + Felder (Kein KeyError mehr möglich)
        layout.addRow(get_t("patch_repo_label", "Patch Repo:"), self.patch_repo)
        layout.addRow(get_t("patch_branch_label", "Patch Branch:"), self.patch_branch)
        layout.addRow(get_t("emu_repo_label", "EMU Repo:"), self.emu_repo)
        layout.addRow(get_t("emu_branch_label", "EMU Branch:"), self.emu_branch)
        layout.addRow(get_t("github_username_label", "GitHub User:"), self.username)
        layout.addRow(get_t("github_token_label", "GitHub Token:"), self.token)
        layout.addRow(get_t("github_user_name_label", "Git Name:"), self.user_name)
        layout.addRow(get_t("github_user_email_label", "Git Email:"), self.user_email)

        # Buttons erstellen
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)

        if self.save_button:
            self.save_button.setText(get_t("save", "Speichern"))
        if self.cancel_button:
            self.cancel_button.setText(get_t("cancel", "Abbrechen"))

        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        """Speichert die eingegebenen Daten"""
        cfg = {
            "repo_url": self.patch_repo.text().strip(),
            "branch": self.patch_branch.text().strip(),
            "emu_repo_url": self.emu_repo.text().strip(),
            "emu_branch": self.emu_branch.text().strip(),
            "username": self.username.text().strip(),
            "token": self.token.text().strip(),
            "user_name": self.user_name.text().strip(),
            "user_email": self.user_email.text().strip(),
        }
        try:
            save_github_config(cfg)
            self.accept()
        except Exception as e:
            print(f"Fehler beim Speichern der GitHub-Config: {e}")
            self.reject()

from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize, QThread, pyqtSignal, QUrl

class TaskWorker(QThread):
    progress = pyqtSignal(int)
    info = pyqtSignal(str, str)
    finished = pyqtSignal(object)

    def __init__(self, target_fn, *args, **kwargs):
        super().__init__()
        self.target_fn = target_fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            # Übergibt den progress-Slot als 'progress_callback' an deine Funktionen
            result = self.target_fn(
                *self.args, progress_callback=self.progress.emit, **self.kwargs
            )
            self.finished.emit(result)
        except Exception as e:
            self.info.emit(f"Fehler: {str(e)}", "error")
            self.progress.emit(100)

# =====================
# PATCH MANAGER GUI
# =====================
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QSizePolicy,
    QFrame,
    QProgressBar,
    QSlider,
)

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QTime, Qt, QPoint
from PyQt6.QtGui import QPainter, QPolygon, QColor

class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)
        self.setMinimumSize(100, 100)

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QPolygon
        from PyQt6.QtCore import Qt, QPoint, QTime

        side = min(self.width(), self.height())
        time = QTime.currentTime()

        # --- MATRIX CHECK ---
        # Wir schauen im Hauptfenster nach, ob der Modus aktiv ist
        main_win = self.window()
        is_matrix = (
            getattr(main_win, "current_config", {}).get("theme_mode") == "matrix"
        )

        # Farben definieren
        color_accent = (
            QColor("#00FF41") if is_matrix else QColor("#EAFF00")
        )  # Grün oder Gelb
        color_bg = (
            QColor("#000000") if is_matrix else QColor("#1A1A1A")
        )  # Schwarz oder Dunkelgrau
        color_hour = (
            QColor("#008F11") if is_matrix else QColor(255, 0, 0)
        )  # Dunkelgrün oder Rot
        color_min = (
            QColor("#00FF41") if is_matrix else QColor(200, 200, 200)
        )  # Hellgrün oder Grau

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # In die Mitte des Widgets schieben
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        # --- Zifferblatt (Hintergrund) ---
        painter.setPen(color_accent)
        painter.setBrush(color_bg)
        painter.drawEllipse(-95, -95, 190, 190)

        # --- Markierungen (Stunden) ---
        painter.setPen(color_accent)
        for i in range(12):
            painter.drawLine(80, 0, 90, 0)
            painter.rotate(30.0)

        # --- Stundenzeiger ---
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color_hour)
        painter.save()
        painter.rotate(30.0 * ((time.hour() + time.minute() / 60.0)))
        painter.drawConvexPolygon(
            QPolygon([QPoint(6, 10), QPoint(-6, 10), QPoint(0, -50)])
        )
        painter.restore()

        # --- Minutenzeiger ---
        painter.setBrush(color_min)
        painter.save()
        painter.rotate(6.0 * (time.minute() + time.second() / 60.0))
        painter.drawConvexPolygon(
            QPolygon([QPoint(4, 10), QPoint(-4, 10), QPoint(0, -80)])
        )
        painter.restore()

        # --- Sekundenzeiger ---
        painter.setBrush(color_accent)
        painter.save()
        painter.rotate(6.0 * time.second())
        painter.drawConvexPolygon(
            QPolygon([QPoint(2, 10), QPoint(-2, 10), QPoint(0, -90)])
        )
        painter.restore()

        # Mittelpunkt abdecken
        painter.setBrush(color_accent)
        painter.drawEllipse(-5, -5, 10, 10)

# ---------------- MATRIX CINEMATIC SPLASH ----------------
from PyQt6.QtWidgets import QWidget, QLabel, QProgressBar, QVBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import os, random, platform, subprocess

import os, sys, platform, subprocess, locale, importlib.util, threading, shutil, ctypes, random
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QColor

# =============================================================================
# 1. WINDOWS SYSTEM UTILS
# =============================================================================
# is_admin() und verify_tools() sind weiter oben zentral definiert.
# Keine zweite Implementierung: die doppelte Version war unter Linux
# insbesondere wegen winsound() problematisch.

import sys
import random
import platform
import threading
import subprocess

from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QEasingCurve,
    QPropertyAnimation, pyqtProperty
)
from PyQt6.QtGui import QFont, QPainter, QColor, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel,
    QProgressBar, QHBoxLayout, QApplication
)

# Windows sound
if platform.system() == "Windows":
    import winsound

class CinematicMatrixSplash(QWidget):
    finished = pyqtSignal()

    def __init__(self, duration=4000):
        super().__init__()
        
        # Sicherheits-Fallback für fehlerhafte duration-Werte (Verhindert ZeroDivisionError)
        if not duration or duration <= 0:
            duration = 4000

        # Systemspezifische Imports absichern
        import platform
        import random

        self.is_closing = False
        self.os_type = platform.system()

        # Animation state
        self._corner_factor = 0.0
        self.flash_alpha = 0
        self.prog = 0

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(int(screen.width() * 0.6), int(screen.height() * 0.6))
        self.move(screen.center() - self.rect().center())

        # Matrix config
        self.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=-"
        self.columns = self.width() // 15
        self.drops = [random.randint(-20, 0) for _ in range(self.columns)]

        # Logo Ascii Art
        self.logo_text = [
            r" ◢◤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◥◣ ",
            r" █               _______  _______  _______  _______  __   __              █ ",
            r" █             |       ||       ||   _   ||       ||  |_|  |              █ ",
            r" █             |   _   ||  _____||  |_|  ||       ||       |              █ ",
            r" █             |  | |  || |_____ |       ||       ||       |              █ ",
            r" █             |  |_|  ||_____  ||       ||      _||       |              █ ",
            r" █             |       | _____| ||   _   ||     |_ | ||_|| |              █ ",
            r" █             |_______||_______||__| |__||_______||_|   |_|              █ ",
            r" █                                                                        █ ",
            r" █               _______  _______  _______  _______  __   __              █ ",
            r" █             |       ||   _   ||       ||       ||  | |  |              █ ",
            r" █             |    ___||  |_|  ||_     _||       ||  |_|  |              █ ",
            r" █             |   |___ |       |  |   |  |       ||       |              █ ",
            r" █             |    ___||       |  |   |  |      _||       |              █ ",
            r" █             |   |    |   _   |  |   |  |     |_ | ||_|| |              █ ",
            r" █             |___|    |__| |__|  |___|  |_______||_|   |_|              █ ",
            r" █                                                                        █ ",
            r" █   __   __  _______  __    _  _______  _______  _______  ______         █ ",
            r" █  |  |_|  ||   _   ||  |  | ||   _   ||     __||    ___||    _ |        █ ",
            r" █  |       ||  |_|  ||   |_| ||  |_|  ||    |  ||   |___ |   | ||        █ ",
            r" █  |       ||       ||       ||       ||    |  ||    ___||   |_||_       █ ",
            r" █  |       ||       ||  _    ||       ||    |  ||   |___ |    __  |      █ ",
            r" █  | ||_|| ||   _   || | |   ||   _   ||    |__||   |___ |   |  | |      █ ",
            r" █  |_|   |_||__| |__||_|  |__||__| |__||_______||_______||___|  |_|      █ ",
            r" █                                                                        █ ",
            r" █──────────────────[ SYSTEM: NEURAL_LINK OPERATIONAL ]───────────────────█ ",
            r" █                   >> OSCAM EMU PATCH MANAGER v1.2.6  <<               █ ",
            r" █             >> CODENAME: Speedy_Oscam-_Patch_Manager 2026 <<           █ ",
            r" ◥◣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◢◤ "
        ]

        # Layout setup
        main = QGridLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        self.ui = QWidget()
        self.ui.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 15, 8, 230);
                border: 1px solid rgba(0,255,65,120);
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self.ui)

        # Header component
        header = QHBoxLayout()
        self.title = QLabel("[ CORE BOOT ]")
        self.title.setStyleSheet("color:#00FF41;")

        self.host = QLabel(f"OS: {self.os_type}")
        self.host.setStyleSheet("color:#00AA44;")

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.host)
        layout.addLayout(header)
        layout.addStretch()

        # Logo widget
        self.lbl_logo = QLabel("\n".join(self.logo_text))
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("color:#00FF41;")
        self.lbl_logo.setFont(QFont("Consolas", 10))
        layout.addWidget(self.lbl_logo)
        layout.addStretch()

        # Status text widget
        self.status = QLabel("INITIALIZING...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("color:#00FF41;")
        layout.addWidget(self.status)

                # Progress bar component (Matrix Cyberpunk Redesign)
        self.pbar = QProgressBar()
        self.pbar.setMaximum(100)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(0, 255, 65, 180);
                border-radius: 3px;
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                                   stop:0 #000803, stop:1 #001205);
                height: 10px;
                /* Subtiler Matrix-Glow-Effekt nach unten */
                margin-bottom: 5px;
            }
            QProgressBar::chunk {
                /* Neongrüner High-Tech-Farbverlauf mit Digital-Glow */
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                   stop:0 #008f11, 
                                                   stop:0.5 #00FF41, 
                                                   stop:1 #39FF14);
                /* Erzeugt einen abgehackten, digitalen Block-Look */
                width: 4px;
                margin: 0.5px;
                border-radius: 1px;
            }
        """)
        layout.addWidget(self.pbar)


        main.addWidget(self.ui, 0, 0)

        # Active engine timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)

        self.timer_prog = QTimer(self)
        self.timer_prog.timeout.connect(self.update_progress)
        self.timer_prog.start(duration // 100)

        self.timer_glitch = QTimer(self)
        self.timer_glitch.timeout.connect(self.glitch)
        self.timer_glitch.start(120)

        # Geometric corner vector animation
        self.anim = QPropertyAnimation(self, b"corner_factor")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

        # Überprüfungen nach dem Rendern triggern
        QTimer.singleShot(400, self.run_bootstrap_checks)

    # ---------------- AUTOMATISCHER HINTERGRUND-CHECK IM SPLASH SCREEN ----------------
        
    def run_bootstrap_checks(self):
        """Überprüft und installiert Git Core sowie alle Python-Pakete im Splash-Thread."""
        import sys
        import shutil
        import subprocess
        import platform
        import os
        import time
        import importlib.util
        import locale

        # ---------------------------------------------------------
        # 1. SYSTEMSPRACHE ERMITTELN
        # ---------------------------------------------------------
        # locale.getdefaultlocale() ist ab Python 3.11 deprecated
        # und wird in Python 3.15 entfernt.
        try:
            sys_lang = locale.getlocale()[0] or ""
            is_german = sys_lang.lower().startswith("de")
        except Exception:
            is_german = False

        anything_installed = False

        # ---------------------------------------------------------
        # 2. GIT PRÜFEN / INSTALLIEREN
        # ---------------------------------------------------------
        if platform.system() == "Windows" and not shutil.which("git"):
            anything_installed = True

            msg_git = (
                ">> [KRITISCH] GIT CORE FEHLT! STARTE WINGET HINTERGRUND-INSTALLATION... <<"
                if is_german else
                ">> [CRITICAL] GIT CORE MISSING! RUNNING WINGET SILENT DEPLOYMENT... <<"
            )

            self.status.setText(msg_git)
            self.status.setStyleSheet("color: #FF0055; font-weight: bold;")
            QApplication.processEvents()

            winget_cmd = [
                "winget",
                "install",
                "--id",
                "Git.Git",
                "--exact",
                "--silent",
                "--force",
                "--disable-interactivity",
                "--accept-source-agreements",
                "--accept-package-agreements"
            ]

            try:
                result = subprocess.run(
                    winget_cmd,
                    capture_output=True,
                    text=True,
                    check=False
                )

                # -------------------------------------------------
                # GIT-PFAD NACH DER INSTALLATION AKTUALISIEREN
                # -------------------------------------------------
                possible_git_paths = [
                    r"C:\Program Files\Git\cmd",
                    r"C:\Program Files\Git\bin",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\cmd"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Git\bin"),
                ]

                for git_path in possible_git_paths:
                    if os.path.isdir(git_path):
                        if git_path not in os.environ.get("PATH", ""):
                            os.environ["PATH"] = (
                                git_path
                                + os.pathsep
                                + os.environ.get("PATH", "")
                            )

                # Vorhandene Windows-PATH-Hilfsfunktion benutzen
                try:
                    if "fix_windows_path" in globals():
                        fix_windows_path()
                except Exception:
                    pass

                # -------------------------------------------------
                # GIT TATSÄCHLICH TESTEN
                # -------------------------------------------------
                git_executable = shutil.which("git")

                if git_executable:
                    msg_git_ok = (
                        ">> [✓] GIT CORE ERFOLGREICH INSTALLIERT! SYSTEMPFAD AKTUALISIERT. <<"
                        if is_german else
                        ">> [✓] GIT CORE DEPLOYED SUCCESSFULLY! ENVIRONMENT REFRESHED. <<"
                    )

                    self.status.setText(msg_git_ok)
                    self.status.setStyleSheet("color: #00FF41;")
                    QApplication.processEvents()
                    time.sleep(1.5)

                else:
                    # Winget kann erfolgreich beendet sein, obwohl
                    # Git für den aktuellen Prozess noch nicht verfügbar ist.
                    stderr = (result.stderr or "").strip()
                    stdout = (result.stdout or "").strip()

                    details = stderr or stdout or "Git konnte nach der Installation nicht gefunden werden."

                    self.status.setText(
                        f">> [!] GIT NICHT VERFÜGBAR: {details[:80]} <<"
                    )
                    self.status.setStyleSheet(
                        "color: #FF0055; font-weight: bold;"
                    )
                    QApplication.processEvents()
                    time.sleep(3)

            except FileNotFoundError:
                self.status.setText(
                    ">> [!] WINGET NICHT GEFUNDEN. GIT MUSS MANUELL INSTALLIERT WERDEN. <<"
                )
                self.status.setStyleSheet(
                    "color: #FF0055; font-weight: bold;"
                )
                QApplication.processEvents()
                time.sleep(3)

            except Exception as e:
                self.status.setText(
                    f">> [!] INSTALLATION FAILED: {str(e)[:80]} <<"
                )
                self.status.setStyleSheet(
                    "color: #FF0055; font-weight: bold;"
                )
                QApplication.processEvents()
                time.sleep(3)

        # ---------------------------------------------------------
        # 3. PYTHON-ABHÄNGIGKEITEN PRÜFEN
        # ---------------------------------------------------------
        msg_scan = (
            "PROGNOSTIZIERE PYTHON MODUL-ABHÄNGIGKEITEN..."
            if is_german else
            "SCANNING PYTHON MODULE DEPENDENCIES..."
        )

        self.status.setText(msg_scan)
        self.status.setStyleSheet("color: #00FF41;")
        QApplication.processEvents()

        missing_pkgs = []

        pkgs_to_check = globals().get(
            "REQUIRED_PACKAGES",
            [
                "PyQt6",
                "requests",
                "packaging",
                "psutil",
                "urllib3"
            ]
         )

        # ---------------------------------------------------------
        # 4. FEHLENDE MODULE ERMITTELN
        # ---------------------------------------------------------
        for package in pkgs_to_check:
            try:
                if importlib.util.find_spec(package) is None:
                    missing_pkgs.append(package)
            except Exception:
                missing_pkgs.append(package)

        # ---------------------------------------------------------
        # 5. FEHLENDE PAKETE INSTALLIEREN
        # ---------------------------------------------------------
        if missing_pkgs:
            anything_installed = True

            msg_pip = (
                f">> PIP INSTALLATION LÄUFT FÜR: {', '.join(missing_pkgs)} <<"
                if is_german else
                f">> PIP DEPLOYMENT RUNNING FOR: {', '.join(missing_pkgs)} <<"
            )

            self.status.setText(msg_pip)
            self.status.setStyleSheet("color: #00D4FF;")
            QApplication.processEvents()

            try:
                # -------------------------------------------------
                # PIP AKTUALISIEREN
                # -------------------------------------------------
                pip_upgrade = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "pip"
                    ],
                    capture_output=True,
                    text=True,
                    check=False
                )

                # -------------------------------------------------
                # EINZELNE PAKETE INSTALLIEREN
                # -------------------------------------------------
                failed_packages = []

                for package in missing_pkgs:
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            package
                        ],
                        capture_output=True,
                        text=True,
                        check=False
                    )

                    if result.returncode != 0:
                        failed_packages.append(package)

                # -------------------------------------------------
                # INSTALLATION FEHLGESCHLAGEN
                # -------------------------------------------------
                if failed_packages:
                    failed_text = ", ".join(failed_packages)

                    self.status.setText(
                        f">> [!] PIP FEHLER: {failed_text} <<"
                    )
                    self.status.setStyleSheet(
                        "color: #FF0055; font-weight: bold;"
                    )
                    QApplication.processEvents()
                    time.sleep(3)

                    # Keine Endlosschleife durch automatischen Neustart
                    self.finalize_boot(is_german)
                    return

                # -------------------------------------------------
                # INSTALLATION ERFOLGREICH
                # -------------------------------------------------
                msg_reload = (
                    ">> INSTALLATION BEENDET. START KERNEL-HOT-RELOAD... <<"
                    if is_german else
                    ">> MODULE DEPLOYMENT COMPLETE. ENVIRONMENT HOT-RELOAD IN PROGRESS... <<"
                )

                self.status.setText(msg_reload)
                self.status.setStyleSheet("color: #00FF41;")
                QApplication.processEvents()

                time.sleep(1)

                # -------------------------------------------------
                # PROGRAMM MIT NEUEM PYTHON-ENVIRONMENT NEUSTARTEN
                # -------------------------------------------------
                os.execv(
                    sys.executable,
                    [sys.executable] + sys.argv
                )

                return

            except Exception as e:
                self.status.setText(
                    f"DEPENDENCY CONFLICT DETECTED: {str(e)[:80]}"
                )
                self.status.setStyleSheet(
                    "color: #FF0055; font-weight: bold;"
                )
                QApplication.processEvents()
                time.sleep(2)

        # ---------------------------------------------------------
        # 6. BOOTSTRAP ABGESCHLOSSEN
        # ---------------------------------------------------------
        if not anything_installed:

            # Den originalen, langsamen Balken-Timer stoppen
            if hasattr(self, "timer_prog"):
                try:
                    self.timer_prog.stop()
                except Exception:
                    pass

            msg_finishing = (
                "COMPLETING CORE SYSTEM INTEGRATION..."
                if not is_german else
                "PROZESSIERE SYSTEM-INTEGRATION..."
            )

            self.status.setText(msg_finishing)
            self.status.setStyleSheet("color: #00FF41;")
            QApplication.processEvents()

            # -----------------------------------------------------
            # PROGRESSBAR FLÜSSIG AUF 100% SETZEN
            # -----------------------------------------------------
            current_progress = getattr(self, "prog", 0)

            while current_progress < 100:
                current_progress += 2

                if current_progress > 100:
                    current_progress = 100

                self.prog = current_progress

                self.pbar.setValue(current_progress)

                # GUI sofort aktualisieren
                QApplication.processEvents()

                time.sleep(0.01)

            # -----------------------------------------------------
            # ABSCHLUSSMELDUNG
            # -----------------------------------------------------
            msg_verified = (
                ">> [SYSTEM] ALLE ABHÄNGIGKEITEN ÜBERPRÜFT. "
                "KEINE AKTION ERFORDERLICH. <<"
                if is_german else
                ">> [SYSTEM] ALL DEPENDENCIES VERIFIED. "
                "NO ACTION REQUIRED. <<"
            )
 
            self.status.setText(msg_verified)
            self.status.setStyleSheet(
            "color: #00FF41; font-weight: bold;"
            )

            QApplication.processEvents()

            # -----------------------------------------------------
            # 2,5 SEKUNDEN HALTEN, DANN WEITER
            # -----------------------------------------------------
            QTimer.singleShot(
                2500,
                lambda: self.finalize_boot(is_german)
            )

        else:
            self.finalize_boot(is_german)

    # WICHTIG: Diese Methode muss exakt 4 Leerzeichen eingerückt sein (so wie run_bootstrap_checks)!
    def finalize_boot(self, is_german=False):
        """Beendet den Ladevorgang sauber nach Ablauf der Wartezeiten."""
        msg_release = (
            "NEURAL LINK BEREIT. STARTE HAUPT-BENUTZEROBERFLÄCHE..."
            if is_german else
            "NEURAL LINK OPERATIONAL. RELEASING MAIN GUI INTERFACE..."
        )
        self.status.setText(msg_release)
        self.status.setStyleSheet("color: #00FF41;")
        QTimer.singleShot(800, self.finish)
    # ---------------- BEREITS EXISTIERENDE SYSTEMPROPERTY-FUNKTIONEN ----------------
    @pyqtProperty(float)
    def corner_factor(self):
        return self._corner_factor

    @corner_factor.setter
    def corner_factor(self, v):
        self._corner_factor = v
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 220))
        p.setFont(QFont("Consolas", 10))

        # MATRIX ANIMATION MATRIX RAIN ENGINE
        for i in range(len(self.drops)):
            x = i * 15
            y = self.drops[i] * 15
            char = random.choice(self.chars)

            if 0 < y < self.height():
                p.setPen(QColor(0, 255, 65, 200))
                p.drawText(x, y, char)

            self.drops[i] += 1
            if y > self.height() or random.random() > 0.98:
                self.drops[i] = random.randint(-10, 0)

        # CHROMATIC CORNERS
        w, h = self.width(), self.height()
        off = int((1 - self._corner_factor) * 80)
        pen = QPen(QColor(0, 255, 65, 200))
        pen.setWidth(3)
        p.setPen(pen)

        L = 35
        p.drawLine(off, off, off + L, off)
        p.drawLine(off, off, off, off + L)
        p.drawLine(w - off, off, w - off - L, off)
        p.drawLine(w - off, off, w - off, off + L)
        p.drawLine(off, h - off, off + L, h - off)
        p.drawLine(off, h - off, off, h - off - L)
        p.drawLine(w - off, h - off, w - off - L, h - off)
        p.drawLine(w - off, h - off, w - off, h - off - L)

        if self.flash_alpha > 0:
            p.setPen(QPen(QColor(255, 255, 255, self.flash_alpha)))
            p.drawRect(5, 5, w - 10, h - 10)

    def glitch(self):
        if self.is_closing:
            return
        if random.random() > 0.9:
            self.lbl_logo.setStyleSheet("color:#00FFFF;")
            self.play_sound("glitch")
        else:
            self.lbl_logo.setStyleSheet("color:#00FF41;")

    def update_progress(self):
        if self.prog < 100:
            self.prog += 1
            self.pbar.setValue(self.prog)

    def play_sound(self, mode):
        def run():
            try:
                if self.os_type == "Windows":
                    if mode == "glitch":
                        winsound.Beep(random.randint(800, 2000), 20)
                    elif mode == "end":
                        winsound.MessageBeep()
                elif self.os_type in ["Linux", "Darwin"]:
                    print("\a", end="")
            except:
                pass
        threading.Thread(target=run, daemon=True).start()

    def finish(self):
        self.is_closing = True
        self.play_sound("end")
        QTimer.singleShot(300, lambda: (self.finished.emit(), self.close()))

# ===================== CLEAN PATCH FOLDER =====================


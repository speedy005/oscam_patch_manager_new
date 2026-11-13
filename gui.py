"""OSCam Patch Manager module fragment: Main Patch Manager GUI."""
from PyQt6.QtCore import QEvent, QObject, QSettings
from PyQt6.QtWidgets import (
    QApplication,
    QPushButton,
    QToolButton,
    QAbstractButton,
)
import math
import os
import struct
import tempfile
import wave
import shlex
from PyQt6.QtCore import QThread, pyqtSignal
from weather import open_weather_window


def _open_cyber_center(gui):
    from cyber_center import CyberCenterDialog

    colors = getattr(gui, "current_diff_colors", None)
    if not isinstance(colors, dict):
        colors = globals().get("current_diff_colors", {})

    dialog = CyberCenterDialog(
        gui,
        language=getattr(gui, "LANG", "de"),
        colors=colors,
    )
    dialog.exec()



def _open_patch_diff_viewer(gui):
    from patch_diff_viewer import PatchDiffViewer

    dialog = PatchDiffViewer(
        gui,
        language=getattr(gui, "LANG", "de"),
    )
    dialog.exec()


def _open_achievement_system(gui):
    from achievement_system import AchievementDialog

    dialog = AchievementDialog(
        gui,
        language=getattr(gui, "LANG", "de"),
    )
    dialog.exec()


def _open_ai_assistant(gui):
    from ai_assistant import AIAssistantDialog

    dialog = AIAssistantDialog(
        gui,
        language=getattr(gui, "LANG", "de"),
    )
    dialog.exec()


from gui_helpers import (
    _PatchCreateBridge,
    _PatchCreateWorker,
    ResponsiveGridReflow,
    ButtonClickSoundFilter,
    SystemSoundManager,
)

_ACTIVE_SOUND_MANAGER = None


def safe_play(filename):
    """Kompatibler Ersatz für workers.safe_play, zentral und plattformneutral."""
    manager = _ACTIVE_SOUND_MANAGER
    if manager is not None:
        return manager.play_legacy_name(filename)
    # Falls vor Erstellung der GUI ein Sound angefordert wird, einfach still bleiben.
    return False


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

from bootstrap import ONLINE_PATCHES, ensure_dependencies, get_setting, save_setting
from config_manager import load_config, save_config
from dialogs_splash import GithubConfigDialog, TaskWorker
from git_manager import find_git_executable, get_oscam_version, git_command, git_commit_id
from github_patch_upload import github_upload_patch_file
from github_repo_upload import github_upload_oscam_emu_folder, run_bash
from patch_format import load_github_config
from patch_operations import backup_old_patch, clean_patch_folder, create_patch, ensure_git_repository, patch_oscam_emu_git
from paths import ALT_PATCH_FILE, APP_VERSION, CONFIG_FILE, OLD_PATCH_DIR, OLD_PATCH_FILE, PATCH_FILE, PATCH_EMU_GIT_DIR, STREAMREPO, STREAM_REPO_CHOICES, TEMP_REPO, get_selected_stream_repo_name, get_selected_stream_repo_url, now
from system_check import SystemCheckWorker
from themes import DIFF_COLORS, current_color_name, current_diff_colors
from translations import LANG, TEXTS
from ui_components import StreamToGui
from workers import NcamBonecrewInstallWorker, OSCamUpdateWorker, S3InstallWorker, S4InstallWorker
from packaging.version import Version

from music_player_mixin import MusicPlayerMixin
from gui_actions import PatchManagerActionsMixin
from gui_git import PatchManagerGitMixin
from gui_installation import PatchManagerInstallationMixin
from gui_layout import PatchManagerLayoutMixin
from gui_logs import PatchManagerLogsMixin
from gui_patch import PatchManagerPatchMixin
from gui_settings import PatchManagerSettingsMixin
from gui_core import PatchManagerCoreMixin


class PatchManagerGUI(
    PatchManagerActionsMixin,
    PatchManagerGitMixin,
    PatchManagerInstallationMixin,
    PatchManagerLayoutMixin,
    PatchManagerLogsMixin,
    PatchManagerPatchMixin,
    PatchManagerSettingsMixin,
    PatchManagerCoreMixin,
    MusicPlayerMixin,
    QWidget,
):
    def __init__(self):
        # 1. IMPORTS & INITIALER SCHUTZ
        from PyQt6.QtGui import QFont, QFontMetrics
        from PyQt6.QtGui import QColor, QFont, QTextCursor, QIcon
        from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize, QUrl
        from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QComboBox
        import subprocess, platform, shutil, os, re, sys

        # Build-Log-Verzeichnis bereits beim Programmstart anlegen. So ist
        # sichtbar, ob genau diese gui.py ausgeführt wird, auch wenn später
        # kein S3/S4/NCam-Terminal gestartet werden kann.
        try:
            self.build_log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "build_logs"
            )
            os.makedirs(self.build_log_dir, exist_ok=True)
        except OSError as log_setup_error:
            self.build_log_dir = None
            print(f"[BUILD-LOG] Verzeichnis konnte nicht angelegt werden: {log_setup_error}")

        # Neue Build-Logs dieser Sitzung auf erfolgreiche Abschlüsse prüfen.
        self._achievement_seen_build_logs = set()
        try:
            if self.build_log_dir and os.path.isdir(self.build_log_dir):
                self._achievement_seen_build_logs = {
                    os.path.abspath(os.path.join(self.build_log_dir, name))
                    for name in os.listdir(self.build_log_dir)
                    if name.lower().endswith(".log")
                }
        except OSError as exc:
            print(f"[ACHIEVEMENT] Log-Baseline fehlgeschlagen: {exc}")

        self._achievement_log_timer = QTimer()
        self._achievement_log_timer.setInterval(1500)
        self._achievement_log_timer.timeout.connect(
            self._check_build_achievement_logs
        )
        self._achievement_log_timer.start()

        self.is_loading = True  # Schutz vor Timer während Setup

        # 2. ATTR-BOOTSTRAP
        self.btn_matrix = None
        self.slider_speed = None
        self.color_box = None
        self.status_leds = []  # System-Status LEDs
        self.user_leds = []  # User-Blink-LEDs
        self.all_buttons = []
        self.option_buttons = {}
        self.buttons = {}

        # Keine feste Revision beim Programmstart.
        # Create Patch verwendet dadurch automatisch den aktuellen
        # Streamboard-HEAD und den aktuellen Stand des gewählten
        # OSCam-Emu-Repositories, solange der Benutzer nichts auswählt.
        self.selected_streamboard_commit = None
        self.selected_emu_commit = None
        self.selected_emu_commit_repo_url = ""
        # Nur Anzeige des zuletzt tatsächlich gebauten Patches.
        # Diese Werte sind KEINE feste Auswahl und werden bei Create Patch
        # nicht als Basis erzwungen.
        self.display_streamboard_commit = None
        self.display_emu_commit = None
        globals()["SELECTED_STREAMBOARD_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT_REPO_URL"] = ""

        self._blink_state = True

        super().__init__()
        self.current_config = self.load_config_from_file()
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = "S3 Simplebuild (Original)"
        self.s3_repo_combo = None
        self.s3_install_worker = None
        self.sound_manager = SystemSoundManager(self, volume=0.45)
        global _ACTIVE_SOUND_MANAGER
        _ACTIVE_SOUND_MANAGER = self.sound_manager
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.sound_manager.shutdown)
        self.sound_manager.play_login()
        # Globalen Klicksound-Filter registrieren
        self.button_click_sound_filter = ButtonClickSoundFilter(
            self.sound_manager,
            self
        )

        QApplication.instance().installEventFilter(
            self.button_click_sound_filter
        )
        # --- TIMER-SEKTION ---
        # 3. INFOSCREEN & REDIRECTOR FIX
        self.current_rev = getattr(
            self, "current_rev", "11943"
        )  # Falls nicht schon gesetzt
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        try:
            self.stdout_redir = StreamToGui()
            self.stdout_redir.callback = lambda msg: self.append_info(
                self.info_text, msg, "info"
            )
            sys.stdout = self.stdout_redir
            self.stderr_redir = StreamToGui()
            self.stderr_redir.callback = lambda msg: self.append_info(
                self.info_text, msg, "error"
            )
            sys.stderr = self.stderr_redir
        except Exception:
            pass

        
        # S3-Repository-Auswahl und Worker initialisieren
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        
        self.current_config = self.load_config_from_file()

        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_install_worker = None

        # Die ComboBox hier erstellen und NICHT wieder auf None setzen.
        self.s3_repo_combo = QComboBox()

        for name, url in self.s3_repository_options.items():
            self.s3_repo_combo.addItem(name, url)

        index = self.s3_repo_combo.findText(self.selected_s3_repository)
        if index >= 0:
            self.s3_repo_combo.setCurrentIndex(index)

        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )


        # ComboBox erst nach der Initialisierung erstellen
        self.s3_repo_combo = QComboBox()

        for name, url in self.s3_repository_options.items():
            self.s3_repo_combo.addItem(name, url)

        index = self.s3_repo_combo.findText(
            self.selected_s3_repository
        )

        if index >= 0:
            self.s3_repo_combo.setCurrentIndex(index)

        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_repo_combo = None
        self.s3_install_worker = None

        ## --- Pfad für Standard S3 ---
        stored_s3 = self.current_config.get("s3_custom_path", "/opt/s3")
        self.S3_PATH = os.path.normpath(stored_s3)

        # --- Pfad für NCam Bonecrew (EIGENE VARIABLE!) ---
        stored_ncam = self.current_config.get(
            "ncam_custom_path", "/opt/s3_ncam_bonecrew_test"
        )
        self.NCAM_PATH = os.path.normpath(stored_ncam)

        # --- NEU: SOFORT-CHECK BEIM START ---
        # Wir triggern die Prüfung kurz nach dem Start, damit der Button
        # von "Install" auf "OK" springt, falls S3 gefunden wurde.
        QTimer.singleShot(100, self.update_ui_texts)

        stored_lang = str(self.current_config.get("language", "de")).lower()
        self.LANG = stored_lang if stored_lang in ["en", "de"] else "de"

        # TEXT muss VOR init_ui() verfügbar sein.
        # init_ui() erzeugt bereits Buttons/Labels und verwendet dafür
        # self.TEXT.get(...). update_language() wird erst nach init_ui()
        # aufgerufen und kann daher nicht die Erstinitialisierung übernehmen.
        self.TEXT = TEXTS.get(
            self.LANG,
            TEXTS.get("en", {})
        )

        self.patch_modifier = self.current_config.get("patch_modifier", "Default")
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.PLUGIN_DIR = self.base_dir  # Plugin-Verzeichnis

        stored_work_dir = self.current_config.get("work_dir", self.base_dir)
        if not isinstance(stored_work_dir, str) or not stored_work_dir.strip():
            stored_work_dir = self.base_dir

        self.WORK_DIR = os.path.normpath(stored_work_dir)
        self.TEMP_REPO = os.path.join(self.base_dir, "streamboard-git")  # Temp-Repo Ordner
        self.PATCH_EMU_GIT_DIR = os.path.join(
            self.base_dir, "oscam-emu-git"
        )  # Emu-Git Ordner
        current_path = self.current_config.get(
            "s3_patch_path", globals().get("OLD_PATCH_DIR", "./")
        )
        self.OLD_PATCH_DIR = os.path.normpath(current_path)
        self.OLD_PATCH_FILE = os.path.join(self.OLD_PATCH_DIR, "oscam-emu.patch")
        self.ALT_PATCH_FILE = os.path.join(self.OLD_PATCH_DIR, "oscam-emu.altpatch")
        # --- Direkt nach ALT_PATCH_FILE einfügen ---
        target_dirs = [
            self.PLUGIN_DIR,
            self.TEMP_REPO,
            self.PATCH_EMU_GIT_DIR,
            self.OLD_PATCH_DIR,
        ]

        for d in target_dirs:
            if d and not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except:
                    pass

        # Basis-Variablen
        self.active_button_key = ""
        self.main_grid_layout = None
        self.latest_version = (
            globals().get("APP_VERSION", "1.0.0").replace("v", "").strip()
        )
        self.BUTTON_RADIUS = 5

        # 5. HAUPT-UI AUFBAUEN
        self.live_indicator = QLabel()
        # Initialer Text
        self.live_indicator.setText(
            "<span style='color:#ff0000;'>●</span> <span style='color:#ffffff;'>LIVE | System Monitor</span>"
        )
        self.live_indicator.setStyleSheet(
            """
            font-weight: bold; 
            font-family: 'Courier New', monospace;
            font-size: 22px;
            background: transparent;
        """
        )

        self.init_ui()
        self._fit_all_button_texts()
        # 6. TIMER VORBEREITEN (Nur für User-LEDs, nicht starten)
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.animate_status_bar)

        # 7. THEME & FARBEN
        saved_color = self.current_config.get("color", "Classics")
        if hasattr(self, "color_box") and self.color_box:
            self.color_box.blockSignals(True)
            index = self.color_box.findText(saved_color)
            if index != -1:
                self.color_box.setCurrentIndex(index)
            self.color_box.blockSignals(False)
            self.color_box.currentIndexChanged.connect(self.change_colors)
        self.color_box.setToolTip(
            "Farbschema der Oberfläche auswählen"
            if str(getattr(self, "LANG", self.cfg.get("language", "de"))).lower() in ("de", "0")
            else "Choose the interface color theme"
        )
        self.color_box.setToolTipDuration(10000)

        self.update_language()
        #self.change_colors()

        # Theme-Status ohne Blinken anwenden
        target_theme = self.current_config.get("theme_mode", "standard")
        if hasattr(self, "toggle_matrix"):
            self.toggle_matrix(force_state=target_theme)

        # ----------------------------
        # 8. FINALER SLIDER- & LED-FIX
        # ----------------------------
        current_speed = self.current_config.get("blink_speed", 0)

        if hasattr(self, "slider_speed") and self.slider_speed:
            self.slider_speed.blockSignals(True)
            self.slider_speed.setValue(current_speed)
            self.slider_speed.blockSignals(False)

            if hasattr(self, "update_label_only"):
                self.update_label_only(current_speed)

            if hasattr(self, "update_blink_speed"):
                self.slider_speed.valueChanged.connect(self.update_blink_speed)

        # System-Status LEDs immer statisch setzen
        if hasattr(self, "set_system_leds_static"):
            self.set_system_leds_static()

        # User-LED Timer beim Start stoppen
        if hasattr(self, "blink_timer"):
            self.blink_timer.stop()

        if hasattr(self, "update_blink_speed"):
            self.update_blink_speed(current_speed)

        if hasattr(self, "update_plugin_button_state"):
            self.update_plugin_button_state()

        # --- LED STATUS WIEDERHERSTELLEN ---
        # 1. Den Wert aus der geladenen Config holen (Standard: True)
        saved_led_enabled = self.current_config.get("led_enabled", True)

        # 2. Die Checkbox visuell synchronisieren (ohne Signale zu feuern)
        if hasattr(self, "led_checkbox"):
            self.led_checkbox.blockSignals(True)
            self.led_checkbox.setChecked(saved_led_enabled)
            self.led_checkbox.blockSignals(False)

        # 3. Die tatsächliche Blink-Logik/Timer starten oder stoppen
        # WICHTIG: Wir blockieren kurzzeitig das Speichern, damit beim Start
        # nicht unnötig in die config.json geschrieben wird (Performance & Loop-Schutz)
        self._block_config_save = True
        self.toggle_leds(saved_led_enabled)
        self._block_config_save = False

        # 4. Falls die LEDs aus sind, sofort den dunklen Zustand erzwingen
        if not saved_led_enabled:
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()

        lang = getattr(self, "LANG", "de").lower()
        init_msg = (
            "Initialisiere Generator..."
            if lang == "de"
            else "Initializing Generator..."
        )

        # Ganz am Ende der __init__ einfügen:

        # 1. Wert aus Config holen
        saved_led_enabled = self.current_config.get("led_enabled", True)

        # 2. Checkbox finden und setzen (WICHTIG: Name prüfen!)
        # Falls die Checkbox bei dir anders heißt, hier anpassen:
        target_cb = getattr(self, "led_checkbox", None)
        if target_cb:
            target_cb.blockSignals(True)
            target_cb.setChecked(saved_led_enabled)
            target_cb.blockSignals(False)

        # 3. Die Logik final erzwingen
        self.toggle_leds(saved_led_enabled)

        # 4. Falls der Timer trotzdem läuft, obwohl er aus sein soll:
        if not saved_led_enabled and hasattr(self, "blink_timer"):
            self.blink_timer.stop()
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()

        # 1. Willkommens-Info (500ms)
        # QTimer.singleShot(500, self.show_welcome_info)

        # 2. System-Check (2000ms) - Injiziert sich in den Anker
        QTimer.singleShot(2000, lambda: self.run_full_system_check(clear_log=False))


        # 4. OSCam Monitor (8500ms)
        QTimer.singleShot(4500, self.start_oscam_update_check)
        self.init_button_signals()

        self.is_loading = False  # Initialisierung abgeschlossen

        # Hauptfenster bei jedem Start im echten Vollbild anzeigen.
        QTimer.singleShot(0, self.showFullScreen)

    # =====================================================================
    # ANIMATIONS-LOGIK (Verhindert AttributeError)
    # =====================================================================

    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtCore import QUrl

    def change_language(self, index=None):
        """Wechselt die Sprache, aktualisiert die UI und führt die Abschlussanimation aus."""
        import os
        import platform
        import re

        from PyQt6.QtCore import QTimer, QRect, Qt
        from PyQt6.QtGui import QFont, QColor, QPixmap
        from PyQt6.QtWidgets import QApplication, QGroupBox, QLabel

        # Schutz vor mehrfacher Ausführung
        if not getattr(self, "language_box", None):
            return
        if getattr(self, "_block_language_change", False):
            return
        self._block_language_change = True

        pbar = getattr(self, "progress_bar", None)
        finished = {"value": False}

        def log_error(stage, exc):
            print(f"[change_language] {stage}: {exc}")

        def release_lock():
            self._block_language_change = False

        def update_pbar(value, text):
            if pbar is not None:
                pbar.setValue(value)
                pbar.setFormat(f"{text} %p%")
            QApplication.processEvents()

        def strip_icons(text):
            return re.sub(r"^[^\w\s]+", "", str(text)).strip()

        def blink_widget(widget, times=6, interval=300):
            if widget is None:
                return
            widget.show()
            widget.raise_()
            state = {"count": 0}

            def toggle():
                widget.setVisible(not widget.isVisible())
                state["count"] += 1
                if state["count"] < times * 2:
                    QTimer.singleShot(interval, toggle)
                else:
                    widget.setVisible(True)

            toggle()

        def after_animation():
            """Aktualisiert die verbleibenden Labels und startet den Abschluss."""
            try:
                lang_dict = getattr(self, "TEXT", {}) or {}
                is_de = getattr(self, "LANG", "en") == "de"

                if hasattr(self, "commit_label"):
                    self.commit_label.setText(
                        lang_dict.get(
                            "commit_count_label",
                            "Anzahl Commits:" if is_de else "Commit Count:",
                        )
                    )

                if hasattr(self, "color_label"):
                    self.color_label.setText(
                        lang_dict.get("color_label", "Farbe:" if is_de else "Color:")
                    )

                if hasattr(self, "log_button"):
                    self.log_button.setText(
                        lang_dict.get(
                            "log_button_text",
                            " Log speichern" if is_de else " Save Log",
                        )
                    )

                if hasattr(self, "music_button"):
                    self.music_button.setText(
                        ("🎵 Musik ausschalten" if self.music_button.isChecked() else "🎵 Musik einschalten")
                        if is_de else
                        ("🎵 Music off" if self.music_button.isChecked() else "🎵 Music on")
                    )
                    self.music_button.setToolTip(
                        "Hintergrundmusik aus dem Ordner sounds ein- oder ausschalten."
                        if is_de else
                        "Toggle background music from the sounds folder."
                    )

                if hasattr(self, "music_title_combo"):
                    self._refresh_background_music_titles()
                if hasattr(self, "music_player_button"):
                    self.music_player_button.setText(
                        "🎚 Player öffnen" if is_de else "🎚 Open player"
                    )
                    self.music_player_button.setToolTip(
                        "Separaten Cyber Music Player öffnen"
                        if is_de else "Open the separate Cyber Music Player"
                    )
                    self.music_player_button.setToolTip(
                        "Separaten Cyber Music Player öffnen"
                        if is_de else
                        "Open the separate Cyber Music Player"
                    )

                # Auch ein bereits geöffnetes Player-Fenster live umschalten.
                player_window = getattr(self, "_music_player_window", None)
                if player_window is not None:
                    try:
                        player_window.set_language()
                        player_window.refresh_tracks()
                    except Exception as player_exc:
                        log_error("Externer Musikplayer konnte nicht aktualisiert werden", player_exc)

                # Live-Konsole: neue Werkzeugbuttons der gewählten Sprache anpassen.
                if hasattr(self, "copy_log_button"):
                    self.copy_log_button.setText(
                        lang_dict.get("copy_log_button", "LOG KOPIEREN" if is_de else "COPY LOG")
                    )
                    self.copy_log_button.setToolTip(
                        lang_dict.get(
                            "copy_log_tooltip",
                            "Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren"
                            if is_de else "Copy all visible console output to the clipboard",
                        )
                    )
                if hasattr(self, "clear_console_button"):
                    self.clear_console_button.setText(
                        lang_dict.get("clear_console_button", "KONSOLE LEEREN" if is_de else "CLEAR CONSOLE")
                    )
                    self.clear_console_button.setToolTip(
                        lang_dict.get(
                            "clear_console_tooltip",
                            "Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert"
                            if is_de else "Clear only the visible console output; log files remain unchanged",
                        )
                    )
                if hasattr(self, "cyber_center_button"):
                    self.cyber_center_button.setText("OSCAM CONTROL CENTER")
                    self.cyber_center_button.setToolTip(
                        "Zentrale für alle OSCam-Control-Center-Funktionen"
                        if is_de else
                        "Central hub for all OSCam Control Center features"
                    )
                if hasattr(self, "patch_diff_button"):
                    self.patch_diff_button.setText(
                        "PATCH VERGLEICHEN" if is_de else "COMPARE PATCHES"
                    )
                    self.patch_diff_button.setToolTip(
                        "Zwei Patch-Dateien oder Git-Commits vergleichen"
                        if is_de else
                        "Compare two patch files or Git commits"
                    )
                if hasattr(self, "achievement_button"):
                    self.achievement_button.setText(
                        "🏆 ERFOLGE" if is_de else "🏆 ACHIEVEMENTS"
                    )
                    self.achievement_button.setToolTip(
                        "Deine OSCam-Erfolge und Fortschritte anzeigen"
                        if is_de else
                        "View your OSCam achievements and progress"
                    )
                if hasattr(self, "ai_assistant_button"):
                    self.ai_assistant_button.setText(
                        "🤖 KI-ASSISTENT" if is_de else "🤖 AI ASSISTANT"
                    )
                    self.ai_assistant_button.setToolTip(
                        "KI-Chat für Patch-Analyse und Fehlersuche öffnen"
                        if is_de else
                        "Open AI chat for patch analysis and troubleshooting"
                    )
                if hasattr(self, "weather_button"):
                    self.weather_button.setText(
                        "🌤 Wetter anzeigen" if is_de else "🌤 Show weather"
                    )
                    self.weather_button.setToolTip(
                        "Aktuelles Wetter und 5-Tage-Vorhersage anzeigen"
                        if is_de else
                        "Show current weather and 5-day forecast"
                    )

                # BUILD-LOG-Analyse und Systemdiagnose ebenfalls live umschalten.
                if hasattr(self, "analyze_build_logs_button"):
                    self.analyze_build_logs_button.setText(
                        lang_dict.get("analyze_build_logs_button", "BUILD-LOG ANALYSIEREN" if is_de else "ANALYZE BUILD LOG")
                    )
                    self.analyze_build_logs_button.setToolTip(
                        lang_dict.get("analyze_build_logs_tooltip", "Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen" if is_de else "Check the newest build log for common errors and warnings")
                    )
                if hasattr(self, "diagnostics_button"):
                    self.diagnostics_button.setText(
                        lang_dict.get("system_diagnostics_button", "SYSTEM-DIAGNOSE" if is_de else "SYSTEM DIAGNOSTICS")
                    )
                    self.diagnostics_button.setToolTip(
                        lang_dict.get("system_diagnostics_tooltip", "System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build" if is_de else "Check system, tool directories and existing build logs; does not start a build")
                    )

                if hasattr(self, "header_label"):
                    self.header_label.setText(
                        strip_icons(
                            lang_dict.get(
                                "settings_header",
                                "Einstellungen" if is_de else "Settings",
                            )
                        )
                    )

                # OSCam-Status kurz hervorheben
                status_label = getattr(self, "status_label", None)
                if status_label:
                    timestamp = getattr(self, "last_timestamp", "--:--:--")
                    rev = getattr(self, "current_rev", "----")
                    msg = lang_dict.get(
                        "oscam_uptodate",
                        "OSCam ist aktuell." if is_de else "OSCam is up to date.",
                    )
                    state = {"count": 0}

                    def blink_status():
                        color = "#FF0000" if state["count"] % 2 == 0 else "#00FF00"
                        status_label.setText(
                            f"✅ <span style='font-size:24px;color:#FF0000;font-weight:bold;'>"
                            f"[{timestamp}]</span> "
                            f"<span style='font-size:24px;color:#00FF00;font-weight:bold;'>"
                            f"{msg}</span> "
                            f"<span style='font-size:24px;color:{color};font-weight:bold;'>"
                            f"{rev}</span>"
                        )
                        state["count"] += 1
                        if state["count"] < 6:
                            QTimer.singleShot(300, blink_status)

                    blink_status()

                # Gruppentitel an die gewählte Sprache anpassen
                for box in self.findChildren(QGroupBox):
                    title = box.title()
                    if "Settings" in title or "Einstellungen" in title:
                        box.setTitle("Einstellungen" if is_de else "Settings")
                    if any(term in title for term in ("Configuration", "Konfiguration", "GitHub")):
                        box.setTitle(
                            "GitHub Konfiguration" if is_de else "GitHub Configuration"
                        )

                if hasattr(self, "btn_modifier"):
                    self.btn_modifier.setText(
                        f"👤 {strip_icons(lang_dict.get('modifier_button_text', 'Patch Autor' if is_de else 'Patch Author'))}"
                    )

                if hasattr(self, "btn_patch_online"):
                    self.btn_patch_online.setText(
                        f"🌐 {strip_icons(lang_dict.get('patch_online_download', 'Patches aus Git laden' if is_de else 'Load Patches from Git'))}"
                    )

                # Theme und Tooltips nach den Textänderungen erneut anwenden
                try:
                    if hasattr(self, "apply_global_button_style"):
                        self.apply_global_button_style()
                except Exception as exc:
                    log_error("Button-Theme/Tooltips konnten nicht aktualisiert werden", exc)

                # Button-Texte nach der Layout-Neuberechnung anpassen
                try:
                    if hasattr(self, "_fit_all_button_texts"):
                        layout = self.layout()
                        if layout is not None:
                            layout.activate()
                        QTimer.singleShot(0, self._fit_all_button_texts)
                        QTimer.singleShot(250, self._fit_all_button_texts)
                except Exception as exc:
                    log_error("Button-Text-Anpassung fehlgeschlagen", exc)

                # Finales Label vorbereiten und zunächst verstecken
                if hasattr(self, "final_label") and self.final_label:
                    self.final_label.setText(
                        lang_dict.get(
                            "final_label",
                            "🛠️ Was bauen wir heute?" if is_de else "🛠️ What are we building today?",
                        )
                    )
                    self.final_label.hide()

                

                def final_blink():
                    try:
                        # Abschlusstext unmittelbar vor der Animation anhand
                        # der aktuell gewählten Sprache aktualisieren.
                        current_is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
                        current_text = (
                            "🛠️ Was bauen wir heute?"
                            if current_is_de
                            else "🛠️ What are we building today?"
                        )
                        final_geom = pbar.geometry() if pbar is not None else QRect(20, 20, 400, 40)
                        final_label = getattr(self, "final_label", None)

                        if final_label is None:
                            final_label = QLabel(
                                lang_dict.get(
                                    "final_label",
                                    "🛠️ Was bauen wir heute?" if is_de else "🛠️ What are we building today?",
                                ),
                                self,
                            )
                            self.final_label = final_label

                        # Nur den Text aktualisieren. Das eigentliche Blinken
                        # übernimmt on_update_check_finished(), damit Revision
                        # und Abschlusslabel dieselbe Zeitsteuerung verwenden.
                        final_label.setText(current_text)
                        final_label.setAlignment(
                            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                        )
                        final_label.setGeometry(final_geom)

                        # Abschlussmeldung bis zum Ende des Systemchecks verbergen.
                        final_label.hide()

                        if pbar is not None:
                            # 100 % bleibt der letzte Fortschrittswert
                            # nach Abschluss des Sprachwechsels.
                            pbar.setValue(100)
                            pbar.setFormat("%p%")

                        try:
                            if hasattr(self, "hide_language_overlay"):
                                self.hide_language_overlay()
                        except Exception as exc:
                            log_error("Overlay konnte nicht ausgeblendet werden", exc)
                    except Exception as exc:
                        log_error("Abschlussanimation fehlgeschlagen", exc)
                    finally:
                        finished["value"] = True
                        release_lock()

                        btn = getattr(self, "buttons", {}).get("patch_create")

                        # Den Systemcheck nach dem Sprachwechsel starten.
                        # Die Abschlussmeldung bleibt bis zum Check-Ende verborgen.
                        try:
                            if not getattr(self, "_checking_active", False):
                                QTimer.singleShot(
                                    0,
                                    lambda: self.run_full_system_check(clear_log=True),
                                )
                        except Exception as refresh_exc:
                            log_error(
                                "System-Monitor konnte nach Sprachwechsel nicht aktualisiert werden",
                                refresh_exc,
                            )

                QTimer.singleShot(500, final_blink)

            except Exception as exc:
                log_error("Fehler beim Abschluss des Sprachwechsels", exc)
                try:
                    if hasattr(self, "hide_language_overlay"):
                        self.hide_language_overlay()
                except Exception as hide_exc:
                    log_error("Overlay konnte nicht ausgeblendet werden", hide_exc)
                finally:
                    finished["value"] = True
                    release_lock()

        try:
            selected = self.language_box.currentText().upper()
            self.LANG = (
                "de"
                if any(token in selected for token in ("DE", "DEU", "DEUTSCH"))
                else "en"
            )
            # Persist language immediately so it survives a normal restart.
            # Keep both config aliases in sync for older code paths.
            try:
                config_obj = getattr(self, "cfg", None)
                if not isinstance(config_obj, dict):
                    config_obj = getattr(self, "current_config", None)
                if not isinstance(config_obj, dict):
                    config_obj = {}
                config_obj["language"] = self.LANG
                if hasattr(self, "cfg"):
                    self.cfg = config_obj
                if hasattr(self, "current_config"):
                    self.current_config = config_obj
                save_config_func = globals().get("save_config")
                if callable(save_config_func) and not getattr(self, "is_loading", False):
                    save_config_func(config_obj, gui_instance=self, silent=True)
            except Exception as save_exc:
                print(f"[change_language] Sprache konnte nicht gespeichert werden: {save_exc}")
            is_de = self.LANG == "de"

            overlay_text = "Sprache wird angepasst..." if is_de else "Switching language..."
            update_pbar(10, f"⏳ {overlay_text}")

            if hasattr(self, "loading_overlay") and hasattr(self, "loading_label"):
                from PyQt6.QtCore import Qt
                self.loading_overlay.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
                )
                self.loading_overlay.setGeometry(self.rect())
                self.loading_label.setText(overlay_text)
                self.loading_overlay.show()
                self.loading_overlay.raise_()
                QApplication.processEvents()

            safe_play_func = globals().get("safe_play")
            if callable(safe_play_func):
                try:
                    safe_play_func("service-logout.oga")
                except Exception as exc:
                    log_error("Sprachwechsel-Sound fehlgeschlagen", exc)

            load_text = "Texte werden geladen..." if is_de else "Loading texts..."
            update_pbar(30, f"⏳ {load_text}")

            all_texts = globals().get("TEXTS", {})
            if not all_texts:
                try:
                    all_texts = ensure_dependencies()
                except Exception as exc:
                    log_error("Sprachdateien konnten nicht geladen werden", exc)
                    all_texts = {}

            self.TEXT = all_texts.get(self.LANG, {})
            lang_dict = self.TEXT

            
            ui_text = "UI wird aktualisiert..." if is_de else "Updating UI..."
            update_pbar(50, f"⏳ {ui_text}")

            update_language = getattr(self, "update_language", None)
            if callable(update_language):
                update_language()

            # Alle UI-Texte aktualisieren, einschließlich "Rechte fixen"
            update_ui_texts = getattr(self, "update_ui_texts", None)
            if callable(update_ui_texts):
                try:
                    update_ui_texts()
                except Exception as exc:
                    log_error("UI-Texte konnten nicht aktualisiert werden", exc)


            # Status der Installationsbuttons prüfen und Beschriftung aktualisieren
            button_config = (
                ("btn_s3", "S3", "S3_PATH", "/opt/s3", "s3"),
                ("btn_s4", "S4", "S4_PATH", "/opt/simplebuild4", "s4"),
                ("btn_ncam", "NCam", "NCAM_PATH", "/opt/ncam", "ncam"),
            )

            for btn_attr, display_name, path_attr, default_path, executable in button_config:
                btn = getattr(self, btn_attr, None)
                if btn is None:
                    continue

                exe = executable + (".exe" if platform.system() == "Windows" else "")
                path = getattr(self, path_attr, default_path)
                exists = os.path.exists(os.path.join(path, exe))

                label = (
                    f"{display_name} OK"
                    if exists
                    else (
                        f"{display_name} installieren"
                        if is_de
                        else f"Install {display_name}"
                    )
                )

                # Grün = vorhanden, Orange = fehlt
                color = "#2ecc71" if exists else "#f39c12"
                btn.setText(f"🚀 {label}")
                btn._original_text = f"🚀 {label}"
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        text-align: left;
                        padding-left: 8px;
                        font-weight: bold;
                        color: {color};
                        background-color: #3d3d3d;
                        border: 1px solid {color};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {color};
                        color: black;
                    }}
                    """
                )

            try:
                if hasattr(self, "apply_global_button_style"):
                    self.apply_global_button_style()
            except Exception as exc:
                log_error("Installationsbutton-Theme fehlgeschlagen", exc)

            try:
                if hasattr(self, "_fit_all_button_texts"):
                    layout = self.layout()
                    if layout is not None:
                        layout.activate()
                    QTimer.singleShot(0, self._fit_all_button_texts)
                    QTimer.singleShot(250, self._fit_all_button_texts)
            except Exception as exc:
                log_error("Button-Text-Anpassung fehlgeschlagen", exc)

            anim_text = "Animation & Systemcheck..." if is_de else "Animation & system check..."

            update_pbar(80, f"⏳ {anim_text}")

            from PyQt6.QtCore import QTimer

            show_animation = getattr(self, "show_language_animation", None)
            animation_callback_called = {"value": False}

            def finish_language_animation_once():
                if animation_callback_called["value"]:
                    return
                animation_callback_called["value"] = True
                after_animation()

            if callable(show_animation):

                try:
                    show_animation(
                        self.LANG,
                        callback=finish_language_animation_once,
                    )
                except Exception as exc:
                    raise

                # Sicherheitsnetz, falls die Animation keinen Callback auslöst.
                def force_finish_language_animation():
                    if animation_callback_called["value"]:
                        return


                    for name in (
                        "text_fade_in",
                        "flag_fade_in",
                        "flag_slide",
                        "out_anim",
                        "f_out",
                    ):
                        anim = getattr(self, name, None)
                        if anim is not None:
                            try:
                                anim.stop()
                            except Exception:
                                pass

                    for name in ("text_label", "flag_label"):
                        widget = getattr(self, name, None)
                        if widget is not None:
                            try:
                                widget.hide()
                                widget.deleteLater()
                            except Exception:
                                pass
                            setattr(self, name, None)

                    finish_language_animation_once()

                QTimer.singleShot(6000, force_finish_language_animation)

            else:
                finish_language_animation_once()

            QApplication.processEvents()

            # Layout nach dem Sprachwechsel wie beim Programmstart neu anpassen.
            try:
                fit_buttons = getattr(self, "_fit_all_button_texts", None)
                if callable(fit_buttons):
                    QTimer.singleShot(0, fit_buttons)
                    QTimer.singleShot(250, fit_buttons)
                    QTimer.singleShot(700, fit_buttons)

                for widget in self.findChildren(QWidget):
                    try:
                        layout = widget.layout()
                        if layout is not None:
                            layout.invalidate()
                            layout.activate()
                        widget.updateGeometry()
                    except (RuntimeError, AttributeError):
                        pass

                self.updateGeometry()
                QApplication.processEvents()
            except Exception as layout_exc:
                log_error("Layout-Aktualisierung fehlgeschlagen", layout_exc)

        except Exception as exc:
            log_error("Sprachwechsel fehlgeschlagen", exc)
            try:
                if hasattr(self, "hide_language_overlay"):
                    self.hide_language_overlay()
            except Exception as hide_exc:
                log_error("Overlay konnte nicht ausgeblendet werden", hide_exc)
            finally:
                if not finished["value"]:
                    release_lock()









    
    def run_full_system_check(self, clear_log=True):
        """
        Startet den Systemcheck ohne die GUI zu blockieren.

        Alle langsamen/blockierenden Operationen laufen im Worker-Thread.
        Die GUI wird ausschließlich über Qt-Signale aktualisiert.
        """

        from PyQt6.QtCore import QThread

        # ------------------------------------------------------------
        # Doppelstart verhindern
        # ------------------------------------------------------------

        if getattr(self, "_checking_active", False):
            return

        self._checking_active = True
        self.is_loading = True

        # ------------------------------------------------------------
        # UI vorbereiten
        # ------------------------------------------------------------

        if hasattr(self, "hide_final_label"):
            try:
                self.hide_final_label()
            except Exception:
                pass
        elif hasattr(self, "final_label"):
            try:
                if self.final_label:
                    self.final_label.hide()
            except Exception:
                pass

        if clear_log and hasattr(self, "log_window"):
            try:
                self.log_window.clear()
            except Exception:
                pass

        widget = getattr(self, "info_text", None)
        pbar = getattr(self, "progress_bar", None)

        if widget is None:
            self.is_loading = False
            self._checking_active = False
            return

        # ------------------------------------------------------------
        # Progressbar
        # ------------------------------------------------------------

        if pbar:

            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setTextVisible(True)

            pbar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #444444;
                    border-radius: 8px;
                    background-color: #0A0A0A;
                    color: black;
                    text-align: center;
                    font-weight: 900;
                    font-size: 20px;
                    min-height: 35px;
                }

                QProgressBar::chunk {
                    background-color: qlineargradient(
                        spread:pad,
                        x1:0,
                        y1:0,
                        x2:1,
                        y2:0,
                        stop:0 #FF00FF,
                        stop:0.5 #00FFFF,
                        stop:1 #39FF14
                    );
                    border-radius: 6px;
                }
                """
            )

            pbar.setFormat(
                "🚀 Initialisiere System...   %p%"
            )
            pbar.show()

        # ------------------------------------------------------------
        # Info-Widget leeren
        # ------------------------------------------------------------

        # HTML-Puffer bei jedem Systemcheck neu initialisieren.
        self._system_check_html = []
        self._system_check_display_finished = False

        # Anzeige nur leeren, wenn dies ausdrücklich angefordert wurde.
        if clear_log:
            widget.setHtml("")

        def append_html(fragment):
            """
            Dieser Slot läuft im GUI-Thread.
            """

            if not fragment:
                return

            # Systemcheck-Ausgabe nicht-destruktiv am Ende einfügen.
            # So bleiben Update- und Konfigurationsmeldungen erhalten.
            self._system_check_html.append(fragment)

            try:
                from PyQt6.QtGui import QTextCursor

                cursor = widget.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)

                # Jedes neue HTML-Fragment in einem eigenen Absatz beginnen.
                if widget.document().characterCount() > 1:
                    cursor.insertBlock()

                widget.setTextCursor(cursor)
                cursor.insertHtml(fragment)
                widget.setTextCursor(cursor)
            except Exception as exc:
                log_error("Systemcheck-HTML konnte nicht eingefügt werden", exc)

        def update_progress(value, text):
            """
            Dieser Slot läuft im GUI-Thread.
            """

            if not pbar:
                return

            value = max(
                0,
                min(100, int(value))
            )

            pbar.setValue(value)
            pbar.setFormat(
                f"{text}   %p%"
            )

        # ------------------------------------------------------------
        # Worker / Thread erstellen
        # ------------------------------------------------------------

        self._system_check_thread = QThread(self)

        # ------------------------------------------------------------
        # Eingestellte Repo-URL aus deiner Anwendung holen
        #
        # Passe die Attributnamen hier nur an, falls deine URL anders
        # gespeichert wird.
        # ------------------------------------------------------------

        repo_url = ""

        possible_repo_attributes = (
            "repo_url",
            "repository_url",
            "github_repo_url",
            "REPO_URL",
            "GITHUB_REPO_URL",
            "repo",
        )

        for attr_name in possible_repo_attributes:

            try:
                value = getattr(
                    self,
                    attr_name,
                    "",
                )

                if isinstance(value, str) and value.strip():
                    repo_url = value.strip()
                    break

            except Exception:
                pass

        # ------------------------------------------------------------
        # Worker
        # ------------------------------------------------------------

        self._system_check_worker = SystemCheckWorker(
            lang=getattr(
                self,
                "LANG",
                "de",
            ),
            repo_url=repo_url,
        )

        self._system_check_worker.moveToThread(
            self._system_check_thread
        )

        # ------------------------------------------------------------
        # Signale
        # ------------------------------------------------------------

        self._system_check_worker.html.connect(
            append_html
        )

        self._system_check_worker.progress.connect(
            update_progress
        )

        self._system_check_worker.error.connect(
            lambda message: append_html(
                "<br>"
                "<div style='"
                "text-align:center;"
                "color:#FF0000;"
                "font-family:Arial Black;"
                "font-size:18pt;"
                "'>"
                f"❌ System Check Error:<br>{message}"
                "</div>"
            )
        )

        self._system_check_worker.finished.connect(
            self._system_check_finished
        )

        # ------------------------------------------------------------
        # Worker nach Beendigung aufräumen
        # ------------------------------------------------------------

        self._system_check_worker.finished.connect(
            self._system_check_thread.quit
        )

        self._system_check_worker.finished.connect(
            self._system_check_worker.deleteLater
        )

        self._system_check_thread.finished.connect(
            self._system_check_thread.deleteLater
        )

        # ------------------------------------------------------------
        # Thread starten
        # ------------------------------------------------------------

        self._system_check_thread.started.connect(
            self._system_check_worker.run
        )
        if hasattr(self, "sound_manager"):
            self.sound_manager.play_start()

        self._system_check_thread.start()
            
        
    def _show_final_label_after_system_check(self):
        """Zeigt die Abschlussmeldung in der aktuellen Sprache an."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QLabel

        pbar = getattr(self, "progress_bar", None)
        if pbar is None:
            return

        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        text = "🛠️ Was bauen wir heute?" if is_de else "🛠️ What are we building today?"

        label = getattr(self, "final_label", None)
        if label is None:
            label = QLabel(self)
            label.setObjectName("final_label")
            self.final_label = label

        label.setText(text)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        pos = pbar.mapTo(self, pbar.rect().topLeft())
        label.setGeometry(pos.x(), pos.y(), pbar.width(), pbar.height())
        label.setStyleSheet(
            "QLabel { background-color: black; color: cyan; "
            "border: 2px solid cyan; border-radius: 6px; "
            "font-family: Arial, Segoe UI, sans-serif; "
            "font-size: 20px; font-weight: bold; }"
        )
        label.show()
        label.raise_()

    def _system_check_finished(self):
        """
        Wird nach erfolgreichem oder fehlerhaftem Worker-Ende
        im GUI-Thread ausgeführt.
        """
        if (
            not getattr(self, "_system_check_had_error", False)
            and hasattr(self, "sound_manager")
        ):
            self.sound_manager.play_success()
        pbar = getattr(
            self,
            "progress_bar",
            None,
        )

        if pbar:
            pbar.setValue(100)

            is_de = (
                getattr(
                    self,
                    "LANG",
                    "de",
                ).lower()
                == "de"
            )

            # 100 % bleibt die letzte Anzeige im Fortschrittsbalken.
            pbar.setFormat("%p%")

        # ------------------------------------------------------------
        # Status zurücksetzen
        # ------------------------------------------------------------

        self.is_loading = False
        self._checking_active = False

        # Gespeicherten OSCam-Status erst jetzt zusammen mit dem
        # Abschlusslabel anzeigen. Es wird kein Netzwerkcheck gestartet.
        if getattr(self, "_oscam_check_completed", False):
            try:
                self.on_update_check_finished(
                    bool(getattr(self, "_oscam_update_available", False)),
                    getattr(self, "last_remote_rev", None)
                    or getattr(self, "current_rev", None),
                    refresh_only=True,
                )
            except Exception as label_exc:
                log_error(
                    "OSCam-Anzeige konnte nach Systemcheck nicht aktualisiert werden",
                    label_exc,
                )
        else:
            label = getattr(self, "final_label", None)
            if label is not None:
                label.hide()

        # ------------------------------------------------------------
        # Vorhandene Update-Prüfung beibehalten
        #
        # Wichtig:
        # Sie läuft jetzt NACH dem Systemcheck.
        # ------------------------------------------------------------

        # Abschlussmeldung erst nach dem beendeten Systemcheck anzeigen.
        try:
            self._show_final_label_after_system_check()
        except Exception as label_exc:
            log_error(
                "Abschlussmeldung konnte nicht angezeigt werden",
                label_exc,
            )

        try:
            self.check_for_update_on_start()
        except Exception as e:
            widget = getattr(
                self,
                "info_text",
                None,
            )

            if widget:
                widget.append(
                    "<br>"
                    "<span style='"
                    "color:#F57A08;"
                    "font-weight:bold;"
                    "'>"
                    f"⚠️ Update check: {e}"
                    "</span>"
                )

        # Ab jetzt darf ein später eintreffender OSCam-Status direkt ans Ende.
        self._system_check_display_finished = True

        # OSCam-Status zuletzt anzeigen, auch wenn er vor dem Systemcheck fertig war.
        try:
            oscam_html = (
                getattr(self, "_last_oscam_info_html", None)
                or getattr(self, "_pending_oscam_info_html", None)
            )
            if oscam_html and not getattr(
                self, "_oscam_info_in_update_block", False
            ):
                self.append_info(
                    getattr(self, "info_text", None),
                    oscam_html,
                    "html",
                )
            self._pending_oscam_info_html = None
        except Exception as exc:
            log_error("OSCam-Status konnte nicht angehängt werden", exc)

        # ------------------------------------------------------------
        # Referenzen behalten wir bis zum Thread-Ende.
        # Danach können sie freigegeben werden.
        # ------------------------------------------------------------

        try:
            thread = getattr(
                self,
                "_system_check_thread",
                None,
            )

            if thread and not thread.isRunning():
                self._system_check_thread = None
                self._system_check_worker = None

        except Exception:
            pass
    

    # ===================== OSCam-EMU BUTTON WRAPPERS =====================
    
    
    
    


    



    def hide_final_label(self):
        """Blendet das finale Status-Label aus und stoppt dessen Blink-Timer."""
        timer = getattr(self, "_final_message_blink_timer", None)

        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self._final_message_blink_timer = None

        label = getattr(self, "final_label", None)
        if label is not None:
            label.hide()

        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()


    # ========================== SimpleBuild 4 ==========================
    import os
    import platform
    import shutil

    
    







    # ========================== S3 ==========================
    
    




    





    
    









    def choose_oscam_source(self):
        """Öffnet eine separate Auswahlbox für das OSCam-Quellrepository."""
        from PyQt6.QtWidgets import QInputDialog
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        names = list(STREAM_REPO_CHOICES.keys())
        current = get_selected_stream_repo_name()
        selected, accepted = QInputDialog.getItem(
            self,
            "OSCam-Quelle auswählen" if is_de else "Select OSCam source",
            "Repository für Patch-Erstellung:" if is_de else "Repository for patch creation:",
            names,
            names.index(current) if current in names else 0,
            False,
        )
        if not accepted or selected not in STREAM_REPO_CHOICES:
            return
        try:
            config_path = globals().get("CONFIG_FILE", "config.json")
            config = {}
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                    if isinstance(loaded, dict):
                        config = loaded
            config["oscam_source"] = selected
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=4, ensure_ascii=False)
            # Aktuelle Laufzeit-Workflows verwenden ebenfalls die Auswahl.
            globals()["STREAMREPO_URL"] = STREAM_REPO_CHOICES[selected]
            self.oscam_source_button.setText("Oscam Git URL")
            message = (
                        f"OSCam-Quelle eingestellt: {selected}\n{STREAM_REPO_CHOICES[selected]}"
                        if is_de
                        else f"OSCam source configured: {selected}\n{STREAM_REPO_CHOICES[selected]}"
                    )
            if hasattr(self, "append_info"):
                self.append_info(self.info_text, message, "success")
            elif hasattr(self, "info_text"):
                self.info_text.append(message)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "OSCam-Quelle" if is_de else "OSCam source",
                (
                    f"Einstellung konnte nicht gespeichert werden:\n{exc}"
                    if is_de
                    else f"Could not save setting:\n{exc}"
                ),
            )



    def _play_sys_sound(self, sound_type="standard"):
        """Spielt Systemfeedback über den gemeinsamen Windows/Linux-Backend."""
        manager = getattr(self, "sound_manager", None) or _ACTIVE_SOUND_MANAGER
        if manager is None:
            return False
        kind = str(sound_type).lower()
        if kind in ("error", "critical", "failure"):
            return manager.play_error()
        if kind in ("warning", "exclamation"):
            return manager.play_warning()
        if kind in ("click", "button"):
            return manager.play("click")
        return manager.play_info()









    from PyQt6.QtWidgets import (
        QLabel,
        QGraphicsOpacityEffect,
        QGraphicsDropShadowEffect,
    )
    from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QTimer
    from PyQt6.QtGui import QFont, QColor

    def hide_language_overlay(self):
        """Blendet das Sprachwechsel-Overlay aus und gibt Mausklicks frei."""
        from PyQt6.QtCore import Qt

        overlay = getattr(self, "loading_overlay", None)
        if overlay is not None:
            try:
                overlay.hide()
                overlay.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
                )
                overlay.setGeometry(0, 0, 0, 0)
                overlay.lower()
            except RuntimeError:
                pass

        label = getattr(self, "loading_label", None)
        if label is not None:
            try:
                label.hide()
            except RuntimeError:
                pass

    def show_language_animation(self, lang_code, callback=None):
        from PyQt6.QtWidgets import (
            QLabel,
            QGraphicsOpacityEffect,
            QGraphicsDropShadowEffect,
        )
        from PyQt6.QtCore import (
            QPropertyAnimation,
            QRect,
            QEasingCurve,
            QTimer,
            QVariantAnimation,
        )
        from PyQt6.QtGui import QFont, QFontInfo, QColor
        from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QTimer
        from PyQt6.QtGui import QFont, QColor

        # 1. Cleanup
        if hasattr(self, "text_label") and self.text_label:
            self.text_label.deleteLater()
        if hasattr(self, "flag_label") and self.flag_label:
            self.flag_label.deleteLater()
        if hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        is_de = lang_code.lower() == "de"
        text_msg = "Sprache wird umgestellt..." if is_de else "Switching language..."
                # 3. Flagge als echtes SVG-Bild statt Emoji anzeigen
        from PyQt6.QtCore import QByteArray, Qt
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtGui import QPainter

        if is_de:
            flag_svg = """
            <svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"
                 viewBox="0 0 120 80">
                <rect width="120" height="26.67" y="0" fill="#000000"/>
                <rect width="120" height="26.67" y="26.67" fill="#DD0000"/>
                <rect width="120" height="26.66" y="53.34" fill="#FFCE00"/>
            </svg>
            """
        else:
            flag_svg = """
            <svg xmlns="http://www.w3.org/2000/svg" width="120" height="80"
                 viewBox="0 0 60 30">
                <rect width="60" height="30" fill="#012169"/>
                <path d="M0 0 L60 30 M60 0 L0 30"
                      stroke="#FFFFFF" stroke-width="6"/>
                <path d="M0 0 L60 30 M60 0 L0 30"
                      stroke="#C8102E" stroke-width="2.5"/>
                <path d="M30 0 V30 M0 15 H60"
                      stroke="#FFFFFF" stroke-width="10"/>
                <path d="M30 0 V30 M0 15 H60"
                      stroke="#C8102E" stroke-width="5"/>
            </svg>
            """

        pixmap = QPixmap(120, 80)
        pixmap.fill(Qt.GlobalColor.transparent)

        renderer = QSvgRenderer(QByteArray(flag_svg.encode("utf-8")))
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        self.flag_label = QLabel(self)
        self.flag_label.setPixmap(pixmap)
        self.flag_label.setFixedSize(120, 80)

        t_y = (self.height() - 80) // 2
        f_x = (self.width() - 120) // 2
        f_y = t_y - 100

        # Sprachtext-Label vor den Animationen erstellen
        self.text_label = QLabel(text_msg, self)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.text_label.setGeometry(
            20, t_y + 15, max(1, self.width() - 40), 42
        )
        self.text_label.setStyleSheet(
            "color: rgba(255, 111, 0, 0); background: transparent;"
        )
        self.text_label.show()
        self.text_label.raise_()

        self.flag_label.move(f_x, f_y)

        flag_opacity = QGraphicsOpacityEffect(self.flag_label)
        flag_opacity.setOpacity(0)
        self.flag_label.setGraphicsEffect(flag_opacity)
        self.flag_label.show()

        # Schatteneffekt separat auf dem Textlabel verwenden.
        # Der Opacity-Effekt der Flagge bleibt dadurch erhalten.
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        self.shadow = QGraphicsDropShadowEffect(self.text_label)
        self.shadow.setBlurRadius(5)
        self.shadow.setColor(QColor(255, 111, 0, 220))
        self.shadow.setOffset(0, 0)
        self.text_label.setGraphicsEffect(self.shadow)

        # 4. Animationen: Einblenden -> Glow -> Ausblenden
        from PyQt6.QtCore import QTimer, QVariantAnimation
        from PyQt6.QtGui import QColor

        self._language_animation_finishing = False
        self._language_animation_callback_done = False

        def finish_animation():
            if self._language_animation_callback_done:
                return

            self._language_animation_callback_done = True

            for attr in ("text_label", "flag_label"):
                widget = getattr(self, attr, None)
                if widget is not None:
                    widget.hide()
                    widget.deleteLater()
                    setattr(self, attr, None)

            if callback:
                try:
                    callback()
                except Exception:
                    import traceback
                    traceback.print_exc(file=sys.__stderr__)


        def fade_out():
            if self._language_animation_finishing:
                return

            self._language_animation_finishing = True

            # Text ausblenden
            self.out_anim = QVariantAnimation(self)
            self.out_anim.setDuration(600)
            self.out_anim.setStartValue(QColor(255, 111, 0, 255))
            self.out_anim.setEndValue(QColor(255, 111, 0, 0))
            self.out_anim.valueChanged.connect(
                lambda c: (
                    self.text_label.setStyleSheet(
                        f"color: {c.name(QColor.NameFormat.HexArgb)}; "
                        "background: transparent;"
                    )
                    if getattr(self, "text_label", None) else None
                )
            )

            # Flagge gleichzeitig ausblenden
            opacity = self.flag_label.graphicsEffect()
            self.f_out = QPropertyAnimation(opacity, b"opacity", self)
            self.f_out.setDuration(600)
            self.f_out.setStartValue(1.0)
            self.f_out.setEndValue(0.0)
            self.f_out.finished.connect(finish_animation)

            self.out_anim.start()
            self.f_out.start()


        def start_glow_pulse(times=6):
            state = {"i": 0}

            def toggle():
                if self._language_animation_finishing:
                    return

                shadow = getattr(self, "shadow", None)
                if shadow is not None:
                    shadow.setBlurRadius(
                        5 + (state["i"] % 2) * 25
                    )

                state["i"] += 1

                if state["i"] < times * 2:
                    QTimer.singleShot(180, toggle)
                else:
                    fade_out()

            toggle()

        # Text-Fade-In
        self.text_fade_in = QVariantAnimation(self)
        self.text_fade_in.setDuration(900)
        self.text_fade_in.setStartValue(QColor(255, 111, 0, 0))
        self.text_fade_in.setEndValue(QColor(255, 111, 0, 255))
        self.text_fade_in.valueChanged.connect(
            lambda c: (
                self.text_label.setStyleSheet(
                    f"color: {c.name(QColor.NameFormat.HexArgb)}; "
                    "background: transparent;"
                )
                if getattr(self, "text_label", None) else None
            )
        )

        # Flaggen-Fade-In
        self.flag_fade_in = QPropertyAnimation(flag_opacity, b"opacity", self)
        self.flag_fade_in.setDuration(900)
        self.flag_fade_in.setStartValue(0.0)
        self.flag_fade_in.setEndValue(1.0)

        # Flaggen-Slide
        self.flag_slide = QPropertyAnimation(self.flag_label, b"geometry", self)
        self.flag_slide.setDuration(900)
        self.flag_slide.setStartValue(
            QRect(f_x, f_y + 50, self.flag_label.width(), self.flag_label.height())
        )
        self.flag_slide.setEndValue(
            QRect(f_x, f_y, self.flag_label.width(), self.flag_label.height())
        )
        self.flag_slide.setEasingCurve(QEasingCurve.Type.OutBack)

        # Erst nach dem Einblenden mit dem Glow beginnen
        self.flag_fade_in.finished.connect(
            lambda: QTimer.singleShot(100, start_glow_pulse)
        )

        self.text_fade_in.start()
        self.flag_fade_in.start()
        self.flag_slide.start()







    








    import os
    import re
    import requests
    from datetime import datetime

    # --- Hilfsfunktionen innerhalb der Klasse ---









    def change_colors(self):
        """
        Aktualisiert das komplette Farbschema der GUI.

        Funktionen:
        - Liest die aktuell gewählte Farbe sicher aus der Config/ComboBox.
        - Aktualisiert current_diff_colors zentral.
        - Repaintet die normalen Buttons.
        - Schützt S3/S4/NCam-Installationsbuttons vor Theme-Überschreibung.
        - Aktualisiert Checkbox, Header, Badges und Status.
        - Setzt den LED-Zustand nach dem Repaint erneut.
        - Synchronisiert theme_mode mit dem gewählten Theme.
        - Speichert die Änderung zentral.
        """

        from PyQt6.QtWidgets import QPushButton

        global current_diff_colors, current_color_name

        # ============================================================
        # 0. FINAL LABEL AUSBLENDEN
        # ============================================================
        try:
            if hasattr(self, "hide_final_label"):
                self.hide_final_label()
            elif getattr(self, "final_label", None):
                self.final_label.hide()
        except RuntimeError:
            pass

        # ============================================================
        # 1. CONFIG SICHER ERMITTELN
        # ============================================================
        config_obj = getattr(
            self,
            "cfg",
            getattr(self, "current_config", {})
        )

        if not isinstance(config_obj, dict):
            config_obj = {}

        saved_color = config_obj.get("color", "Classics")

        # ============================================================
        # 2. AKTUELLE FARBE ERMITTELN
        # ============================================================
        color_from_combo = ""

        try:
            if hasattr(self, "color_box") and self.color_box:
                color_from_combo = self.color_box.currentText().strip()
        except RuntimeError:
            color_from_combo = ""

        # Während des Startvorgangs niemals eine leere/noch nicht
        # initialisierte ComboBox verwenden.
        if getattr(self, "is_loading", False):
            current_color_name = saved_color
        elif color_from_combo:
            current_color_name = color_from_combo
        else:
            current_color_name = saved_color

        # ============================================================
        # 3. THEME SUCHEN
        # ============================================================
        base_colors = DIFF_COLORS.get(current_color_name)

        # Fallback, falls Theme-Key nicht existiert
        if not base_colors:
            base_colors = DIFF_COLORS.get(
                saved_color,
                DIFF_COLORS.get(
                    "Classics",
                    {
                        "bg": "#2F2F2F",
                        "fg": "#FFFFFF",
                        "hover": "#444444",
                        "active": "#222222",
                    },
                ),
            )

        # ============================================================
        # 4. FARBEN ZENTRAL AUFBAUEN
        # ============================================================
        bg = base_colors.get("bg", "#2F2F2F")
        fg = base_colors.get(
            "fg",
            base_colors.get("text", "#FFFFFF")
        )

        hover = base_colors.get("hover")

        if not hover:
            if hasattr(self, "adjust_color"):
                hover = self.adjust_color(bg, 1.20)
            else:
                hover = bg

        active = base_colors.get("active")

        if not active:
            if hasattr(self, "adjust_color"):
                active = self.adjust_color(bg, 0.80)
            else:
                active = bg

        current_diff_colors.clear()
        current_diff_colors.update({
            **base_colors,
            "bg": bg,
            "fg": fg,
            "text": base_colors.get("text", fg),
            "hover": hover,
            "active": active,
        })

        # Aktive Farbpalette für alle Zusatzfenster bereitstellen.
        self.current_diff_colors = current_diff_colors

        # ============================================================
        # 5. SOUND
        # ============================================================
        try:
            safe_play_func = globals().get("safe_play")
            if safe_play_func:
                safe_play_func("dialog-information.oga")
        except Exception:
            pass

        # ============================================================
        # 6. ALLGEMEINES REPAINT
        # ============================================================
        try:
            if hasattr(self, "repaint_ui_colors"):
                self.repaint_ui_colors()
        except Exception:
            pass


        # ============================================================
        # 7/8. KEINE Sonderfarbe für aktive Grid-Buttons:
        # Alle Buttons bleiben im ausgewählten Farbschema.
        # ============================================================

        # ============================================================
        # 9. INSTALLATIONSBUTTONS EXPLIZIT SCHÜTZEN
        #
        # Ihre individuelle Farbe bleibt erhalten.
        # ============================================================
        for attr_name in ("btn_s3", "btn_s4", "btn_ncam"):

            btn = getattr(self, attr_name, None)

            if not btn:
                continue

            try:
                # Vorhandenes individuelles Styling NICHT verändern.
                # Falls der Button noch keinen Style besitzt,
                # bekommt er einen neutralen Fallback.
                if not btn.styleSheet().strip():

                    btn.setStyleSheet(
                        f"""
                        QPushButton {{
                            text-align: left;
                            padding-left: 8px;
                            font-weight: bold;
                            background-color: {bg};
                            color: {fg};
                            border: 2px solid {fg};
                            border-radius: 8px;
                        }}
                        """
                    )


            except RuntimeError:
                pass

        # ============================================================
        # 10. TELEMETRIE CHECKBOX
        # ============================================================
        telemetry_cb = getattr(self, "telemetry_cb", None)

        if telemetry_cb:

            try:
                telemetry_cb.setStyleSheet(
                    f"""
                    QCheckBox {{
                        background-color: {bg};
                        color: {fg};
                        border: 2px solid {fg};
                        border-radius: 4px;
                        padding: 5px 10px;
                        font-weight: 700;
                    }}

                    QCheckBox:hover {{
                        background-color: {hover};
                    }}

                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 2px solid {fg};
                        border-radius: 3px;
                        background-color: transparent;
                    }}

                    QCheckBox::indicator:hover {{
                        border: 1px solid white;
                    }}

                    QCheckBox::indicator:checked {{
                        background-color: {fg};
                        border: 1px solid white;
                    }}
                    """
                )

            except RuntimeError:
                pass

        # ============================================================
        # 11. HEADER CONTAINER
        # ============================================================
        header_container = getattr(self, "header_container", None)

        if header_container:

            try:
                header_container.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: {bg};
                        border: 1px solid #444444;
                        border-radius: 8px;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 12. BADGES
        # ============================================================
        badge_style = f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid #444444;
                border-radius: 6px;
            }}

            QFrame:hover {{
                border: 2px solid {fg};
            }}
        """

        left_badge = getattr(self, "left_badge", None)

        if left_badge:
            try:
                left_badge.setStyleSheet(badge_style)
            except RuntimeError:
                pass

        right_badge = getattr(self, "right_badge", None)

        if right_badge:
            try:
                right_badge.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: transparent;
                        border: 1px solid #444444;
                        border-radius: 6px;
                    }}

                    QFrame:hover {{
                        border: 2px solid {fg};
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 13. HEADER LABEL
        # ============================================================
        header_label = getattr(self, "header_label", None)

        if header_label:

            try:
                header_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {fg};
                        font-weight: bold;
                        font-size: 15px;
                        background: transparent;
                        border: none;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 14. STATUS LABEL
        # ============================================================
        status_label = getattr(self, "status_label", None)

        if status_label:

            try:
                status_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {fg};
                        font-weight: bold;
                        font-size: 18px;
                        background: transparent;
                        border: none;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 15. LED-STATUS ERZWINGEN
        #
        # MUSS NACH DEM REPAINT KOMMEN.
        # ============================================================
        is_led_enabled = config_obj.get("led_enabled", True)

        blink_timer = getattr(self, "blink_timer", None)

        if blink_timer:

            try:
                blink_timer.stop()
            except RuntimeError:
                pass

        # LEDs zuerst in definierten statischen Zustand bringen
        try:
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()
        except Exception:
            pass

        # Danach Blinkbetrieb wieder aktivieren
        if is_led_enabled:

            try:
                slider = getattr(self, "slider_speed", None)

                speed_val = slider.value() if slider else 500

                if 10 <= speed_val < 950 and blink_timer:
                    blink_timer.start(speed_val)

            except (RuntimeError, ValueError, TypeError):
                pass

        # ============================================================
        # 16. CONFIG AKTUALISIEREN
        # ============================================================
        old_color = config_obj.get("theme_color", config_obj.get("color"))

        config_changed = old_color != current_color_name

        if config_changed:
            # Keep both keys synchronized: older code reads "color", while
            # the settings selector reads "theme_color".
            config_obj["color"] = current_color_name
            config_obj["theme_color"] = current_color_name

            # Nur bei tatsächlicher Farbänderung Theme-Modus neu setzen
            if "matrix" in str(current_color_name).lower():
                config_obj["theme_mode"] = "matrix"
            else:
                config_obj["theme_mode"] = "standard"


        # ============================================================
        # 17. INSTANZEN SYNCHRONISIEREN
        # ============================================================
        try:
            if hasattr(self, "cfg"):
                self.cfg = config_obj

            if hasattr(self, "current_config"):
                self.current_config = config_obj

        except Exception:
            pass

        # ============================================================
        # 18. SPEICHERN
        #
        # Während des Startvorgangs nicht unnötig speichern.
        # ============================================================
        if not getattr(self, "is_loading", False):

            try:
                save_config_func = globals().get("save_config")

                if save_config_func:
                    save_config_func(
                        config_obj,
                        gui_instance=self,
                        silent=True
                    )

            except Exception as e:
                print(f"[change_colors] Config konnte nicht gespeichert werden: {e}")

        # ============================================================
        # 18b. FARBMELDUNG IM GROSSEN INFOSCREEN
        #
        # Nur bei einer tatsächlichen Änderung melden.
        # Die Meldung wird ANGEHÄNGT und überschreibt keine
        # vorhandenen Infoscreen-Meldungen.
        # ============================================================
        if config_changed and not getattr(self, "is_loading", False):

            try:
                info_widget = getattr(self, "info_text", None)

                if info_widget is not None and hasattr(self, "append_info"):

                    lang = str(getattr(self, "LANG", "de")).lower()

                    if lang.startswith("de"):
                        color_msg = (
                            f"🎨 Farbe eingestellt: <b>{current_color_name}</b>"
                        )
                    else:
                        color_msg = (
                            f"🎨 Color selected: <b>{current_color_name}</b>"
                        )

                    # WICHTIG:
                    # Den bereits aufgebauten großen Infoscreen niemals neu setzen
                    # oder leeren. Der komplette System-Check-Block (Copyright,
                    # LIVE/System Monitor, Autor/Version, Hauptmerkmale,
                    # Systemdaten, Tools, Netzwerk, Repositories, Statistik
                    # und "System-Check OK. Bereit.") bleibt erhalten.
                    #
                    # Vor dem Anhängen merken wir uns den aktuellen HTML-Inhalt.
                    # append_info fügt anschließend ausschließlich am Ende ein.
                    existing_html = info_widget.toHtml()

                    self.append_info(
                        info_widget,
                        color_msg,
                        "info"
                    )

                    # Sicherheitsprüfung: Falls eine unerwartete UI-Aktion
                    # den Inhalt verändert hätte, den vollständigen bisherigen
                    # Infoscreen wiederherstellen und die Farbm­eldung danach
                    # erneut anhängen.
                    if existing_html and not info_widget.toHtml().startswith(
                        existing_html[:80]
                    ):
                        info_widget.setHtml(existing_html)
                        self.append_info(
                            info_widget,
                            color_msg,
                            "info"
                        )

            except Exception as e:
                print(f"[change_colors] Farbmeldung im Infoscreen fehlgeschlagen: {e}")

        # ============================================================
        # 19. BUTTON-TEXTE NACH THEME/STYLE SICHER ANPASSEN
        # ============================================================
        try:
            from PyQt6.QtCore import QTimer

            if hasattr(self, "_fit_all_button_texts"):

                # Nach dem ersten Theme-Repaint
                QTimer.singleShot(
                    100,
                    self._fit_all_button_texts
                )

                # Nach Sprach-/Layout-Updates
                QTimer.singleShot(
                    500,
                    self._fit_all_button_texts
                )

                # Nach vollständiger GUI-Initialisierung
                QTimer.singleShot(
                    1000,
                    self._fit_all_button_texts
                )

        except Exception as e:
            print(f"[change_colors] Button-Text-Anpassung fehlgeschlagen: {e}")

        # Letzter Schritt: sämtliche Buttons (einschließlich S3/S4/NCam und
        # Stats) erhalten das ausgewählte Theme, dessen Hover-Farbe und Tooltips.
        try:
            self.apply_global_button_style()
        except Exception as exc:
            print(f"[change_colors] Button-Theme/Tooltips konnten nicht aktualisiert werden: {exc}")



    





    def change_emu_repo(self):
        """Wählt das OSCam-Emu-Git-Repository für die nächste Patch-Erstellung."""
        from PyQt6.QtWidgets import QInputDialog, QApplication, QMessageBox
        from PyQt6.QtCore import QTimer
        import re

        presets=[
            "https://github.com/oscam-mirror/oscam-emu.git",
            "https://github.com/speedy005/Oscam-emu.git",
        ]
        current=str(getattr(self,"EMUREPO",None) or globals().get("EMUREPO",presets[0])).strip()
        if current and current not in presets:
            presets.insert(0,current)

        is_de=str(getattr(self,"LANG","de")).lower()[:2]=="de"
        dialog=QInputDialog(self)
        dialog.setWindowTitle("OSCam-Emu Git auswählen" if is_de else "Select OSCam-Emu Git")
        dialog.setLabelText("Repository-URL auswählen oder eigene Git-URL eingeben:" if is_de else "Select a repository URL or enter your own Git URL:")
        dialog.setComboBoxItems(presets)
        dialog.setComboBoxEditable(True)
        dialog.setTextValue(current or presets[0])
        dialog.setOkButtonText("Übernehmen" if is_de else "Apply")
        dialog.setCancelButtonText("Abbrechen" if is_de else "Cancel")

        if not dialog.exec():
            return False
        new_url=(dialog.textValue() or "").strip()
        valid=bool(re.match(r"^(https?://|ssh://|git@|file://|/|[A-Za-z]:[\\/])",new_url))
        if not valid:
            QMessageBox.warning(self,"OSCam-Emu Git",
                "Bitte eine gültige Git-Repository-URL eingeben." if is_de else
                "Please enter a valid Git repository URL.")
            return False

        # Die Auswahl sofort als aktive Patch-Quelle merken.
        # create_patch() darf hier NICHT wieder auf eine alte
        # emu_repo_url aus der geladenen Config zurückfallen.
        self.EMUREPO = new_url
        self.selected_emu_repo_url = new_url
        self.selected_emu_repo_branch = str(
            getattr(self, "selected_emu_repo_branch", "master") or "master"
        ).strip() or "master"

        # Eine OSCam-Emu-Revision gehört immer zu genau EINEM Repository.
        # Wird über "Repo URL" das Repository gewechselt, darf eine zuvor
        # ausgewählte SHA aus dem alten Repository nicht weiterverwendet werden.
        self.selected_emu_commit = None
        self.selected_emu_commit_repo_url = ""
        self.display_emu_commit = None
        globals()["SELECTED_EMU_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT_REPO_URL"] = ""

        globals()["EMUREPO"] = new_url
        globals()["SELECTED_EMU_REPO_URL"] = new_url
        globals()["SELECTED_EMU_REPO_BRANCH"] = self.selected_emu_repo_branch
        if hasattr(self,"cfg"):
            self.cfg["EMUREPO"]=new_url
            self.cfg["emu_repo_url"]=new_url
            saver=globals().get("save_config")
            if callable(saver):
                saver(self.cfg,gui_instance=self)

        pbar=getattr(self,"progress_bar",None)
        if pbar:
            pbar.setValue(100)
            pbar.setFormat(("✅ OSCam-Emu Git gesetzt: %p%" if is_de else "✅ OSCam-Emu Git selected: %p%"))
            pbar.show()
            QTimer.singleShot(2500,getattr(self,"pbar_idle",lambda:pbar.setValue(0)))
        # Nach einem Repo-Wechsel die Revision-Anzeige sofort auf den
        # aktuellen Stand des neu gewählten OSCam-Emu-Repositories setzen.
        try:
            self.update_revision_button_labels()
        except Exception:
            pass

        if hasattr(self,"info_text"):
            self.info_text.append(
                f"<b>✅ OSCam-Emu Git: {new_url}</b>"
            )
            
            self.info_text.append(
                "<b>ℹ️ OSCam-Emu Revision:</b> "
                "<b>Auswahl zurückgesetzt – beim nächsten Create Patch "
                "wird der aktuelle Branch-Stand dieses Repositories verwendet.</b>"
            )

            self.info_text.ensureCursorVisible()
        return True




    
    def resizeEvent(self, event):
        """
        Zentrale Steuerung für die UI-Skalierung bei Auflösungsänderung.
        Passt Header, Logo, Schriftgrößen und Overlay an.
        """
        super().resizeEvent(event)

        # Sichtbares finales Label an die aktuelle Position des Fortschrittsbalkens anpassen.
        try:
            pbar = getattr(self, "progress_bar", None)
            label = getattr(self, "final_label", None)

            if (
                pbar is not None
                and label is not None
                and label.isVisible()
                and label.parentWidget() == self
            ):
                pbar_pos = pbar.mapTo(self, pbar.rect().topLeft())
                label.setGeometry(
                    pbar_pos.x(),
                    pbar_pos.y(),
                    pbar.width(),
                    pbar.height(),
                )
                label.raise_()
        except Exception as exc:
            print(f"[FINAL-LABEL-RESIZE] {exc!r}", flush=True)

        # Responsive Breiten für Status- und Einstellungsleiste:
        # feste Pixelbreiten waren auf schmalen Fenstern unnötig platzintensiv.
        try:
            compact = self.width() < 1150
            if hasattr(self, "status_info_label"):
                self.status_info_label.setFixedWidth(145 if compact else 220)
                self.status_info_label.setStyleSheet(
                    "color: #FF0000; font-size: %dpx; font-weight: bold; border: none; background: transparent;"
                    % (20 if compact else 25)
                )
            if hasattr(self, "btn_matrix"):
                self.btn_matrix.setFixedWidth(180 if compact else 300)
            if hasattr(self, "btn_theme"):
                self.btn_theme.setFixedWidth(130 if compact else 200)
            if hasattr(self, "slider_speed"):
                self.slider_speed.setFixedWidth(75 if compact else 110)
            if hasattr(self, "lbl_speed_val"):
                self.lbl_speed_val.setFixedWidth(65 if compact else 85)
            if hasattr(self, "language_box"):
                self.language_box.setFixedWidth(65 if compact else 80)
            if hasattr(self, "color_label"):
                self.color_label.setFixedWidth(85 if compact else 120)
            if hasattr(self, "color_box"):
                self.color_box.setFixedWidth(250)
            if hasattr(self, "commit_label"):
                self.commit_label.setFixedWidth(100 if compact else 140)
            if hasattr(self, "commit_spin"):
                self.commit_spin.setFixedWidth(65 if compact else 75)
            if hasattr(self, "btn_check_tools"):
                self.btn_check_tools.setFixedWidth(165 if compact else 360)
        except RuntimeError:
            # Widgets können während des Schließens bereits zerstört sein.
            pass

        # Buttonhöhen und Beschriftungen bei jeder Fenstergrößenänderung neu berechnen.
        QTimer.singleShot(0, self._fit_all_button_texts)

        # 1. Header-Steuerelemente responsiv anpassen
        if hasattr(self, "header_widget"):
            QTimer.singleShot(0, self._fit_header_controls)

        # 2. Dynamische Schriftgrößen berechnen
        dynamic_size = max(10, int(self.width() / 90))

        button_font = QFont(
            "Arial", dynamic_size, QFont.Weight.Bold
        )
        label_font = QFont(
            "Arial", max(9, dynamic_size - 1)
        )
        clock_font = QFont(
            "Arial",
            max(12, int(dynamic_size * 0.9)),
            QFont.Weight.Bold,
        )

        # 3. Alle Buttons aktualisieren
        for btn in getattr(self, "all_buttons", []):
            btn.setFont(button_font)

            if not btn.icon().isNull():
                icon_dim = int(dynamic_size * 2.0)
                btn.setIconSize(QSize(icon_dim, icon_dim))

        # 4. Aktions-Grid aktualisieren
        for btn in getattr(self, "buttons", {}).values():
            btn.setFont(button_font)

        # 5. Uhr aktualisieren
        
        # Uhr und Datum immer gleich groß und fett
        clock_date_font = QFont(
            "Segoe UI",
            max(12, int(dynamic_size * 0.9)),
            QFont.Weight.Bold,
        )

        if hasattr(self, "digital_clock"):
            self.digital_clock.setFont(clock_date_font)

        if hasattr(self, "date_label"):
            self.date_label.setFont(clock_date_font)


        # 6. Header-Labels aktualisieren
        if hasattr(self, "lang_label"):
            self.lang_label.setFont(label_font)

        if hasattr(self, "color_label"):
            self.color_label.setFont(label_font)

        if hasattr(self, "commit_label"):
            self.commit_label.setFont(label_font)

        # 7. Logo einmal nach der Layout-Aktualisierung skalieren
        if (
            hasattr(self, "logo_label")
            and getattr(self, "original_pixmap", None) is not None
        ):
            QTimer.singleShot(0, self._fit_header_logo)

        # 8. Info-Text aktualisieren
        if hasattr(self, "info_text"):
            text_font = QFont(
                "Courier", max(10, dynamic_size)
            )
            self.info_text.setFont(text_font)

        # 9. Lade-Overlay nur skalieren, wenn es sichtbar ist.
        # Ein verborgenes Overlay darf nach dem Sprachwechsel nicht
        # versehentlich wieder die gesamte Fensterfläche belegen.
        overlay = getattr(self, "loading_overlay", None)
        if overlay is not None and overlay.isVisible():
            overlay.setGeometry(self.rect())


    def _save_window_state(self):
        """Speichert Fenstergröße, Position und Maximierungszustand."""
        try:
            settings = getattr(
                self, "_window_settings",
                QSettings("speedy005", "OSCamPatchManager")
            )
            settings.setValue("window/geometry", self.saveGeometry())
            settings.setValue("window/maximized", self.isMaximized())
            settings.sync()
            print("[WINDOW] Fensterzustand gespeichert:", settings.fileName())
        except Exception as exc:
            print(f"[WINDOW] Speichern fehlgeschlagen: {exc}")

    def _restore_window_state_after_show(self):
        """Startet das Hauptfenster immer im echten Vollbildmodus."""
        try:
            self.showFullScreen()
            self.updateGeometry()
            print("[WINDOW] Echtes Vollbild aktiviert.", flush=True)
        except Exception as exc:
            print(f"[WINDOW] Vollbild fehlgeschlagen: {exc}", flush=True)

    def closeEvent(self, event):
        self._save_window_state()
        super().closeEvent(event)


    def _check_build_achievement_logs(self):
        """Zählt neue erfolgreiche SimpleBuild-Läufe genau einmal."""
        import os
        import re

        log_dir = getattr(self, "build_log_dir", None)
        if not log_dir or not os.path.isdir(log_dir):
            return

        seen = getattr(self, "_achievement_seen_build_logs", set())
        try:
            filenames = os.listdir(log_dir)
        except OSError as exc:
            print(f"[ACHIEVEMENT] Build-Logs nicht lesbar: {exc}")
            return

        for filename in filenames:
            if not filename.lower().endswith(".log"):
                continue

            log_path = os.path.abspath(os.path.join(log_dir, filename))
            if log_path in seen:
                continue

            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
                    handle.seek(0, os.SEEK_END)
                    size = handle.tell()
                    handle.seek(max(0, size - 16384), os.SEEK_SET)
                    tail = handle.read()

                match = re.search(r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", tail)
                if not match:
                    continue

                seen.add(log_path)
                if int(match.group(1)) == 0:
                    try:
                        from achievement_system import record_event
                        record_event("build_success", filename)
                        print(f"[ACHIEVEMENT] Erfolgreicher Build gezählt: {filename}")
                    except Exception as exc:
                        print(f"[ACHIEVEMENT] Registrierung fehlgeschlagen: {exc}")

            except OSError as exc:
                print(f"[ACHIEVEMENT] Logdatei nicht lesbar ({filename}): {exc}")

        self._achievement_seen_build_logs = seen







    
    

    
  



    

    
    


    # ======= HIER EINSETZEN =======


    








    # 🔹 HIER EINSETZEN 🔹




    # ---------------------
        # hier später:
        # - git pull
        # - zip download + entpacken
        # - oder installer starten



    





    # ===================== ZIP PATCH =====================





    
    





        # ---------------------
        # PLUGIN UPDATE
        # ---------------------





    # ---------------------
    # UPDATE CHECK
    # ---------------------
        # =====================
        # INIT UI
        # =====================

    def init_ui(self):
        from PyQt6.QtWidgets import (
            QVBoxLayout,
            QHBoxLayout,
            QGridLayout,
            QLabel,
            QPushButton,
            QWidget,
            QTextEdit,
            QComboBox,
            QSpinBox,
            QProgressBar,
            QApplication,
            QFrame,
            QFileDialog,
        )
        from PyQt6.QtWidgets import QStyle, QSizePolicy
        from PyQt6.QtGui import QPixmap, QFont
        from PyQt6.QtCore import Qt, QSize, QTimer, QDateTime

        import subprocess
        import os
        import requests

        # ---------------------------------------------------------
        # 1. Grundwerte & Hauptlayout
        # ---------------------------------------------------------
        self.UI_BUTTON_H = 50
        self.UI_BADGE_H = 50
        self.UI_PROGRESS_H = 25
        self.UI_STATUS_H = 50
        self.UI_RADIUS = 10

        B_HEIGHT = self.UI_BUTTON_H
        B_WIDTH = 300
        CONTROL_HEIGHT = self.UI_BUTTON_H
        self.BUTTON_HEIGHT = self.UI_BUTTON_H
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 10, 12, 14)
        self.setStyleSheet("""
            QWidget { background-color: #10141d; color: #e8f1ff; }
            QGroupBox {
                background-color: #171d29;
                border: 1px solid #29384b;
                border-radius: 12px;
                margin-top: 13px;
                padding: 10px 8px 8px 8px;
                font-weight: 800;
                color: #35e6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #35e6ff;
                letter-spacing: 1px;
            }
            QToolTip {
                background: #111827; color: #f2f7ff;
                border: 1px solid #35e6ff; padding: 7px; border-radius: 6px;
            }
        """)
        self.create_buttons()
        
        # =========================================================
        # HEADER-BEREICH (STEAM / DISCORD CLEAN)
        # =========================================================

        header_widget = QFrame()
        self.header_widget = header_widget
        header_widget.setMinimumHeight(160)
        header_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_widget.setStyleSheet(
            """
            QFrame {
                background-color: #2F2F2F;
                border: 1px solid #444;
                border-radius: 10px;
            }
            QLabel {
                background-color: transparent;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                color: #EAFF00 !important;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #EAFF00;
                color: white !important;
            }
        """
        )

        header_layout = QHBoxLayout(header_widget)
        self.header_layout = header_layout
        header_layout.setContentsMargins(8, 6, 0, 6)
        header_layout.setSpacing(6)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # =========================================================
        # LEFT SECTION
        # =========================================================

        left_header_container = QWidget()
        left_header_layout = QHBoxLayout(left_header_container)
        self.left_header_layout = left_header_layout
        left_header_layout.setContentsMargins(4, 0, 0, 0)
        left_header_layout.setSpacing(8)
        left_header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # --- INFO BUTTON ---
        self.info_button = QPushButton()
        self.info_button.setMinimumSize(36, 36)
        self.info_button.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed
        )

        icon_info = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxInformation
        )
        self.info_button.setIcon(icon_info)
        self.info_button.setIconSize(QSize(28, 28))
        self.info_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Tooltip entsprechend der aktuellen Sprache
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")

        self.info_button.setToolTip(
            "Zeigt Informationen über das OSCam Toolkit an."
            if is_de
            else "Displays information about the OSCam Toolkit."
        )
        self.info_button.setToolTipDuration(10000)

        # Klick öffnet das Info-Fenster
        self.info_button.clicked.connect(self.show_info)

        left_header_layout.addWidget(self.info_button)


        # =========================================================
        # CLOCK + DATE (WICHTIG: VBOX = UNTEREINANDER)
        # =========================================================

        time_date_container = QWidget()
        time_date_layout = QVBoxLayout(time_date_container)
        time_date_layout.setContentsMargins(0, 0, 0, 0)
        time_date_layout.setSpacing(1)
        time_date_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        bold_font_time = QFont("Segoe UI", 8, QFont.Weight.Bold)
        bold_font_date = QFont("Segoe UI", 8, QFont.Weight.Bold)

        # --- CLOCK ---
        self.digital_clock = QLabel("--:--:--")
        self.digital_clock.setFont(bold_font_time)
        self.digital_clock.setStyleSheet("color: red;")
        time_date_layout.addWidget(self.digital_clock, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- DATE ---
        self.date_label = QLabel("--.--.----")
        self.date_label.setFont(bold_font_date)
        self.date_label.setStyleSheet("color: orange; background: transparent;")
        time_date_layout.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignLeft)


        
        # =========================================================
        # BUTTON CARD + S3 REPOSITORY-AUSWAHL
        # =========================================================

        btn_card = QWidget()
        btn_card_layout = QVBoxLayout(btn_card)
        btn_card_layout.setContentsMargins(0, 0, 0, 0)
        btn_card_layout.setSpacing(6)
        btn_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        s3_s4_h_layout = QHBoxLayout()
        s3_s4_h_layout.setSpacing(8)
        s3_s4_h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _install_btn in (self.btn_s3, self.btn_s4, self.btn_ncam):
            _install_btn.setMinimumSize(105, 45)
            _install_btn.setMaximumWidth(260)
            _install_btn.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )

        s3_s4_h_layout.addWidget(self.btn_s3)
        s3_s4_h_layout.addWidget(self.btn_s4)
        btn_card_layout.addLayout(s3_s4_h_layout)

        btn_card_layout.addWidget(
            self.btn_ncam,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # ---------------------------------------------------------
        # S3 GIT-REPOSITORY AUSWÄHLEN
        # ---------------------------------------------------------
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        # Konfiguration laden, sofern noch nicht vorhanden.
        if not isinstance(getattr(self, "current_config", None), dict):
            self.current_config = {}

        self.cfg = self.current_config

        saved_repo_name = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)",
        )

        if saved_repo_name == "S3 Simplebuild":
            saved_repo_name = "S3 Simplebuild speeddy005"
        if saved_repo_name not in self.s3_repository_options:
            saved_repo_name = "S3 Simplebuild (Original)"

        self.selected_s3_repository = saved_repo_name

        self.s3_repo_label = QLabel("S3 Git-Quelle:")
        self.s3_repo_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.s3_repo_label.setStyleSheet(
            "color: #EAFF00; background: transparent; "
            "font-weight: bold; border: none;"
        )

        self.s3_repo_combo = QComboBox()
        self.s3_repo_combo.setObjectName("s3RepositoryCombo")
        self.s3_repo_combo.addItems(
            list(self.s3_repository_options.keys())
        )
        self.s3_repo_combo.setCurrentText(saved_repo_name)
        self.s3_repo_combo.setMinimumWidth(230)
        self.s3_repo_combo.setMinimumHeight(34)
        self.s3_repo_combo.setToolTip(
            "Repository auswählen, das bei der S3-Installation verwendet wird."
        )
        self.s3_repo_combo.setStyleSheet("""
            QComboBox {
                color: #EAFF00;
                background-color: #252525;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 5px 8px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 1px solid #EAFF00;
            }
            QComboBox QAbstractItemView {
                color: #EAFF00;
                background-color: #252525;
                selection-background-color: #444;
                selection-color: white;
            }
        """)

        s3_repo_row = QHBoxLayout()
        s3_repo_row.setContentsMargins(0, 0, 0, 0)
        s3_repo_row.setSpacing(6)
        s3_repo_row.addWidget(self.s3_repo_label)
        s3_repo_row.addWidget(self.s3_repo_combo, 1)

        # Die Git-Quelle wird erst nach Auswahl des Installationspfads abgefragt.
        # Deshalb wird die ComboBox nicht unter den drei Hauptbuttons angezeigt.

        # Nur verbinden, nicht zusätzlich den S3-Button verdrahten.
        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )

        # =========================================================
        # LEFT BUILD (ORDER WICHTIG!)
        # =========================================================

        left_header_layout.addWidget(time_date_container)
        left_header_layout.addWidget(btn_card)



        # =========================================================
        #         FINAL HEADER ASSEMBLY
        # =========================================================

        # LEFT-HEADER wird erst beim finalen Layout einmalig eingefügt.

        # =========================================================
        # SIGNALS (UNCHANGED)
        # =========================================================

        self.btn_s3.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_s3.customContextMenuRequested.connect(self.select_s3_path_manually)
        self.btn_s3.clicked.connect(self.start_s3_install)

        self.btn_s4.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_s4.customContextMenuRequested.connect(self.select_s4_path_manually)
        self.btn_s4.clicked.connect(self.start_s4_install)

        self.btn_ncam.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_ncam.customContextMenuRequested.connect(self.select_ncam_path_manually)
        self.btn_ncam.clicked.connect(self.start_ncam_install)


        # =========================================================
        # FINAL HEADER ATTACH
        # =========================================================

        header_layout.addWidget(left_header_container, 0)
        #header_layout.addStretch(1)
        # --- MIDDLE: Logo (responsive) ---
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumSize(0, 0)
        self.logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        header_layout.addWidget(self.logo_label, 1)


        self.original_pixmap = None

        try:
            url = (
                "https://raw.githubusercontent.com/"
                "speedy005/oscam_patch_manager_new/master/"
                "speedy_banner.png"
            )

            resp = requests.get(url, timeout=5)
            resp.raise_for_status()

            pixmap = QPixmap()
            if pixmap.loadFromData(resp.content):
                self.original_pixmap = pixmap
                QTimer.singleShot(0, self._fit_header_logo)
            else:
                raise ValueError("Logo konnte nicht geladen werden")

        except Exception as exc:
            self.logo_label.setText("OSCAM TOOLKIT")
            self.logo_label.setStyleSheet(
                "color: white; font-size: 18px;"
            )
            self.original_pixmap = None
            print(f"Logo konnte nicht geladen werden: {exc}")



        # --- RIGHT: Log-Button + Version & Autor (OPTIMIERT) ---
        right_header_container = QWidget()
        right_header_layout = QHBoxLayout(right_header_container)
        self.right_header_layout = right_header_layout
        right_header_layout.setContentsMargins(0, 0, 0, 0)
        right_header_layout.setSpacing(8)
        right_header_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        # --- INSTALLATION / PATCH-BEREICH ZWISCHEN LABEL/LOG ---
        lang = getattr(self, "LANG", "de").lower()
        # Zwei Spalten: links die Patch-Ordner, rechts die Patch-Kopieraktionen.
        install_path_container = QWidget()
        install_path_layout = QHBoxLayout(install_path_container)
        install_path_layout.setContentsMargins(0, 0, 0, 0)
        install_path_layout.setSpacing(3)
        # Patch-Buttons oben bündig mit "Log speichern" / "Musik einschalten"
        install_path_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        path_button_column = QWidget()
        path_button_layout = QVBoxLayout(path_button_column)
        path_button_layout.setContentsMargins(0, 0, 0, 0)
        path_button_layout.setSpacing(3)
        path_button_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        patch_button_column = QWidget()
        patch_button_layout = QVBoxLayout(patch_button_column)
        patch_button_layout.setContentsMargins(0, 0, 0, 0)
        patch_button_layout.setSpacing(3)
        patch_button_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )

        self.header_btn_s3_ncam = QPushButton(self.TEXT.get("patch_folder_s3_ncam", "S3-NCam-Bonecrew-Pfad"))
        self.header_btn_s3_ncam.setMinimumSize(240, 50)
        self.header_btn_s3_ncam.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_s3_ncam.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_s3_ncam.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirOpenIcon))
        self.header_btn_s3_ncam.setIconSize(QSize(20, 20))
        self.header_btn_s3_ncam.setToolTip(
            self.TEXT.get("patch_folder_s3_ncam_tooltip", "S3-NCam-Bonecrew-Pfad wählen")
        )
        self.header_btn_s3_ncam.clicked.connect(self.select_ncam_patch_path_manually)
        path_button_layout.addWidget(self.header_btn_s3_ncam)

        # Player direkt unter dem S3-Patch-Pfad platzieren.
        self.music_player_button = QPushButton("🎚 Player öffnen" if lang == "de" else "🎚 Open player")
        self.music_player_button.setMinimumSize(240, 50)
        self.music_player_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.music_player_button.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.music_player_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.music_player_button.setToolTip(
            "Separaten Cyber Music Player öffnen"
            if lang == "de" else "Open the separate Cyber Music Player"
        )
        self.music_player_button.clicked.connect(self.open_external_music_player)
        self._music_player_window = None
        

        self.header_btn_s4 = QPushButton(self.TEXT.get("patch_folder_s4", "S4-Pfad"))
        self.header_btn_s4.setMinimumSize(240, 50)
        self.header_btn_s4.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_s4.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_s4.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirOpenIcon))
        self.header_btn_s4.setIconSize(QSize(20, 20))
        self.header_btn_s4.setToolTip(
            self.TEXT.get("patch_folder_s4_tooltip", "S4-Pfad wählen")
        )
        self.header_btn_s4.clicked.connect(self.select_s4_patch_path_manually)
        path_button_layout.addWidget(self.header_btn_s4)
        path_button_layout.addWidget(self.music_player_button)
        # Die beiden Patch-Kopieraktionen ebenfalls untereinander.
        self.header_btn_patch_ncam = QPushButton(self.TEXT.get("patch_copy_s3_ncam", "Patch → S3-NCam"))
        self.header_btn_patch_ncam.setMinimumSize(240, 50)
        self.header_btn_patch_ncam.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_patch_ncam.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_patch_ncam.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        self.header_btn_patch_ncam.setIconSize(QSize(20, 20))
        self.header_btn_patch_ncam.setToolTip(
            "Kopiert oscam-emu.patch in den konfigurierten S3-NCam-Bonecrew-Patch-Ordner."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Copies oscam-emu.patch to the configured S3-NCam-Bonecrew patch folder."
        )
        self.header_btn_patch_ncam.clicked.connect(
            lambda checked=False: self.copy_patch_to_target("ncam")
        )
        patch_button_layout.addWidget(self.header_btn_patch_ncam)

        self.header_btn_patch_s4 = QPushButton(self.TEXT.get("patch_copy_s4", "Patch → S4"))
        self.header_btn_patch_s4.setMinimumSize(240, 50)
        self.header_btn_patch_s4.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_patch_s4.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_patch_s4.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        self.header_btn_patch_s4.setIconSize(QSize(20, 20))
        self.header_btn_patch_s4.setToolTip(
            "Kopiert oscam-emu.patch in den konfigurierten S4-Patch-Ordner."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Copies oscam-emu.patch to the configured S4 patch folder."
        )
        self.header_btn_patch_s4.clicked.connect(
            lambda checked=False: self.copy_patch_to_target("s4")
        )
        patch_button_layout.addWidget(self.header_btn_patch_s4)

        # --- WETTERBUTTON ---
        self.weather_button = QPushButton(
            "🌤 Wetter anzeigen" if lang == "de" else "🌤 Show weather"
        )
        self.weather_button.setMinimumSize(240, 50)
        self.weather_button.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )
        self.weather_button.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.weather_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.weather_button.setToolTip(
            "Aktuelles Wetter und 5-Tage-Vorhersage anzeigen"
            if lang == "de"
            else "Show current weather and 5-day forecast"
        )
        self.weather_button.clicked.connect(
            lambda checked=False: open_weather_window(self)
        )
        patch_button_layout.addWidget(self.weather_button)

        install_path_layout.addWidget(path_button_column)
        install_path_layout.addWidget(patch_button_column)

        
        # ---------------------------------------------------------
        # HEADER-AKTIONEN
        # Log speichern | Stats
        # Oscam Git URL leicht nach links versetzt darunter
        # ---------------------------------------------------------

        header_actions_container = QWidget()
        header_actions_layout = QGridLayout(header_actions_container)
        header_actions_layout.setContentsMargins(0, 0, 0, 0)
        header_actions_layout.setHorizontalSpacing(3)
        header_actions_layout.setVerticalSpacing(3)
        header_actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )

        # Einheitlicher Stil für ALLE Aktionsbuttons
        action_button_style = """
            QPushButton {
                color: #EAFF00;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 7px;
                padding: 2px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #EAFF00;
                color: white;
            }
            QPushButton:pressed {
                background-color: #222;
                border: 1px solid white;
            }
        """

        # Stil erst nach Definition anwenden (verhindert UnboundLocalError).
        self.music_player_button.setStyleSheet(action_button_style)

        # --- LOG SPEICHERN ---
        log_text = "Log speichern" if lang == "de" else "Save Log"

        self.log_button = QPushButton(log_text)
        self.log_button.setMinimumSize(120, 50)
        self.log_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.log_button.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.log_button.setIcon(
            self.style().standardIcon(
                QApplication.style().StandardPixmap.SP_DriveHDIcon
            )
        )
        self.log_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.log_button.setToolTip(
            "Speichert den aktuellen Log-/Protokollinhalt in einer Datei."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Saves the current log output to a file."
        )
        self.log_button.setStyleSheet(action_button_style)

        if hasattr(self, "export_log"):
            self.log_button.clicked.connect(self.export_log)

        # Musik-Einstellungen dauerhaft speichern (Titel und Wiedergabestatus).
        self._music_settings = QSettings("speedy005", "OSCamPatchManager")

        # --- HINTERGRUNDMUSIK (sounds-Ordner im Tool-Verzeichnis) ---
        self.music_button = QPushButton("🎵 Musik einschalten" if lang == "de" else "🎵 Music on")
        self.music_button.setCheckable(True)
        self.music_button.setMinimumSize(120, 50)
        self.music_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.music_button.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.music_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.music_button.setStyleSheet(action_button_style)

        # Log- und Musikbutton immer exakt gleich groß halten.
        self.log_button.setFixedSize(240, 50)
        self.music_button.setFixedSize(240, 50)

        self.music_button.setToolTip(
            "Hintergrundmusik aus dem Ordner sounds ein- oder ausschalten."
            if lang == "de" else
            "Toggle background music from the sounds folder."
        )
        # Erst alle Musik-Attribute und die Titelauswahl initialisieren.
        # Das Wiederherstellen von "playing" kann toggled direkt auslösen.
        self._background_music_files = []
        self._background_music_player = None
        self._background_music_output = None
        self.music_title_combo = QComboBox()
        self.music_title_combo.setMinimumWidth(200)
        self.music_title_combo.setMaximumWidth(240)
        self.music_title_combo.setToolTip(
            "Musiktitel auswählen" if lang == "de" else "Choose a music track"
        )
        self.music_title_combo.setStyleSheet(
            "QComboBox { padding: 5px 8px; border-radius: 6px; }"
        )
        self.music_title_combo.currentIndexChanged.connect(self.on_background_music_selection_changed)
        self._refresh_background_music_titles()

        # Gespeicherten Titel und Wiedergabestatus laden.
        saved_playing = self._music_settings.value(
            "music/playing", False, type=bool
        )
        saved_resume_track = str(
            self._music_settings.value("music_player/resume_track", "") or ""
        )
        preferred_track = (
            saved_resume_track if saved_playing and saved_resume_track
            else str(self._music_settings.value("music/track", "__random__") or "__random__")
        )

        preferred_index = self.music_title_combo.findData(preferred_track)
        if preferred_index >= 0:
            self.music_title_combo.blockSignals(True)
            self.music_title_combo.setCurrentIndex(preferred_index)
            self.music_title_combo.blockSignals(False)

        self._background_music_restore_track = saved_resume_track
        try:
            self._background_music_restore_position = max(
                0, int(self._music_settings.value("music_player/resume_position", 0))
            )
        except (TypeError, ValueError):
            self._background_music_restore_position = 0

        self._background_music_restore_attempts = 0
        self._background_music_restore_pending = bool(
            saved_playing
            and saved_resume_track
            and self._background_music_restore_position > 0
        )

        self.music_button.toggled.connect(self.toggle_background_music)
        self.music_button.setChecked(saved_playing)

        # Speichern unabhängig vom geöffneten NEON-BEAST-Fenster.
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

        self._background_music_save_timer = QTimer(self)
        self._background_music_save_timer.setInterval(2000)
        self._background_music_save_timer.timeout.connect(
            self._save_background_music_state
        )
        self._background_music_save_timer.start()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._save_background_music_state)

        if self._background_music_restore_pending:
            QTimer.singleShot(700, self._retry_background_music_restore)

        # --- STATS ---
        self.telemetry_cb = QPushButton("Stats")
        self.telemetry_cb.setCheckable(True)
        self.telemetry_cb.setMinimumSize(58, 32)
        self.telemetry_cb.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.telemetry_cb.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.telemetry_cb.setChecked(
            bool(get_setting("allow_telemetry", True))
        )
        self.telemetry_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.telemetry_cb.setToolTip(
            "Anonyme Nutzungsstatistik (Hit-Counter) erlauben/verbieten."
            if lang == "de" else
            "Allow/disallow anonymous usage statistics (Hit-Counter)."
        )
        self.telemetry_cb.setAccessibleName(
            "Stats aktivieren oder deaktivieren"
        )
        self.telemetry_cb.setStyleSheet(action_button_style)
        self.telemetry_cb.toggled.connect(self.on_telemetry_changed)

        # --- OSCAM-GIT-URL ---
        self.oscam_source_button = QPushButton("Oscam Git URL")
        self.oscam_source_button.setMinimumSize(300, 45)
        self.oscam_source_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.oscam_source_button.setFont(
            QFont("Segoe UI", 8, QFont.Weight.Bold)
        )
        self.oscam_source_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirLinkIcon))
        self.oscam_source_button.setIconSize(QSize(20, 20))
        self.oscam_source_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.oscam_source_button.setToolTip(
            "Quelle für Create Patch und OSCam-Emu-Git Patch auswählen"
            if lang == "de" else
            "Choose source for Create Patch and OSCam-Emu-Git Patch"
        )
        self.oscam_source_button.setStyleSheet(action_button_style)
        self.oscam_source_button.clicked.connect(self.choose_oscam_source)

        # --- OBERE REIHE ---
        header_actions_layout.addWidget(self.log_button, 0, 0, 1, 2) 

        # Musikbutton direkt unter "Log speichern".
        header_actions_layout.addWidget(self.music_button, 1, 0, 1, 2)
        header_actions_layout.addWidget(
            self.music_title_combo, 2, 0, 1, 1,
            alignment=Qt.AlignmentFlag.AlignCenter
        )
        header_actions_layout.addWidget(
            self.oscam_source_button, 2, 1, 1, 1,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Aktionsblock rechts neben den Patch-Kopierbuttons einsetzen.
        install_path_layout.addWidget(header_actions_container)


        # Kompakte, zum bestehenden Header passende Optik.
        for _btn in (
            self.header_btn_s3_ncam,
            self.header_btn_s4,
            self.header_btn_patch_ncam,
            self.header_btn_patch_s4,
        ):
            _btn.setMinimumWidth(0)
            _btn.setCursor(Qt.CursorShape.PointingHandCursor)
            _btn.setStyleSheet("""
                QPushButton {
                    color: #EAFF00;
                    background-color: #3d3d3d;
                    border: 1px solid #555;
                    border-radius: 7px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                    border: 1px solid #EAFF00;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #222;
                    border: 1px solid white;
                }
            """)

        # Die Installations-/Patch-Aktionen sind Teil des rechten Header-Bereichs;
        # das Logo bleibt dadurch mittig zwischen linker und rechter Seite.

        # Fonts definieren, BEVOR sie benutzt werden (löst NameError)
        bold_font_header = QFont("Segoe UI", 25, QFont.Weight.Bold)
        bold_font_version = QFont("Segoe UI", 25, QFont.Weight.Bold)

        # Container für die Labels rechts oben
        version_text_container = QWidget()
        version_text_layout = QVBoxLayout(version_text_container)
        version_text_layout.setContentsMargins(8, 0, 8, 0)
        version_text_layout.setSpacing(2)
        version_text_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        # Farben und Version holen
        current_diff_colors = getattr(self, "current_diff_colors", {"fg": "#FF0000"})
        text_color = current_diff_colors.get("fg", "#EAFF00")
        app_v = getattr(self, "APP_VERSION", globals().get("APP_VERSION", "4.0.0"))

        # Das Haupt-Versionslabel (Das farbige)
        # WICHTIG: Wir weisen es self.version_label zu, damit es später aktualisierbar ist
        self.version_label = QLabel(f"v{app_v}")
        self.version_label.setFont(bold_font_version)
        self.version_label.setStyleSheet(
            f"color: {text_color}; background: transparent; margin-bottom: 5px;"
        )

        # Autor Label (Blau im Screenshot)
        self.by_label = QLabel("by speedy005")
        self.by_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.by_label.setStyleSheet("color: #0055ff; background: transparent;")

        # In den kleinen Container packen
        version_text_layout.addWidget(self.version_label)
        version_text_layout.addWidget(self.by_label)

        # Installations-/Patch-Buttons rechts neben dem mittigen Banner.
        # Version, Stats und "by speedy005" bleiben ganz rechts.
        right_header_layout.addWidget(install_path_container)
        right_header_layout.setSpacing(4)

        # Versionsanzeige etwas nach rechts verschieben
        right_header_layout.addSpacing(40)

        right_header_layout.addWidget(version_text_container)

        self.telemetry_cb.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        right_header_layout.addWidget(
            self.telemetry_cb,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        # Zum Haupt-Header hinzufügen
        header_layout.addWidget(right_header_container, 0)

        main_layout.addWidget(header_widget)
        QTimer.singleShot(0, self._fit_header_controls)
        # Theme-Farben und Tooltips werden zentral anhand der aktuellen Sprache
        # und des ausgewählten Farbschemas gesetzt.
        self.apply_global_button_style()

        # ---------------------------------------------------------
        # INFO + PROGRESS
        # ---------------------------------------------------------
        # Große Live-Konsole als visueller Mittelpunkt der Oberfläche
        console_panel = QGroupBox("LIVE SYSTEM CONSOLE  /  STATUS & LOGS")
        self.console_panel = console_panel
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(10, 12, 10, 10)
        console_layout.setSpacing(8)
        self.info_text = QTextEdit()
        self.info_text.setObjectName("liveConsole")
        self.info_text.setReadOnly(True)
        # Begrenzung der sichtbaren Live-Konsole verhindert, dass sehr lange
        # Sitzungen unbegrenzt Speicher belegen. Build-Log-Dateien bleiben unberührt.
        try:
            self.info_text.document().setMaximumBlockCount(10000)
        except Exception as exc:
            print(f"[console] Begrenzung der Konsolenhistorie nicht verfügbar: {exc}")
        self.info_text.setMinimumHeight(0)
        self.info_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.info_text.setFont(QFont("Consolas", 11))
        self.info_text.setStyleSheet("""
            QTextEdit#liveConsole {
                background-color: #080c12; color: #b9f7ff;
                border: 1px solid #24465a; border-radius: 9px;
                padding: 10px; selection-background-color: #176b80;
            }
        """)
        # Werkzeugleiste: zwei Reihen mit 5 und 4 Buttons.
        console_tools = QVBoxLayout()
        console_tools.setContentsMargins(0, 0, 0, 0)
        console_tools.setSpacing(4)

        is_de = str(getattr(self, "LANG", LANG)).lower() == "de"
        copy_log_button = QPushButton("LOG KOPIEREN" if is_de else "COPY LOG")
        copy_log_button.setToolTip(
            "Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren"
            if is_de else "Copy all visible console output to the clipboard"
        )
        def copy_visible_console():
            """Kopiert ausschließlich den aktuell sichtbaren Konsoleninhalt."""
            try:
                QApplication.clipboard().setText(self.info_text.toPlainText())
            except Exception as exc:
                self.append_info(self.info_text, f"Kopieren fehlgeschlagen: {exc}", "error")

        copy_log_button.clicked.connect(copy_visible_console)
        self.copy_log_button = copy_log_button

        analyze_build_logs_button = QPushButton("BUILD-LOG ANALYSIEREN" if is_de else "ANALYZE BUILD LOG")
        analyze_build_logs_button.setToolTip(
            "Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen"
            if is_de else "Check the newest build log for common errors and warnings"
        )
        analyze_build_logs_button.clicked.connect(self.analyze_latest_build_log)
        self.analyze_build_logs_button = analyze_build_logs_button

        diagnostics_button = QPushButton("SYSTEM-DIAGNOSE" if is_de else "SYSTEM DIAGNOSTICS")
        diagnostics_button.setToolTip(
            "System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build"
            if is_de else "Check system, tool directories and existing build logs; does not start a build"
        )
        diagnostics_button.clicked.connect(self.open_diagnostics_dialog)
        self.diagnostics_button = diagnostics_button

        log_history_button = QPushButton("BUILD-LOG-VERLAUF" if is_de else "BUILD LOG HISTORY")
        log_history_button.setToolTip(
            "Alle Build-Logs nach Status, Zeit und Fehlerhinweisen vergleichen"
            if is_de else "Compare all build logs by status, time and error indicators"
        )
        log_history_button.clicked.connect(self.open_build_log_history)
        self.log_history_button = log_history_button

        clear_console_button = QPushButton("KONSOLE LEEREN" if is_de else "CLEAR CONSOLE")
        clear_console_button.setToolTip(
            "Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert"
            if is_de else "Clear only the visible console output; log files remain unchanged"
        )
        clear_console_button.clicked.connect(self.info_text.clear)
        self.clear_console_button = clear_console_button

        cyber_center_button = QPushButton("OSCAM CONTROL CENTER")
        cyber_center_button.setToolTip(
            "Zentrale für alle OSCam-Control-Center-Funktionen"
            if is_de else
            "Central hub for all OSCam Control Center features"
        )
        cyber_center_button.clicked.connect(
            lambda checked=False: _open_cyber_center(self)
        )
        self.cyber_center_button = cyber_center_button

        patch_diff_button = QPushButton(
            "PATCH VERGLEICHEN" if is_de else "COMPARE PATCHES"
        )
        patch_diff_button.setToolTip(
            "Zwei Patch-Dateien oder Git-Commits vergleichen"
            if is_de else
            "Compare two patch files or Git commits"
        )
        patch_diff_button.clicked.connect(
            lambda checked=False: _open_patch_diff_viewer(self)
        )
        self.patch_diff_button = patch_diff_button

        achievement_button = QPushButton(
            "🏆 ERFOLGE" if is_de else "🏆 ACHIEVEMENTS"
        )
        achievement_button.setToolTip(
            "Deine OSCam-Erfolge und Fortschritte anzeigen"
            if is_de else
            "View your OSCam achievements and progress"
        )
        achievement_button.clicked.connect(
            lambda checked=False: _open_achievement_system(self)
        )
        self.achievement_button = achievement_button

        ai_assistant_button = QPushButton(
            "🤖 KI-ASSISTENT" if is_de else "🤖 AI ASSISTANT"
        )
        ai_assistant_button.setToolTip(
            "KI-Chat für Patch-Analyse und Fehlersuche öffnen"
            if is_de else
            "Open AI chat for patch analysis and troubleshooting"
        )
        ai_assistant_button.clicked.connect(
            lambda checked=False: _open_ai_assistant(self)
        )
        self.ai_assistant_button = ai_assistant_button

        tool_buttons = (
            copy_log_button,
            analyze_build_logs_button,
            diagnostics_button,
            log_history_button,
            clear_console_button,
            cyber_center_button,
            patch_diff_button,
            achievement_button,
            ai_assistant_button,
        )

        from PyQt6.QtCore import QSize
        from PyQt6.QtWidgets import QStyle

        # Echte Qt-Symbole statt Emoji: funktionieren unabhängig von Emoji-Schriften.
        icon_labels = (
            ("LOG KOPIEREN", "COPY LOG"),
            ("BUILD-LOG ANALYSIEREN", "ANALYZE BUILD LOG"),
            ("SYSTEM-DIAGNOSE", "SYSTEM DIAGNOSTICS"),
            ("BUILD-LOG-VERLAUF", "BUILD LOG HISTORY"),
            ("KONSOLE LEEREN", "CLEAR CONSOLE"),
            ("OSCAM CONTROL CENTER", "OSCAM CONTROL CENTER"),
            ("PATCH VERGLEICHEN", "COMPARE PATCHES"),
            ("ERFOLGE", "ACHIEVEMENTS"),
            ("KI-ASSISTENT", "AI ASSISTANT"),
        )

        icon_names = (
            "SP_FileIcon",
            "SP_FileDialogContentsView",
            "SP_ComputerIcon",
            "SP_FileDialogDetailedView",
            "SP_TrashIcon",
            "SP_ComputerIcon",
            "SP_FileDialogDetailedView",
            "SP_DialogApplyButton",
            "SP_MessageBoxInformation",
        )

        for tool_button, labels, icon_name in zip(
            tool_buttons, icon_labels, icon_names
        ):
            tool_button.setText(labels[0] if is_de else labels[1])

            pixmap = getattr(
                QStyle.StandardPixmap,
                icon_name,
                QStyle.StandardPixmap.SP_FileIcon
            )
            tool_button.setIcon(self.style().standardIcon(pixmap))
            tool_button.setIconSize(QSize(20, 20))

            tool_font = tool_button.font()
            tool_font.setPointSizeF(13.0)
            tool_font.setBold(True)
            tool_button.setFont(tool_font)

            tool_button.setMinimumHeight(38)
            tool_button.setSizePolicy(
                QSizePolicy.Policy.Fixed,
                QSizePolicy.Policy.Fixed
            )

            # Automatische natürliche Breite inklusive echtem Qt-Icon.
            tool_button.ensurePolished()
            tool_button.adjustSize()

        # Dynamische Reihen mit maximal acht Buttons pro Reihe.
        # Erfolge steht am Ende der ersten Reihe, KI-Assistent beginnt Reihe zwei.
        buttons_per_row = 8

        for row_start in range(0, len(tool_buttons), buttons_per_row):
            button_row = QHBoxLayout()
            button_row.setSpacing(8)

            row_buttons = tool_buttons[
                row_start:row_start + buttons_per_row
            ]

            for tool_button in row_buttons:
                button_row.addWidget(tool_button)

            button_row.addStretch(1)
            console_tools.addLayout(button_row)
        console_layout.addLayout(console_tools)
        console_layout.addWidget(self.info_text, 1)
        main_layout.addWidget(console_panel, 20)

        # Auto-Scroll wird beim Hinzufügen neuer Meldungen gesteuert.
        # Kein periodischer Timer: so bleibt die Konsole ruhig, wenn der
        # Benutzer ältere Einträge liest.
        self.scroll_timer = None

        main_layout.addSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(self.UI_PROGRESS_H)
        self.progress_bar.setMaximumHeight(45)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet(
            """
        QProgressBar {
            border: 1px solid #444;
            border-radius: 8px;
            background-color: #1A1A1A;
            color: white;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                              stop:0 #F37804, stop:1 #FFD700);
            border-radius: 8px;
        }
        """
        )
        main_layout.addWidget(self.progress_bar)
        # self.pbar_idle()
        # ---------------------------------------------------------
        # STATUS-BAR (MAXIMALER AUSBAU: GROSSE ANZEIGEN & ZIP)
        # ---------------------------------------------------------
        status_bar_container = QFrame()
        status_bar_container.setFixedHeight(self.UI_STATUS_H)
        status_bar_container.setStyleSheet(
            "QFrame { background-color: rgba(0,0,0,0.4); border: 1px solid #444; border-radius: 10px; }"
        )

        status_bar_layout = QHBoxLayout(status_bar_container)
        status_bar_layout.setContentsMargins(15, 0, 15, 0)
        status_bar_layout.setSpacing(12)

        # FIX 1: Feste Breite und statische Attribute verhindern das "Zucken" des Textes
        self.status_info_label = QLabel("SYSTEM STATUS:")
        self.status_info_label.setFixedWidth(220)  # Reserviert festen Platz
        self.status_info_label.setAttribute(Qt.WidgetAttribute.WA_StaticContents)
        self.status_info_label.setStyleSheet(
            "color: #FF0000; font-size: 22px; font-weight: bold; border: none; background: transparent;"
        )
        status_bar_layout.addWidget(self.status_info_label)

        # Listen-Trennung für Stabilität
        self.status_leds = []  # Bleiben immer statisch (Grün/Rot)
        self.user_leds = []  # Nur für Slider-Blinken

        tools_to_check = [
            "py",
            "qt6",
            "snd",
            "git",
            "patch",
            "zip",
            "gcc",
            "make",
            "ssl",
            "usb",
        ]
        label_colors = {
            "py": "#3776AB",
            "qt6": "#41CD52",
            "snd": "#FF0000",
            "git": "#2ecc71",
            "patch": "#3498db",
            "zip": "#E24A39",
            "gcc": "#f1c40f",
            "make": "#e67e22",
            "ssl": "#9b59b6",
            "usb": "#1abc9c",
        }

        for tool in tools_to_check:
            exists = False
            display_name = tool.upper()

            # --- SYSTEM CHECK ---
            if tool == "py":
                exists = True
                display_name = f"PY {sys.version_info.major}.{sys.version_info.minor}"
            elif tool == "qt6":
                exists = importlib.util.find_spec("PyQt6") is not None
            elif tool == "snd":
                exists = (
                    any(shutil.which(c) for c in ["paplay", "pw-play", "aplay"])
                    or platform.system() == "Windows"
                )
                display_name = "SOUND"
            elif tool in ["ssl", "usb"]:
                if platform.system() == "Linux" and shutil.which("dpkg"):
                    pkg = "libssl-dev" if tool == "ssl" else "libusb-1.0-0-dev"
                    exists = (
                        subprocess.run(
                            ["dpkg-query", "-W", "-f='${Status}'", pkg],
                            capture_output=True,
                            text=True,
                        ).returncode
                        == 0
                    )
                else:
                    exists = True
            else:
                exists = shutil.which(tool) is not None

            # Tool Container
            t_widget = QWidget()
            # FIX 2: Feste Breite für Container verhindert Layout-Verschiebungen in der Zeile
            t_widget.setMinimumWidth(80)
            t_lay = QHBoxLayout(t_widget)
            t_lay.setContentsMargins(0, 0, 0, 0)
            t_lay.setSpacing(6)

            # SYSTEM LED (Wird nur EINMAL gefärbt)
            led = QLabel()
            led.setFixedSize(16, 16)
            led.tool_exists = exists
            led.base_color = "#27ae60" if exists else "#c0392b"
            led.setStyleSheet(
                f"background-color: {led.base_color}; border-radius: 8px; border: 2px solid #555;"
            )
            led.setCursor(Qt.CursorShape.PointingHandCursor)
            led.mousePressEvent = lambda e, t=tool: self.show_tool_help(t)

            self.status_leds.append(led)

            # Text
            c = label_colors.get(tool, "#FFF")
            lbl = QLabel(display_name)
            lbl.setStyleSheet(
                f"color: {c}; font-size: 20px; font-weight: bold; font-family: 'Segoe UI';"
            )

            t_lay.addWidget(led)
            t_lay.addWidget(lbl)
            status_bar_layout.addWidget(t_widget)

        status_bar_layout.addStretch()

        # ---------------------------------------------------------
        # USER-LED entfernt (Punkt gelöscht)
        self.user_leds = []

        # ---------------------------------------------------------
        # SPEED REGLER
        # ---------------------------------------------------------
        speed_icon = QLabel("⚡")
        speed_icon.setStyleSheet(
            "font-size: 20px; border: none; background: transparent;"
        )
        status_bar_layout.addWidget(speed_icon)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setFixedWidth(110)
        self.slider_speed.setRange(50, 1000)
        self.slider_speed.setInvertedAppearance(True)

        current_speed = self.current_config.get("blink_speed", 500)
        self.slider_speed.setValue(current_speed)
        self.slider_speed.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider_speed.setStyleSheet(
            "QSlider::groove:horizontal { border: 1px solid #666; height: 6px; background: #222; border-radius: 3px; }"
            "QSlider::handle:horizontal { background: #F37804; border: 1px solid #444; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }"
        )

        if hasattr(self, "update_blink_speed"):
            self.slider_speed.valueChanged.connect(self.update_blink_speed)

        status_bar_layout.addWidget(self.slider_speed)

        self.lbl_speed_val = QLabel("")
        self.lbl_speed_val.setStyleSheet(
            "color: #aaa; font-size: 12px; font-weight: bold; border: none;"
        )
        self.lbl_speed_val.setFixedWidth(85)
        status_bar_layout.addWidget(self.lbl_speed_val)

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------
        self.btn_matrix = QPushButton("📟 MATRIX MODE")
        self.btn_matrix.setFixedSize(300, self.UI_BUTTON_H)
        self.btn_matrix.setStyleSheet(
            "QPushButton { background-color: #000; color: #00FF41; border: 1px solid #008F11; border-radius: 6px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #008F11; color: black; }"
        )
        if hasattr(self, "toggle_matrix"):
            self.btn_matrix.clicked.connect(lambda checked=False: self.toggle_matrix())
        status_bar_layout.addWidget(self.btn_matrix)

        self.btn_theme = QPushButton("🌓 THEME")
        self.btn_theme.setFixedSize(200, self.UI_BUTTON_H)
        self.btn_theme.setStyleSheet(
            "QPushButton { background-color: #444; color: red; border: 1px solid #666; border-radius: 6px; font-size: 18px; font-weight: bold; } QPushButton:hover { background-color: #555; border: 1px solid #F37804; }"
        )
        self.btn_theme.clicked.connect(self.toggle_theme)
        status_bar_layout.addWidget(self.btn_theme)

        main_layout.addWidget(status_bar_container)

        # --- ANIMATIONS-TIMER STARTEN ---
        self._blink_state = True
        self.master_timer = QTimer(self)
        self.master_timer.timeout.connect(self.animate_everything)
        self.master_timer.start(500)  # 500ms Takt für das Blinken
        # ---------------------------------------------------------
        # KONTROLL-BLOCK MIT HEADER
        # ---------------------------------------------------------

        controls_group = QFrame()
        # FIX: Wir setzen eine feste Mindesthöhe für den gesamten Block,
        # damit er beim Start nicht zusammenfällt.
        controls_group.setMinimumHeight(40)

        controls_group.setStyleSheet(
            f"""
        QFrame {{
            border: 1px solid #bbb;
            border-radius: 10px;
            background-color: #2F2F2F;
        }}
        /* FIX: Wir erzwingen hier im Stylesheet, dass alle Buttons 
           im Kasten sofort ihre Zielhöhe einnehmen */
        QPushButton {{
            min-height: 45px;
            max-height: 45px;
        }}
        """
        )
        controls_group_layout = QVBoxLayout(controls_group)

        # OPTIMIERUNG: Mehr Abstand nach oben (20) und unten (20) macht den Kasten höher
        controls_group_layout.setContentsMargins(0, 20, 15, 20)
        # Mehr Abstand zwischen Header und den Reglern
        controls_group_layout.setSpacing(0)

        translated_text = self.get_t("settings_header", "Einstellungen")
        self.controls_header = QLabel(translated_text)

        self.controls_header.setMinimumWidth(280)
        # OPTIMIERUNG: Header-Höhe von 28 auf 45 erhöht für mehr Präsenz
        self.controls_header.setMinimumHeight(50)
        self.controls_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bg = current_diff_colors.get("bg", "#2F2F2F")  # Dunkelgrauer Hintergrund
        fg = current_diff_colors.get("fg", "#EAFF00")  # NEONGELBE SCHRIFT

        self.controls_header.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-size: 20px;          /* Schrift im Header vergrößert */
                font-weight: bold;
                padding-left: 15px;
                padding-right: 15px;
                border-radius: 8px;
            }}
            """
        )

        controls_group_layout.addWidget(
            self.controls_header, alignment=Qt.AlignmentFlag.AlignLeft
        )

        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        # OPTIMIERUNG: Auch hier mehr Innenabstand für die Zeile
        controls_layout.setContentsMargins(0, 0, 5, 5)
        controls_layout.setSpacing(0)

        # Nutze hier deine neue B_HEIGHT (z.B. 60), falls definiert, sonst BUTTON_HEIGHT
        CONTROL_HEIGHT = getattr(self, "B_HEIGHT", 50)
        controls_layout.addStretch(0)
        control_style = f"""
        QComboBox, QSpinBox {{
            font-size: 18px;
            border-radius: {self.BUTTON_RADIUS}px;
            border: 2px solid #555;
            padding: 4px 8px;
            color: white;
            background-color: #444;
            height: {CONTROL_HEIGHT}px;
            margin-left: -2px;   /* Schiebt die Box näher an den Doppelpunkt des Labels */
        }}
        """

        def make_label(text):
            lbl = QLabel(text)
            lbl.setMinimumHeight(CONTROL_HEIGHT)

            # FIX: Von 85 auf 65 verringert, damit die Boxen näher am Wort kleben
            lbl.setFixedWidth(50)

            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            lbl.setStyleSheet(
                f"""
                color: {fg}; 
                font-weight: bold; 
                font-size: 18px;
                background: transparent;
                padding-left: 0px;
            """
            )
            return lbl

        # --- 1. Sprache-Dropdown (Kompakt) ---
        self.lang_label = make_label(self.get_t("language_label", "Sprache:"))
       

        self.language_box = QComboBox()
        self.language_box.addItems(["EN", "DE"])
        self.language_box.setFixedSize(80, B_HEIGHT)
        self.language_box.setStyleSheet(
            f"""
            QComboBox {{
                background-color: #444444; color: white; font-weight: bold; font-size: 20px;
                border: 2px solid #555555; border-radius: 6px; padding-left: 5px;
            }}
            QComboBox::drop-down {{ border: none; width: 0px; }}
            QComboBox::down-arrow {{
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #FF0000;
            }}
        """
        )

        # Sprach-Logik (Einmalig)
        saved_lang = self.cfg.get("language", "de").lower()
        (
            self.language_box.setCurrentIndex(0)
            if saved_lang == "en"
            else self.language_box.setCurrentIndex(1)
        )
        self.language_box.currentIndexChanged.connect(self.change_language)
        self.language_box.setToolTip(
            "Sprache der Oberfläche auswählen"
            if str(self.cfg.get("language", "de")).lower() == "de"
            else "Choose the interface language"
        )
        self.language_box.setToolTipDuration(10000)

        # --- 2. Farbe/Style (Kompakt) ---
        self.color_label = make_label(self.get_t("color_label", "Farbe:"))
        self.color_label.setFixedWidth(120)
        self.color_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.color_box = QComboBox()
        self.color_box.addItems(list(DIFF_COLORS.keys()))
        # Older versions stored the theme as "color", newer UI code may use
        # "theme_color". Prefer the newer key but retain backward compatibility.
        saved_color = self.cfg.get("theme_color", self.cfg.get("color", "Classics"))
        index = self.color_box.findText(saved_color)
        self.color_box.setCurrentIndex(index if index >= 0 else 0)
        self.color_box.setFixedSize(250, CONTROL_HEIGHT)
        self.color_box.setStyleSheet(control_style)
        self.color_box.currentIndexChanged.connect(self.change_colors)

        # --- 3. Commits (Kompakt) ---
        self.commit_label = make_label(self.get_t("commit_count_label", "Commits:"))

        # Breite festlegen (sizeHint + Puffer)
        
        

        # HÖHE festlegen (z.B. 35 Pixel, passend zu deinen CONTROL_HEIGHT Werten)
        self.commit_label.setFixedSize(140, self.UI_BUTTON_H)

        self.commit_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.commit_spin = QSpinBox()
        self.commit_spin.setRange(1, 20)
        self.commit_spin.setFixedSize(75, CONTROL_HEIGHT)
        self.commit_spin.setValue(self.cfg.get("commit_count", 10))
        self.commit_spin.valueChanged.connect(self.commit_value_changed)
        self.commit_spin.setToolTip(
            "Anzahl der Commits für die Anzeige bzw. Auswertung festlegen"
            if str(getattr(self, "LANG", self.cfg.get("language", "de"))).lower() in ("de", "0")
            else "Set the number of commits to display or analyze"
        )
        self.commit_spin.setToolTipDuration(10000)

        self.commit_spin.setStyleSheet(
            """
            QSpinBox {
                background-color: #222222; color: #FFFFFF; font-size: 20px; font-weight: bold;
                border: 2px solid #555555; border-radius: 6px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #333333; width: 25px; border-left: 1px solid #555555;
            }
            QSpinBox::up-arrow { border-left: 6px solid transparent; border-right: 6px solid transparent; border-bottom: 6px solid #FF0000; }
            QSpinBox::down-arrow { border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid #FF0000; }
        """
        )

        # Signal wurde bereits einmalig oben verbunden.
        saved_commits = self.cfg.get("commit_count", 10)
        if int(self.commit_spin.value()) != int(saved_commits):
            self.commit_spin.setValue(saved_commits)

        self.btn_check_tools = QPushButton(
            self.get_t("check_tools_button", "🛠️ Tools prüfen")
        )
        self.btn_check_tools.setFixedSize(220, 45)

        # --- 0. Container Erstellung (Korrektur: QGroupBox statt QFrame) ---
        controls_group = QGroupBox("")
        controls_group_layout = QVBoxLayout(controls_group)

        # Stylesheet: Macht den Kasten extrem flach und rückt den Titel bündig
        controls_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 8px;
                margin-top: 10px; 
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
                color: #00FF00;
            }
        """
        )
        # Erzwingt eine geringe Höhe für den gesamten Block
        # controls_group.setMaximumHeight(140)

        button_style = """
            QPushButton {
                background-color: #444444;
                color: white;
                font-weight: bold; 
                font-size: 24px;          /* Ein kleiner Schritt zurück auf 28px wirkt oft Wunder */
                font-family: sans-serif;
                
                border-radius: 6px;
                border: 3px solid #555555;

                /* ZENTRIERUNG ERZWINGEN */
                text-align: center;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover { 
                background-color: #333333; 
                color: #FFD700; 
                border: 3px solid #FFD700;
            }
        """
        # --- Deine neuen Maße (Jetzt auch im Code genutzt!) ---
        B_WIDTH = 440
        B_HEIGHT = self.UI_BUTTON_H
        I_SIZE = 25

        # --- 2. Ordner-Buttons (Mit korrekter Höhe und Icon-Größe) ---
        f_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        # --- 2. Ordner-Buttons (Oben) ---
        f_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        self.btn_open_work = QPushButton(" Arbeitsordner")
        self.btn_open_work.setIcon(f_icon)
        self.btn_open_work.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_work.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_work.setStyleSheet(button_style)
        self.btn_open_work.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "WORK_DIR", self.base_dir)
            )
        )

        self.btn_open_temp = QPushButton(" Temp-Repo")
        self.btn_open_temp.setIcon(f_icon)
        self.btn_open_temp.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_temp.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_temp.setStyleSheet(button_style)
        self.btn_open_temp.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "TEMP_REPO", ".")
            )
        )

        self.btn_open_emu = QPushButton(" Emu-Git")
        self.btn_open_emu.setIcon(f_icon)
        self.btn_open_emu.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_emu.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_emu.setStyleSheet(button_style)
        self.btn_open_emu.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "PATCH_EMU_GIT_DIR", ".")
            )
        )

        # --- 3. Funktions-Buttons (Unten) ---
        self.btn_check_tools = QPushButton("🛠️ Tools prüfen")
        self.btn_check_tools.setIconSize(QSize(I_SIZE, I_SIZE))  # Icon-Größe für Emojis
        self.btn_check_tools.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_check_tools.setStyleSheet(button_style)
        self.btn_check_tools.clicked.connect(self.run_full_system_check)

        self.btn_modifier = QPushButton("👤 Patch Autor")
        self.btn_modifier.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_modifier.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_modifier.setStyleSheet(button_style)
        self.btn_modifier.clicked.connect(self.change_modifier_name)

        self.btn_repo_url = QPushButton("🌐 Repo URL")
        self.btn_repo_url.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_repo_url.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_repo_url.setStyleSheet(button_style)
        self.btn_repo_url.clicked.connect(self.change_emu_repo)

        # --- Konfiguration (kannst du zentral anpassen) ---
        self.font_size_buttons = 12  # Hier die gewünschte Schriftgröße in Pixeln ändern
        current_lang = getattr(self, "lang", "de")  # Erkennt deine gewählte Sprache

        # 1. FARBSCHEMA ERMITTELN (Passend zu deinem toggle_theme)
        is_dark = "#2F2F2F" in self.styleSheet() or not self.styleSheet()

        if is_dark:
            # MATRIX / DARK COLORS (Orange/Gold)
            c1, c2, b_color = "#F37804", "#8B4513", "#444"
        else:
            # LIGHT / SYSTEM COLORS (Blau)
            c1, c2, b_color = "#3498db", "#2980b9", "#1c5980"

        # 2. TEXTE FÜR MEHRSPRACHIGKEIT
        lang = getattr(self, "LANG", "de").lower()
        text_patch_online = "🌐 Patch Online " if lang == "de" else "🌐 Load Patch "

        # 3. BUTTON ERSTELLEN
        self.btn_patch_online = QPushButton(text_patch_online)
        self.btn_patch_online.setFixedSize(B_WIDTH, B_HEIGHT)

        # 4. DYNAMISCHES STYLESHEET (Mit Variablen und Font-Fix 700)
        self.btn_patch_online.setStyleSheet(
            f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 {c1}, stop:1 {c2});
                color: white; 
                font-weight: 700; 
                font-size: {self.font_size_buttons}px;
                border: 1px solid {b_color};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 {c2}, stop:1 {c1});
                border: 1px solid #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {b_color};
                border: 1px solid {b_color};
                border-radius: 10px;
                padding: 0px;
            }}
        """
        )

        # 5. VERKNÜPFUNG
        if hasattr(self, "handle_online_patch_button"):
            self.btn_patch_online.clicked.connect(self.handle_online_patch_button)

        # --- Bestehender Button: Commit Check ---
        self.btn_check_commit = QPushButton("🔄 Commit Check")
        self.btn_check_commit.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_check_commit.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_check_commit.setStyleSheet(button_style)
        self.btn_check_commit.clicked.connect(self.check_for_new_commit)

        # --- Manuelles Projekt-Backup ---
        self.btn_backup_gui = QPushButton("💾 Backup erstellen")
        self.btn_backup_gui.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_backup_gui.setFixedSize(300, B_HEIGHT)
        self.btn_backup_gui.setStyleSheet(button_style)
        self.btn_backup_gui.setToolTip(
            "Erstellt backup/backup_gi.zip mit dem aktuellen Projektstand"
        )
        self.btn_backup_gui.clicked.connect(self.create_gi_backup)

        # --- 4. GRID-LAYOUT (Header-Fix: Badge 220px, Lücke 5px, Badge 280px, Weißer Text) ---
        from PyQt6.QtWidgets import QFrame

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 0, 10, 10)
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(8)

        # Farben: Basis transparent (Neon weg), Hover nutzt System-Style
        base_bg = "transparent"
        hover_bg = current_diff_colors.get("btn_hover", "#2a4a6a")

        # Haupt-Container (Gesamtbreite: 220 + 5 + 280 = 505px)
        self.header_container = QWidget()
        self.header_container.setFixedSize(950, self.UI_BADGE_H)
        self.header_container.mousePressEvent = self.on_header_clicked

        h_layout = QHBoxLayout(self.header_container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(10)  # EXAKT 5 Pixel Lücke zwischen den Badges

        # --- A) LINKER BADGE (Einstellungen - Länge 220) ---
        self.left_badge = QFrame()
        self.left_badge.setFixedSize(180, self.UI_BADGE_H)
        self.left_badge.setStyleSheet(
            f"""
            QFrame {{
                background-color: {base_bg};
                border: 1px solid #444444;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {hover_bg};
                border: 1px solid #777777;
            }}
        """
        )

        left_layout = QHBoxLayout(self.left_badge)
        left_layout.setContentsMargins(10, 0, 10, 0)

        # Icon links
        icon_label = QLabel()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        icon_label.setPixmap(icon.pixmap(20, 20))
        left_layout.addWidget(icon_label)

        # --- TITEL (Dynamisch ans Theme angepasst) ---
        # Aktuelle Akzentfarbe aus dem Theme laden (z.B. Neongelb)
        t_fg = current_diff_colors.get("fg", "#EAFF00")

        title_text = " Einstellungen" if self.LANG == "de" else " Settings"
        self.header_label = QLabel(title_text)

        # 'white' durch die Theme-Variable {t_fg} ersetzt
        self.header_label.setStyleSheet(
            f"""
            QLabel {{
                color: {t_fg}; 
                font-weight: bold; 
                font-size: 15px; 
                background: transparent; 
                border: none;
            }}
        """
        )

        left_layout.addWidget(self.header_label)
        left_layout.addStretch()
        h_layout.addWidget(self.left_badge)

        # --- B) RECHTER BADGE (OSCam Status - Länge 280) ---
        self.right_badge = QFrame()
        self.right_badge.setFixedSize(600, self.UI_BADGE_H)
        self.right_badge.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: 1px solid #444444;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: transparent;
                border: 1px solid #777777;
            }}
        """
        )

        right_layout = QHBoxLayout(self.right_badge)
        right_layout.setContentsMargins(
            10, 0, 10, 0
        )  # Margins setzen, um Platz für Text zu schaffen

        # Status-Label (Zwingend WEISSE Schrift)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 18px; background: transparent; border: none;"
        )

        # Füge das Label ohne Stretch hin
        right_layout.addWidget(self.status_label)

        # Keine weiteren Strecken mehr erforderlich
        h_layout.addWidget(self.right_badge)

        # --- Integration ins Grid (Zeile 0) ---
        grid_layout.addWidget(self.header_container, 0, 0, 1, 4)
        grid_layout.addWidget(self.btn_open_work, 1, 9)

        grid_layout.addWidget(self.btn_open_emu, 0, 6)
        grid_layout.addWidget(self.btn_repo_url, 0, 7)

        grid_layout.addWidget(self.btn_open_temp, 0, 8)
        grid_layout.addWidget(self.btn_backup_gui, 0, 9)

        # --- EINSTELLUNGEN: kompakt, linksbündig, eine Reihe ---
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(0, 0, 0, 0)
        settings_row.setSpacing(6)

        # Sprache
        self.lang_label.setFixedWidth(120)
        self.lang_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.language_box.setFixedWidth(90)

        settings_row.addWidget(self.lang_label)
        settings_row.addWidget(self.language_box)

        # Abstand zwischen den Gruppen
        settings_row.addSpacing(8)

        # Farbe
        self.color_label.setFixedWidth(80)
        self.color_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.color_box.setFixedWidth(250)

        settings_row.addWidget(self.color_label)
        settings_row.addWidget(self.color_box)

        settings_row.addSpacing(8)

        # Commits
        self.commit_label.setFixedWidth(140)
        self.commit_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.commit_spin.setFixedWidth(80)

        settings_row.addWidget(self.commit_label)
        settings_row.addWidget(self.commit_spin)

        # Backup-Button direkt hinter der Commit-Anzahl-Auswahl
        #settings_row.addWidget(self.btn_backup_gui)

        # Freier Platz bleibt rechts von den Einstellungen
        settings_row.addStretch(1)

        # Einstellungen in einer einzigen Reihe links anordnen
        grid_layout.addLayout(settings_row, 1, 0, 1, 6)

        # Die vier Git-/Revisions-Buttons direkt unter den Ordner-Buttons anordnen.
        # Die Widgets werden aus ihren bisherigen Layout-Positionen verschoben.
        grid_layout.addWidget(self.oscam_source_button, 1, 6)

        # Repo URL ist bereits oben neben Emu-Git platziert.

        # Keine Grid-Spalte künstlich verbreitern
        for i in range(grid_layout.columnCount()):
            grid_layout.setColumnStretch(i, 0)

        # Kleine Abstände zwischen den Grid-Elementen
        grid_layout.setHorizontalSpacing(6)
        grid_layout.setVerticalSpacing(6)


        # Layout zum Kasten hinzufügen
        controls_group_layout.addLayout(grid_layout)
        main_layout.addWidget(controls_group)

        # --- UNTERE SEKTION: klare Priorität für Patch-Aktionen ---
        self.grid_container = QGroupBox("PATCH & BUILD")
        self.grid_container.setObjectName("patchBuildPanel")
        self.grid_container.setStyleSheet("""
            QGroupBox#patchBuildPanel {
                margin-top: 4px;
            }

            QGroupBox#patchBuildPanel::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px 5px;
                top: -10px;
            }
        """)
        self.layout_grid_buttons = QGridLayout(self.grid_container)
        # Kompakte, gleichmäßige Abstände; das Grid passt die Spaltenzahl
        # anhand der tatsächlich verfügbaren Breite dynamisch an.
        self.layout_grid_buttons.setHorizontalSpacing(6)
        self.layout_grid_buttons.setVerticalSpacing(6)
        self.layout_grid_buttons.setContentsMargins(8, 8, 8, 8)

        # Container zuerst einbetten, dann die vorhandenen Aktionsbuttons erzeugen.
        main_layout.addWidget(self.grid_container)
        self.setup_grid_buttons()

        # Die sechs bisher oben rechts platzierten Aktionsbuttons werden
        # in den PATCH & BUILD-Bereich integriert. Die Reihenfolge folgt
        # dem typischen Arbeitsablauf: Patch holen/erstellen, prüfen und
        # anwenden, sichern, anschließend Repository-/Systemwerkzeuge.
        
        patch_build_order = [
            getattr(self, "btn_patch_online", None),
            getattr(self, "buttons", {}).get("patch_create"),
            getattr(self, "buttons", {}).get("patch_renew"),
            getattr(self, "buttons", {}).get("patch_check"),
            getattr(self, "buttons", {}).get("patch_apply"),
            getattr(self, "buttons", {}).get("patch_zip"),
            getattr(self, "buttons", {}).get("backup_old"),
            getattr(self, "buttons", {}).get("clean_folder"),
            getattr(self, "buttons", {}).get("change_old_dir"),
            getattr(self, "btn_check_commit", None),
            getattr(self, "btn_modifier", None),
            getattr(self, "btn_check_tools", None),

            # Beenden
            getattr(self, "buttons", {}).get("exit"),

            # Direkt danach: Rechte fixen
            getattr(self, "btn_fix_perms", None),
        ]


        # Alte Grid-Einträge leeren und in der gewünschten Reihenfolge neu
        # einsetzen. Signale/Callbacks bleiben dabei unverändert verbunden.
        patch_layout = self.layout_grid_buttons
        while patch_layout.count():
            item = patch_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self.grid_container)

        from PyQt6.QtWidgets import QSizePolicy
        seen_patch_buttons = set()
        ordered_patch_buttons = []
        for button in patch_build_order:
            if button is None or id(button) in seen_patch_buttons:
                continue
            seen_patch_buttons.add(id(button))
            ordered_patch_buttons.append(button)
            button.setParent(self.grid_container)
            # Die sechs verschobenen Buttons sollen sich genauso flexibel
            # an die Spaltenbreite anpassen wie die nativen Patch-Buttons.
            if button in (
                getattr(self, "btn_patch_online", None),
                #getattr(self, "btn_backup_gui", None),
                getattr(self, "btn_repo_url", None),
                getattr(self, "btn_check_commit", None),
                getattr(self, "btn_modifier", None),
                getattr(self, "btn_check_tools", None),
            ):
                button.setMinimumSize(250, 45)
                # Keine künstliche Maximalbreite: sonst entstehen im rechten
                # Bereich große Lücken, obwohl das Grid seine Spalten streckt.
                button.setMaximumHeight(45)
                button.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed,
                )

        # Erst kompakt einsetzen; ResponsiveGridReflow ordnet danach anhand
        # der realen Containerbreite in passende Spalten um.
        for index, button in enumerate(ordered_patch_buttons):
            patch_layout.addWidget(button, index, 0)

        # ResponsiveGridReflow liest dieselbe Layout-Reihenfolge aus und
        # passt die Spaltenzahl beim Fenster-Resize automatisch an.
        reflow = getattr(self, "_patch_grid_reflow", None)
        if reflow is not None:
            reflow.reflow()

        # Weitere Werkzeuge in einer separaten, responsiven Sektion.

        self.setup_option_buttons(main_layout)

        # Revisions-Buttons auf dieselbe Zeile wie „Oscam Git URL“ setzen.
        # Repo URL bleibt oben neben Emu-Git und wird nicht erneut verschoben.
        revision_button_min_width = 220
        revision_button_height = 45
        for col, key in ((7, "streamboard_checkout"), (8, "oscam_emu_revision")):
            entry = self.option_buttons.get(key)
            if entry:
                button = entry[0] if isinstance(entry, (tuple, list)) else entry
                # Keine feste Breite erzwingen: Das Grid muss die Buttons an
                # die tatsächlich verfügbare Fensterbreite anpassen können.
                button.setMinimumWidth(revision_button_min_width)
                button.setMaximumWidth(16777215)
                button.setFixedHeight(revision_button_height)
                button.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed,
                )
                button.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                button.setStyleSheet(
                    button.styleSheet()
                    + "\nQPushButton { padding-left: 6px; padding-right: 6px; margin: 0px; }"
                )
                button.setToolTip(button.text())
                grid_layout.addWidget(
                    button, 1, col,
                    alignment=Qt.AlignmentFlag.AlignVCenter
                )


        
        
        # ---------------------------------------------------------
        # TIMER & DIGITAL CLOCK
        # ---------------------------------------------------------
        def update_digital_clock():
            now = QDateTime.currentDateTime()
            # Aktiviert die digitale Uhrzeit-Aktualisierung:
            self.digital_clock.setText(now.toString("HH:mm:ss"))
            # Aktualisiert das Datum:
            self.date_label.setText(now.toString("dd.MM.yyyy"))

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(update_digital_clock)
        self.clock_timer.start(1000)
        update_digital_clock()


        # ---------------------------------------------------------
        # FINAL SETTINGS
        # ---------------------------------------------------------
        self.change_colors()
        self.update_language()

        # Einheitliches Farbschema nach der vollständigen UI-Initialisierung
        # nochmals anwenden. Einige Widgets/Statusprüfungen werden verzögert
        # erstellt oder aktualisiert; diese Aufrufe stellen sicher, dass deren
        # individuelle Styles nicht dauerhaft das Theme überschreiben.
        # Stats bleibt eine QCheckBox und wird vom Button-Styling nicht verändert.
        for _style_delay in (0, 250, 1000):
            QTimer.singleShot(
                _style_delay,
                lambda: self.apply_global_button_style()
                if hasattr(self, "apply_global_button_style") else None,
            )

        # 2. Fenster- und Konsolengröße bildschirmabhängig konfigurieren.
        from gui_layout_helper import configure_window_layout

        toolbar_buttons = (
            self.copy_log_button,
            self.analyze_build_logs_button,
            self.diagnostics_button,
            self.log_history_button,
            self.clear_console_button,
            self.cyber_center_button,
            self.patch_diff_button,
            self.achievement_button,
            self.ai_assistant_button,
        )

        configure_window_layout(
            self,
            self.info_text,
            toolbar_buttons
        )

        self.setWindowTitle(
            f"OSCam Toolkit v{APP_VERSION} | {getattr(self, 'patch_modifier', 'speedy005')}"
        )

        # Fenstereinstellungen laden; Wiederherstellung erfolgt nach show().
        self._window_settings = QSettings("speedy005", "OSCamPatchManager")

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._save_window_state)

        self.updateGeometry()

        # 4. Signale sind bereits an den jeweiligen Handlern verbunden:
        #    Farbe -> change_colors(), Commits -> commit_value_changed().
        #    Keine zweite Verbindung hier, damit kein doppeltes Speichern/Feedback entsteht.

        # 5. System-Check mit kleiner Verzögerung starten
        # Wir definieren das Design zentral für ALLE Buttons der App
        neon_style = """
            QPushButton {
                background-color: #3d3d3d !important;
                color: #EAFF00 !important;
                border: 1px solid #555 !important;
                border-radius: 8px !important;
                padding: 5px !important;
                font-weight: bold !important;
                font-size: 12pt !important;
            }
            QPushButton:hover {
                background-color: #4d4d4d !important;
                border: 1px solid #EAFF00 !important;
                color: white !important;
            }
        """

        # --- THEME BEIM START LADEN (Matrix-Check) ---
        # 1. Sicherstellen, dass wir die aktuellsten Daten haben
        # Falls self.current_config noch leer ist, laden wir sie hier kurz manuell
        if not hasattr(self, "current_config") or not self.current_config:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        self.current_config = json.load(f)
                    self.cfg = self.current_config
                except Exception as e:
                    print(f"Fehler beim Laden der Konfiguration: {e}")
                    self.current_config = {}
                    self.cfg = self.current_config
            else:
                self.current_config = {}
                self.cfg = self.current_config

        # S3-Git-Repositories
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        # Gespeicherte Auswahl wiederherstellen
        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_repo_combo = None
        self.s3_install_worker = None

        cfg = getattr(self, "current_config", {})
        saved_theme = cfg.get("theme_mode", "standard")

        # 2. Matrix erzwingen
        if saved_theme == "matrix":
            # Wir setzen is_loading auf True, um Sounds/Logs beim Start zu blockieren
            was_loading = getattr(self, "is_loading", False)
            self.is_loading = True

            # WICHTIG: Erst das normale Stylesheet löschen, dann Matrix setzen
            self.setStyleSheet("")
            self.toggle_matrix(force_state="matrix")

            # Uhr-Update
            if hasattr(self, "analog_clock"):
                self.analog_clock.update()

            self.is_loading = was_loading
        else:
            # Falls nicht Matrix, Standard-Neon setzen
            self.setStyleSheet(self.styleSheet() + neon_style)

        # TEMPORÄRE LAYOUT-DIAGNOSE: tatsächliche Höhen nach dem Anzeigen messen
        def _debug_layout_sizes():
            print("\\n========== OSCAM LAYOUT DIAGNOSE ==========", flush=True)
            print(
                f"Fenster: height={self.height()}, "
                f"sizeHint={self.sizeHint().height()}, "
                f"minimum={self.minimumHeight()}",
                flush=True,
            )
            print(
                f"Hauptlayout: height={main_layout.geometry().height()}, "
                f"sizeHint={main_layout.sizeHint().height()}",
                flush=True,
            )

            for i in range(main_layout.count()):
                item = main_layout.itemAt(i)
                widget = item.widget()
                if widget is not None:
                    print(
                        f"{i}: {widget.objectName() or widget.__class__.__name__}: "
                        f"height={widget.height()}, "
                        f"sizeHint={widget.sizeHint().height()}, "
                        f"minimumHint={widget.minimumSizeHint().height()}, "
                        f"minimum={widget.minimumHeight()}, "
                        f"maximum={widget.maximumHeight()}",
                        flush=True,
                    )

            for name in ("console_panel", "info_text", "header_widget", "controls_group", "grid_container"):
                widget = getattr(self, name, None)
                if widget is not None:
                    print(
                        f"{name}: height={widget.height()}, "
                        f"sizeHint={widget.sizeHint().height()}, "
                        f"minimumHint={widget.minimumSizeHint().height()}, "
                        f"minimum={widget.minimumHeight()}, "
                        f"maximum={widget.maximumHeight()}",
                        flush=True,
                    )

            exit_btn = getattr(self, "buttons", {}).get("exit")
            if exit_btn is not None:
                print(
                    f"EXIT BUTTON: text={exit_btn.text()!r}, "
                    f"height={exit_btn.height()}, "
                    f"sizeHint={exit_btn.sizeHint().height()}, "
                    f"minimum={exit_btn.minimumHeight()}, "
                    f"maximum={exit_btn.maximumHeight()}, "
                    f"fixed={exit_btn.minimumHeight() == exit_btn.maximumHeight()}, "
                    f"parent={exit_btn.parentWidget().__class__.__name__ if exit_btn.parentWidget() else None}",
                    flush=True,
                )
                print(f"EXIT STYLE: {exit_btn.styleSheet()}", flush=True)

            print("========== ENDE DIAGNOSE ==========\\n", flush=True)

        QTimer.singleShot(2500, _debug_layout_sizes)

    # =====================
    # BUTTON & COLOR HANDLING
    # =====================
    


    
    
    # =====================
    # BUTTON & COLOR HANDLING
    # =====================








    
    



    

    # =====================
    # GITHUB EMU CREDENTIALS
    # =====================


    def edit_emu_github_config(self, info_widget=None, progress_callback=None):
        """
        Öffnet den GitHub-Konfigurationsdialog mit Regenbogen-ProgressBar,
        schwarzer Schrift, Sound und zweisprachigem UI.
        """
        from PyQt6.QtWidgets import QFormLayout, QLabel, QDialogButtonBox, QApplication
        from PyQt6.QtCore import QTimer

        # --- Final Label verstecken ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        widget = info_widget or getattr(self, "info_text", None)
        pbar = getattr(self, "progress_bar", None)
        current_lang = str(getattr(self, "LANG", "de")).lower()[:2]
        

        # --- Styles ---
        rainbow = (
            "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
            "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
        )
        style_rainbow = f"""
            QProgressBar {{
                text-align: center;
                font-weight: bold;
                border: 2px solid #222;
                border-radius: 6px;
                background-color: #111;
                color: black;
                font-size: 11pt;
            }}
            QProgressBar::chunk {{
                background-color: {rainbow};
                border-radius: 4px;
            }}
        """
        style_fade = """
            QProgressBar {
                text-align: center;
                font-weight: bold;
                border: 2px solid #222;
                border-radius: 6px;
                background-color: #111;
                color: black;
                font-size: 11pt;
            }
            QProgressBar::chunk { background-color: transparent; }
        """

        # --- Helper-Funktionen ---
        def set_progress(val, txt=None):
            if pbar:
                pbar.setStyleSheet(style_rainbow)
                pbar.setValue(val)
                pbar.setFormat(txt if txt else "%p%")
                pbar.show()
            if progress_callback:
                try:
                    progress_callback(val)
                except:
                    pass
            QApplication.processEvents()

        def finalize_pbar(text, visible_seconds=3):
            if pbar:
                pbar.setValue(100)
                pbar.setFormat(text)
                QTimer.singleShot(
                    visible_seconds * 1000, lambda: pbar.setStyleSheet(style_fade)
                )
                QTimer.singleShot(visible_seconds * 1000, lambda: pbar.setValue(0))
                if progress_callback:
                    QTimer.singleShot(
                        visible_seconds * 1000, lambda: progress_callback(0)
                    )

        def play_sound(action="open"):
            if "safe_play" in globals():
                sound_map = {"open": "dialog-information.oga", "save": "complete.oga"}
                safe_play(sound_map.get(action, "complete.oga"))

        def get_txt(key, default=""):
            lang_pkg = TEXTS.get(current_lang, TEXTS.get("de", {}))
            return lang_pkg.get(key, default)

        # --- Start Progress ---
        set_progress(
            20,
            "⏳ "
            + (
                get_txt("loading_config", "Konfiguration wird geladen...")
                if is_de
                else "Loading configuration..."
            ),
        )
        play_sound("open")

        dialog = GithubConfigDialog(self)
        set_progress(50)

        # UI Texte anpassen
        layout = dialog.layout()
        if isinstance(layout, QFormLayout):
            mapping = [
                (dialog.patch_repo, "patch_repo_label", "Patch Repo:"),
                (dialog.patch_branch, "patch_branch_label", "Patch Branch:"),
                (dialog.emu_repo, "emu_repo_label", "EMU Repo:"),
                (dialog.emu_branch, "emu_branch_label", "EMU Branch:"),
                (dialog.username, "github_username_label", "GitHub User:"),
                (dialog.token, "github_token_label", "Token:"),
                (dialog.user_name, "github_user_name_label", "Git Name:"),
                (dialog.user_email, "github_user_email_label", "Git Email:"),
            ]
            for field, key, default in mapping:
                label = layout.labelForField(field)
                if label and isinstance(label, QLabel):
                    label.setText(get_txt(key, default))

        # Buttons anpassen
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
            cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if save_btn:
                save_btn.setText(get_txt("save", "Speichern"))
            if cancel_btn:
                cancel_btn.setText(get_txt("cancel", "Abbrechen"))

        set_progress(
            80, "🔧 " + (get_txt("config_ready", "Bereit") if is_de else "Ready")
        )

        # --- Dialog ausführen ---
        if dialog.exec():
            msg = get_txt("github_config_saved", "GitHub Konfiguration gespeichert.")
            self.append_info(widget, msg, "success")
            play_sound("save")
            finalize_pbar(
                "✅ " + (get_txt("saved", "Gespeichert!") if is_de else "Saved!")
            )
        else:
            finalize_pbar("%p%")

    # =====================
    # RUN ACTION WRAPPER
    # =====================

    # =====================
    # BUTTON CALLBACKS
    # =====================

    





    


    






def auto_install_emoji_font():
    """Installiert Noto Color Emoji bei Bedarf unter Windows oder Linux."""

    def _run_install():
        os_type = platform.system()

        try:
            print("[SYSTEM] Prüfe Emoji-Schriftart...")

            if os_type == "Linux":
                font_dir = os.path.expanduser("~/.local/share/fonts")
                target_path = os.path.join(font_dir, "NotoColorEmoji.ttf")

                # Ist die Schriftart bereits installiert, nichts tun.
                if os.path.isfile(target_path) and os.path.getsize(target_path) > 0:
                    print("[SYSTEM] Emoji-Schriftart bereits vorhanden.")
                    return

            elif os_type == "Windows":
                font_dir = os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Microsoft", "Windows", "Fonts"
                )
                target_path = os.path.join(font_dir, "NotoColorEmoji.ttf")

                if os.path.isfile(target_path) and os.path.getsize(target_path) > 0:
                    print("[SYSTEM] Emoji-Schriftart bereits vorhanden.")
                    return
            else:
                print("[SYSTEM] Automatische Emoji-Installation nicht unterstützt.")
                return

            import requests
            import zipfile
            import io

            url = (
                "https://github.com/speedy005/"
                "oscam_patch_manager_new/raw/master/Noto_Color_Emoji.zip"
            )

            response = requests.get(url, timeout=20)
            response.raise_for_status()

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                ttf_name = next(
                    (f for f in z.namelist() if f.lower().endswith(".ttf")),
                    None
                )

                if not ttf_name:
                    print("[!] Keine TTF-Datei im Emoji-Archiv gefunden.")
                    return

                font_data = z.read(ttf_name)

            os.makedirs(font_dir, exist_ok=True)

            with open(target_path, "wb") as f:
                f.write(font_data)

            if os_type == "Linux":
                subprocess.run(
                    ["fc-cache", "-f", font_dir],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                print("[✓] Emoji-Schriftart installiert. Neustart empfohlen.")

            elif os_type == "Windows":
                ctypes.windll.gdi32.AddFontResourceW(target_path)
                ctypes.windll.user32.SendMessageW(0xFFFF, 0x001D, 0, 0)
                print("[✓] Emoji-Schriftart installiert.")

        except Exception as e:
            print(f"[!] Emoji-Schriftart: {e}")

    threading.Thread(target=_run_install, daemon=True).start()





# =============================================================================
# EXECUTION BOOTLOADER: Oscam Emu Patch Manager by speedy005
# =============================================================================

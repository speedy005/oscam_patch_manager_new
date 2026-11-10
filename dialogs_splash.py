# -*- coding: utf-8 -*-
"""
OSCam EMU Patch Manager – Splash und Hilfsklassen
Kompatibel mit PyQt6.

Öffentliche Klassen:
    GithubConfigDialog
    TaskWorker
    AnalogClock
    SplashSoundManager
    SplashBootstrapWorker
    CinematicMatrixSplash

Hinweise:
    - Mindestlaufzeit des Splashscreens: 15 Sekunden.
    - Audio ist optional.
    - Fehlende Python-Pakete werden im Hintergrund installiert.
    - Nach einer Paketinstallation wird ein Neustart angefordert.
"""

import importlib.util
import json
import math
import os
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from PyQt6.QtCore import QSize
from PyQt6.QtCore import (
    Qt,
    QTime,
    QPoint,
    QTimer,
    QUrl,
    QThread,
    QEasingCurve,
    QPropertyAnimation,
    pyqtProperty,
    pyqtSignal,
)

from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPen,
    QPolygon,
)

from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QWidget,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QMessageBox,
    QSizePolicy,
    QPlainTextEdit,
)


# ============================================================
# OPTIONALE AUDIOUNTERSTÜTZUNG
# ============================================================

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

    MULTIMEDIA_AVAILABLE = True

except (ImportError, RuntimeError):
    QAudioOutput = None
    QMediaPlayer = None
    MULTIMEDIA_AVAILABLE = False


# ============================================================
# KONFIGURATION
# ============================================================

REQUIRED_PACKAGES = {
    "requests": "requests",
    "packaging": "packaging",
    "psutil": "psutil",
    "urllib3": "urllib3",
}


def _tool_roots():
    """Liefert mögliche Programmverzeichnisse ohne Duplikate."""
    roots = []

    if getattr(sys, "frozen", False):
        roots.append(Path(sys.executable).resolve().parent)

    roots.append(Path(__file__).resolve().parent)
    roots.append(Path.cwd())

    result = []

    for root in roots:
        if root not in result:
            result.append(root)

    return result


def _find_sounds_dir():
    for root in _tool_roots():
        candidate = root / "sounds"

        if candidate.is_dir():
            return candidate

    return _tool_roots()[0] / "sounds"


def _config_path():
    return Path(__file__).resolve().parent / "github_upload_config.json"


if "TEXTS" not in globals():
    TEXTS = {
        "de": {
            "github_dialog_title": "GitHub-Konfiguration",
            "patch_repo_label": "Patch-Repository:",
            "patch_branch_label": "Patch-Branch:",
            "emu_repo_label": "EMU-Repository:",
            "emu_branch_label": "EMU-Branch:",
            "github_username_label": "GitHub-Benutzer:",
            "github_token_label": "GitHub-Token:",
            "github_user_name_label": "Git-Name:",
            "github_user_email_label": "Git-E-Mail:",
            "save": "Speichern",
            "cancel": "Abbrechen",
        }
    }


if "load_github_config" not in globals():

    def load_github_config():
        path = _config_path()

        if not path.exists():
            return {}

        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            return data if isinstance(data, dict) else {}

        except (OSError, ValueError):
            return {}


if "save_github_config" not in globals():

    def save_github_config(config):
        """Speichert die Konfiguration atomar."""
        path = _config_path()
        temporary_path = path.with_suffix(".json.tmp")

        try:
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(
                    config,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            os.replace(temporary_path, path)

        finally:
            try:
                if temporary_path.exists():
                    temporary_path.unlink()
            except OSError:
                pass


# ============================================================
# GITHUB-KONFIGURATIONSDIALOG
# ============================================================

class GithubConfigDialog(QDialog):
    """GitHub-Konfiguration für den Patch Manager."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lang = getattr(parent, "LANG", "de")
        translations = TEXTS.get(
            self.lang,
            TEXTS.get("de", {}),
        )

        def tr(key, default):
            return translations.get(key, default)

        self.setWindowTitle(
            tr("github_dialog_title", "GitHub-Konfiguration")
        )
        self.setMinimumWidth(700)
        self.resize(900, 560)

        layout = QFormLayout(self)

        self.patch_repo = QLineEdit()
        self.patch_branch = QLineEdit("master")

        self.emu_repo = QLineEdit()
        self.emu_branch = QLineEdit("master")

        self.username = QLineEdit()
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)

        self.user_name = QLineEdit("speedy005")
        self.user_email = QLineEdit("patch@oscam.local")

        try:
            cfg = load_github_config() or {}

            self.patch_repo.setText(cfg.get("repo_url", ""))
            self.patch_branch.setText(cfg.get("branch", "master"))

            self.emu_repo.setText(cfg.get("emu_repo_url", ""))
            self.emu_branch.setText(cfg.get("emu_branch", "master"))

            self.username.setText(cfg.get("username", ""))
            self.token.setText(cfg.get("token", ""))

            self.user_name.setText(
                cfg.get("user_name", "speedy005")
            )
            self.user_email.setText(
                cfg.get("user_email", "patch@oscam.local")
            )

        except Exception as exc:
            print(f"Konfiguration konnte nicht geladen werden: {exc}")

        fields = [
            ("patch_repo_label", "Patch-Repository:", self.patch_repo),
            ("patch_branch_label", "Patch-Branch:", self.patch_branch),
            ("emu_repo_label", "EMU-Repository:", self.emu_repo),
            ("emu_branch_label", "EMU-Branch:", self.emu_branch),
            ("github_username_label", "GitHub-Benutzer:", self.username),
            ("github_token_label", "GitHub-Token:", self.token),
            ("github_user_name_label", "Git-Name:", self.user_name),
            ("github_user_email_label", "Git-E-Mail:", self.user_email),
        ]

        for key, default, widget in fields:
            layout.addRow(tr(key, default), widget)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        save_button = buttons.button(
            QDialogButtonBox.StandardButton.Save
        )
        cancel_button = buttons.button(
            QDialogButtonBox.StandardButton.Cancel
        )

        if save_button:
            save_button.setText(tr("save", "Speichern"))

        if cancel_button:
            cancel_button.setText(tr("cancel", "Abbrechen"))

        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def save(self):
        config = {
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
            save_github_config(config)
            self.accept()

        except Exception as exc:
            QMessageBox.critical(
                self,
                "GitHub-Konfiguration",
                f"Speichern fehlgeschlagen:\n{exc}",
            )


# ============================================================
# TASK-WORKER
# ============================================================

class TaskWorker(QThread):
    """
    Führt eine Funktion im Hintergrund aus.

    result_ready:
        Enthält den Rückgabewert der Funktion.

    finished:
        Bleibt das native QThread-Signal und wird nicht überschrieben.
    """

    progress = pyqtSignal(int)
    info = pyqtSignal(str, str)
    result_ready = pyqtSignal(object)

    def __init__(self, target_fn, *args, parent=None, **kwargs):
        super().__init__(parent)

        self.target_fn = target_fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.target_fn(
                *self.args,
                progress_callback=self.progress.emit,
                **self.kwargs,
            )

            self.result_ready.emit(result)

        except Exception as exc:
            self.info.emit(
                f"Fehler bei der Hintergrundaufgabe: {exc}",
                "error",
            )
            self.progress.emit(100)


# ============================================================
# ANALOGUHR
# ============================================================

class AnalogClock(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

        self.setMinimumSize(100, 100)

    def paintEvent(self, event):
        side = min(self.width(), self.height())
        current_time = QTime.currentTime()

        config = getattr(
            self.window(),
            "current_config",
            {},
        )

        is_matrix = (
            isinstance(config, dict)
            and config.get("theme_mode") == "matrix"
        )

        accent = QColor("#00FF41") if is_matrix else QColor("#EAFF00")
        background = QColor("#000000") if is_matrix else QColor("#1A1A1A")
        hour_color = QColor("#008F11") if is_matrix else QColor(255, 0, 0)
        minute_color = (
            QColor("#00FF41")
            if is_matrix
            else QColor(200, 200, 200)
        )

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.translate(
            self.width() / 2,
            self.height() / 2,
        )
        painter.scale(side / 200.0, side / 200.0)

        painter.setPen(accent)
        painter.setBrush(background)
        painter.drawEllipse(-95, -95, 190, 190)

        for _ in range(12):
            painter.setPen(accent)
            painter.drawLine(80, 0, 90, 0)
            painter.rotate(30.0)

        painter.setPen(Qt.PenStyle.NoPen)

        painter.save()
        painter.setBrush(hour_color)
        painter.rotate(
            30.0 * (
                current_time.hour()
                + current_time.minute() / 60.0
            )
        )
        painter.drawConvexPolygon(
            QPolygon([
                QPoint(6, 10),
                QPoint(-6, 10),
                QPoint(0, -50),
            ])
        )
        painter.restore()

        painter.save()
        painter.setBrush(minute_color)
        painter.rotate(
            6.0 * (
                current_time.minute()
                + current_time.second() / 60.0
            )
        )
        painter.drawConvexPolygon(
            QPolygon([
                QPoint(4, 10),
                QPoint(-4, 10),
                QPoint(0, -80),
            ])
        )
        painter.restore()

        painter.save()
        painter.setBrush(accent)
        painter.rotate(6.0 * current_time.second())
        painter.drawConvexPolygon(
            QPolygon([
                QPoint(2, 10),
                QPoint(-2, 10),
                QPoint(0, -90),
            ])
        )
        painter.restore()

        painter.setBrush(accent)
        painter.drawEllipse(-5, -5, 10, 10)

        painter.end()


# ============================================================
# AUDIO-MANAGER – AUDIO IST OPTIONAL
# ============================================================

class SplashSoundManager:
    """Verwaltet optionale Musik und Soundeffekte."""

    SUPPORTED_EXTENSIONS = {
        ".wav", ".mp3", ".ogg", ".flac",
        ".m4a", ".aac", ".wma",
    }

    EVENT_FILES = {
        "music": (
            "intro_music.ogg",
            "soundtrack.ogg",
            "background.mp3",
            "music.mp3",
        ),
        "startup": (
            "boot.wav",
            "startup.wav",
            "start.wav",
            "intro.wav",
            "boot.ogg",
            "startup.mp3",
        ),
        "ready": (
            "success.wav",
            "ready.wav",
            "complete.wav",
            "finished.wav",
            "success.ogg",
            "success.mp3",
        ),
        "error": (
            "error.wav",
            "fail.wav",
            "warning.wav",
            "alert.wav",
            "error.ogg",
            "error.mp3",
        ),
        "glitch": (
            "glitch.wav",
            "static.wav",
            "digital.wav",
            "hack.wav",
            "glitch.ogg",
            "glitch.mp3",
        ),
        "impact": (
            "power_surge.wav",
            "impact.wav",
            "bass_drop.wav",
            "explosion.wav",
            "impact.ogg",
            "impact.mp3",
        ),
    }

    KEYWORDS = {
        "startup": ("boot", "startup", "intro", "launch"),
        "ready": ("success", "ready", "complete", "finished"),
        "error": ("error", "fail", "warning", "alert"),
        "glitch": ("glitch", "static", "digital", "hack"),
        "impact": ("impact", "surge", "explosion", "bass_drop"),
    }

    MIN_INTERVAL_MS = {
        "startup": 1000,
        "ready": 1500,
        "error": 900,
        "glitch": 500,
        "impact": 350,
    }

    def __init__(self, parent=None, enabled=True, master_volume=1.0, sound_profile=None):
        self.parent = parent
        try:
            self.master_volume = max(0.0, min(1.0, float(master_volume)))
        except (TypeError, ValueError):
            self.master_volume = 0.65
        self.sounds_dir = _find_sounds_dir()
        self.sound_profile = (
            dict(sound_profile) if isinstance(sound_profile, dict) else {}
        )
        self.files = []

        self.enabled = bool(MULTIMEDIA_AVAILABLE) and bool(enabled)
        self.players = {}
        self.last_play = {}

        self.music_player = None
        self.music_audio = None

        self.refresh()

        if not self.enabled:
            return

        try:
            self.music_player, self.music_audio = self._make_player(
                parent,
                0.32,
            )

            for event in self.EVENT_FILES:
                if event == "music":
                    continue

                self.players[event] = self._make_player(
                    parent,
                    0.65,
                )

            self.music_player.mediaStatusChanged.connect(
                self._loop_music
            )

        except Exception as exc:
            print(f"Audio nicht verfügbar: {exc}")

            self.enabled = False
            self.players.clear()
            self.music_player = None
            self.music_audio = None

    @staticmethod
    def _make_player(parent, volume):
        audio = QAudioOutput(parent)
        audio.setVolume(volume)

        player = QMediaPlayer(parent)
        player.setAudioOutput(audio)

        return player, audio

    def refresh(self):
        try:
            if not self.sounds_dir.is_dir():
                self.files = []
                return

            self.files = sorted(
                (
                    path for path in self.sounds_dir.iterdir()
                    if path.is_file()
                    and path.suffix.lower() in self.SUPPORTED_EXTENSIONS
                ),
                key=lambda path: path.name.lower(),
            )

        except OSError:
            self.files = []

    def _match(self, event):
        selected = self.sound_profile.get(event, "__auto__")

        if selected == "__none__":
            return None

        if selected not in (None, "", "__auto__"):
            wanted = Path(str(selected)).name.lower()
            for path in self.files:
                if path.name.lower() == wanted:
                    return path
            return None

        by_name = {
            path.name.lower(): path
            for path in self.files
        }

        for filename in self.EVENT_FILES.get(event, ()):
            path = by_name.get(filename.lower())

            if path is not None:
                return path

        keywords = self.KEYWORDS.get(event, (event,))

        for path in self.files:
            stem = (
                path.stem.lower()
                .replace("-", "_")
                .replace(" ", "_")
            )

            if any(word in stem for word in keywords):
                return path

        # Nur für den Startsound wird eine Fallback-Datei verwendet.
        if event == "startup" and self.files:
            return self.files[0]

        return None

    def _loop_music(self, status):
        if not self.enabled or self.music_player is None:
            return

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.music_player.setPosition(0)
            self.music_player.play()

    def play_music(self, volume=0.32):
        if not self.enabled or self.music_player is None:
            return False

        path = self._match("music")

        if path is None:
            return False

        try:
            volume = max(0.0, min(1.0, float(volume)))

            self.music_audio.setVolume(volume * self.master_volume)
            self.music_player.setSource(
                QUrl.fromLocalFile(str(path.resolve()))
            )
            self.music_player.play()

            return True

        except Exception as exc:
            print(f"Hintergrundmusik konnte nicht starten: {exc}")
            return False

    def play(self, event, volume=None, force=False):
        if not self.enabled:
            return False

        entry = self.players.get(event)

        if entry is None:
            return False

        path = self._match(event)

        if path is None:
            return False

        now = time.monotonic()
        interval = self.MIN_INTERVAL_MS.get(event, 500) / 1000.0

        if (
            not force
            and now - self.last_play.get(event, 0.0) < interval
        ):
            return False

        player, audio = entry

        try:
            if (
                player.playbackState()
                == QMediaPlayer.PlaybackState.PlayingState
            ):
                return False

            level = 0.65 if volume is None else float(volume)
            level = max(0.0, min(1.0, level))

            audio.setVolume(level * self.master_volume)
            player.setSource(
                QUrl.fromLocalFile(str(path.resolve()))
            )
            player.play()

            self.last_play[event] = now
            return True

        except Exception as exc:
            print(f"Soundeffekt '{event}' fehlgeschlagen: {exc}")
            return False

    def is_playing(self, event):
        if not self.enabled:
            return False

        if event == "music":
            player = self.music_player
        else:
            entry = self.players.get(event)
            player = entry[0] if entry else None

        if player is None:
            return False

        return (
            player.playbackState()
            == QMediaPlayer.PlaybackState.PlayingState
        )

    def stop_music(self):
        if self.music_player is not None:
            try:
                self.music_player.stop()
            except Exception:
                pass

    def stop(self):
        self.stop_music()

        for player, _audio in self.players.values():
            try:
                player.stop()
            except Exception:
                pass


# ============================================================
# BOOTSTRAP-WORKER
# ============================================================

class SplashBootstrapWorker(QThread):
    """Prüft und installiert benötigte Pakete im Hintergrund."""

    status_changed = pyqtSignal(str)
    progress_changed = pyqtSignal(int)
    completed = pyqtSignal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cancel_requested = False
        self._process = None

    def cancel(self):
        self.cancel_requested = True

        process = self._process

        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    def _run_command(self, command, timeout=600):
        process = None

        try:
            with tempfile.TemporaryFile(
                mode="w+t",
                encoding="utf-8",
                errors="replace",
            ) as stdout_file, tempfile.TemporaryFile(
                mode="w+t",
                encoding="utf-8",
                errors="replace",
            ) as stderr_file:

                kwargs = {
                    "stdout": stdout_file,
                    "stderr": stderr_file,
                    "text": True,
                }

                if os.name == "nt":
                    kwargs["creationflags"] = getattr(
                        subprocess,
                        "CREATE_NO_WINDOW",
                        0,
                    )

                process = subprocess.Popen(command, **kwargs)
                self._process = process
                started = time.monotonic()

                while process.poll() is None:
                    if self.cancel_requested:
                        process.terminate()

                        try:
                            process.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()

                        return -1, "", "Abgebrochen"

                    if time.monotonic() - started > timeout:
                        process.kill()
                        process.wait()

                        return -1, "", "Zeitüberschreitung"

                    time.sleep(0.1)

                code = process.returncode

                stdout_file.seek(0)
                stderr_file.seek(0)

                return (
                    code,
                    stdout_file.read(),
                    stderr_file.read(),
                )

        except Exception as exc:
            if process is not None and process.poll() is None:
                try:
                    process.kill()
                    process.wait()
                except OSError:
                    pass

            return -1, "", str(exc)

        finally:
            self._process = None

    def run(self):
        try:
            if self.cancel_requested:
                self.completed.emit(False, "Abgebrochen")
                return

            self.progress_changed.emit(5)
            self.status_changed.emit("PRÜFE SYSTEMUMGEBUNG ...")

            if os.name == "nt":
                if shutil.which("git"):
                    self.status_changed.emit("GIT VERFÜGBAR")
                else:
                    self.status_changed.emit(
                        "GIT NICHT GEFUNDEN – PRÜFE PYTHON-PAKETE"
                    )

            missing = []

            for package, import_name in REQUIRED_PACKAGES.items():
                if self.cancel_requested:
                    self.completed.emit(False, "Abgebrochen")
                    return

                try:
                    present = (
                        importlib.util.find_spec(import_name) is not None
                    )
                except (
                    ImportError,
                    ValueError,
                    ModuleNotFoundError,
                ):
                    present = False

                if not present:
                    missing.append(package)

            self.progress_changed.emit(20)

            if self.cancel_requested:
                self.completed.emit(False, "Abgebrochen")
                return

            if not missing:
                self.progress_changed.emit(100)
                self.completed.emit(True, "ready")
                return

            for index, package in enumerate(missing):
                if self.cancel_requested:
                    self.completed.emit(False, "Abgebrochen")
                    return

                self.status_changed.emit(
                    f"INSTALLIERE {package.upper()} ..."
                )

                code, stdout, stderr = self._run_command([
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    package,
                ])

                if self.cancel_requested:
                    self.completed.emit(False, "Abgebrochen")
                    return

                if code != 0:
                    details = (stderr or stdout or "").strip()
                    details = details[-1200:]

                    self.completed.emit(
                        False,
                        f"Installation von {package} fehlgeschlagen:\n"
                        f"{details or 'Keine Fehlerdetails verfügbar.'}",
                    )
                    return

                progress = 20 + int(
                    75 * (index + 1) / len(missing)
                )
                self.progress_changed.emit(progress)

            self.progress_changed.emit(100)
            self.completed.emit(True, "restart")

        except Exception as exc:
            self.completed.emit(
                False,
                f"Bootstrap-Fehler: {exc}",
            )


class MatrixLogoWidget(QWidget):
    """Zeichnet ein ASCII-Logo mit festen Zeichenpositionen."""

    def __init__(self, lines, parent=None):
        super().__init__(parent)
        self.lines = list(lines)
        self.logo_font = QFont("DejaVu Sans Mono")
        self.logo_font.setStyleHint(QFont.StyleHint.Monospace)
        self.logo_font.setBold(True)
        self.logo_font.setPixelSize(12)
        self.setMinimumSize(0, 0)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground,
            True,
        )

    def set_logo_font(self, font):
        self.logo_font = QFont(font)
        self.updateGeometry()
        self.update()

    def sizeHint(self):
        metrics = QFontMetrics(self.logo_font)
        cell_width = max(1, metrics.horizontalAdvance("M"))
        line_height = max(1, metrics.lineSpacing())
        columns = max((len(line) for line in self.lines), default=0)
        return QSize(columns * cell_width, line_height * len(self.lines) + 4)

    def paintEvent(self, event):
        if not self.lines:
            return

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.TextAntialiasing,
            True,
        )
        painter.setFont(self.logo_font)
        painter.setPen(QColor("#00FF41"))

        metrics = QFontMetrics(self.logo_font)
        cell_width = max(1, metrics.horizontalAdvance("M"))
        line_height = max(1, metrics.lineSpacing())
        columns = max(len(line) for line in self.lines)

        start_x = max(
            0,
            (self.width() - columns * cell_width) // 2,
        )
        start_y = max(
            0,
            (self.height() - line_height * len(self.lines)) // 2,
        )

        for row, line in enumerate(self.lines):
            y = start_y + row * line_height
            for column, char in enumerate(line):
                x = start_x + column * cell_width
                painter.drawText(
                    x,
                    y,
                    cell_width,
                    line_height,
                    Qt.AlignmentFlag.AlignCenter,
                    char,
                )

        painter.end()

# ============================================================
# CINEMATIC MATRIX SPLASH
# ============================================================

class CinematicMatrixSplash(QWidget):
    """Animierter Matrix-Splashscreen mit mindestens 15 Sekunden Laufzeit."""

    finished = pyqtSignal()

    MIN_DURATION_MS = 5000

    
  
    LOGO_RAW = [
        " ◢◤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◥◣ ",
        " █                 _______  _______  _______  _______  __   __                █ ",
        " █               |       ||       ||   _   ||       ||  |_|  |                █ ",
        " █               |   _   ||  _____||  |_|  ||       ||       |                █ ",
        " █               |  | |  || |_____ |       ||       ||       |                █ ",
        " █               |  |_|  ||_____  ||       ||      _||       |                █ ",
        " █               |       | _____| ||   _   ||     |_ | ||_|| |                █ ",
        " █               |_______||_______||__| |__||_______||_|   |_|                █ ",
        " █                                                                            █ ",
        " █                 _______  _______  _______  _______  __   __                █ ",
        " █               |       ||   _   ||       ||       ||  | |  |                █ ",
        " █               |    ___||  |_|  ||_     _||       ||  |_|  |                █ ",
        " █               |   |___ |       |  |   |  |       ||       |                █ ",
        " █               |    ___||       |  |   |  |      _||       |                █ ",
        " █               |   |    |   _   |  |   |  |     |_ | ||_|| |                █ ",
        " █               |___|    |__| |__|  |___|  |_______||_|   |_|                █ ",
        " █                                                                            █ ",
        " █     __   __  _______  __    _  _______  _______  _______  ______           █ ",
        " █    |  |_|  ||   _   ||  |  | ||   _   ||     __||    ___||    _ |          █ ",
        " █    |       ||  |_|  ||   |_| ||  |_|  ||    |  ||   |___ |   | ||          █ ",
        " █    |       ||       ||       ||       ||    |  ||    ___||   |_||_         █ ",
        " █    |       ||       ||  _    ||       ||    |  ||   |___ |    __  |        █ ",
        " █    | ||_|| ||   _   || | |   ||   _   ||    |__||   |___ |   |  | |        █ ",
        " █    |_|   |_||__| |__||_|  |__||__| |__||_______||_______||___|  |_|        █ ",
        " █                                                                            █ ",
        " █  ──────────────────[ SYSTEM: NEURAL_LINK OPERATIONAL ]───────────────────  █ ",
        " █                     >> OSCAM EMU PATCH MANAGER v1.9.4  <<                  █ ",
        " █               >> CODENAME: Speedy_Oscam-_Patch_Manager 2026 <<             █ ",
        " ◥◣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◢◤ ",
    ]


    
    @staticmethod
    def _make_logo(lines):
        # Äußere Leerzeichen entfernen und einheitliche Breite bestimmen
        cleaned = [line.strip() for line in lines]
        width = max(len(line) for line in cleaned)

        result = []

        # Oberer Rahmen: exakt dieselbe Zeichenbreite wie alle Zeilen
        result.append("◢◤" + "━" * (width - 4) + "◥◣")

        # Innenzeilen: Seitenränder auf dieselben Zeichenpositionen setzen
        for line in cleaned[1:-1]:
            content = line

            if content.startswith("█"):
                content = content[1:]

            if content.endswith("█"):
                content = content[:-1]

            content = content[:width - 2].center(width - 2)
            result.append("█" + content + "█")

        # Unterer Rahmen
        result.append("◥◣" + "━" * (width - 4) + "◢◤")

        return result

    LOGO_TEXT = _make_logo.__func__(LOGO_RAW)




    def __init__(self, duration=22000, parent=None, sound_enabled=True, sound_volume=65, variant='bot', animation_speed=100, sound_profile=None):
        super().__init__(parent)

        try:
            duration = int(duration)
        except (TypeError, ValueError):
            duration = self.MIN_DURATION_MS

        self.duration = max(self.MIN_DURATION_MS, duration)
        self.variant = variant if variant in ('bot', 'premium', 'minimal', 'dashboard', 'reactor360', 'nebula') else 'bot'
        try:
            self.animation_speed = max(50, min(200, int(animation_speed)))
        except (TypeError, ValueError):
            self.animation_speed = 100
        self.started_at = time.monotonic()

        self.is_closing = False
        self._worker = None
        self._close_retry_scheduled = False
        self._bootstrap_done = False
        self._success_sequence_started = False
        self._success_sequence_finished = False
        self._bootstrap_success = False
        self._restart_pending = False
        self._error_close_scheduled = False
        self._dashboard_last_bucket = -1
        self._dashboard_impact_played = False
        self._reactor360_impact_played = False
        self._nebula_impact_played = False

        self.os_type = platform.system()

        self._corner_factor = 0.0
        self.flash_alpha = 0
        self.prog = 0
        self.scanner_y = 0
        self.glitch_count = 0
        self.pulse = 0.0
        self.shockwaves = []
        self.sparks = []
        self.rgb_until = 0.0
        self.rgb_offset = 0
        self.shake = 0.0

        self.chars = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+=-"
            "アイウエオカキクケコサシスセソタチツテト"
        )

        self.sounds = SplashSoundManager(
            self,
            enabled=sound_enabled,
            master_volume=max(0, min(100, int(sound_volume))) / 100.0,
            sound_profile=sound_profile,
        )

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self._center_and_size()
        self._initialize_matrix()
        self._build_ui()
        self._apply_variant()

        self.center_on_screen()
        self.show()

        QTimer.singleShot(0, self.center_on_screen)
        QTimer.singleShot(0, self._fit_logo_font)

        self._start_animations()

        QTimer.singleShot(
            2500,
            lambda: self._trigger_power_surge(1.0),
        )
        QTimer.singleShot(
            5000,
            lambda: self._trigger_power_surge(1.6),
        )
        QTimer.singleShot(
            7500,
            lambda: self._trigger_power_surge(1.25),
        )

        QTimer.singleShot(0, self.run_bootstrap_checks)

        self.sounds.play_music(0.32)
        self.sounds.play("startup", 0.70, force=True)

    def _center_and_size(self):
        app = QApplication.instance()
        screen = None

        if app is not None:
            screen = app.primaryScreen()

        if screen is None:
            self.resize(1000, 650)
            return

        geometry = screen.availableGeometry()

        width = min(1400, int(geometry.width() * 0.96))
        height = min(850, int(geometry.height() * 0.92))  

        self.resize(width, height)

        self.move(
            geometry.x() + (geometry.width() - width) // 2,
            geometry.y() + (geometry.height() - height) // 2,
        )

    def _initialize_matrix(self):
        self.columns = max(1, self.width() // 14)

        self.drops = [
            random.randint(-40, 0)
            for _ in range(self.columns)
        ]

        self.trails = [
            random.randint(6, 24)
            for _ in range(self.columns)
        ]

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self._initialize_matrix()
        self._fit_logo_font()


    
    def _fit_logo_font(self):
        """Passt die Schriftgröße für alle Logo-Teile einheitlich an."""
        label = getattr(self, "lbl_logo", None)
        if label is None:
            return
        if getattr(self, 'variant', 'bot') != 'bot':
            font = QFont('DejaVu Sans')
            font.setBold(True)
            font.setPixelSize(42 if self.variant == 'premium' else 48)
            label.setFont(font)
            return

        font = QFont("DejaVu Sans Mono")
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setBold(True)

        lines = self.LOGO_TEXT
        available_width = max(300, self.width() - 36)
        available_height = max(180, int(self.height() * 0.62))
        selected_size = 8

        for size in range(30, 7, -1):
            font.setPixelSize(size)
            metrics = QFontMetrics(font)
            widest_line = max(metrics.horizontalAdvance(line) for line in lines)
            total_height = metrics.lineSpacing() * len(lines)
            if widest_line <= available_width and total_height <= available_height:
                selected_size = size
                break

        font.setPixelSize(selected_size)
        self._logo_font_size = selected_size

        # Der obere Logo-Teil bleibt normal grün.
        self.lbl_logo.setFont(font)
        self.lbl_logo.setText("\n".join(self._logo_top_lines))
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setWordWrap(False)
        self.lbl_logo.setMinimumWidth(0)
        self.lbl_logo.setMinimumHeight(0)
        self.lbl_logo.setContentsMargins(0, 0, 0, 0)

        # Die drei hervorgehobenen Zeilen verwenden dieselbe Monospace-Schrift
        # und dieselbe Größe. Nur der eigentliche Text ist farbig; die beiden
        # seitlichen Rahmenzeichen bleiben im normalen Matrix-Grün.
        colors = ("#0000FF", "#FFA500", "#FF0000")
        markers = (
            "SYSTEM: NEURAL_LINK OPERATIONAL",
            "OSCAM EMU PATCH MANAGER v1.9.4",
            "CODENAME: Speedy Oscam Patch Manager 2026",
        )
        import html
        def preserve_spaces(value):
            # Im <pre>-Block bleiben normale Leerzeichen exakt erhalten.
            # NBSP darf hier nicht verwendet werden, da es je nach Font-Rendering
            # eine andere Breite haben kann und dadurch sichtbare Rahmenlücken erzeugt.
            return html.escape(value)

        line_height = QFontMetrics(font).lineSpacing()
        for label, raw_line, color, marker in zip(
            self.logo_color_labels, self._logo_color_lines, colors, markers
        ):
            label.setFont(font)
            # Exakt eine normale Logo-Zeilenhöhe verhindert, dass die untere
            # Pixelreihe der senkrechten Rahmenzeichen abgeschnitten wird.
            label.setFixedHeight(line_height)
            marker_start = raw_line.find(marker)
            if marker_start >= 0:
                prefix = preserve_spaces(raw_line[:marker_start])
                highlighted = preserve_spaces(marker)
                suffix = preserve_spaces(raw_line[marker_start + len(marker):])
                content_html = (
                    f'<span style="color:#00FF41; white-space:pre">{prefix}</span>'
                    f'<span style="color:{color}; white-space:pre">{highlighted}</span>'
                    f'<span style="color:#00FF41; white-space:pre">{suffix}</span>'
                )
            else:
                content_html = (
                    f'<span style="color:#00FF41; white-space:pre">'
                    f'{preserve_spaces(raw_line)}</span>'
                )
            label.setText(
                '<html><head><style>body{margin:0;padding:0;white-space:pre;}'
                'pre{margin:0;padding:0;white-space:pre;}</style></head><body>'
                '<pre style="margin:0; padding:0; line-height:100%; font-family:\'DejaVu Sans Mono\', monospace; '
                f'font-size:{selected_size}px; font-weight:bold;">'
                f'{content_html}'
                '</pre></body></html>'
            )
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(False)
            label.setContentsMargins(0, 0, 0, 0)
            label.setMinimumWidth(0)
            label.setMinimumHeight(0)

        self.lbl_logo_bottom.setFont(font)
        self.lbl_logo_bottom.setText(self._logo_bottom_line)
        self.lbl_logo_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_bottom.setWordWrap(False)
        self.lbl_logo_bottom.setContentsMargins(0, 0, 0, 0)

    def _apply_variant(self):
        if self.variant == "bot":
            return

        if self.variant == "dashboard":
            self.title.setText("◈  OSCAM // MATRIX BOOT DASHBOARD")
            self.lbl_logo.setText("OSCAM\nBOOT SYSTEM")
            self.lbl_logo.setStyleSheet(
                "color:#65E6FF;background:transparent;border:none;"
                "font-weight:800;letter-spacing:5px;"
            )
            subtitle_text = "LIVE DIAGNOSTICS  •  SYSTEM INITIALIZATION"

            if getattr(self, "pbar", None) is not None:
                self.pbar.setStyleSheet("""
                    QProgressBar {
                        color:#DDFBFF;
                        background:rgba(0,12,20,220);
                        border:1px solid #20DDF5;
                        border-radius:5px;
                        text-align:center;
                        min-height:12px;
                    }
                    QProgressBar::chunk {
                        border-radius:4px;
                        background:qlineargradient(
                            x1:0,y1:0,x2:1,y2:0,
                            stop:0 #007C91,
                            stop:0.5 #20DDF5,
                            stop:1 #9DFFB0
                        );
                    }
                """)

        elif self.variant == "reactor360":
            self.title.setText("◈  OSCAM PATCH MANAGER // REACTOR 360°")
            self.lbl_logo.setText("Oscam Patch Manager\nby Speedy005")
            self.lbl_logo.setFont(
                QFont("DejaVu Sans", 36, QFont.Weight.Black)
            )
            self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_logo.setStyleSheet(
                "color:#00E5FF;background:transparent;border:none;"
                "font-weight:900;letter-spacing:2px;"
            )

            self._reactor360_glow = QGraphicsDropShadowEffect(self.lbl_logo)
            self._reactor360_glow.setOffset(0, 0)
            self._reactor360_glow.setColor(QColor(0, 229, 255))
            self._reactor360_glow.setBlurRadius(24)
            self.lbl_logo.setGraphicsEffect(self._reactor360_glow)
            subtitle_text = "MULTICOLOR ENERGY CORE  •  SYSTEM INITIALIZATION"

            self.ui.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True
            )
            self.ui.setAttribute(
                Qt.WidgetAttribute.WA_NoSystemBackground, True
            )
            self.ui.setAutoFillBackground(False)
            self.ui.setObjectName("Reactor360Overlay")
            self.ui.setStyleSheet("""
                QWidget#Reactor360Overlay {
                    background: transparent;
                    border: none;
                }
                QLabel {
                    background: transparent;
                    border: none;
                }
            """)

            self.title.setStyleSheet(
                "color:#39FF88;background:transparent;border:none;"
                "font-weight:bold;"
            )
            self.host.setStyleSheet(
                "color:#A855F7;background:transparent;border:none;"
            )

            if getattr(self, "pbar", None) is not None:
                self.pbar.setStyleSheet("""
                    QProgressBar {
                        color:#FFFFFF;
                        background:rgba(8,5,22,220);
                        border:1px solid #A855F7;
                        border-radius:5px;
                        text-align:center;
                        min-height:12px;
                    }
                    QProgressBar::chunk {
                        border-radius:4px;
                        background:qlineargradient(
                            x1:0,y1:0,x2:1,y2:0,
                            stop:0 #00E5FF,
                            stop:0.25 #287BFF,
                            stop:0.5 #A855F7,
                            stop:0.75 #FF35C7,
                            stop:1 #39FF88
                        );
                    }
                """)

        elif self.variant == "nebula":
            self.title.setText("✦  OSCAM // NEBULA QUANTUM PORTAL")
            self.lbl_logo.setText("Oscam Patch Manager\nby Speedy005")
            self.lbl_logo.setFont(
                QFont("DejaVu Sans", 34, QFont.Weight.Black)
            )
            self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lbl_logo.setStyleSheet(
                "color:#B9C8FF;background:transparent;border:none;"
                "font-weight:900;"
            )

            # Ursprüngliches Label behält seinen Layout-Platz, wird aber unsichtbar.
            self.lbl_logo.setGraphicsEffect(None)
            self.lbl_logo.setStyleSheet(
                "color:rgba(0,0,0,0);background:transparent;border:none;"
            )

            # Separates, frei bewegliches NEBULA-Logo.
            self._nebula_fly_logo = QLabel(
                "Oscam Patch Manager\nby Speedy005", self.ui
            )
            self._nebula_fly_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._nebula_fly_logo.setWordWrap(False)

            # Die endgültige Schriftgröße wird im Timer anhand der
            # tatsächlichen Fenstergröße berechnet.
            self._nebula_fly_logo.setFont(
                QFont("DejaVu Sans", 20, QFont.Weight.Black)
            )
            self._nebula_fly_logo.resize(400, 92)
            self._nebula_logo_width_cache = -1
            self._nebula_fly_logo.setStyleSheet(
                "color:#B9C8FF;background:transparent;border:none;"
                "font-weight:900;letter-spacing:2px;"
            )

            self._nebula_glow = QGraphicsDropShadowEffect(
                self._nebula_fly_logo
            )
            self._nebula_glow.setOffset(0, 0)
            self._nebula_glow.setColor(QColor(145, 105, 255))
            self._nebula_glow.setBlurRadius(30)
            self._nebula_fly_logo.setGraphicsEffect(self._nebula_glow)
            self._nebula_fly_logo.raise_()

            subtitle_text = "QUANTUM PORTAL  •  SYSTEM INITIALIZATION"

            self.ui.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground, True
            )
            self.ui.setAttribute(
                Qt.WidgetAttribute.WA_NoSystemBackground, True
            )
            self.ui.setAutoFillBackground(False)
            self.ui.setObjectName("NebulaPortalOverlay")
            self.ui.setStyleSheet("""
                QWidget#NebulaPortalOverlay {
                    background: transparent;
                    border: none;
                }
                QLabel {
                    background: transparent;
                    border: none;
                }
            """)

            self.title.setStyleSheet(
                "color:#D8C5FF;background:transparent;border:none;"
                "font-weight:bold;"
            )
            self.host.setStyleSheet(
                "color:#80DFFF;background:transparent;border:none;"
            )

            if getattr(self, "pbar", None) is not None:
                self.pbar.setStyleSheet("""
                    QProgressBar {
                        color:#F5F0FF;
                        background:rgba(8,5,24,225);
                        border:1px solid #9875FF;
                        border-radius:6px;
                        text-align:center;
                        min-height:12px;
                    }
                    QProgressBar::chunk {
                        border-radius:5px;
                        background:qlineargradient(
                            x1:0,y1:0,x2:1,y2:0,
                            stop:0 #7655FF,
                            stop:0.35 #62CFFF,
                            stop:0.7 #D8A7FF,
                            stop:1 #FFD78A
                        );
                    }
                """)

        elif self.variant == "premium":
            self.title.setText("◈  OSCAM // PREMIUM START")
            self.lbl_logo.setText("OSCAM\nPATCH MANAGER")
            self.lbl_logo.setStyleSheet(
                "color:#65E6FF;background:transparent;border:none;"
                "font-weight:800;letter-spacing:5px;"
            )
            subtitle_text = "SECURE SYSTEM INITIALIZATION"

            # Dreifarbiger Neon-Pulse nur fuer Premium
            self._premium_glow = QGraphicsDropShadowEffect(self.lbl_logo)
            self._premium_glow.setOffset(0, 0)
            self.lbl_logo.setGraphicsEffect(self._premium_glow)
            self._update_premium_logo_glow()

            # Premium-Oberfläche leicht transparent, damit der Reaktor
            # hinter Logo und Statusanzeigen sichtbar bleibt.
            # Premium: Hintergrund des Kind-Widgets transparent halten,
            # damit der animierte Cyber-Reactor dahinter sichtbar bleibt.
            self.ui.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.ui.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
            self.ui.setAutoFillBackground(False)
            self.ui.setStyleSheet("""
                QWidget#CyberReactorOverlay {
                    background: transparent;
                    border: none;
                }
                QLabel {
                    background: transparent;
                    border: none;
                }
            """)
            self.ui.setObjectName("CyberReactorOverlay")
            if getattr(self, "pbar", None) is not None:
                self.pbar.setStyleSheet("""
                    QProgressBar {
                        color: #DDFBFF;
                        background: rgba(10, 35, 60, 210);
                        border: 1px solid #36CFF5;
                        border-radius: 5px;
                        text-align: center;
                        min-height: 12px;
                    }
                    QProgressBar::chunk {
                        border-radius: 4px;
                        background: qlineargradient(
                            x1:0, y1:0, x2:1, y2:0,
                            stop:0 #0879C9, stop:0.5 #42E5FF,
                            stop:1 #D8FFFF
                        );
                    }
                """)
        else:
            self.title.setText("OSCAM PATCH MANAGER")
            self.lbl_logo.setText("OSCAM")
            self.lbl_logo.setStyleSheet(
                "color:#D7E2EA;background:transparent;border:none;"
                "font-weight:600;letter-spacing:3px;"
            )
            subtitle_text = "SYSTEM START"

        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setWordWrap(True)

        for label in self.logo_color_labels:
            label.hide()
        self.lbl_logo_bottom.hide()

        if getattr(self, "subtitle", None) is not None:
            self.subtitle.setText(subtitle_text)

    def _build_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        self.ui = QWidget(self)
        self.ui.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 5, 3, 235);
                border: none;
                border-radius: 0px;
            }
        """)

        layout = QVBoxLayout(self.ui)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        # Kopfzeile bleibt am oberen Rand.
        header = QHBoxLayout()

        self.title = QLabel("◈  OSCAM // NEURAL BOOT")
        self.title.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.title.setStyleSheet(
            "color:#8DFFB0;border:none;background:transparent;"
        )

        self.host = QLabel(f"OS: {self.os_type.upper()}  •  SECURE LINK")
        self.host.setFont(QFont("Consolas", 9))
        self.host.setStyleSheet(
            "color:#00B83F;border:none;background:transparent;"
        )

        header.addWidget(self.title)
        header.addStretch(1)
        header.addWidget(self.host)
        layout.addLayout(header)

        # Logo in mehrere Labels aufteilen, damit nur die drei unteren
        # Einträge farbig sind. Die übrigen ASCII-Zeilen bleiben unverändert.
        system_index = next(i for i, line in enumerate(self.LOGO_TEXT) if "SYSTEM:" in line)
        manager_index = next(i for i, line in enumerate(self.LOGO_TEXT) if "OSCAM EMU PATCH MANAGER" in line)
        codename_index = next(i for i, line in enumerate(self.LOGO_TEXT) if "CODENAME:" in line)
        self._logo_top_lines = self.LOGO_TEXT[:system_index]
        self._logo_color_lines = [
            self.LOGO_TEXT[system_index],
            self.LOGO_TEXT[manager_index],
            self.LOGO_TEXT[codename_index],
        ]
        self._logo_bottom_line = self.LOGO_TEXT[-1]

        self.lbl_logo = QLabel("\n".join(self._logo_top_lines))
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setWordWrap(False)
        self.lbl_logo.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.lbl_logo.setMinimumWidth(0)
        self.lbl_logo.setContentsMargins(0, 0, 0, 0)
        self.lbl_logo.setStyleSheet(
            "color:#00FF41;border:none;background:transparent;"
        )

        self.logo_color_labels = []
        for _ in range(3):
            color_label = QLabel()
            color_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            color_label.setStyleSheet(
                "border:none;background:transparent;"
            )
            self.logo_color_labels.append(color_label)

        self.lbl_logo_bottom = QLabel(self._logo_bottom_line)
        self.lbl_logo_bottom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo_bottom.setWordWrap(False)
        self.lbl_logo_bottom.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.lbl_logo_bottom.setStyleSheet(
            "color:#00FF41;border:none;background:transparent;"
        )

        self.subtitle = QLabel(
            "PATCH INTELLIGENCE  •  REPOSITORY SYNC  •  DIAGNOSTICS"
        )
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle.setFont(QFont("Consolas", 9))
        self.subtitle.setStyleSheet(
            "color:#00A832;border:none;background:transparent;"
        )

        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        # Keine Zwischenräume zwischen den ASCII-Zeilen: sonst entstehen
        # sichtbare Lücken im seitlichen Rahmen genau bei den farbigen Zeilen.
        center_layout.setSpacing(0)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.lbl_logo, 0, Qt.AlignmentFlag.AlignHCenter)
        for color_label in self.logo_color_labels:
            center_layout.addWidget(color_label, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(self.lbl_logo_bottom, 0, Qt.AlignmentFlag.AlignHCenter)
        center_layout.addWidget(self.subtitle, 0, Qt.AlignmentFlag.AlignHCenter)

        # Gleiche Stretch-Faktoren ober- und unterhalb des Blocks halten ihn
        # mittig im freien Bereich; Status, Balken und Footer bleiben unten.
        layout.addStretch(1)
        layout.addLayout(center_layout, 0)
        layout.addStretch(1)

        self.status = QLabel("INITIALIZING NEURAL INTERFACE ...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        self.status.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        self.status.setStyleSheet(
            "color:#7CFF9A;border:none;background:transparent;"
        )
        layout.addWidget(self.status)

        self.pbar = QProgressBar()
        self.pbar.setRange(0, 100)
        self.pbar.setValue(0)
        self.pbar.setTextVisible(False)
        self.pbar.setFixedHeight(16)
        self.pbar.setStyleSheet("""
            QProgressBar {
                border:1px solid #008F11;
                border-radius:5px;
                background:#000803;
                padding:2px;
            }
            QProgressBar::chunk {
                border-radius:3px;
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 #006B20,
                    stop:0.45 #00FF41,
                    stop:0.75 #00DDFF,
                    stop:1 #FFFFFF
                );
            }
        """)
        layout.addWidget(self.pbar)

        if self.variant == "dashboard":
            self.dashboard_metrics = QLabel(
                "CPU: --%   RAM: --%   DISK: --%   PYTHON: "
                + platform.python_version()
            )
            self.dashboard_metrics.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            self.dashboard_metrics.setStyleSheet(
                "color:#65E6FF;background:rgba(0,18,28,190);"
                "border:1px solid #087F91;border-radius:4px;padding:6px;"
            )
            layout.addWidget(self.dashboard_metrics)

            self.dashboard_log = QPlainTextEdit()
            self.dashboard_log.setReadOnly(True)
            self.dashboard_log.setMaximumBlockCount(7)
            self.dashboard_log.setMinimumHeight(76)
            self.dashboard_log.setMaximumHeight(100)
            self.dashboard_log.setFont(QFont("Consolas", 8))
            self.dashboard_log.setStyleSheet("""
                QPlainTextEdit {
                    color:#9DFFB0;
                    background:rgba(0,8,14,220);
                    border:1px solid #087F91;
                    border-radius:4px;
                    padding:5px;
                }
            """)
            layout.addWidget(self.dashboard_log)
            self._append_dashboard_log("DASHBOARD INITIALIZED")

        footer = QHBoxLayout()
        sound_state = "ON" if self.sounds.enabled else "AUDIO OPTIONAL"
        self.volume_label = QLabel(
            f"CORE v4.0  •  POWER MODE  •  SOUND: {sound_state}"
            f"  •  {len(self.sounds.files)} FILE(S)"
        )
        self.volume_label.setFont(QFont("Consolas", 8))
        self.volume_label.setStyleSheet(
            "color:#008F11;border:none;background:transparent;"
        )
        footer.addWidget(self.volume_label)
        footer.addStretch(1)

        self.close_button = QPushButton("ABBRECHEN  ×")
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton {
                color:#7CFF9A;
                background:rgba(0,25,10,220);
                border:1px solid #008F11;
                border-radius:5px;
                padding:8px 16px;
                font-family:Consolas;
                font-weight:bold;
            }
            QPushButton:hover {
                color:#001A08;
                background:#00FF41;
                border-color:#9DFFB0;
            }
            QPushButton:disabled {
                color:#366B43;
            }
        """)
        self.close_button.clicked.connect(self.finish)
        footer.addWidget(self.close_button)
        layout.addLayout(footer)

        main.addWidget(self.ui)

    def _append_dashboard_log(self, message):
        if self.variant != "dashboard":
            return

        log = getattr(self, "dashboard_log", None)
        if log is None:
            return

        timestamp = time.strftime("%H:%M:%S")
        log.appendPlainText(f"[{timestamp}] {message}")

    def _update_dashboard_metrics(self):
        if self.is_closing or self.variant != "dashboard":
            return

        label = getattr(self, "dashboard_metrics", None)
        if label is None:
            return

        try:
            import psutil

            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage(os.path.abspath(os.sep)).percent

            label.setText(
                f"CPU: {cpu:5.1f}%   "
                f"RAM: {ram:5.1f}%   "
                f"DISK: {disk:5.1f}%   "
                f"PYTHON: {platform.python_version()}"
            )
        except Exception as exc:
            label.setText(
                f"SYSTEM MONITOR UNAVAILABLE: {type(exc).__name__}"
            )

    def center_on_screen(self):
        app = QApplication.instance()

        if app is None:
            return

        screen = app.primaryScreen()

        if screen is None:
            return

        geometry = screen.availableGeometry()

        self.move(
            geometry.x() + (geometry.width() - self.width()) // 2,
            geometry.y() + (geometry.height() - self.height()) // 2,
        )

    def _start_animations(self):
        speed_factor = 100.0 / self.animation_speed

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(max(1, round(25 * speed_factor)))

        self.timer_glitch = QTimer(self)
        self.timer_glitch.timeout.connect(self.glitch)
        if self.variant == "bot":
            self.timer_glitch.start(max(1, round(100 * speed_factor)))

        self.timer_scanner = QTimer(self)
        self.timer_scanner.timeout.connect(self._update_scanner)
        if self.variant == "bot":
            self.timer_scanner.start(max(1, round(16 * speed_factor)))

        self.completion_timer = QTimer(self)
        self.completion_timer.timeout.connect(self._check_completion)
        self.completion_timer.start(100)

        if self.variant == "dashboard":
            self.dashboard_timer = QTimer(self)
            self.dashboard_timer.timeout.connect(
                self._update_dashboard_metrics
            )
            self.dashboard_timer.start(1500)
            QTimer.singleShot(0, self._update_dashboard_metrics)

        self.anim = QPropertyAnimation(self, b"corner_factor", self)
        self.anim.setDuration(max(1, round(1800 * speed_factor)))
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()

    # --------------------------------------------------------
    # ANIMATIONEN
    # --------------------------------------------------------

    def _tick(self):
        if self.is_closing:
            return

        self.pulse += 0.12
        if self.variant == "premium":
            self._update_premium_logo_glow()
        elif self.variant == "nebula":
            colors = (
                QColor(145, 105, 255),
                QColor(75, 205, 255),
                QColor(255, 205, 125),
                QColor(205, 145, 255),
            )
            phase = (self.pulse * 0.025) % len(colors)
            index = int(phase)
            fraction = phase - index
            first = colors[index]
            second = colors[(index + 1) % len(colors)]

            r = round(first.red() * (1 - fraction) + second.red() * fraction)
            g = round(first.green() * (1 - fraction) + second.green() * fraction)
            b = round(first.blue() * (1 - fraction) + second.blue() * fraction)

            self._nebula_glow.setColor(QColor(r, g, b))
            self._nebula_glow.setBlurRadius(
                24 + 26 * (0.5 + 0.5 * math.sin(self.pulse * 0.16))
            )
            self._nebula_fly_logo.setStyleSheet(
                f"color:rgb({r},{g},{b});"
                "background:transparent;border:none;"
                "font-weight:900;letter-spacing:2px;"
            )

            # Schrift dynamisch an die aktuelle Fensterbreite anpassen.
            area_width = self.ui.width()
            area_height = self.ui.height()
            available_text = max(80, int(area_width * 0.48))

            if self._nebula_logo_width_cache != area_width:
                logo_font = QFont("DejaVu Sans", QFont.Weight.Black)
                chosen_width = 0

                for pixel_size in range(44, 7, -1):
                    logo_font.setPixelSize(pixel_size)
                    metrics = QFontMetrics(logo_font)
                    measured = max(
                        metrics.horizontalAdvance("Oscam Patch Manager"),
                        metrics.horizontalAdvance("by Speedy005"),
                    )
                    if measured <= available_text - 32:
                        chosen_width = measured
                        break

                self._nebula_fly_logo.setFont(logo_font)
                logo_width = max(1, int(area_width * 0.72))
                self._nebula_fly_logo.setFixedSize(logo_width, 92)
                self._nebula_logo_width_cache = area_width

            logo_width = self._nebula_fly_logo.width()
            logo_height = self._nebula_fly_logo.height()
            travel = max(0, area_width - logo_width - 32)
            wave = 0.5 + 0.5 * math.sin(self.pulse * 0.075)
            x = 16 + int(travel * wave)
            y = int(
                area_height * 0.52 - logo_height / 2
                + 16 * math.sin(self.pulse * 0.11)
            )
            self._nebula_fly_logo.move(x, y)
            self._nebula_fly_logo.raise_()

        elif self.variant == "reactor360":
            colors = (
                QColor(0, 229, 255),
                QColor(40, 123, 255),
                QColor(168, 85, 247),
                QColor(255, 53, 199),
                QColor(57, 255, 136),
            )
            phase = (self.pulse * 0.035) % len(colors)
            index = int(phase)
            fraction = phase - index
            first = colors[index]
            second = colors[(index + 1) % len(colors)]

            r = round(first.red() * (1 - fraction) + second.red() * fraction)
            g = round(first.green() * (1 - fraction) + second.green() * fraction)
            b = round(first.blue() * (1 - fraction) + second.blue() * fraction)

            self._reactor360_glow.setColor(QColor(r, g, b))
            self._reactor360_glow.setBlurRadius(
                18 + 16 * (0.5 + 0.5 * math.sin(self.pulse * 0.22))
            )
            self.lbl_logo.setStyleSheet(
                f"color:rgb({r},{g},{b});"
                "background:transparent;border:none;"
                "font-weight:900;letter-spacing:2px;"
            )

        self.shake *= 0.78

        for index in range(len(self.drops)):
            self.drops[index] += 1

            if (
                self.drops[index] * 15 > self.height()
                or random.random() > 0.997
            ):
                self.drops[index] = random.randint(-40, 0)
                self.trails[index] = random.randint(6, 24)

        rings = []

        for x, y, radius, alpha in self.shockwaves:
            radius += 10
            alpha -= 3.6

            if (
                alpha > 0
                and radius < max(self.width(), self.height()) * 1.3
            ):
                rings.append((x, y, radius, alpha))

        self.shockwaves = rings

        particles = []

        for x, y, vx, vy, life, color in self.sparks:
            x += vx
            y += vy
            vx *= 0.987
            vy = vy * 0.987 + 0.045
            life -= 1

            if life > 0:
                particles.append(
                    (x, y, vx, vy, life, color)
                )

        self.sparks = particles[-1200:]
        self.update()

    def _update_premium_logo_glow(self):
        if self.variant != "premium":
            return

        effect = getattr(self, "_premium_glow", None)
        if effect is None:
            return

        # Sanfter Farbwechsel: Cyan -> Violett -> Pink -> Cyan
        colors = (
            QColor(53, 232, 255),
            QColor(196, 107, 255),
            QColor(255, 77, 184),
        )
        phase = (self.pulse * 0.12) % 3.0
        index = int(phase)
        fraction = phase - index

        first = colors[index]
        second = colors[(index + 1) % len(colors)]

        r = round(first.red() * (1 - fraction) + second.red() * fraction)
        g = round(first.green() * (1 - fraction) + second.green() * fraction)
        b = round(first.blue() * (1 - fraction) + second.blue() * fraction)

        color = QColor(r, g, b)
        effect.setColor(color)
        effect.setBlurRadius(18 + 10 * (0.5 + 0.5 * math.sin(self.pulse * 0.18)))

        self.lbl_logo.setStyleSheet(
            f"color:rgb({r},{g},{b});background:transparent;border:none;"
            "font-weight:800;letter-spacing:5px;"
        )

    def _trigger_boot_impact(self):
        if self.is_closing:
            return

        self._spawn_burst(
            self.width() // 2,
            self.height() // 2,
            1.0,
        )

        self.flash_alpha = max(self.flash_alpha, 95)
        self.rgb_until = time.monotonic() + 0.3
        self.rgb_offset = 12
        self.shake = 8

    def _spawn_burst(self, cx, cy, intensity):
        palette = [
            QColor(0, 255, 65),
            QColor(120, 255, 180),
            QColor(0, 220, 255),
            QColor(255, 255, 255),
        ]

        for _ in range(int(100 * intensity)):
            angle = random.random() * math.tau
            speed = random.uniform(2.0, 12.0) * intensity

            self.sparks.append((
                float(cx),
                float(cy),
                math.cos(angle) * speed,
                math.sin(angle) * speed,
                random.randint(18, 42),
                random.choice(palette),
            ))

    
    def _trigger_power_surge(self, intensity=1.0):
        if self.is_closing:
            return

        intensity = max(0.25, min(2.5, float(intensity)))

        cx = self.width() // 2
        cy = self.height() // 2

        for index in range(8):
            self.shockwaves.append((
                cx,
                cy,
                index * 7 + 2,
                min(255, int(225 * intensity)),
            ))

        self._spawn_burst(cx, cy, intensity)

        self.flash_alpha = min(
            185,
            max(self.flash_alpha, int(120 * intensity)),
        )

        self.rgb_until = time.monotonic() + 0.38
        self.rgb_offset = random.randint(6, 24)
        self.shake = min(18, 7 * intensity)

        # Während der finalen Sequenz keine zusätzlichen Sounds.
        if not self._success_sequence_started:
            if not self.sounds.play("impact", 0.90, force=True):
                self.sounds.play("glitch", 0.60, force=True)

        self.update()


    def _update_scanner(self):
        if self.is_closing:
            return

        self.scanner_y = (
            self.scanner_y + 5
        ) % max(1, self.height())

        self.update()

    
    def glitch(self):
        if self.is_closing:
            return

        if random.random() < 0.18:
            self.glitch_count += 1

            self.lbl_logo.setStyleSheet(
                "color:#00FFFF;border:none;background:transparent;"
            )

            self.flash_alpha = max(self.flash_alpha, 22)
            self.rgb_until = (
                time.monotonic() + random.uniform(0.08, 0.20)
            )
            self.rgb_offset = random.randint(3, 18)

            # Zufällige Glitch-Sounds nur vor der finalen Sequenz.
            if (
                not self._success_sequence_started
                and random.random() < 0.20
            ):
                self.sounds.play("glitch", 0.28)

        else:
            self.lbl_logo.setStyleSheet(
                "color:#00FF41;border:none;background:transparent;"
            )


    def update_progress(self):
        """Kompatibilität mit älteren Aufrufen."""
        self.prog = min(100, self.prog + 1)
        self.pbar.setValue(self.prog)

    # --------------------------------------------------------
    # BOOTSTRAP UND ERGEBNISSE
    # --------------------------------------------------------

    def run_bootstrap_checks(self):
        if self.is_closing:
            return

        if self._worker is not None:
            if self._worker.isRunning():
                return

        self._bootstrap_done = False
        self._bootstrap_success = False

        self.status.setText(
            "SCANNING SYSTEM AND DEPENDENCIES ..."
        )

        self._worker = SplashBootstrapWorker(self)

        self._worker.status_changed.connect(self._on_status)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.completed.connect(
            self._on_bootstrap_complete
        )

        self._worker.start()

    def _on_status(self, message):
        if not self.is_closing:
            self.status.setText("›  " + message)
            self._append_dashboard_log(message)

    def _on_progress(self, value):
        if self.is_closing:
            return

        self.prog = max(0, min(100, int(value)))
        self.pbar.setValue(self.prog)

        if self.variant == "dashboard":
            bucket = (self.prog // 10) * 10

            if bucket != self._dashboard_last_bucket:
                self._dashboard_last_bucket = bucket
                if bucket > 0:
                    self._append_dashboard_log(
                        f"BOOT PROGRESS: {bucket}%"
                    )

            if self.prog >= 50 and not self._dashboard_impact_played:
                self._dashboard_impact_played = True
                self.sounds.play("impact", 0.55, force=True)

        elif (
            self.variant == "nebula"
            and self.prog >= 50
            and not self._nebula_impact_played
        ):
            self._nebula_impact_played = True
            self.sounds.play("impact", 0.70, force=True)

        elif (
            self.variant == "reactor360"
            and self.prog >= 50
            and not self._reactor360_impact_played
        ):
            self._reactor360_impact_played = True
            self.sounds.play("impact", 0.65, force=True)

    
    def _on_bootstrap_complete(self, success, result):
        self._bootstrap_done = True

        if self.is_closing:
            self._schedule_close_when_worker_stops()
            return

        if not success:
            if result == "Abgebrochen":
                self.finish()
                return

            self._bootstrap_success = False
            self._append_dashboard_log("BOOTSTRAP ERROR")
            self.sounds.play("error", 0.70, force=True)

            self.status.setText("BOOTSTRAP FAILED:\n" + result)
            self.status.setStyleSheet(
                "color:#FF496C;border:none;background:transparent;"
            )
            self.close_button.setText("SCHLIESSEN  ×")

            if not self._error_close_scheduled:
                self._error_close_scheduled = True
                QTimer.singleShot(5000, self.finish)

            return

        if result == "restart":
            self._restart_pending = True
            self.prog = 100
            self.pbar.setValue(100)
            self.status.setText(
                "PACKAGES INSTALLED — RESTART REQUIRED ..."
            )
            return

        self._bootstrap_success = True
        self._append_dashboard_log("SYSTEM ONLINE — FINAL SEQUENCE")
        self.prog = 100
        self.pbar.setValue(100)

        self.status.setText(
            "SYSTEM ONLINE  //  FINAL SEQUENCE PENDING"
        )
        self.status.setStyleSheet(
            "color:#9DFFB0;border:none;background:transparent;"
        )

        self._success_sequence_started = True
        self._success_sequence_finished = False

        if self.sounds.play("ready", 0.70, force=True):
            QTimer.singleShot(12000, self._play_final_glitch)
        else:
            # Audio fehlt oder konnte nicht gestartet werden.
            QTimer.singleShot(0, self._play_final_glitch)


    def _play_final_glitch(self):
        if self.is_closing:
            return

        if self.sounds.play("glitch", 0.70, force=True):
            QTimer.singleShot(
                1500,
                self._finish_final_audio_sequence,
            )
        else:
            self._finish_final_audio_sequence()


    def _finish_final_audio_sequence(self):
        if self.is_closing:
            return

        self._success_sequence_finished = True
        self._check_completion()


        
    def _check_completion(self):
        if self.is_closing:
            return

        elapsed = (
            time.monotonic() - self.started_at
        ) * 1000

        # Mindestlaufzeit von 15 Sekunden erzwingen.
        if elapsed < self.duration:
            return

        if self._restart_pending:
            self._restart_application()
            return

        # Nicht schließen, solange der Bootstrap noch läuft.
        if not self._bootstrap_done:
            return

        if self._bootstrap_success:
            # Bei Erfolg erst nach der finalen Audiosequenz schließen.
            if not self._success_sequence_finished:
                return

            self.finish()
            return

        # Bei Fehlern schließt der vorhandene Fehler-Timer.


    # --------------------------------------------------------
    # NEUSTART
    # --------------------------------------------------------

    def _restart_application(self):
        if self.is_closing:
            return

        worker = self._worker

        if worker is not None and worker.isRunning():
            QTimer.singleShot(
                100,
                self._restart_application,
            )
            return

        self.sounds.stop()

        try:
            if getattr(sys, "frozen", False):
                args = [sys.executable, *sys.argv[1:]]
            else:
                args = [sys.executable, *sys.argv]

            os.execv(sys.executable, args)

        except Exception as exc:
            self._restart_pending = False

            self.status.setText(
                f"RESTART FAILED:\n{exc}"
            )
            self.status.setStyleSheet(
                "color:#FF496C;border:none;background:transparent;"
            )

            self.close_button.setText("SCHLIESSEN  ×")
            self._bootstrap_success = False
            self._bootstrap_done = True

    # --------------------------------------------------------
    # QT-PROPERTY
    # --------------------------------------------------------

    @pyqtProperty(float)
    def corner_factor(self):
        return self._corner_factor

    @corner_factor.setter
    def corner_factor(self, value):
        self._corner_factor = float(value)
        self.update()

    # --------------------------------------------------------
    # ZEICHNEN
    # --------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Alternative Premium- und Minimal-Hintergründe.
        # Die originale Bot-Matrix bleibt davon unberührt.
        if self.variant == "nebula":
            # NEBULA OVERDRIVE - QUANTUM PORTAL
            painter.fillRect(self.rect(), QColor(2, 3, 17))

            cx = width // 2
            cy = height // 2 - 8
            base = max(55, min(width, height) // 5)
            t = self.pulse * 0.018
            pulse = 0.5 + 0.5 * math.sin(t * 2.2)

            palette = (
                QColor(145, 75, 255),
                QColor(50, 205, 255),
                QColor(255, 190, 95),
                QColor(210, 105, 255),
                QColor(95, 245, 255),
            )

            # Kosmischer Hintergrund mit Sternen
            for i in range(150):
                sx = (i * 127 + 19) % max(1, width)
                sy = (i * 71 + 13) % max(1, height)
                twinkle = 0.5 + 0.5 * math.sin(t * 3.0 + i * 1.7)
                alpha = int(35 + 170 * twinkle)
                painter.setPen(QColor(155, 195, 255, alpha))
                painter.drawPoint(sx, sy)

            # Bewegte kosmische Energiebänder
            for i, color in enumerate(palette[:3]):
                color.setAlpha(20 + int(18 * pulse))
                painter.setPen(QPen(color, max(3, base // 7)))
                offset = math.sin(t * 1.3 + i * 2.1) * 55
                painter.drawLine(
                    0, int(cy + offset + i * 35),
                    width, int(cy - offset - i * 25)
                )

            # Energetischer Außenbereich
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for i in range(10):
                radius = base + 18 + i * 12
                alpha = int(25 + 85 * (
                    0.5 + 0.5 * math.sin(t * 1.5 + i)
                ))
                color = QColor(palette[i % len(palette)])
                color.setAlpha(alpha)
                painter.setPen(QPen(color, 2))
                painter.drawEllipse(
                    QPoint(cx, cy),
                    radius,
                    int(radius * 0.58)
                )

            # Rotierende Quantum-Ringe
            ring_specs = (
                (base + 40, 0.54, 1.0),
                (base + 27, 0.82, -1.3),
                (base + 12, 0.42, 1.8),
                (base - 3, 0.73, -2.1),
                (base - 18, 0.34, 2.7),
            )

            for index, (radius, flatten, speed) in enumerate(ring_specs):
                color = palette[index % len(palette)]
                painter.save()
                painter.translate(cx, cy)
                painter.rotate(math.degrees(t * speed))

                color = QColor(color)
                color.setAlpha(175)
                painter.setPen(QPen(color, 3 if index % 2 == 0 else 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(
                    -radius, -int(radius * flatten),
                    radius * 2, int(radius * flatten * 2)
                )

                # Ring-Segmente
                for segment in range(24):
                    angle = segment * math.tau / 24
                    inner = radius - 5
                    outer = radius + (13 if segment % 3 == 0 else 5)
                    x1 = int(math.cos(angle) * inner)
                    y1 = int(math.sin(angle) * inner * flatten)
                    x2 = int(math.cos(angle) * outer)
                    y2 = int(math.sin(angle) * outer * flatten)

                    alpha = int(70 + 175 * (
                        0.5 + 0.5 * math.sin(t * 4 + segment + index)
                    ))
                    segment_color = QColor(palette[index % len(palette)])
                    segment_color.setAlpha(alpha)
                    painter.setPen(QPen(segment_color, 2))
                    painter.drawLine(x1, y1, x2, y2)

                painter.restore()

            # 36 rotierende Energie-Speichen
            for i in range(36):
                angle = t * (1.0 if i % 2 else -0.8) + i * math.tau / 36
                inner = base * 0.48
                outer = base + 58
                x1 = cx + int(math.cos(angle) * inner)
                y1 = cy + int(math.sin(angle) * inner * 0.58)
                x2 = cx + int(math.cos(angle) * outer)
                y2 = cy + int(math.sin(angle) * outer * 0.58)

                color = QColor(palette[i % len(palette)])
                color.setAlpha(int(65 + 130 * (
                    0.5 + 0.5 * math.sin(t * 3 + i)
                )))
                painter.setPen(QPen(color, 2))
                painter.drawLine(x1, y1, x2, y2)

            # Plasma-Blitze: gezackte, animierte Entladungen
            for bolt in range(9):
                angle = t * (0.65 if bolt % 2 else -0.8) + bolt * math.tau / 9
                previous = None

                for step in range(13):
                    fraction = step / 12
                    radius = base * (0.72 + fraction * 0.95)
                    jitter = math.sin(
                        t * 8 + bolt * 5.7 + step * 3.1
                    ) * (5 + fraction * 12)

                    a = angle + jitter / max(1, radius)
                    x = cx + int(math.cos(a) * radius)
                    y = cy + int(math.sin(a) * radius * 0.58)

                    if previous is not None:
                        color = QColor(palette[bolt % len(palette)])
                        color.setAlpha(int(210 - fraction * 85))
                        painter.setPen(QPen(color, 2 if step % 3 else 3))
                        painter.drawLine(previous[0], previous[1], x, y)

                    previous = (x, y)

            # Drei wandernde Shockwaves
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for wave in range(3):
                phase = (t * 0.48 + wave / 3) % 1.0
                radius = int(25 + phase * (base + 125))
                alpha = int(170 * (1.0 - phase))
                color = QColor(palette[wave])
                color.setAlpha(alpha)
                painter.setPen(QPen(color, 3 if wave == 0 else 2))
                painter.drawEllipse(
                    QPoint(cx, cy),
                    radius,
                    int(radius * 0.58)
                )

            # Schwarzes Portal mit mehrschichtigem Energierand
            painter.setPen(QPen(QColor(160, 105, 255, 240), 4))
            painter.setBrush(QColor(1, 2, 12, 250))
            painter.drawEllipse(
                QPoint(cx, cy),
                int(base * 0.66),
                int(base * 0.39)
            )

            for i in range(5):
                radius_x = int(base * (0.60 - i * 0.065))
                radius_y = int(base * (0.35 - i * 0.037))
                color = QColor(palette[i % len(palette)])
                color.setAlpha(100 + int(100 * pulse))
                painter.setPen(QPen(color, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(
                    QPoint(cx, cy), radius_x, radius_y
                )

            # 120 Partikel im spiralförmigen Sog
            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(120):
                direction = 1 if i % 2 else -1
                angle = (
                    t * (1.1 + (i % 7) * 0.09) * direction
                    + i * 2.399
                )
                phase = (i * 0.137 + t * (0.20 + (i % 5) * 0.035)) % 1.0
                distance = base * (0.52 + phase * 1.45)

                x = cx + int(math.cos(angle) * distance)
                y = cy + int(math.sin(angle) * distance * 0.58)

                color = QColor(palette[i % len(palette)])
                color.setAlpha(int(55 + 190 * (1.0 - phase)))
                painter.setBrush(color)

                size = 2 if i % 4 else 4
                painter.drawEllipse(QPoint(x, y), size, size)

            # Heller Quantum-Reaktorkern
            core_radius = int(9 + pulse * 15)

            for layer in range(7, 0, -1):
                radius = core_radius + layer * 7
                color = QColor(palette[layer % len(palette)])
                color.setAlpha(max(12, 75 - layer * 7))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(color, 4))
                painter.drawEllipse(
                    QPoint(cx, cy), radius, int(radius * 0.72)
                )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(215, 190, 255, 230))
            painter.drawEllipse(
                QPoint(cx, cy), core_radius, core_radius
            )
            painter.setBrush(QColor(100, 225, 255, 220))
            painter.drawEllipse(
                QPoint(cx, cy), max(3, core_radius // 2),
                max(3, core_radius // 2)
            )

            # Scannerlinien über dem Portal
            scan_y = int((t * 95) % max(1, height))
            painter.setPen(QPen(QColor(80, 205, 255, 55), 1))
            painter.drawLine(0, scan_y, width, scan_y)

            scan_y2 = int((t * 95 + height // 2) % max(1, height))
            painter.setPen(QPen(QColor(175, 100, 255, 35), 1))
            painter.drawLine(0, scan_y2, width, scan_y2)

            # Holografisches HUD
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(100, 205, 255, 190), 2))
            corner = 42

            for x, y, dx, dy in (
                (20, 20, 1, 1),
                (width - 20, 20, -1, 1),
                (20, height - 20, 1, -1),
                (width - 20, height - 20, -1, -1),
            ):
                painter.drawLine(x, y, x + dx * corner, y)
                painter.drawLine(x, y, x, y + dy * corner)

            # Kleine technische Messskalen
            for i in range(31):
                x = 32 + i * max(1, (width - 64) // 30)
                tick = 12 if i % 5 == 0 else 5
                painter.setPen(QPen(QColor(100, 190, 255, 125), 1))
                painter.drawLine(x, 35, x, 35 + tick)
                painter.drawLine(x, height - 35, x, height - 35 - tick)

            painter.setFont(QFont("Consolas", 9))
            painter.setPen(QColor(165, 185, 255, 220))
            painter.drawText(32, 58, "NEBULA // QUANTUM OVERDRIVE")
            painter.drawText(32, 76, "EVENT HORIZON: ACTIVE")
            painter.drawText(
                width - 220, 58,
                f"CORE POWER: {int(50 + pulse * 50):03d}%"
            )
            painter.drawText(
                width - 220, 76,
                f"PORTAL ENERGY: {self.prog:03d}%"
            )
            # Untere HUD-Texte oberhalb der Messskala platzieren.
            painter.drawText(
                30, height - 65,
                "OSC // QUANTUM SYSTEMS"
            )
            painter.drawText(
                width - 205, height - 65,
                "OVERDRIVE SEQUENCE"
            )

            painter.end()
            return

        if self.variant == "reactor360":
            # MATRIX REACTOR 360 - MULTICOLOR
            painter.fillRect(self.rect(), QColor(3, 3, 16))

            cx, cy = width // 2, height // 2
            base = max(65, min(width, height) // 5)
            rotation = self.pulse

            palette = (
                QColor(0, 229, 255),
                QColor(40, 123, 255),
                QColor(168, 85, 247),
                QColor(255, 53, 199),
                QColor(57, 255, 136),
            )

            # Dezentes futuristisches Energieraster
            grid_step = 42
            painter.setPen(QPen(QColor(50, 90, 170, 22), 1))
            for gx in range(0, width, grid_step):
                painter.drawLine(gx, 0, gx, height)
            for gy in range(0, height, grid_step):
                painter.drawLine(0, gy, width, gy)

            # Pulsierender äußerer Energiehof
            core_pulse = 0.5 + 0.5 * math.sin(self.pulse * 2.0)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            for offset, alpha in ((44, 10), (30, 17), (16, 25)):
                painter.setPen(QPen(
                    QColor(90, 80, 255, alpha), 3
                ))
                painter.drawEllipse(
                    QPoint(cx, cy),
                    base + offset,
                    int((base + offset) * 0.76),
                )

            # Fünf gegenläufige, unterschiedlich geneigte Ringe
            ring_specs = (
                (base + 34, 0.72, 0.65, 0),
                (base + 17, 0.48, -0.95, 1),
                (base, 0.82, 1.35, 2),
                (base - 17, 0.58, -1.65, 3),
                (base - 31, 0.34, 2.10, 4),
            )

            for radius, flatten, speed, color_index in ring_specs:
                color = palette[color_index]
                angle = rotation * speed

                painter.save()
                painter.translate(cx, cy)
                painter.rotate(math.degrees(angle))

                painter.setPen(QPen(
                    QColor(color.red(), color.green(), color.blue(), 150),
                    2 if color_index % 2 else 3,
                ))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(
                    -radius,
                    -int(radius * flatten),
                    radius * 2,
                    int(radius * flatten * 2),
                )

                # Leuchtende Segmentmarkierungen entlang jedes Rings
                for segment in range(12):
                    a = segment * math.tau / 12
                    inner = radius - 5
                    outer = radius + 7

                    x1 = math.cos(a) * inner
                    y1 = math.sin(a) * inner * flatten
                    x2 = math.cos(a) * outer
                    y2 = math.sin(a) * outer * flatten

                    alpha = int(
                        85 + 140 * (
                            0.5 + 0.5 * math.sin(
                                self.pulse * 1.7 + segment + color_index
                            )
                        )
                    )
                    painter.setPen(QPen(
                        QColor(
                            color.red(), color.green(),
                            color.blue(), alpha
                        ),
                        3,
                    ))
                    painter.drawLine(
                        int(x1), int(y1), int(x2), int(y2)
                    )

                painter.restore()

            # Rotierende Speichen in fünf Neonfarben
            for index in range(20):
                angle = rotation * (1.0 if index % 2 else -0.72)
                angle += index * math.tau / 20

                inner = base * 0.48
                outer = base + 38
                color = palette[index % len(palette)]

                x1 = cx + math.cos(angle) * inner
                y1 = cy + math.sin(angle) * inner * 0.76
                x2 = cx + math.cos(angle) * outer
                y2 = cy + math.sin(angle) * outer * 0.76

                alpha = int(
                    75 + 115 * (
                        0.5 + 0.5 * math.sin(self.pulse + index)
                    )
                )
                painter.setPen(QPen(
                    QColor(
                        color.red(), color.green(),
                        color.blue(), alpha
                    ),
                    2,
                ))
                painter.drawLine(
                    int(x1), int(y1), int(x2), int(y2)
                )

            # 50 umlaufende Partikel mit wechselnden Farben
            painter.setPen(Qt.PenStyle.NoPen)

            for index in range(50):
                direction = 1 if index % 2 else -1
                angle = (
                    self.pulse * (0.65 + (index % 5) * 0.13) * direction
                    + index * math.tau / 50
                )
                orbit = (
                    base + 42
                    + 10 * math.sin(self.pulse * 0.8 + index)
                )

                px = cx + math.cos(angle) * orbit
                py = cy + math.sin(angle) * orbit * 0.76

                color = palette[index % len(palette)]
                alpha = int(
                    90 + 155 * (
                        0.5 + 0.5 * math.sin(
                            self.pulse * 2.0 + index
                        )
                    )
                )
                painter.setBrush(QColor(
                    color.red(), color.green(),
                    color.blue(), alpha
                ))

                dot = 2 if index % 4 else 4
                painter.drawEllipse(
                    QPoint(int(px), int(py)), dot, dot
                )

            # Zentraler Energiekern
            core_radius = int(17 + core_pulse * 12)

            for index, color in enumerate(palette):
                glow_radius = core_radius + 23 + index * 5
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(
                    QColor(
                        color.red(), color.green(),
                        color.blue(), 35 + index * 9
                    ),
                    2,
                ))
                painter.drawEllipse(
                    QPoint(cx, cy), glow_radius, glow_radius
                )

            painter.setBrush(QColor(130, 80, 255, 55))
            painter.setPen(QPen(QColor(255, 255, 255, 230), 2))
            painter.drawEllipse(
                QPoint(cx, cy), core_radius, core_radius
            )

            painter.setBrush(QColor(255, 255, 255, 230))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPoint(cx, cy),
                max(3, core_radius // 3),
                max(3, core_radius // 3),
            )

            # Kurze RGB-Glitch-Linien bei aktiver Glitch-Phase
            if self.rgb_until > time.monotonic():
                offset = int(self.pulse * 9) % max(1, height)
                painter.fillRect(
                    0, offset, width, 2,
                    QColor(255, 53, 199, 95)
                )
                painter.fillRect(
                    0, min(height - 2, offset + 7), width, 2,
                    QColor(0, 229, 255, 85)
                )

            # Futuristischer HUD-Rahmen
            margin = 22
            length = 68
            accent = QColor(
                90, 190, 255,
                int(125 + 90 * core_pulse)
            )
            painter.setPen(QPen(accent, 2))

            corners = (
                (margin, margin, 1, 1),
                (width - margin, margin, -1, 1),
                (margin, height - margin, 1, -1),
                (width - margin, height - margin, -1, -1),
            )

            for x, y, dx, dy in corners:
                painter.drawLine(x, y, x + dx * length, y)
                painter.drawLine(x, y, x, y + dy * length)

            # Kleine farbige Statusmarkierungen
            painter.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            painter.setPen(QColor(57, 255, 136, 185))
            painter.drawText(
                margin + 5, margin + 22,
                "REACTOR 360 // ONLINE"
            )
            painter.setPen(QColor(0, 229, 255, 175))
            painter.drawText(
                width - margin - 180,
                height - margin - 8,
                "MULTICOLOR ENERGY CORE"
            )

            painter.end()
            return

        if self.variant in ("premium", "minimal"):
            if self.variant == "premium":
                # OSCAM CYBER REACTOR – animierter Premium-Hintergrund
                painter.fillRect(self.rect(), QColor(3, 8, 22))

                # Dezente digitale Lichtbahnen
                line_y = int((self.pulse * 2.4) % max(1, height))
                painter.fillRect(0, line_y, width, 2, QColor(50, 210, 255, 105))
                painter.fillRect(0, max(0, line_y - 14), width, 28,
                                 QColor(20, 130, 220, 18))

                cx, cy = width // 2, height // 2
                base = max(65, min(width, height) // 5)
                rotation = self.pulse * 2.2

                # Äußerer Reaktor-Glow
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for offset, alpha in ((30, 9), (20, 15), (10, 23)):
                    painter.setPen(QPen(QColor(0, 155, 255, alpha), 3))
                    painter.drawEllipse(
                        QPoint(cx, cy), base + offset, int((base + offset) * 0.72)
                    )

                # Drei rotierende Energieringe
                ring_specs = (
                    (base + 18, 0.40, rotation, QColor(35, 205, 255, 155), 2),
                    (base - 2, 0.29, -rotation * 1.35, QColor(100, 235, 255, 125), 2),
                    (base - 23, 0.18, rotation * 1.8, QColor(25, 145, 255, 180), 3),
                )
                for radius, flatten, angle, color, thickness in ring_specs:
                    painter.save()
                    painter.translate(cx, cy)
                    painter.rotate(angle * 57.2958)
                    pen = QPen(color, thickness)
                    painter.setPen(pen)
                    painter.drawEllipse(
                        -radius, -int(radius * flatten),
                        radius * 2, int(radius * flatten * 2)
                    )
                    painter.restore()

                # Rotierende Speichen und Energie-Segmente
                for index in range(12):
                    angle = rotation + index * (math.tau / 12)
                    inner = base * 0.58
                    outer = base + 25
                    x1 = cx + math.cos(angle) * inner
                    y1 = cy + math.sin(angle) * inner * 0.72
                    x2 = cx + math.cos(angle) * outer
                    y2 = cy + math.sin(angle) * outer * 0.72
                    alpha = int(75 + 95 * (0.5 + 0.5 * math.sin(self.pulse + index)))
                    painter.setPen(QPen(QColor(65, 220, 255, alpha), 2))
                    painter.drawLine(int(x1), int(y1), int(x2), int(y2))

                # Umlaufende leuchtende Partikel
                for index in range(32):
                    angle = self.pulse * 0.75 + index * (math.tau / 32)
                    orbit = base + 35 + 8 * math.sin(self.pulse * 0.7 + index)
                    px = cx + math.cos(angle) * orbit
                    py = cy + math.sin(angle) * orbit * 0.72
                    alpha = int(90 + 150 * (0.5 + 0.5 * math.sin(
                        self.pulse * 1.8 + index * 0.8
                    )))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(80, 225, 255, alpha))
                    dot = 2 if index % 3 else 4
                    painter.drawEllipse(QPoint(int(px), int(py)), dot, dot)

                # Heller Reaktorkern mit pulsierendem Zentrum
                core_pulse = 0.5 + 0.5 * math.sin(self.pulse * 2.0)
                core_radius = int(13 + core_pulse * 7)
                painter.setBrush(QColor(20, 145, 220, 35))
                painter.setPen(QPen(QColor(80, 225, 255, 175), 2))
                painter.drawEllipse(QPoint(cx, cy), core_radius + 13, core_radius + 13)
                painter.setBrush(QColor(50, 205, 255, 35))
                painter.setPen(QPen(QColor(180, 250, 255, 220), 2))
                painter.drawEllipse(QPoint(cx, cy), core_radius, core_radius)

                # Kleine HUD-Anzeigen
                painter.setFont(QFont("Consolas", 9))
                painter.setPen(QColor(80, 210, 245, 175))


                # Eckrahmen mit pulsierender Neon-Helligkeit
                accent = QColor(45, 200, 245, int(125 + 90 * core_pulse))
                margin = 22
                length = 65
                painter.setPen(QPen(accent, 2))
                corners = (
                    (margin, margin, 1, 1),
                    (width - margin, margin, -1, 1),
                    (margin, height - margin, 1, -1),
                    (width - margin, height - margin, -1, -1),
                )
                for x, y, dx, dy in corners:
                    painter.drawLine(x, y, x + dx * length, y)
                    painter.drawLine(x, y, x, y + dy * length)

                painter.end()
                return
            else:
                painter.fillRect(self.rect(), QColor(12, 17, 25))
                accent = QColor(135, 160, 180, 65)
                glow = QColor(100, 130, 155, 12)
                line_y = int((self.pulse * 0.8) % max(1, height))

            # Dezente horizontale Lichtfläche
            painter.fillRect(0, line_y, width, 2, accent)
            painter.fillRect(0, max(0, line_y - 12), width, 24, glow)

            # Eckrahmen
            margin = 22
            length = 65 if self.variant == "premium" else 38
            pen = QPen(accent)
            pen.setWidth(2)
            painter.setPen(pen)

            # Oben links
            painter.drawLine(margin, margin, margin + length, margin)
            painter.drawLine(margin, margin, margin, margin + length)

            # Oben rechts
            painter.drawLine(width - margin - length, margin, width - margin, margin)
            painter.drawLine(width - margin, margin, width - margin, margin + length)

            # Unten links
            painter.drawLine(margin, height - margin, margin + length, height - margin)
            painter.drawLine(margin, height - margin - length, margin, height - margin)

            # Unten rechts
            painter.drawLine(width - margin - length, height - margin, width - margin, height - margin)
            painter.drawLine(width - margin, height - margin - length, width - margin, height - margin)

            # Dezente animierte Akzentlinie
            if self.variant == "premium":
                pen = QPen(QColor(90, 220, 255, 115))
                pen.setWidth(1)
                painter.setPen(pen)
                center_y = height // 2
                painter.drawLine(width // 4, center_y + 55, width * 3 // 4, center_y + 55)

            painter.end()
            return

        # Hintergrund abdecken
        painter.fillRect(self.rect(), QColor(0, 0, 0, 248))

        band = int((self.pulse * 31) % max(1, height))
        painter.fillRect(0, band, width, 3, QColor(0, 255, 65, 30))
        painter.fillRect(0, (band + height // 3) % max(1, height), width, 2, QColor(0, 220, 255, 20))

        # Matrix-Regen
        painter.setFont(QFont("Consolas", 10))
        for index, drop in enumerate(self.drops):
            x = index * 14
            y = drop * 15
            trail = self.trails[index]

            for segment in range(trail):
                sy = y - segment * 15
                if 0 < sy < height:
                    alpha = max(8, 175 - segment * (145 // max(1, trail)))
                    if segment == 0:
                        painter.setPen(QColor(220, 255, 230, 245))
                    else:
                        painter.setPen(QColor(0, 255, 65, alpha))
                    painter.drawText(x, sy, random.choice(self.chars))

        # Schockwellen
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for rx, ry, radius, alpha in self.shockwaves:
            alpha = max(0, min(255, int(alpha)))
            painter.setPen(QPen(QColor(0, 255, 95, alpha), 2 if radius < 100 else 1))
            painter.drawEllipse(QPoint(int(rx), int(ry)), int(radius), int(radius))

        # Partikel
        painter.setPen(Qt.PenStyle.NoPen)
        for sx, sy, vx, vy, life, color in self.sparks:
            spark_color = QColor(color)
            spark_color.setAlpha(max(0, min(255, int(life * 7))))
            painter.setBrush(spark_color)
            radius = 2 if life > 12 else 1
            painter.drawEllipse(QPoint(int(sx), int(sy)), radius, radius)

        # --- ANIMIERTER RAHMEN (Exakt passend zum UI-Container ausgerichtet) ---
        # Wir holen uns die echte Geometrie des UI-Containers `self.ui`, 
        # damit die Linien garantiert an dessen Ecken und Rändern sitzen!
        ui_rect = self.ui.geometry()
        ux = ui_rect.x()
        uy = ui_rect.y()
        uw = ui_rect.width()
        uh = ui_rect.height()

        length = 46
        glow_alpha = int(165 + 75 * (0.5 + 0.5 * math.sin(self.pulse)))

        painter.setPen(QPen(QColor(0, 255, 65, glow_alpha), 3))

        # Ecken exakt auf den Rand des inneren `self.ui`-Containers legen
        corners = [
            (ux, uy, 1, 1),                           # Oben links
            (ux + uw, uy, -1, 1),                     # Oben rechts
            (ux, uy + uh, 1, -1),                     # Unten links
            (ux + uw, uy + uh, -1, -1),               # Unten rechts
        ]

        for x, y, dx, dy in corners:
            painter.drawLine(x, y, x + dx * length, y)
            painter.drawLine(x, y, x, y + dy * length)

        # RGB-Glitches
        if time.monotonic() < self.rgb_until:
            tear_y = int((self.pulse * 97) % max(1, height))
            painter.fillRect(0, tear_y, width, 4, QColor(0, 220, 255, 90))
            painter.fillRect(self.rgb_offset, (tear_y + 9) % max(1, height), max(1, width - self.rgb_offset), 3, QColor(255, 0, 90, 75))

        # Scanner
        painter.fillRect(0, self.scanner_y, width, 4, QColor(0, 255, 100, 65))

        # HUD
        painter.setFont(QFont("Consolas", 9))
        painter.setPen(QColor(0, 255, 65, 190))
        painter.drawText(28, height - 30, "SYS.MON / OSCAM CORE")
        painter.drawText(width - 235, height - 30, f"GLITCH EVENTS: {self.glitch_count:03d}")

        if self.flash_alpha > 0:
            painter.fillRect(self.rect(), QColor(0, 255, 65, self.flash_alpha))
            self.flash_alpha = max(0, self.flash_alpha - 7)

        painter.end()

    # --------------------------------------------------------
    # SCHLIESSEN UND THREAD-AUFRÄUMEN
    # --------------------------------------------------------

    def finish(self):
        if self.is_closing:
            return

        self.is_closing = True

        for name in (
            "timer",
            "timer_glitch",
            "timer_scanner",
            "completion_timer",
        ):
            timer = getattr(self, name, None)

            if timer is not None:
                timer.stop()

        animation = getattr(self, "anim", None)

        if animation is not None:
            animation.stop()

        self.close_button.setEnabled(False)
        self.sounds.stop()

        worker = self._worker

        if worker is not None and worker.isRunning():
            worker.cancel()
            self._schedule_close_when_worker_stops()
            return

        self.finished.emit()
        self.close()

    def _schedule_close_when_worker_stops(self):
        if self._close_retry_scheduled:
            return

        self._close_retry_scheduled = True

        QTimer.singleShot(
            100,
            self._close_when_worker_stops,
        )

    def _close_when_worker_stops(self):
        self._close_retry_scheduled = False

        worker = self._worker

        if worker is not None and worker.isRunning():
            self._schedule_close_when_worker_stops()
            return

        if self.is_closing:
            self.finished.emit()
            self.close()

    def closeEvent(self, event):
        worker = self._worker

        if worker is not None and worker.isRunning():
            self.is_closing = True
            worker.cancel()

            event.ignore()
            self._schedule_close_when_worker_stops()
            return

        self.sounds.stop()
        event.accept()

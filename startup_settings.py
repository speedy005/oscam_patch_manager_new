"""Startup splash settings for OSCam Control Center."""

import json
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QGroupBox

try:
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
except (ImportError, RuntimeError):
    QAudioOutput = None
    QMediaPlayer = None

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QCheckBox, QSlider, QPushButton, QHBoxLayout, QMessageBox
)

from paths import CONFIG_FILE
from config_manager import save_config


class StartupSettingsDialog(QDialog):
    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)
        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self._preview_window = None

        self.setWindowTitle(self._tr(
            "Startanimation – Einstellungen",
            "Startup animation – Settings"
        ))
        self.setMinimumWidth(520)

        self.config = {}
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self.config = loaded
        except (OSError, json.JSONDecodeError, TypeError):
            pass

        self.sound_profiles = self.config.get("splash_sound_profiles", {})
        if not isinstance(self.sound_profiles, dict):
            self.sound_profiles = {}
        self._active_profile_variant = None
        self._sound_preview_player = None
        self._sound_preview_audio = None
        if QMediaPlayer is not None and QAudioOutput is not None:
            try:
                self._sound_preview_audio = QAudioOutput(self)
                self._sound_preview_audio.setVolume(0.8)
                self._sound_preview_player = QMediaPlayer(self)
                self._sound_preview_player.setAudioOutput(
                    self._sound_preview_audio
                )
            except Exception:
                self._sound_preview_player = None
                self._sound_preview_audio = None
        self._build_ui()
        self._apply_theme()

    def _tr(self, de, en):
        return de if self.language == "de" else en

    def _config_int(self, key, default, minimum, maximum):
        try:
            return max(minimum, min(maximum, int(self.config.get(key, default))))
        except (TypeError, ValueError):
            return default

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel(self._tr(
            "STARTANIMATION KONFIGURIEREN",
            "CONFIGURE STARTUP ANIMATION"
        ))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(self._tr(
            "Wähle das Design und passe Animation und Sound an.",
            "Choose the design and customize animation and sound."
        ))
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()
        form.setSpacing(12)

        self.mode = QComboBox()
        self.mode.addItem(self._tr("Bot-Animation (Matrix)", "Bot animation (Matrix)"), "bot")
        self.mode.addItem(self._tr("Premium – Cyan Tech", "Premium – Cyan Tech"), "premium")
        self.mode.addItem(self._tr("Matrix Boot Dashboard", "Matrix Boot Dashboard"), "dashboard")
        self.mode.addItem(self._tr("Matrix Reactor 360° – Multicolor", "Matrix Reactor 360° – Multicolor"), "reactor360")
        self.mode.addItem(self._tr("NEBULA – Quantum Portal", "NEBULA – Quantum Portal"), "nebula")
        self.mode.addItem(self._tr("Minimal – schlicht", "Minimal – clean"), "minimal")
        self.mode.addItem(self._tr("Keine Startanimation", "No splash screen"), "off")

        current_mode = str(self.config.get("splash_mode", "bot")).lower()
        index = self.mode.findData(current_mode)
        self.mode.setCurrentIndex(index if index >= 0 else 0)
        form.addRow(self._tr("Startbildschirm:", "Startup screen:"), self.mode)

        self.sound = QCheckBox(self._tr(
            "Startsound und Musik abspielen",
            "Play startup sound and music"
        ))
        self.sound.setChecked(bool(self.config.get("splash_sound_enabled", True)))
        form.addRow(self._tr("Audio:", "Audio:"), self.sound)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(self._config_int("splash_volume", 65, 0, 100))
        self.volume_label = QLabel()
        self.volume.valueChanged.connect(
            lambda value: self.volume_label.setText(f"{value} %")
        )
        self.volume_label.setText(f"{self.volume.value()} %")
        volume_row = QHBoxLayout()
        volume_row.addWidget(self.volume, 1)
        volume_row.addWidget(self.volume_label)
        form.addRow(self._tr("Lautstärke:", "Volume:"), volume_row)

        self.duration = QSlider(Qt.Orientation.Horizontal)
        self.duration.setRange(5, 60)
        self.duration.setValue(
            self._config_int("splash_duration", 22000, 5000, 60000) // 1000
        )
        self.duration_label = QLabel()
        self.duration.valueChanged.connect(
            lambda value: self.duration_label.setText(f"{value} s")
        )
        self.duration_label.setText(f"{self.duration.value()} s")
        duration_row = QHBoxLayout()
        duration_row.addWidget(self.duration, 1)
        duration_row.addWidget(self.duration_label)
        form.addRow(self._tr("Mindestlaufzeit:", "Minimum duration:"), duration_row)

        self.speed = QSlider(Qt.Orientation.Horizontal)
        self.speed.setRange(50, 200)
        self.speed.setValue(self._config_int("splash_speed", 100, 50, 200))
        self.speed_label = QLabel()
        self.speed.valueChanged.connect(
            lambda value: self.speed_label.setText(f"{value} %")
        )
        self.speed_label.setText(f"{self.speed.value()} %")
        speed_row = QHBoxLayout()
        speed_row.addWidget(self.speed, 1)
        speed_row.addWidget(self.speed_label)
        form.addRow(self._tr("Animationstempo:", "Animation speed:"), speed_row)

        layout.addLayout(form)

        # Individuelle Sound-Auswahl je Splash-Variante
        sound_group = QGroupBox(self._tr(
            "SOUND-PROFIL DER AUSGEWÄHLTEN VARIANTE",
            "SOUND PROFILE FOR SELECTED VARIANT"
        ))
        sound_form = QFormLayout(sound_group)
        sound_form.setSpacing(8)

        self.sound_profile_combos = {}
        self.sound_preview_buttons = {}

        sound_dir = Path(__file__).resolve().parent / "sounds"
        supported = {
            ".wav", ".mp3", ".ogg", ".flac",
            ".m4a", ".aac", ".wma",
        }
        try:
            sound_files = sorted(
                (
                    item.name for item in sound_dir.iterdir()
                    if item.is_file() and item.suffix.lower() in supported
                ),
                key=str.lower,
            )
        except OSError:
            sound_files = []

        sound_events = (
            ("music", self._tr("Hintergrundmusik", "Background music")),
            ("startup", self._tr("Startsound", "Startup sound")),
            ("impact", self._tr("Impact / Energie", "Impact / energy")),
            ("ready", self._tr("Erfolg", "Success")),
            ("error", self._tr("Fehler", "Error")),
            ("glitch", self._tr("Glitch", "Glitch")),
        )

        for event, caption in sound_events:
            row = QHBoxLayout()
            combo = QComboBox()
            combo.addItem(self._tr("Automatisch", "Automatic"), "__auto__")
            combo.addItem(self._tr("Kein Sound", "No sound"), "__none__")
            for filename in sound_files:
                combo.addItem(filename, filename)

            preview = QPushButton(self._tr("▶", "▶"))
            preview.setToolTip(self._tr(
                "Ausgewählte Datei abspielen",
                "Play selected file"
            ))
            preview.setMaximumWidth(42)
            preview.clicked.connect(
                lambda checked=False, key=event: self._preview_sound(key)
            )

            combo.currentIndexChanged.connect(
                lambda _index, key=event: self._update_sound_preview(key)
            )
            row.addWidget(combo, 1)
            row.addWidget(preview)
            sound_form.addRow(caption + ":", row)

            self.sound_profile_combos[event] = combo
            self.sound_preview_buttons[event] = preview

        layout.addWidget(sound_group)

        note = QLabel(self._tr(
            "Der Systemcheck kann länger dauern als die eingestellte Laufzeit. "
            "Der Startbildschirm schließt erst nach Abschluss der Prüfungen.",
            "System checks may take longer than the selected duration. "
            "The splash screen closes only after the checks finish."
        ))
        note.setWordWrap(True)
        note.setStyleSheet("font-size: 11px;")
        layout.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self.preview_button = QPushButton(self._tr("Vorschau", "Preview"))
        self.preview_button.clicked.connect(self._preview)
        buttons.addWidget(self.preview_button)

        save_button = QPushButton(self._tr("Speichern", "Save"))
        save_button.clicked.connect(self._save)
        buttons.addWidget(save_button)

        close_button = QPushButton(self._tr("Schließen", "Close"))
        close_button.clicked.connect(self.close)
        buttons.addWidget(close_button)

        layout.addLayout(buttons)
        self.mode.currentIndexChanged.connect(self._update_preview_button)
        self.mode.currentIndexChanged.connect(self._on_mode_changed)
        self._active_profile_variant = self.mode.currentData()
        self._load_profile_for_mode()
        self._update_preview_button()

    def _capture_current_profile(self):
        variant = self._active_profile_variant
        if not variant or not hasattr(self, "sound_profile_combos"):
            return

        profile = {}
        for event, combo in self.sound_profile_combos.items():
            profile[event] = combo.currentData() or "__auto__"

        self.sound_profiles[variant] = profile

    def _load_profile_for_mode(self):
        variant = self.mode.currentData()
        profile = self.sound_profiles.get(variant, {})
        if not isinstance(profile, dict):
            profile = {}

        for event, combo in self.sound_profile_combos.items():
            value = profile.get(event, "__auto__")
            index = combo.findData(value)
            combo.blockSignals(True)
            combo.setCurrentIndex(index if index >= 0 else 0)
            combo.blockSignals(False)
            self._update_sound_preview(event)

    def _on_mode_changed(self, *_):
        self._capture_current_profile()
        self._active_profile_variant = self.mode.currentData()
        self._load_profile_for_mode()

    def _current_sound_profile(self):
        return {
            event: combo.currentData() or "__auto__"
            for event, combo in self.sound_profile_combos.items()
        }

    def _update_sound_preview(self, event):
        combo = self.sound_profile_combos[event]
        button = self.sound_preview_buttons[event]
        selected = combo.currentData()
        button.setEnabled(
            self._sound_preview_player is not None
            and selected not in (None, "", "__auto__", "__none__")
        )

    def _preview_sound(self, event):
        if self._sound_preview_player is None:
            return

        combo = self.sound_profile_combos[event]
        filename = combo.currentData()
        if filename in (None, "", "__auto__", "__none__"):
            return

        path = Path(__file__).resolve().parent / "sounds" / str(filename)
        if not path.is_file():
            QMessageBox.warning(
                self,
                self._tr("Datei nicht gefunden", "File not found"),
                str(path)
            )
            return

        try:
            self._sound_preview_player.stop()
            self._sound_preview_player.setSource(
                QUrl.fromLocalFile(str(path.resolve()))
            )
            self._sound_preview_player.play()
        except Exception as exc:
            QMessageBox.warning(
                self,
                self._tr("Soundvorschau fehlgeschlagen", "Sound preview failed"),
                str(exc)
            )

    def _update_preview_button(self, *_):
        self.preview_button.setEnabled(self.mode.currentData() != "off")

    def _preview(self):
        if self.mode.currentData() == "off":
            return

        if self._preview_window is not None:
            try:
                self._preview_window.close()
            except RuntimeError:
                pass
            self._preview_window = None

        try:
            from dialogs_splash import CinematicMatrixSplash

            self._preview_window = CinematicMatrixSplash(
                duration=self.duration.value() * 1000,
                sound_enabled=self.sound.isChecked(),
                sound_volume=self.volume.value(),
                variant=self.mode.currentData(),
                animation_speed=self.speed.value(),
                sound_profile=self._current_sound_profile(),
            )
            self._preview_window.finished.connect(self._preview_finished)
            self._preview_window.show()
        except Exception as exc:
            self._preview_window = None
            QMessageBox.critical(
                self,
                self._tr("Vorschau fehlgeschlagen", "Preview failed"),
                str(exc)
            )

    def _preview_finished(self):
        self._preview_window = None

    def _apply_theme(self):
        bg = self.colors.get("bg", "#1D1D1D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        window_bg = self.colors.get("window_bg", "#2F2F2F")
        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {fg}; }}
            QLabel, QCheckBox {{ color: {fg}; background: transparent; }}
            QComboBox, QPushButton {{
                color: {fg}; background: {bg};
                border: 1px solid {hover}; border-radius: 6px; padding: 6px;
            }}
            QPushButton:hover {{ color: #000000; background: {hover}; }}
            QPushButton:disabled {{ color: #777777; border-color: #555555; }}
            QSlider::groove:horizontal {{ height: 6px; background: {bg}; }}
            QSlider::handle:horizontal {{
                width: 14px; margin: -5px 0; border-radius: 7px;
                background: {hover};
            }}
        """)

    def _save(self):
        self._capture_current_profile()
        self.sound_profiles[self.mode.currentData()] = self._current_sound_profile()
        updates = {
            "splash_mode": self.mode.currentData(),
            "splash_sound_enabled": self.sound.isChecked(),
            "splash_volume": self.volume.value(),
            "splash_duration": self.duration.value() * 1000,
            "splash_speed": self.speed.value(),
            "splash_sound_profiles": self.sound_profiles,
        }
        try:
            save_config(updates, silent=True)
        except Exception as exc:
            QMessageBox.critical(
                self,
                self._tr("Speicherfehler", "Save error"),
                str(exc)
            )
            return

        QMessageBox.information(
            self,
            self._tr("Gespeichert", "Saved"),
            self._tr(
                "Die Einstellungen wurden gespeichert und gelten beim nächsten Programmstart.",
                "Settings saved. They will apply at the next program start."
            )
        )

    def closeEvent(self, event):
        if self._sound_preview_player is not None:
            try:
                self._sound_preview_player.stop()
            except Exception:
                pass
        if self._preview_window is not None:
            try:
                self._preview_window.close()
            except RuntimeError:
                pass
            self._preview_window = None
        super().closeEvent(event)

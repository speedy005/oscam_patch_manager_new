"""Musikfunktionen für PatchManagerGUI."""

import os

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox


class MusicPlayerMixin:
    def open_external_music_player(self):
        """Öffnet den separaten Player aus music_player.py."""
        try:
            from music_player import MusicPlayerWindow
            if self._music_player_window is None:
                self._music_player_window = MusicPlayerWindow(self, self)
            self._music_player_window.refresh_tracks()
            self._music_player_window.set_language()
            self._music_player_window.show()
            self._music_player_window.raise_()
            self._music_player_window.activateWindow()
        except Exception as exc:
            print(f"[MUSIC PLAYER] Player konnte nicht geöffnet werden: {exc}")
            QMessageBox.warning(
                self,
                "Music Player",
                f"Der externe Player konnte nicht geladen werden:\\n{exc}"
            )

    def _load_background_music_files(self):
        """Findet unterstützte Musikdateien im sounds-Ordner neben dem Tool."""
        from pathlib import Path

        sounds_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "sounds"
        supported = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac"}
        try:
            sounds_dir.mkdir(parents=True, exist_ok=True)
            return sorted(
                str(path) for path in sounds_dir.iterdir()
                if path.is_file() and path.suffix.lower() in supported
            )
        except OSError as exc:
            print(f"[MUSIC] sounds-Ordner kann nicht gelesen werden: {exc}")
            return []

    def _refresh_background_music_titles(self):
        """Aktualisiert Titelauswahl und Tooltips passend zur UI-Sprache."""
        combo = getattr(self, "music_title_combo", None)
        if combo is None:
            return
        from pathlib import Path
        previous_selection = combo.currentData()
        files = self._load_background_music_files()
        self._background_music_files = files
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("🔀 Zufälliger Titel" if is_de else "🔀 Random track", "__random__")
        for path in files:
            combo.addItem("🎧 " + Path(path).stem, path)
        restore_index = combo.findData(previous_selection)
        if restore_index < 0:
            saved_track = getattr(self, "_music_settings", QSettings("speedy005", "OSCamPatchManager")).value("music/track", "__random__")
            restore_index = combo.findData(saved_track)
        combo.setCurrentIndex(restore_index if restore_index >= 0 else 0)
        if hasattr(self, "_music_settings"):
            self._music_settings.setValue("music/track", combo.currentData())
        combo.setToolTip("Musiktitel auswählen" if is_de else "Choose a music track")
        combo.blockSignals(False)

    def _save_music_state(self, **updates):
        """Speichert Musik-Einstellungen dauerhaft in config.json."""
        from config_manager import load_config, save_config

        try:
            if not isinstance(getattr(self, "current_config", None), dict):
                self.current_config = load_config()

            music_cfg = self.current_config.get("music", {})
            if not isinstance(music_cfg, dict):
                music_cfg = {}

            music_cfg = dict(music_cfg)
            music_cfg.update(updates)

            return save_config(
                {"music": music_cfg},
                gui_instance=self,
                silent=True
            )
        except Exception as exc:
            print(f"[MUSIC] Einstellungen konnten nicht gespeichert werden: {exc}")
            return False

    def on_background_music_selection_changed(self, index):
        """Startet den ausgewählten Titel sofort, falls Musik bereits läuft."""
        combo = getattr(self, "music_title_combo", None)
        player = getattr(self, "_background_music_player", None)
        button = getattr(self, "music_button", None)

        if combo is not None and hasattr(self, "_music_settings"):
            self._music_settings.setValue("music/track", combo.currentData())

        # Während der Start-Wiederherstellung keinen neuen Titel starten.
        if getattr(self, "_restoring_background_music", False):
            return

        if combo is None or player is None or button is None or not button.isChecked():
            return

        self._play_random_background_track()

    def toggle_background_music(self, enabled):
        """Schaltet Hintergrundmusik ein oder aus."""
        from PyQt6.QtCore import QUrl
        from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        button = getattr(self, "music_button", None)

        settings = getattr(self, "_music_settings", QSettings("speedy005", "OSCamPatchManager"))
        settings.setValue("music/playing", bool(enabled))
        if not enabled:
            # Position vor stop() sichern.
            self._save_background_music_state()
            player = getattr(self, "_background_music_player", None)
            if player is not None:
                player.stop()
            if button is not None:
                button.setText("🎵 Musik einschalten" if is_de else "🎵 Music on")
            return

        self._refresh_background_music_titles()
        files = self._background_music_files
        if not files:
            if button is not None:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)
                button.setText("🎵 Keine Musik gefunden" if is_de else "🎵 No music found")
            QMessageBox.information(
                self,
                "Hintergrundmusik" if is_de else "Background music",
                (
                    "Lege MP3-, WAV-, OGG-, FLAC-, M4A- oder AAC-Dateien "
                    "in den Ordner 'sounds' neben der GUI-Datei."
                    if is_de else
                    "Place MP3, WAV, OGG, FLAC, M4A or AAC files "
                    "in the 'sounds' folder next to the GUI file."
                )
            )
            return

        try:
            player = getattr(self, "_background_music_player", None)
            if player is None:
                output = QAudioOutput(self)
                music_cfg = (
                    getattr(self, "current_config", {}) or {}
                ).get("music", {})

                try:
                    saved_volume = int(music_cfg.get("volume", 20))
                except (TypeError, ValueError):
                    saved_volume = 20

                output.setVolume(
                    max(0, min(100, saved_volume)) / 100.0
                )
                player = QMediaPlayer(self)
                player.setAudioOutput(output)
                player.mediaStatusChanged.connect(self._on_background_music_status)
                self._background_music_output = output
                self._background_music_player = player

            self._play_random_background_track()
            if button is not None:
                button.setText("🎵 Musik ausschalten" if is_de else "🎵 Music off")
        except Exception as exc:
            print(f"[MUSIC] Wiedergabe konnte nicht gestartet werden: {exc}")
            if button is not None:
                button.blockSignals(True)
                button.setChecked(False)
                button.blockSignals(False)
                button.setText("🎵 Musik einschalten" if is_de else "🎵 Music on")

    def _play_random_background_track(self):
        from PyQt6.QtCore import QUrl
        import random

        player = getattr(self, "_background_music_player", None)
        files = getattr(self, "_background_music_files", [])
        if player is None or not files:
            return
        combo = getattr(self, "music_title_combo", None)
        selected = combo.currentData() if combo is not None else "__random__"
        if selected and selected != "__random__" and selected in files:
            track = selected
        else:
            previous = getattr(self, "_last_background_track", None)
            choices = [path for path in files if path != previous] or files
            track = random.choice(choices)
        self._last_background_track = track
        player.setSource(QUrl.fromLocalFile(track))
        player.play()

    def _on_background_music_status(self, status):
        """Spielt den gewählten Titel erneut oder wählt einen neuen Zufallstitel."""
        from PyQt6.QtMultimedia import QMediaPlayer

        if (
            status == QMediaPlayer.MediaStatus.EndOfMedia
            and getattr(self, "music_button", None) is not None
            and self.music_button.isChecked()
        ):
            self._play_random_background_track()

    def _save_background_music_state(self):
        """Speichert Titel und Position des zentralen Musikplayers."""
        from PyQt6.QtMultimedia import QMediaPlayer

        settings = getattr(self, "_music_settings", None)
        if settings is None:
            return

        try:
            combo = getattr(self, "music_title_combo", None)
            if combo is not None:
                settings.setValue(
                    "music/track", combo.currentData() or "__random__"
                )

            player = getattr(self, "_background_music_player", None)
            if player is not None:
                track = player.source().toLocalFile()

                if track:
                    settings.setValue("music_player/resume_track", track)

                # Eine gestoppte Wiedergabe darf die letzte Position
                # nicht mit 0 überschreiben.
                if (
                    player.playbackState()
                    != QMediaPlayer.PlaybackState.StoppedState
                ):
                    settings.setValue(
                        "music_player/resume_position",
                        max(0, int(player.position()))
                    )

            button = getattr(self, "music_button", None)
            settings.setValue(
                "music/playing",
                bool(button is not None and button.isChecked())
            )
            settings.sync()

        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            print(f"[MUSIC] Speichern fehlgeschlagen: {exc}")

    def _retry_background_music_restore(self):
        """Stellt die gespeicherte Position nach dem Laden des Mediums wieder her."""
        from PyQt6.QtCore import QTimer

        if not getattr(self, "_background_music_restore_pending", False):
            return

        button = getattr(self, "music_button", None)
        player = getattr(self, "_background_music_player", None)

        if button is None or not button.isChecked() or player is None:
            self._background_music_restore_pending = False
            return

        try:
            current_track = player.source().toLocalFile()
            expected_track = self._background_music_restore_track
            duration = int(player.duration())

            if current_track == expected_track and duration > 0:
                target = min(
                    self._background_music_restore_position,
                    max(0, duration - 1000)
                )
                player.setPosition(target)
                self._background_music_restore_pending = False
                print(f"[MUSIC] Position wiederhergestellt: {target} ms")
                QTimer.singleShot(500, self._save_background_music_state)
                return

        except (AttributeError, RuntimeError, TypeError, ValueError) as exc:
            print(f"[MUSIC] Restore-Versuch fehlgeschlagen: {exc}")

        self._background_music_restore_attempts += 1

        if self._background_music_restore_attempts >= 40:
            self._background_music_restore_pending = False
            print("[MUSIC] Wiederherstellung nach 20 Sekunden abgebrochen.")
            return

        QTimer.singleShot(500, self._retry_background_music_restore)


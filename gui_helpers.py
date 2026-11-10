"""Hilfsklassen für die OSCam Patch Manager GUI."""

import math
import os
import struct
import tempfile
import wave

from PyQt6.QtCore import (
    QEvent, QObject, QThread, QTimer, QUrl, Qt, pyqtSignal
)
from PyQt6.QtWidgets import QAbstractButton
from PyQt6.QtMultimedia import QSoundEffect

class _PatchCreateBridge(QObject):
    """Thread-safe bridge for create_patch logging/progress callbacks."""
    log_message = pyqtSignal(object, str, str)
    progress_value = pyqtSignal(int)
    progress_text = pyqtSignal(str)

    def __init__(self, gui):
        super().__init__(gui)
        self._gui = gui
        # Repository-Auswahl und Commits immer aktuell aus dem GUI lesen.
        # create_patch erhält die Bridge statt des QWidget-Objekts.
        self.info_text = None
        self.progress_bar = None

    _GUI_SETTING_NAMES = frozenset((
        "EMUREPO", "selected_emu_repo_url", "selected_emu_repo_branch",
        "selected_emu_commit", "selected_emu_commit_repo_url",
        "selected_streamboard_commit", "selected_streamboard_repo_url",
    ))

    def __getattr__(self, name):
        if name in self._GUI_SETTING_NAMES:
            return getattr(self._gui, name, None)
        raise AttributeError(name)

    def __setattr__(self, name, value):
        if name in self._GUI_SETTING_NAMES:
            try:
                gui = object.__getattribute__(self, "_gui")
            except AttributeError:
                gui = None
            if gui is not None:
                setattr(gui, name, value)
                return
        super().__setattr__(name, value)

    @property
    def LANG(self):
        return getattr(self._gui, "LANG", "de")

    def append_info(self, _widget, message, level="info"):
        self.log_message.emit(None, str(message), str(level))


class _PatchCreateWorker(QThread):
    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, gui, create_patch_func):
        super().__init__(gui)
        self.gui = gui
        self.create_patch_func = create_patch_func
        self.bridge = _PatchCreateBridge(gui)
        self.bridge.log_message.connect(self._append_log)
        self.bridge.progress_value.connect(self._set_progress)
        self.bridge.progress_text.connect(self._set_progress_text)

    def _append_log(self, _unused, message, level):
        try:
            self.gui.append_info(getattr(self.gui, "info_text", None), message, level)
        except Exception:
            try:
                self.gui.info_text.append(message)
            except Exception:
                pass

    def _set_progress(self, value):
        try:
            self.gui.progress_bar.setValue(value)
        except Exception:
            pass

    def _set_progress_text(self, value):
        try:
            self.gui.progress_bar.setFormat(value)
        except Exception:
            pass

    
    
    
    def run(self):
        try:
            def progress(value=None, text=None):
                if value is not None:
                    self.bridge.progress_value.emit(
                        max(0, min(100, int(value)))
                    )
                if text is not None:
                    self.bridge.progress_text.emit(str(text))

            result = self.create_patch_func(self.bridge, None, progress)
            self.done.emit(result)

        except Exception as exc:
            import traceback
            traceback.print_exc()
            self.failed.emit(str(exc))





class ResponsiveGridReflow(QObject):
    """Reflow a grid of existing buttons whenever its container is resized."""

    def __init__(self, container, layout, min_item_width=205, parent=None):
        super().__init__(parent or container)
        self.container = container
        self.layout = layout
        self.min_item_width = min_item_width
        self._queued = False
        self._last_columns = 0
        container.installEventFilter(self)
        QTimer.singleShot(0, self.reflow)

    def eventFilter(self, obj, event):
        if obj is self.container and event.type() == QEvent.Type.Resize:
            if not self._queued:
                self._queued = True
                QTimer.singleShot(0, self._run_queued_reflow)
        return super().eventFilter(obj, event)

    def _run_queued_reflow(self):
        self._queued = False
        self.reflow()

    def reflow(self):
        if self.container is None or self.layout is None:
            return
        width = max(1, self.container.contentsRect().width())
        spacing = max(0, self.layout.spacing())
        columns = max(1, (width + spacing) // (self.min_item_width + spacing))
        widgets = []
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widgets.append(widget)
        if not widgets:
            return
        columns = min(columns, len(widgets))
        for index, widget in enumerate(widgets):
            self.layout.addWidget(widget, index // columns, index % columns)
        for col in range(max(columns, self._last_columns)):
            self.layout.setColumnStretch(col, 1 if col < columns else 0)
        self._last_columns = columns


class ButtonClickSoundFilter(QObject):
    """Spielt beim Mausklick auf einen Button den Klickton ab."""

    def __init__(self, sound_manager, parent=None):
        super().__init__(parent)
        self.sound_manager = sound_manager

    def eventFilter(self, obj, event):
        try:
            if (
                event.type() == QEvent.Type.MouseButtonPress
                and isinstance(obj, QAbstractButton)
                and obj.isEnabled()
                and self.sound_manager
                and self.sound_manager.enabled
            ):
                sound = getattr(self.sound_manager, "click_sound", None)
                if sound is not None:
                    sound.play()
        except Exception as e:
            print(f"[WARN] Button-Klicksound fehlgeschlagen: {e}")

        return super().eventFilter(obj, event)

from PyQt6.QtCore import QObject, QTimer, QUrl, Qt
from PyQt6.QtMultimedia import QSoundEffect


class SystemSoundManager(QObject):
    """Einheitlicher, dateibasierter Soundmanager für Windows und Linux.

    Alle Sounds werden als PCM-WAV erzeugt und über Qt Multimedia abgespielt.
    Dadurch hängen normale UI-Sounds nicht von Windows-Soundaliasen oder
    Linux-spezifischen OGA-Dateien/Playern ab.
    """

    def __init__(self, parent=None, volume=0.25):
        super().__init__(parent)
        self.enabled = True
        self.volume = self._clamp_volume(volume)
        self._temp_dir = tempfile.mkdtemp(prefix="oscam_sounds_")
        self._effects = {}
        self._closed = False

        # Tonfolgen: (Frequenz, Dauer in ms); None erzeugt eine kurze Pause.
        patterns = {
            "start": [(523.25, 95), (659.25, 95)],
            "success": [(659.25, 85), (783.99, 85), (1046.50, 130)],
            "revision": [(880.00, 65)],
            "exit": [(783.99, 100), (659.25, 100), (523.25, 150)],
            "click": [(1046.50, 80)],
            "info": [(740.00, 70)],
            "warning": [(660.00, 90), (520.00, 120)],
            "error": [(440.00, 130), (330.00, 180)],
            "login": [(523.25, 65), (783.99, 100)],
            "logout": [(783.99, 65), (523.25, 100)],
        }
        for name, pattern in patterns.items():
            self._effects[name] = self._create_effect(name, pattern)

        # Rückwärtskompatible Attribute, die an anderen Stellen direkt
        # verwendet werden (z. B. success_sound.play()).
        self.start_sound = self._effects["start"]
        self.success_sound = self._effects["success"]
        self.revision_sound = self._effects["revision"]
        self.exit_sound = self._effects["exit"]
        self.click_sound = self._effects["click"]

        self.revision_timer = QTimer(self)
        self.revision_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.revision_timer.setInterval(1200)
        self.revision_timer.timeout.connect(self.play_revision)

    @staticmethod
    def _clamp_volume(volume):
        try:
            return max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return 0.25

    def _write_tone(self, path, pattern):
        """Schreibt 16-bit-PCM-WAV mit kurzen Fade-ins/-outs."""
        sample_rate = 22050
        frames = bytearray()
        for frequency, duration_ms in pattern:
            count = max(1, int(sample_rate * duration_ms / 1000))
            if frequency is None:
                frames.extend(b"\x00\x00" * count)
                continue
            for i in range(count):
                fade_in = min(1.0, i / max(1, int(sample_rate * 0.008)))
                fade_out = min(1.0, (count - 1 - i) / max(1, int(sample_rate * 0.012)))
                envelope = max(0.0, min(fade_in, fade_out))
                sample = int(6500 * envelope * math.sin(2 * math.pi * frequency * i / sample_rate))
                frames.extend(struct.pack("<h", sample))
            frames.extend(b"\x00\x00" * int(sample_rate * 0.018))
        with wave.open(path, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(frames)


    def _create_effect(self, name, pattern):
        path = os.path.join(self._temp_dir, f"{name}.wav")
        self._write_tone(path, pattern)

        effect = QSoundEffect(self)
        effect.setSource(QUrl.fromLocalFile(path))

        # Klickton lauter als die übrigen UI-Sounds.
        volume = min(1.0, self.volume * 2.0) if name == "click" else self.volume
        effect.setVolume(volume)

        effect.statusChanged.connect(
            lambda e=effect, n=name: self._log_effect_status(n, e)
        )
        return effect


    @staticmethod
    def _log_effect_status(name, effect):
        # Debug-Ausgabe nur bei Ladefehlern; kein Log-Spam beim normalen Betrieb.
        try:
            if effect.status() == QSoundEffect.Status.Error:
                print(f"[SOUND] Sound '{name}' konnte nicht geladen werden.")
        except Exception:
            pass

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not self.enabled:
            self.stop_revision_blink_sound()
            for effect in self._effects.values():
                try:
                    effect.stop()
                except Exception:
                    pass

    def set_volume(self, volume):
        self.volume = self._clamp_volume(volume)
        for effect in self._effects.values():
            effect.setVolume(self.volume)

    def play(self, name):
        """Spielt einen benannten Sound; unbekannte Namen werden ignoriert."""
        if not self.enabled or self._closed:
            return False
        effect = self._effects.get(str(name).lower())
        if effect is None:
            return False
        try:
            effect.stop()
            effect.play()
            return True
        except Exception as exc:
            print(f"[SOUND] Abspielen von '{name}' fehlgeschlagen: {exc}")
            return False

    def play_start(self): return self.play("start")
    def play_success(self): return self.play("success")
    def play_revision(self): return self.play("revision")
    def play_error(self): return self.play("error")
    def play_info(self): return self.play("info")
    def play_warning(self): return self.play("warning")
    def play_login(self): return self.play("login")
    def play_logout(self): return self.play("logout")

    def play_legacy_name(self, filename):
        """Übersetzt bisherige Freedesktop-Dateinamen in portable Sounds."""
        name = os.path.basename(str(filename)).lower()
        if any(word in name for word in ("error", "failed", "failure")):
            return self.play_error()
        if "warning" in name or "exclamation" in name:
            return self.play_warning()
        if "login" in name or "service-start" in name:
            return self.play_login()
        if "logout" in name or "service-stop" in name:
            return self.play_logout()
        if "complete" in name or "success" in name:
            return self.play_success()
        if "information" in name or "asterisk" in name:
            return self.play_info()
        if "button" in name or "click" in name:
            return self.play("click")
        return self.play_info()

    def start_revision_blink_sound(self):
        # Der Ton wird beim Blink-Ereignis direkt ausgelöst, nicht per Timer.
        self.revision_timer.stop()

    def stop_revision_blink_sound(self):
        self.revision_timer.stop()

    def shutdown(self):
        if self._closed:
            return
        self._closed = True
        self.revision_timer.stop()
        for effect in self._effects.values():
            try:
                effect.stop()
            except Exception:
                pass
        try:
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass



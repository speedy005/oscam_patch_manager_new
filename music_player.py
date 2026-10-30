"""
OSCam Music Player – NEON BEAST Hi-Fi Edition.
Eigenständiges Player-Fenster für den OSCam Patch Manager.
Die Wiedergabe bleibt zentral in der Haupt-GUI.
"""
import math
import struct

from PyQt6.QtCore import Qt, QTimer, QSettings, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QRadialGradient, QLinearGradient,
    QFont
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QSizePolicy, QGridLayout
)


class SpeakerWidget(QWidget):
    """Futuristischer Lautsprecher mit physisch wirkender, beatgesteuerter Membran."""
    def __init__(self, kind="woofer", parent=None):
        super().__init__(parent)
        self.kind = kind
        self.level = 0.05
        self.phase = 0.0
        self.energy = 0.0
        self.setMinimumSize(125, 190)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_level(self, level, phase, energy=None):
        self.level = max(0.0, min(1.0, float(level)))
        self.phase = float(phase)
        self.energy = self.level if energy is None else max(0.0, min(1.0, float(energy)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = max(12, min(w * 0.43, h * 0.43))
        pulse = (0.5 + 0.5 * math.sin(self.phase)) * self.level
        bass_push = self.energy
        accent = QColor("#65ff83")

        # Gehäuse und metallischer Rahmen
        p.setPen(QPen(QColor("#1e5940"), 2))
        p.setBrush(QColor("#080d11"))
        p.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 15, 15)
        p.setPen(QPen(QColor(63, 255, 133, 45 + int(150 * self.level)), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(8, 8, w - 16, h - 16), 12, 12)

        # LED-Halo
        halo = QRadialGradient(cx, cy, r * 1.35)
        halo.setColorAt(0.0, QColor(28, 255, 111, 18 + int(50 * pulse)))
        halo.setColorAt(0.72, QColor(25, 255, 125, 8 + int(32 * pulse)))
        halo.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QRectF(cx-r*1.35, cy-r*1.35, r*2.7, r*2.7))

        # Äußere Befestigungsringe
        p.setPen(QPen(QColor("#315844"), 3))
        p.setBrush(QColor("#111b1c"))
        p.drawEllipse(QRectF(cx-r, cy-r, 2*r, 2*r))
        p.setPen(QPen(QColor(80, 255, 139, 100 + int(130*pulse)), 3 + pulse*2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx-r*.91, cy-r*.91, r*1.82, r*1.82))

        # Membran-Auslenkung: stärker bei Bassenergie
        cone_r = r * (0.70 + 0.045 * bass_push * math.sin(self.phase * 1.7))
        grad = QRadialGradient(cx-r*.2, cy-r*.25, cone_r*1.35)
        grad.setColorAt(0.0, QColor("#526d61"))
        grad.setColorAt(0.30, QColor("#263d36"))
        grad.setColorAt(0.72, QColor("#101b1b"))
        grad.setColorAt(1.0, QColor("#05090b"))
        p.setPen(QPen(QColor("#8bffad"), 1.5))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(cx-cone_r, cy-cone_r, cone_r*2, cone_r*2))

        # konzentrische Sicken
        for factor, alpha in ((0.86, 100), (0.72, 65)):
            p.setPen(QPen(QColor(113, 255, 164, alpha + int(70*pulse)), 1.4))
            p.setBrush(Qt.BrushStyle.NoBrush)
            rr = cone_r * factor
            p.drawEllipse(QRectF(cx-rr, cy-rr, 2*rr, 2*rr))

        dust_r = r * (0.23 if self.kind == "tweeter" else 0.29)
        dust = QRadialGradient(cx-dust_r*.25, cy-dust_r*.3, dust_r*1.5)
        dust.setColorAt(0, QColor("#b7ffd0"))
        dust.setColorAt(.35, QColor("#3d8c62"))
        dust.setColorAt(1, QColor("#07100d"))
        p.setPen(QPen(QColor("#9dffb8"), 1.5))
        p.setBrush(QBrush(dust))
        p.drawEllipse(QRectF(cx-dust_r, cy-dust_r, 2*dust_r, 2*dust_r))

        # Schrauben / technische Details
        p.setPen(QPen(QColor("#789487"), 1))
        for angle in (45, 135, 225, 315):
            a = math.radians(angle)
            sx, sy = cx + math.cos(a)*r*.94, cy + math.sin(a)*r*.94
            p.setBrush(QColor("#253b34"))
            p.drawEllipse(QPointF(sx, sy), 2.4, 2.4)

        # dezente Statusmarkierung
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(85, 255, 130, 80 + int(175*self.level)))
        p.drawEllipse(QRectF(cx-3, cy+r*.98, 6, 3))
        p.end()


class MusicPlayerWindow(QWidget):
    def __init__(self, host, parent=None):
        super().__init__(parent or host, Qt.WindowType.Window)
        self.host = host
        self.settings = QSettings("speedy005", "OSCamPatchManager")
        self.setWindowTitle("OSCam • NEON BEAST Hi-Fi")
        self.setMinimumSize(820, 620)
        self.resize(1080, 760)
        self._phase = 0.0
        self._audio_level = 0.0
        self._audio_peak = 0.0
        self._audio_bands = [0.04] * 24
        self._stereo_levels = [0.0, 0.0]
        self._buffer_output = None
        self._buffer_player = None
        self._buffer_signal_connected = False
        self._fft_ready = False
        self._last_samples = []
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._animate_stereo)
        self._timer.start()
        self.set_language()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background:#070b0e; color:#dcffe8;
                font-family:'Segoe UI'; font-size:10pt;
            }
            QFrame#chassis {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #111a1e, stop:.48 #080e12, stop:1 #14201b);
                border:2px solid #286b49; border-radius:20px;
            }
            QFrame#display {
                background:qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #06110e, stop:1 #030807);
                border:1px solid #39d978; border-radius:13px;
            }
            QFrame#meterPanel {
                background:#0b1514; border:1px solid #245b40; border-radius:10px;
            }
            QLabel#brand {
                color:#75ff9c; font-size:23pt; font-weight:1000;
                letter-spacing:3px;
            }
            QLabel#tagline { color:#5eae7c; font-size:8pt; font-weight:bold; letter-spacing:2px; }
            QLabel#track { color:#e5ff79; font-size:14pt; font-weight:900; }
            QLabel#readout { color:#65f99b; font-size:9pt; font-weight:bold; }
            QLabel#tiny { color:#70a889; font-size:8pt; }
            QPushButton {
                color:#caffdc; background:#13251c; border:1px solid #3ba866;
                border-radius:9px; padding:10px 14px; font-weight:900;
            }
            QPushButton:hover { background:#245b3b; border:1px solid #8dffac; }
            QPushButton#mainplay {
                color:#041009; background:#70ff91; border:1px solid #b5ffca;
                font-size:11pt; min-width:130px;
            }
            QPushButton#mainplay:hover { background:#b0ffc1; }
            QComboBox {
                color:#caffdc; background:#102018; border:1px solid #398657;
                border-radius:7px; padding:8px;
            }
            QSlider::groove:horizontal { height:7px; background:#1b3929; border-radius:3px; }
            QSlider::handle:horizontal {
                background:#7dffa0; border:1px solid #d0ffda;
                width:17px; margin:-5px 0; border-radius:8px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(15, 15, 15, 15)
        chassis = QFrame()
        chassis.setObjectName("chassis")
        layout = QVBoxLayout(chassis)
        layout.setContentsMargins(18, 16, 18, 18)
        layout.setSpacing(11)

        brand = QLabel("◈  OSCAM  NEON BEAST  ◈")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)
        tagline = QLabel("REFERENCE CLASS DIGITAL AUDIO SYSTEM  •  MK-IV")
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        deck = QHBoxLayout()
        deck.setSpacing(12)
        self.left_speaker = SpeakerWidget("woofer")
        self.right_speaker = SpeakerWidget("woofer")
        deck.addWidget(self.left_speaker, 3)

        display = QFrame()
        display.setObjectName("display")
        center = QVBoxLayout(display)
        center.setContentsMargins(14, 12, 14, 12)
        center.setSpacing(8)

        statusrow = QHBoxLayout()
        status = QLabel("● SYSTEM ONLINE")
        status.setObjectName("readout")
        self.signal_label = QLabel("DSP  /  STEREO")
        self.signal_label.setObjectName("readout")
        statusrow.addWidget(status)
        statusrow.addStretch(1)
        statusrow.addWidget(self.signal_label)
        center.addLayout(statusrow)

        self.track_label = QLabel("NEON BEAST  //  READY")
        self.track_label.setObjectName("track")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(self.track_label)

        self.track_combo = QComboBox()
        self.track_combo.currentIndexChanged.connect(self._selection_changed)
        center.addWidget(self.track_combo)

        self.eq_bars = []
        eq = QHBoxLayout()
        eq.setSpacing(3)
        for i in range(24):
            bar = QFrame()
            bar.setMinimumWidth(3)
            bar.setFixedHeight(8)
            bar.setStyleSheet("background:#24523a;border:1px solid #327b4c;border-radius:2px;")
            self.eq_bars.append(bar)
            eq.addWidget(bar, 1)
        center.addLayout(eq)

        freqrow = QHBoxLayout()
        for label in ("SUB", "BASS", "MID", "HIGH", "AIR"):
            lbl = QLabel(label)
            lbl.setObjectName("tiny")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            freqrow.addWidget(lbl)
        center.addLayout(freqrow)

        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        center.addWidget(self.progress)
        self.time_label = QLabel("00:00  /  00:00")
        self.time_label.setObjectName("tiny")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(self.time_label)

        # VU meters
        meter_panel = QFrame()
        meter_panel.setObjectName("meterPanel")
        meters = QGridLayout(meter_panel)
        meters.setContentsMargins(9, 7, 9, 7)
        meters.setHorizontalSpacing(8)
        self.vu_left = QSlider(Qt.Orientation.Horizontal)
        self.vu_right = QSlider(Qt.Orientation.Horizontal)
        for vu in (self.vu_left, self.vu_right):
            vu.setRange(0, 100)
            vu.setEnabled(False)
            vu.setValue(0)
        meters.addWidget(QLabel("L"), 0, 0)
        meters.addWidget(self.vu_left, 0, 1)
        meters.addWidget(QLabel("R"), 1, 0)
        meters.addWidget(self.vu_right, 1, 1)
        center.addWidget(meter_panel)

        deck.addWidget(display, 5)
        deck.addWidget(self.right_speaker, 3)
        layout.addLayout(deck, 1)

        controls = QHBoxLayout()
        self.prev_btn = QPushButton("◀◀  PREV")
        self.play_btn = QPushButton("▶  PLAY")
        self.play_btn.setObjectName("mainplay")
        self.stop_btn = QPushButton("■  STOP")
        self.next_btn = QPushButton("NEXT  ▶▶")
        self.prev_btn.clicked.connect(lambda: self._step_track(-1))
        self.next_btn.clicked.connect(lambda: self._step_track(1))
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)
        for b in (self.prev_btn, self.play_btn, self.stop_btn, self.next_btn):
            controls.addWidget(b)
        layout.addLayout(controls)

        volume = QHBoxLayout()
        volume.addWidget(QLabel("◖ MASTER"))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        music_cfg = (getattr(self.host, "current_config", {}) or {}).get("music", {})
        self.volume.setValue(max(0, min(100, int(music_cfg.get("volume", 20)))))
        self.volume.valueChanged.connect(self._set_volume)
        volume.addWidget(self.volume, 1)
        self.volume_label = QLabel(f"{self.volume.value()} %")
        self.volume_label.setObjectName("readout")
        volume.addWidget(self.volume_label)
        layout.addLayout(volume)

        footer = QLabel("DUAL CHANNEL DSP  •  LIVE FREQUENCY RESPONSE  •  NEON DRIVER ARRAY")
        footer.setObjectName("tagline")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)
        root.addWidget(chassis)
        self.refresh_tracks()

    def set_language(self):
        is_de = str(getattr(self.host, "LANG", "de")).lower().startswith("de")
        self.setWindowTitle("OSCam • NEON BEAST Hi-Fi")
        if not self.track_label.text() or self.track_label.text() == "NEON BEAST  //  READY":
            self.track_label.setText("BEREIT FÜR DEN NÄCHSTEN BUILD-SOUND" if is_de else "READY FOR YOUR NEXT BUILD SESSION")
        self.play_btn.setText("▶  ABSPIELEN" if is_de else "▶  PLAY")
        self.stop_btn.setText("■  STOPP" if is_de else "■  STOP")
        self.volume_label.setText(f"{self.volume.value()} %")

    def refresh_tracks(self):
        source = getattr(self.host, "music_title_combo", None)
        music_cfg = (getattr(self.host, "current_config", {}) or {}).get("music", {})
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        if source is not None:
            for i in range(source.count()):
                self.track_combo.addItem(source.itemText(i), source.itemData(i))
            wanted = str(music_cfg.get("last_track", "") or "")
            idx = self.track_combo.findData(wanted) if wanted else -1
            if idx < 0 and wanted:
                from pathlib import Path
                idx = self.track_combo.findText("🎧 " + Path(wanted).stem)
            self.track_combo.setCurrentIndex(idx if idx >= 0 else max(0, source.currentIndex()))
        self.track_combo.blockSignals(False)

    def _selection_changed(self, index):
        source = getattr(self.host, "music_title_combo", None)
        if source is not None and index >= 0:
            source.setCurrentIndex(index)
        self._sync_state()
        source = getattr(self.host, "music_title_combo", None)
        if source is not None and index >= 0 and hasattr(self.host, "_save_music_state"):
            self.host._save_music_state(last_track=str(source.currentData() or ""))

    def _player(self):
        player = getattr(self.host, "_background_music_player", None)
        self._attach_audio_analysis(player)
        return player

    def _attach_audio_analysis(self, player):
        if player is None or player is self._buffer_player:
            return
        self._buffer_player = player
        try:
            from PyQt6.QtMultimedia import QAudioBufferOutput
            if not hasattr(player, "setAudioBufferOutput"):
                return
            self._buffer_output = QAudioBufferOutput(self)
            self._buffer_output.audioBufferReceived.connect(self._on_audio_buffer)
            player.setAudioBufferOutput(self._buffer_output)
            self._buffer_signal_connected = True
        except (ImportError, AttributeError, TypeError, RuntimeError):
            self._buffer_output = None
            self._buffer_signal_connected = False

    def _on_audio_buffer(self, buffer):
        """Decode PCM, estimate stereo RMS and calculate FFT-like frequency bands."""
        try:
            fmt = buffer.format()
            raw = bytes(buffer.data())
            sample_format = fmt.sampleFormat()
            name = getattr(sample_format, "name", str(sample_format)).lower()
            if "float" in name:
                width, code, scale = 4, "f", 1.0
            elif "int16" in name or "signedint" in name:
                width, code, scale = 2, "h", 32768.0
            elif "int32" in name:
                width, code, scale = 4, "i", 2147483648.0
            elif "uint8" in name:
                width, code, scale = 1, None, 128.0
            else:
                return

            if width == 1:
                mono = [(v - 128) / 128.0 for v in raw]
            else:
                count = len(raw) // width
                unpacked = struct.unpack("<" + code * count, raw[:count * width]) if count else ()
                mono = [max(-1.0, min(1.0, v / scale)) for v in unpacked]
            if not mono:
                return

            channels = max(1, int(fmt.channelCount()))
            if channels >= 2 and len(mono) >= channels:
                left = mono[0::channels]
                right = mono[1::channels]
                def rms(seq):
                    return math.sqrt(sum(v*v for v in seq) / max(1, len(seq)))
                l_rms, r_rms = rms(left), rms(right)
                self._stereo_levels = [min(1.0, l_rms * 4.0), min(1.0, r_rms * 4.0)]
                values = [(left[i] + right[i]) * .5 for i in range(min(len(left), len(right)))]
            else:
                values = mono
                rms_value = math.sqrt(sum(v*v for v in values) / len(values))
                self._stereo_levels = [min(1.0, rms_value*4.0)] * 2

            rms_value = math.sqrt(sum(v*v for v in values) / len(values))
            self._audio_level = min(1.0, rms_value * 4.0)
            self._audio_peak = min(1.0, max(abs(v) for v in values))
            self._last_samples = values[-2048:]

            # Lightweight DFT magnitude sampling across logarithmic frequency bins.
            # Uses normalized sample positions; no external numerical dependency.
            samples = self._last_samples
            n = len(samples)
            bands = []
            if n >= 64:
                for band in range(24):
                    # Frequencies progress logarithmically from low to upper spectrum.
                    k = max(1, int(1.5 * (2 ** (band / 3.0))))
                    k = min(k, n // 2 - 1)
                    real = imag = 0.0
                    stride = max(1, n // 512)
                    for j in range(0, n, stride):
                        window = 0.5 - 0.5 * math.cos(2 * math.pi * j / max(1, n - 1))
                        angle = 2 * math.pi * k * j / n
                        sample = samples[j] * window
                        real += sample * math.cos(angle)
                        imag -= sample * math.sin(angle)
                    magnitude = math.sqrt(real*real + imag*imag) / max(1, (n // stride) * .25)
                    bands.append(max(0.025, min(1.0, magnitude * 2.5)))
                self._fft_ready = True
            else:
                bands = [max(.025, min(1.0, self._audio_level*.45))] * 24
            self._audio_bands = bands
        except (ValueError, TypeError, BufferError, struct.error, RuntimeError, ZeroDivisionError):
            pass

    def _toggle_play(self):
        button = getattr(self.host, "music_button", None)
        if button is None:
            return
        button.setChecked(not button.isChecked())
        self._sync_state()

    def _stop(self):
        player = self._player()
        if player is not None:
            player.stop()
        button = getattr(self.host, "music_button", None)
        if button is not None and button.isChecked():
            button.setChecked(False)
        self._sync_state()

    def _step_track(self, step):
        count = self.track_combo.count()
        if count <= 1:
            return
        index = self.track_combo.currentIndex()
        first = 1 if self.track_combo.itemData(0) == "__random__" else 0
        if index < first:
            index = first
        else:
            index = first + ((index - first + step) % (count - first))
        self.track_combo.setCurrentIndex(index)

    def _set_volume(self, value):
        if hasattr(self.host, "_save_music_state"):
            self.host._save_music_state(volume=int(value))
        output = getattr(self.host, "_background_music_output", None)
        if output is not None:
            output.setVolume(value / 100.0)
        self.volume_label.setText(f"{value} %")

    def _seek(self, value):
        player = self._player()
        if player is not None and player.duration() > 0:
            player.setPosition(int(player.duration() * value / 1000))

    def _sync_state(self):
        player = self._player()
        button = getattr(self.host, "music_button", None)
        playing = bool(button and button.isChecked())
        is_de = str(getattr(self.host, "LANG", "de")).lower().startswith("de")
        self.play_btn.setText(
            ("Ⅱ  PAUSE" if playing else "▶  ABSPIELEN")
            if is_de else ("Ⅱ  PAUSE" if playing else "▶  PLAY")
        )
        if player is None:
            self.progress.setValue(0)
            return
        duration = player.duration()
        position = player.position()
        if duration > 0 and not self.progress.isSliderDown():
            self.progress.setValue(int(position * 1000 / duration))
        def stamp(ms):
            seconds = max(0, int(ms / 1000))
            return f"{seconds//60:02d}:{seconds%60:02d}"
        self.time_label.setText(f"{stamp(position)}  /  {stamp(duration)}")
        current = player.source().fileName()
        if current:
            from pathlib import Path
            self.track_label.setText("♪  " + Path(current).stem)

    def _animate_stereo(self):
        self._phase += 0.22
        button = getattr(self.host, "music_button", None)
        player = getattr(self.host, "_background_music_player", None)
        playing = bool(button and button.isChecked() and player is not None)
        if playing:
            if self._buffer_signal_connected and self._audio_level > 0.003:
                bands = self._audio_bands
                sub = sum(bands[:4]) / 4
                mid = sum(bands[5:14]) / 9
                high = sum(bands[15:]) / 9
                left = max(.06, min(1.0, self._stereo_levels[0] * .75 + sub * .35))
                right = max(.06, min(1.0, self._stereo_levels[1] * .75 + sub * .35))
                self.signal_label.setText("DSP  /  LIVE FFT")
            else:
                bands = [
                    .06 + .72 * abs(math.sin(self._phase * (.32 + i*.045) + i*.61))
                    for i in range(24)
                ]
                sub = .15 + .75 * abs(math.sin(self._phase * .72))
                mid = .12 + .55 * abs(math.sin(self._phase * 1.2))
                high = .10 + .5 * abs(math.sin(self._phase * 1.8))
                left = .18 + .62 * abs(math.sin(self._phase * 1.05))
                right = .18 + .62 * abs(math.sin(self._phase * 1.05 + .8))
                self.signal_label.setText("DSP  /  VISUAL MODE")
            self.left_speaker.set_level(min(1, left*.65 + sub*.5), self._phase*1.6, sub)
            self.right_speaker.set_level(min(1, right*.65 + sub*.5), self._phase*1.6+.8, sub)
            self.vu_left.setValue(int(self._stereo_levels[0]*100))
            self.vu_right.setValue(int(self._stereo_levels[1]*100))
        else:
            bands = [0.025] * 24
            self.left_speaker.set_level(.015, self._phase, 0)
            self.right_speaker.set_level(.015, self._phase, 0)
            self.vu_left.setValue(0)
            self.vu_right.setValue(0)
            self.signal_label.setText("DSP  /  STANDBY")
            self._audio_level *= .72
            self._audio_peak *= .72

        for bar, band in zip(self.eq_bars, bands):
            value = max(0.0, min(1.0, band))
            bar.setFixedHeight(7 + int(value * 43))
            bar.setStyleSheet(
                "background:qlineargradient(x1:0,y1:1,x2:0,y2:0,"
                "stop:0 #1c7041,stop:.65 #63ff91,stop:1 #d7ff7c);"
                "border:1px solid #398b58;border-radius:2px;"
                if playing else
                "background:#173326;border:1px solid #28553b;border-radius:2px;"
            )
        self._sync_state()

    def showEvent(self, event):
        self.refresh_tracks()
        self.set_language()
        super().showEvent(event)

"""
OSCam Music Player – NEON BEAST Hi-Fi Edition.
Eigenständiges Player-Fenster für den OSCam Patch Manager.
Die Wiedergabe bleibt zentral in der Haupt-GUI.
"""

import math
import struct

from PyQt6.QtCore import Qt, QTimer, QSettings, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush,
    QRadialGradient, QLinearGradient
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSlider, QComboBox, QFrame,
    QSizePolicy, QGridLayout
)


# ============================================================
# OSCAM NEON BEAST - ULTIMATE CYBERPUNK EDITION
# ============================================================

def neon_color(hue, saturation=255, value=255, alpha=255):
    return QColor.fromHsv(int(hue) % 360, saturation, value, alpha)


def fft_real(samples):
    """Kompakte iterative Radix-2 FFT ohne externe Abhängigkeiten."""
    n = len(samples)
    if n < 2 or n & (n - 1):
        return []

    data = [complex(v, 0.0) for v in samples]

    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            data[i], data[j] = data[j], data[i]

    size = 2
    while size <= n:
        half = size // 2
        angle = -2.0 * math.pi / size
        step = complex(math.cos(angle), math.sin(angle))

        for start in range(0, n, size):
            w = 1.0 + 0.0j
            for k in range(half):
                even = data[start + k]
                odd = data[start + k + half] * w
                data[start + k] = even + odd
                data[start + k + half] = even - odd
                w *= step

        size *= 2

    return data


# ============================================================
# RGB SPEAKER
# ============================================================

class SpeakerWidget(QWidget):
    """Kompakter Cyberpunk-Lautsprecher mit animierter Membran."""

    def __init__(self, kind="woofer", parent=None):
        super().__init__(parent)
        self.kind = kind
        self.level = 0.02
        self.phase = 0.0
        self.energy = 0.0
        self.hue = 155

        self.setMinimumSize(105, 165)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    def set_level(self, level, phase, energy=None, hue=None):
        self.level = max(0.0, min(1.0, float(level)))
        self.phase = float(phase)
        self.energy = (
            self.level if energy is None
            else max(0.0, min(1.0, float(energy)))
        )
        if hue is not None:
            self.hue = int(hue) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        r = max(12, min(w * 0.42, h * 0.37))

        pulse = (0.5 + 0.5 * math.sin(self.phase)) * self.level
        accent = neon_color(self.hue)

        # Gehäuse
        p.setPen(QPen(QColor("#202a40"), 2))
        p.setBrush(QColor("#080c16"))
        p.drawRoundedRect(QRectF(3, 3, w - 6, h - 6), 15, 15)

        # RGB-Rahmen
        p.setPen(QPen(
            QColor(accent.red(), accent.green(), accent.blue(),
                   80 + int(150 * self.level)), 2
        ))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(8, 8, w - 16, h - 16), 12, 12)

        # Leuchthalo
        halo = QRadialGradient(cx, cy, r * 1.45)
        halo.setColorAt(0, QColor(
            accent.red(), accent.green(), accent.blue(),
            20 + int(55 * pulse)
        ))
        halo.setColorAt(.7, QColor(
            accent.red(), accent.green(), accent.blue(),
            8 + int(25 * pulse)
        ))
        halo.setColorAt(1, QColor(0, 0, 0, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QRectF(
            cx - r * 1.45, cy - r * 1.45,
            r * 2.9, r * 2.9
        ))

        # Außenring
        p.setPen(QPen(QColor("#34415a"), 4))
        p.setBrush(QColor("#101827"))
        p.drawEllipse(QRectF(cx-r, cy-r, 2*r, 2*r))

        p.setPen(QPen(accent, 3 + pulse * 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(
            cx-r*.91, cy-r*.91,
            r*1.82, r*1.82
        ))

        # Membran
        cone_r = r * (
            .70 + .055 * self.energy *
            math.sin(self.phase * 1.7)
        )

        grad = QRadialGradient(
            cx-r*.22, cy-r*.25, cone_r*1.4
        )
        grad.setColorAt(0, QColor("#66738c"))
        grad.setColorAt(.3, QColor("#273b55"))
        grad.setColorAt(.7, QColor("#111c31"))
        grad.setColorAt(1, QColor("#050912"))

        p.setPen(QPen(accent, 1.5))
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(
            cx-cone_r, cy-cone_r,
            cone_r*2, cone_r*2
        ))

        # Membranringe
        for factor, alpha in ((.86, 115), (.70, 75)):
            rr = cone_r * factor
            p.setPen(QPen(QColor(
                accent.red(), accent.green(),
                accent.blue(), alpha
            ), 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QRectF(
                cx-rr, cy-rr, 2*rr, 2*rr
            ))

        # Dustcap
        dust_r = r * (.24 if self.kind == "tweeter" else .29)
        dust = QRadialGradient(
            cx-dust_r*.25, cy-dust_r*.3, dust_r*1.5
        )
        dust.setColorAt(0, QColor("#ffffff"))
        dust.setColorAt(.3, accent)
        dust.setColorAt(1, QColor("#07101e"))

        p.setPen(QPen(accent, 1.5))
        p.setBrush(QBrush(dust))
        p.drawEllipse(QRectF(
            cx-dust_r, cy-dust_r,
            dust_r*2, dust_r*2
        ))

        # Schrauben
        for angle in (45, 135, 225, 315):
            a = math.radians(angle)
            sx = cx + math.cos(a) * r * .94
            sy = cy + math.sin(a) * r * .94

            p.setPen(QPen(QColor("#8290aa"), 1))
            p.setBrush(QColor("#293650"))
            p.drawEllipse(QPointF(sx, sy), 2.5, 2.5)

        p.end()


# ============================================================
# 32 BAND SPECTRUM ANALYZER
# ============================================================

class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bands = [.02] * 32
        self.hue = 155
        self.setMinimumHeight(95)
        self.setMaximumHeight(125)

    def set_bands(self, bands, hue=155):
        self.bands = [
            max(.02, min(1.0, float(v)))
            for v in bands[:32]
        ]
        self.bands += [.02] * (32 - len(self.bands))
        self.hue = hue
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        p.setPen(QPen(QColor("#1c3045"), 1))
        p.setBrush(QColor("#050a13"))
        p.drawRoundedRect(QRectF(0, 0, w, h), 8, 8)

        count = len(self.bands)
        gap = 3
        bar_width = max(2, (w - 18 - gap*(count-1)) / count)
        bottom = h - 10
        usable = h - 22

        for i, value in enumerate(self.bands):
            x = 9 + i * (bar_width + gap)
            bar_h = max(3, usable * value)

            hue = (self.hue + i * 7) % 360
            color = neon_color(hue)

            grad = QLinearGradient(
                x, bottom - bar_h, x, bottom
            )
            grad.setColorAt(0, QColor("#ffffff"))
            grad.setColorAt(.18, color.lighter(125))
            grad.setColorAt(1, color.darker(135))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(
                QRectF(x, bottom-bar_h, bar_width, bar_h),
                2, 2
            )

        p.end()


# ============================================================
# STEREO VU METER
# ============================================================

class StereoMeter(QWidget):

    def __init__(self, channel="L", parent=None):
        super().__init__(parent)
        self.channel = channel
        self.level = 0.0
        self.peak = 0.0
        self.setMinimumHeight(19)
        self.setMaximumHeight(23)

    def set_level(self, level):
        self.level = max(0.0, min(1.0, float(level)))
        self.peak = max(self.level, self.peak * .965)
        self.update()

    def reset(self):
        self.level = 0.0
        self.peak = 0.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#101827"))
        p.drawRoundedRect(QRectF(0, 2, w, h-4), 5, 5)

        segments = 36
        gap = 2
        sw = (w - 8 - (segments-1)*gap) / segments

        active = int(self.level * segments)
        peak = int(self.peak * segments)

        for i in range(segments):
            x = 4 + i*(sw+gap)
            color = (
                QColor("#ff365f") if i >= 32
                else QColor("#ffe05b") if i >= 25
                else QColor("#46ffad")
            )

            if i < active:
                p.setBrush(color)
            else:
                p.setBrush(QColor("#1b2b3c"))

            p.drawRoundedRect(
                QRectF(x, 5, sw, h-10), 1.5, 1.5
            )

        if peak > 0:
            x = 4 + min(segments-1, peak)*(sw+gap)
            p.setPen(QPen(QColor("#ffffff"), 2))
            p.drawLine(
                QPointF(x, 3), QPointF(x, h-3)
            )

        p.end()


# ============================================================
# MAIN MUSIC PLAYER
# ============================================================

class MusicPlayerWindow(QWidget):

    def __init__(self, host, parent=None):
        super().__init__(parent or host, Qt.WindowType.Window)

        self.host = host
        self.settings = QSettings(
            "speedy005", "OSCamPatchManager"
        )

        self.setWindowTitle(
            "OSCam • NEON BEAST ULTIMATE"
        )

        self.setMinimumSize(760, 570)
        self.resize(960, 680)

        self._phase = 0.0
        self._hue = 155

        self._audio_level = 0.0
        self._audio_peak = 0.0
        self._audio_bands = [.02] * 32
        self._stereo_levels = [0.0, 0.0]

        self._buffer_output = None
        self._buffer_player = None
        self._buffer_signal_connected = False
        self._fft_ready = False
        self._last_samples = []

        self.setWindowFlag(
            Qt.WindowType.WindowStaysOnTopHint, False
        )

        self._build_ui()

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._animate_stereo)
        self._timer.start()

        self.set_language()

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    def _build_ui(self):

        self.setStyleSheet("""
            QWidget {
                background:#070b14;
                color:#dceaff;
                font-family:'Segoe UI';
                font-size:9pt;
            }

            QFrame#chassis {
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 #121b30,
                    stop:.5 #080d19,
                    stop:1 #19102c
                );
                border:2px solid #563b87;
                border-radius:19px;
            }

            QFrame#display {
                background:qlineargradient(
                    x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0b1223,
                    stop:1 #040812
                );
                border:1px solid #32d9ff;
                border-radius:12px;
            }

            QFrame#meterPanel {
                background:#0c1525;
                border:1px solid #4d367b;
                border-radius:9px;
            }

            QLabel#brand {
                color:#ffffff;
                font-size:21pt;
                font-weight:1000;
                letter-spacing:3px;
            }

            QLabel#tagline {
                color:#b18aff;
                font-size:8pt;
                font-weight:bold;
                letter-spacing:2px;
            }

            QLabel#track {
                color:#50efff;
                font-size:13pt;
                font-weight:1000;
            }

            QLabel#readout {
                color:#62ffcb;
                font-size:8pt;
                font-weight:bold;
            }

            QLabel#tiny {
                color:#8c9cbd;
                font-size:8pt;
            }

            QPushButton {
                color:#dceaff;
                background:#18243b;
                border:1px solid #59448c;
                border-radius:8px;
                padding:9px 12px;
                font-weight:900;
            }

            QPushButton:hover {
                background:#34315f;
                border:1px solid #50efff;
                color:white;
            }

            QPushButton#mainplay {
                color:#050b18;
                background:#50efff;
                border:1px solid #b8fbff;
                font-size:10pt;
                min-width:120px;
            }

            QPushButton#mainplay:hover {
                background:#b3faff;
            }

            QComboBox {
                color:#e4f5ff;
                background:#101a2e;
                border:1px solid #59448c;
                border-radius:7px;
                padding:7px;
            }

            QComboBox QAbstractItemView {
                color:#ffffff;
                background:#111a2c;
                selection-background-color:#44336c;
            }

            QSlider::groove:horizontal {
                height:6px;
                background:#263450;
                border-radius:3px;
            }

            QSlider::handle:horizontal {
                background:#50efff;
                border:1px solid #ffffff;
                width:15px;
                margin:-5px 0;
                border-radius:7px;
            }

            QSlider::sub-page:horizontal {
                background:#a45cff;
                border-radius:3px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(11, 11, 11, 11)

        chassis = QFrame()
        chassis.setObjectName("chassis")

        layout = QVBoxLayout(chassis)
        layout.setContentsMargins(15, 12, 15, 13)
        layout.setSpacing(9)

        # HEADER
        brand = QLabel("◈ OSCAM NEON BEAST ◈")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        tagline = QLabel(
            "ULTIMATE CYBERPUNK AUDIO SYSTEM  •  MK-V"
        )
        tagline.setObjectName("tagline")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(tagline)

        # MAIN DECK
        deck = QHBoxLayout()
        deck.setSpacing(9)

        self.left_speaker = SpeakerWidget("woofer")
        self.right_speaker = SpeakerWidget("woofer")

        deck.addWidget(self.left_speaker, 2)

        # CENTER DISPLAY
        display = QFrame()
        display.setObjectName("display")

        center = QVBoxLayout(display)
        center.setContentsMargins(10, 9, 10, 9)
        center.setSpacing(6)

        # STATUS
        statusrow = QHBoxLayout()

        self.status_label = QLabel("● SYSTEM ONLINE")
        self.status_label.setObjectName("readout")

        self.signal_label = QLabel("DSP / STANDBY")
        self.signal_label.setObjectName("readout")

        statusrow.addWidget(self.status_label)
        statusrow.addStretch(1)
        statusrow.addWidget(self.signal_label)

        center.addLayout(statusrow)

        # TRACK
        self.track_label = QLabel(
            "NEON BEAST // READY"
        )
        self.track_label.setObjectName("track")
        self.track_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.track_label.setWordWrap(True)
        center.addWidget(self.track_label)

        self.track_combo = QComboBox()
        self.track_combo.currentIndexChanged.connect(
            self._selection_changed
        )
        center.addWidget(self.track_combo)

        # SPECTRUM
        spectrum_title = QLabel(
            "REALTIME FREQUENCY ANALYZER  /  32 BAND"
        )
        spectrum_title.setObjectName("tiny")
        spectrum_title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        center.addWidget(spectrum_title)

        self.spectrum = SpectrumWidget()
        center.addWidget(self.spectrum)

        freqrow = QHBoxLayout()

        for label in (
            "SUB", "BASS", "LOW MID",
            "MID", "HIGH", "AIR"
        ):
            lbl = QLabel(label)
            lbl.setObjectName("tiny")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            freqrow.addWidget(lbl)

        center.addLayout(freqrow)

        # PROGRESS
        self.progress = QSlider(
            Qt.Orientation.Horizontal
        )
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        center.addWidget(self.progress)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("tiny")
        self.time_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        center.addWidget(self.time_label)

        # VU PANEL
        meter_panel = QFrame()
        meter_panel.setObjectName("meterPanel")

        meters = QGridLayout(meter_panel)
        meters.setContentsMargins(8, 6, 8, 6)
        meters.setHorizontalSpacing(8)
        meters.setVerticalSpacing(3)

        self.vu_left = StereoMeter("L")
        self.vu_right = StereoMeter("R")

        lbl_l = QLabel("L")
        lbl_r = QLabel("R")
        lbl_l.setObjectName("readout")
        lbl_r.setObjectName("readout")

        meters.addWidget(lbl_l, 0, 0)
        meters.addWidget(self.vu_left, 0, 1)
        meters.addWidget(lbl_r, 1, 0)
        meters.addWidget(self.vu_right, 1, 1)

        center.addWidget(meter_panel)

        deck.addWidget(display, 5)
        deck.addWidget(self.right_speaker, 2)

        layout.addLayout(deck, 1)

        # PLAYBACK CONTROLS
        controls = QHBoxLayout()
        controls.setSpacing(7)

        self.prev_btn = QPushButton("◀◀")
        self.play_btn = QPushButton("▶ PLAY")
        self.play_btn.setObjectName("mainplay")
        self.stop_btn = QPushButton("■ STOP")
        self.next_btn = QPushButton("▶▶")

        self.prev_btn.setToolTip("Previous track")
        self.next_btn.setToolTip("Next track")
        self.play_btn.setToolTip("Play / Pause")
        self.stop_btn.setToolTip("Stop")

        self.prev_btn.clicked.connect(
            lambda: self._step_track(-1)
        )
        self.next_btn.clicked.connect(
            lambda: self._step_track(1)
        )
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)

        for button in (
            self.prev_btn, self.play_btn,
            self.stop_btn, self.next_btn
        ):
            controls.addWidget(button)

        layout.addLayout(controls)

        # MASTER VOLUME
        volume = QHBoxLayout()

        master = QLabel("◖ MASTER")
        master.setObjectName("readout")
        volume.addWidget(master)

        self.volume = QSlider(
            Qt.Orientation.Horizontal
        )
        self.volume.setRange(0, 100)

        music_cfg = (
            getattr(self.host, "current_config", {}) or {}
        ).get("music", {})

        try:
            initial_volume = int(music_cfg.get("volume", 20))
        except (TypeError, ValueError):
            initial_volume = 20

        self.volume.setValue(
            max(0, min(100, initial_volume))
        )

        self.volume.valueChanged.connect(self._set_volume)
        volume.addWidget(self.volume, 1)

        self.volume_label = QLabel(
            f"{self.volume.value()} %"
        )
        self.volume_label.setObjectName("readout")
        volume.addWidget(self.volume_label)

        layout.addLayout(volume)

        # FOOTER
        footer = QLabel(
            "RGB NEON ENGINE  •  LIVE DSP  •  STEREO DRIVER ARRAY"
        )
        footer.setObjectName("tagline")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(footer)
        root.addWidget(chassis)

        self.refresh_tracks()

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    def set_language(self):
        is_de = str(
            getattr(self.host, "LANG", "de")
        ).lower().startswith("de")

        self.setWindowTitle(
            "OSCam • NEON BEAST ULTIMATE"
        )

        self.play_btn.setText(
            "▶ ABSPIELEN" if is_de else "▶ PLAY"
        )
        self.stop_btn.setText(
            "■ STOPP" if is_de else "■ STOP"
        )

        self.volume_label.setText(
            f"{self.volume.value()} %"
        )

        if self.track_combo.count() == 0:
            self.track_label.setText(
                "BEREIT FÜR DEN NÄCHSTEN BUILD-SOUND"
                if is_de else
                "READY FOR YOUR NEXT BUILD SESSION"
            )

    # --------------------------------------------------------
    # TRACK MANAGEMENT
    # --------------------------------------------------------

    def refresh_tracks(self):
        source = getattr(
            self.host, "music_title_combo", None
        )

        music_cfg = (
            getattr(self.host, "current_config", {}) or {}
        ).get("music", {})

        self.track_combo.blockSignals(True)
        self.track_combo.clear()

        if source is not None:
            for i in range(source.count()):
                self.track_combo.addItem(
                    source.itemText(i),
                    source.itemData(i)
                )

            wanted = str(
                music_cfg.get("last_track", "") or ""
            )

            idx = (
                self.track_combo.findData(wanted)
                if wanted else -1
            )

            if idx < 0 and wanted:
                from pathlib import Path
                idx = self.track_combo.findText(
                    "🎧 " + Path(wanted).stem
                )

            if idx < 0:
                idx = max(0, source.currentIndex())

            if self.track_combo.count():
                self.track_combo.setCurrentIndex(idx)

        self.track_combo.blockSignals(False)

    def _selection_changed(self, index):
        source = getattr(
            self.host, "music_title_combo", None
        )

        if source is not None and index >= 0:
            source.setCurrentIndex(index)

        self._sync_state()

        if (
            source is not None
            and index >= 0
            and hasattr(self.host, "_save_music_state")
        ):
            self.host._save_music_state(
                last_track=str(source.currentData() or "")
            )

    def _step_track(self, step):
        count = self.track_combo.count()

        if count <= 1:
            return

        index = self.track_combo.currentIndex()

        first = (
            1 if self.track_combo.itemData(0) == "__random__"
            else 0
        )

        if index < first:
            index = first
        else:
            index = first + (
                (index - first + step) % (count - first)
            )

        self.track_combo.setCurrentIndex(index)

    # --------------------------------------------------------
    # HOST AUDIO CONNECTION
    # --------------------------------------------------------

    def _player(self):
        player = getattr(
            self.host, "_background_music_player", None
        )
        self._attach_audio_analysis(player)
        return player

    def _attach_audio_analysis(self, player):
        if player is None or player is self._buffer_player:
            return

        self._buffer_player = player
        self._buffer_output = None
        self._buffer_signal_connected = False

        try:
            from PyQt6.QtMultimedia import QAudioBufferOutput

            if not hasattr(player, "setAudioBufferOutput"):
                return

            self._buffer_output = QAudioBufferOutput(self)

            self._buffer_output.audioBufferReceived.connect(
                self._on_audio_buffer
            )

            player.setAudioBufferOutput(self._buffer_output)
            self._buffer_signal_connected = True

        except (
            ImportError, AttributeError,
            TypeError, RuntimeError
        ):
            self._buffer_output = None
            self._buffer_signal_connected = False

    # --------------------------------------------------------
    # LIVE AUDIO ANALYSIS
    # --------------------------------------------------------

    def _on_audio_buffer(self, buffer):
        """PCM-Decoding, Stereo-RMS und logarithmische FFT."""

        try:
            fmt = buffer.format()
            raw = bytes(buffer.data())

            sample_format = fmt.sampleFormat()
            name = getattr(
                sample_format, "name", str(sample_format)
            ).lower()

            if "float" in name:
                width, code, scale = 4, "f", 1.0
            elif "int16" in name or "signedint16" in name:
                width, code, scale = 2, "h", 32768.0
            elif "int32" in name or "signedint32" in name:
                width, code, scale = 4, "i", 2147483648.0
            elif "uint8" in name:
                width, code, scale = 1, None, 128.0
            else:
                return

            if width == 1:
                mono = [
                    (v - 128) / 128.0
                    for v in raw
                ]
            else:
                count = len(raw) // width
                if count == 0:
                    return

                byte_order = fmt.byteOrder()
                endian = (
                    "<" if byte_order == fmt.Endian.LittleEndian
                    else ">"
                )

                unpacked = struct.unpack(
                    endian + code * count,
                    raw[:count * width]
                )

                mono = [
                    max(-1.0, min(1.0, v / scale))
                    for v in unpacked
                ]

            if not mono:
                return

            channels = max(1, int(fmt.channelCount()))

            if channels >= 2 and len(mono) >= channels:
                left = mono[0::channels]
                right = mono[1::channels]

                def rms(seq):
                    return math.sqrt(
                        sum(v*v for v in seq) /
                        max(1, len(seq))
                    )

                l_rms = rms(left)
                r_rms = rms(right)

                self._stereo_levels = [
                    min(1.0, l_rms * 3.5),
                    min(1.0, r_rms * 3.5)
                ]

                length = min(len(left), len(right))

                values = [
                    (left[i] + right[i]) * .5
                    for i in range(length)
                ]

            else:
                values = mono
                rms_value = math.sqrt(
                    sum(v*v for v in values) /
                    max(1, len(values))
                )

                self._stereo_levels = [
                    min(1.0, rms_value * 3.5)
                ] * 2

            if not values:
                return

            rms_value = math.sqrt(
                sum(v*v for v in values) / len(values)
            )

            self._audio_level = min(1.0, rms_value * 3.5)
            self._audio_peak = min(
                1.0, max(abs(v) for v in values)
            )

            self._last_samples = values[-512:]

            # FFT benötigt eine Zweierpotenz.
            available = len(self._last_samples)

            if available >= 64:
                n = 1 << (
                    min(available, 512).bit_length() - 1
                )

                samples = self._last_samples[-n:]

                # Hann-Fenster
                windowed = [
                    samples[i] * (
                        .5 - .5 * math.cos(
                            2 * math.pi * i / max(1, n - 1)
                        )
                    )
                    for i in range(n)
                ]

                spectrum = fft_real(windowed)

                if not spectrum:
                    return

                # 32 logarithmische Frequenzbänder
                bands = []

                for band in range(32):
                    low = max(
                        1, int(2 ** (band * 8 / 32))
                    )
                    high = max(
                        low + 1,
                        int(2 ** ((band + 1) * 8 / 32))
                    )

                    high = min(high, n // 2)

                    if high <= low:
                        high = min(n // 2, low + 1)

                    magnitudes = [
                        abs(spectrum[k]) / max(1, n / 2)
                        for k in range(low, high)
                    ]

                    energy = (
                        math.sqrt(
                            sum(v*v for v in magnitudes) /
                            len(magnitudes)
                        )
                        if magnitudes else 0.0
                    )

                    bands.append(
                        max(.02, min(1.0, energy * 3.2))
                    )

                self._audio_bands = bands
                self._fft_ready = True

        except (
            ValueError, TypeError, BufferError,
            struct.error, RuntimeError, ZeroDivisionError
        ):
            return

    # --------------------------------------------------------
    # PLAYBACK
    # --------------------------------------------------------

    def _toggle_play(self):
        button = getattr(
            self.host, "music_button", None
        )

        if button is None:
            return

        button.setChecked(not button.isChecked())
        self._sync_state()

    def _stop(self):
        player = self._player()

        if player is not None:
            player.stop()

        button = getattr(
            self.host, "music_button", None
        )

        if button is not None and button.isChecked():
            button.setChecked(False)

        self._sync_state()

    def _set_volume(self, value):
        if hasattr(self.host, "_save_music_state"):
            self.host._save_music_state(
                volume=int(value)
            )

        output = getattr(
            self.host, "_background_music_output", None
        )

        if output is not None:
            output.setVolume(value / 100.0)

        self.volume_label.setText(f"{value} %")

    def _seek(self, value):
        player = self._player()

        if player is not None and player.duration() > 0:
            player.setPosition(
                int(player.duration() * value / 1000)
            )

    # --------------------------------------------------------
    # PLAYER STATE
    # --------------------------------------------------------

    def _sync_state(self):
        player = self._player()

        button = getattr(
            self.host, "music_button", None
        )

        playing = bool(
            button and button.isChecked()
        )

        is_de = str(
            getattr(self.host, "LANG", "de")
        ).lower().startswith("de")

        self.play_btn.setText(
            (
                "Ⅱ PAUSE" if playing else "▶ ABSPIELEN"
            ) if is_de else (
                "Ⅱ PAUSE" if playing else "▶ PLAY"
            )
        )

        if player is None:
            self.progress.setValue(0)
            self.time_label.setText("00:00 / 00:00")
            return

        duration = player.duration()
        position = player.position()

        if duration > 0 and not self.progress.isSliderDown():
            self.progress.setValue(
                int(position * 1000 / duration)
            )

        def stamp(ms):
            seconds = max(0, int(ms / 1000))
            return (
                f"{seconds // 60:02d}:"
                f"{seconds % 60:02d}"
            )

        self.time_label.setText(
            f"{stamp(position)} / {stamp(duration)}"
        )

        try:
            current = player.source().fileName()

            if current:
                from pathlib import Path
                self.track_label.setText(
                    "♪  " + Path(current).stem
                )

        except (AttributeError, TypeError, RuntimeError):
            pass

    # --------------------------------------------------------
    # RGB ANIMATION ENGINE
    # --------------------------------------------------------

    def _animate_stereo(self):
        self._phase += .22
        self._hue = (self._hue + 1.5) % 360

        button = getattr(
            self.host, "music_button", None
        )

        player = getattr(
            self.host, "_background_music_player", None
        )

        playing = bool(
            button and button.isChecked() and player is not None
        )

        if playing:
            if (
                self._buffer_signal_connected
                and self._fft_ready
                and self._audio_level > .001
            ):
                bands = self._audio_bands

                sub = sum(bands[:4]) / 4
                bass = sum(bands[4:9]) / 5
                mid = sum(bands[9:21]) / 12
                high = sum(bands[21:]) / 11

                left = max(
                    .05,
                    min(1.0, self._stereo_levels[0])
                )

                right = max(
                    .05,
                    min(1.0, self._stereo_levels[1])
                )

                self.signal_label.setText(
                    "DSP / LIVE FFT"
                )

            else:
                # Visueller Fallback, wenn Audioanalyse fehlt.
                bands = [
                    .05 + .85 * abs(
                        math.sin(
                            self._phase * (.35 + i*.047)
                            + i*.63
                        )
                    )
                    for i in range(32)
                ]

                sub = .15 + .75 * abs(
                    math.sin(self._phase * .72)
                )

                bass = .15 + .7 * abs(
                    math.sin(self._phase * .91)
                )

                mid = .12 + .55 * abs(
                    math.sin(self._phase * 1.2)
                )

                high = .1 + .5 * abs(
                    math.sin(self._phase * 1.8)
                )

                left = .18 + .62 * abs(
                    math.sin(self._phase * 1.05)
                )

                right = .18 + .62 * abs(
                    math.sin(self._phase * 1.05 + .8)
                )

                self.signal_label.setText(
                    "DSP / VISUAL MODE"
                )

            left_push = min(
                1.0, left*.7 + sub*.4 + bass*.2
            )

            right_push = min(
                1.0, right*.7 + sub*.4 + bass*.2
            )

            self.left_speaker.set_level(
                left_push,
                self._phase * 1.6,
                sub,
                self._hue
            )

            self.right_speaker.set_level(
                right_push,
                self._phase * 1.6 + .8,
                sub,
                self._hue + 35
            )

            self.vu_left.set_level(
                self._stereo_levels[0]
            )

            self.vu_right.set_level(
                self._stereo_levels[1]
            )

            self.spectrum.set_bands(
                bands, self._hue
            )

            self.status_label.setText(
                "● AUDIO STREAM ACTIVE"
            )

        else:
            bands = [.02] * 32

            self.left_speaker.set_level(
                .015, self._phase, 0, self._hue
            )

            self.right_speaker.set_level(
                .015, self._phase, 0, self._hue + 35
            )

            self.vu_left.reset()
            self.vu_right.reset()

            self.spectrum.set_bands(
                bands, self._hue
            )

            self.signal_label.setText(
                "DSP / STANDBY"
            )

            self.status_label.setText(
                "● SYSTEM ONLINE"
            )

            self._audio_level *= .72
            self._audio_peak *= .72

            self._stereo_levels = [
                v * .72 for v in self._stereo_levels
            ]

            self._audio_bands = [
                max(.02, v*.85)
                for v in self._audio_bands
            ]

        self._sync_state()

    # --------------------------------------------------------
    # WINDOW EVENTS
    # --------------------------------------------------------

    def showEvent(self, event):
        self.refresh_tracks()
        self.set_language()
        super().showEvent(event)

    def closeEvent(self, event):
        # Nur das Fenster schließen.
        # Die zentrale Host-Wiedergabe läuft weiter.
        self._timer.stop()
        super().closeEvent(event)


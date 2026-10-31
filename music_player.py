
"""
OSCam Music Player – NEON BEAST ULTIMATE
10 Neon Themes | RGB Speakers | 32-Band FFT | Stereo VU

- Zentrale Farbverwaltung
- 10 umschaltbare Neon-Themes
- Theme-Auswahl wird gespeichert
- Fenstergröße und Position werden gespeichert
- Neon LEFT / RIGHT Lautsprecher
- 32-Band FFT Spectrum
- Stereo VU Meter
- Master Volume
- Zentrale OSCam-Wiedergabe
- Keine separate QMediaPlayer-Instanz
"""

import math
import struct

from pathlib import Path

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
# ZENTRALE FARBVERWALTUNG
# ============================================================
#
# ACTIVE_THEME:
#   Bestimmt das Standard-Theme beim ersten Start.
#
# Alle Farben können in COLOR_THEMES geändert werden.
# Eine gespeicherte Theme-Auswahl hat Vorrang.
# ============================================================

ACTIVE_THEME = "fire_ice"


COLOR_THEMES = {

    "cyberpunk": {
        "name": "Cyberpunk Purple / Cyan",
        "background": "#070914",
        "panel": "#121a31",
        "panel_dark": "#080e1b",
        "panel_light": "#1a1030",
        "display": "#111b32",
        "border": "#51418d",
        "border_glow": "#00dcff",
        "text": "#e5f4ff",
        "muted": "#8091b2",
        "brand": "#ff1744",
        "tagline": "#ffff00",
        "status": "#43ffba",
        "section": "#45eaff",
        "track": "#55dfff",
        "readout": "#57ffcc",
        "left": "#00eaff",
        "right": "#ff00cc",
        "volume": "#55edff",
        "slider_track": "#25314b",
        "slider_fill": "#00dfff",
        "slider_fill_end": "#a05cff",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#00dcff",
        "button": "#18233c",
        "button_border": "#59488c",
        "button_hover": "#34335d",
        "button_hover_border": "#50eaff",
        "play_start": "#6fffff",
        "play_middle": "#00c8ff",
        "play_end": "#a27aff",
        "stop": "#ff5799",
        "spectrum_background": "#050a14",
        "spectrum_grid": "#17283b",
        "vu_background": "#101b2b",
        "vu_inactive": "#1b2a3e",
        "vu_low": "#39ffae",
        "vu_mid": "#ffe15c",
        "vu_high": "#ff3e73",
        "speaker_housing": "#090e1b",
        "speaker_border": "#28344d",
        "speaker_metal": "#45526e",
        "speaker_cone_1": "#75849f",
        "speaker_cone_2": "#344967",
        "speaker_cone_3": "#17253d",
        "speaker_cone_4": "#050a13",
    },

    "neon_blue": {
        "name": "Electric Blue",
        "background": "#050b18",
        "panel": "#0c1b32",
        "panel_dark": "#071326",
        "panel_light": "#102747",
        "display": "#0b1c35",
        "border": "#1764a5",
        "border_glow": "#00aaff",
        "text": "#e5f5ff",
        "muted": "#789bbd",
        "brand": "#00aaff",
        "tagline": "#7df9ff",
        "status": "#00ffcc",
        "section": "#00cfff",
        "track": "#62dcff",
        "readout": "#00ffdf",
        "left": "#00eaff",
        "right": "#4169ff",
        "volume": "#00eaff",
        "slider_track": "#183451",
        "slider_fill": "#00aaff",
        "slider_fill_end": "#4169ff",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#00cfff",
        "button": "#102b49",
        "button_border": "#1764a5",
        "button_hover": "#174a70",
        "button_hover_border": "#00dfff",
        "play_start": "#8affff",
        "play_middle": "#00aaff",
        "play_end": "#4169ff",
        "stop": "#ff5577",
        "spectrum_background": "#030b17",
        "spectrum_grid": "#12304b",
        "vu_background": "#0a1b2b",
        "vu_inactive": "#183451",
        "vu_low": "#00ffbb",
        "vu_mid": "#ffe15c",
        "vu_high": "#ff4466",
        "speaker_housing": "#071326",
        "speaker_border": "#17446b",
        "speaker_metal": "#41658a",
        "speaker_cone_1": "#91c9ed",
        "speaker_cone_2": "#315b80",
        "speaker_cone_3": "#163550",
        "speaker_cone_4": "#061426",
    },

    "matrix": {
        "name": "Matrix Green",
        "background": "#020b06",
        "panel": "#071b10",
        "panel_dark": "#031108",
        "panel_light": "#0d2818",
        "display": "#061b0e",
        "border": "#176b35",
        "border_glow": "#00ff66",
        "text": "#d8ffe5",
        "muted": "#75a98a",
        "brand": "#00ff66",
        "tagline": "#aaff00",
        "status": "#00ff99",
        "section": "#00ff66",
        "track": "#8affb0",
        "readout": "#00ff99",
        "left": "#00ff66",
        "right": "#aaff00",
        "volume": "#00ff66",
        "slider_track": "#183b25",
        "slider_fill": "#00ff66",
        "slider_fill_end": "#aaff00",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#00ff66",
        "button": "#102b19",
        "button_border": "#267b43",
        "button_hover": "#17482a",
        "button_hover_border": "#00ff66",
        "play_start": "#aaffbb",
        "play_middle": "#00ff66",
        "play_end": "#aaff00",
        "stop": "#ff5544",
        "spectrum_background": "#020d07",
        "spectrum_grid": "#123820",
        "vu_background": "#061b0e",
        "vu_inactive": "#183b25",
        "vu_low": "#00ff66",
        "vu_mid": "#cfff00",
        "vu_high": "#ff4444",
        "speaker_housing": "#031108",
        "speaker_border": "#176b35",
        "speaker_metal": "#39734b",
        "speaker_cone_1": "#9bc9a8",
        "speaker_cone_2": "#315d3c",
        "speaker_cone_3": "#16351e",
        "speaker_cone_4": "#041008",
    },

    "synthwave": {
        "name": "Synthwave Pink / Purple",
        "background": "#10051c",
        "panel": "#21102e",
        "panel_dark": "#12091d",
        "panel_light": "#30113b",
        "display": "#1d0d2d",
        "border": "#8738a8",
        "border_glow": "#ff35d3",
        "text": "#fff0ff",
        "muted": "#b18bbd",
        "brand": "#ff35d3",
        "tagline": "#ffb8f4",
        "status": "#8dffdb",
        "section": "#ff65e8",
        "track": "#ff9cf0",
        "readout": "#b8fff1",
        "left": "#00eaff",
        "right": "#ff35d3",
        "volume": "#ff65e8",
        "slider_track": "#43204e",
        "slider_fill": "#ff35d3",
        "slider_fill_end": "#7b3cff",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#ff35d3",
        "button": "#321640",
        "button_border": "#8738a8",
        "button_hover": "#57246b",
        "button_hover_border": "#ff65e8",
        "play_start": "#ffb8f4",
        "play_middle": "#ff35d3",
        "play_end": "#7b3cff",
        "stop": "#ff5577",
        "spectrum_background": "#10051c",
        "spectrum_grid": "#462052",
        "vu_background": "#1d0d2d",
        "vu_inactive": "#43204e",
        "vu_low": "#55ffbb",
        "vu_mid": "#ffe15c",
        "vu_high": "#ff3e73",
        "speaker_housing": "#12091d",
        "speaker_border": "#8738a8",
        "speaker_metal": "#80518f",
        "speaker_cone_1": "#d7a5e8",
        "speaker_cone_2": "#704080",
        "speaker_cone_3": "#351940",
        "speaker_cone_4": "#10051c",
    },

    "fire_ice": {
        "name": "Fire & Ice",
        "background": "#0a0d18",
        "panel": "#171d2c",
        "panel_dark": "#0b1220",
        "panel_light": "#2b1720",
        "display": "#111c2b",
        "border": "#a64b55",
        "border_glow": "#ff6633",
        "text": "#fff1e8",
        "muted": "#a7a9bd",
        "brand": "#ff6633",
        "tagline": "#ffd166",
        "status": "#8dffcf",
        "section": "#ff9966",
        "track": "#ffc08a",
        "readout": "#8dffcf",
        "left": "#00d9ff",
        "right": "#ff6633",
        "volume": "#ff9966",
        "slider_track": "#29334a",
        "slider_fill": "#00d9ff",
        "slider_fill_end": "#ff6633",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#00d9ff",
        "button": "#202b40",
        "button_border": "#8a5365",
        "button_hover": "#493047",
        "button_hover_border": "#ff9966",
        "play_start": "#9fffff",
        "play_middle": "#00d9ff",
        "play_end": "#ff6633",
        "stop": "#ff4455",
        "spectrum_background": "#080e19",
        "spectrum_grid": "#26364c",
        "vu_background": "#111c2b",
        "vu_inactive": "#29334a",
        "vu_low": "#00e6a0",
        "vu_mid": "#ffd166",
        "vu_high": "#ff4455",
        "speaker_housing": "#0b1220",
        "speaker_border": "#4b5368",
        "speaker_metal": "#7c7180",
        "speaker_cone_1": "#d4c6c5",
        "speaker_cone_2": "#665568",
        "speaker_cone_3": "#30283c",
        "speaker_cone_4": "#0b1220",
    },

    "toxic_lime": {
        "name": "Toxic Lime / Acid Green",
        "background": "#080d05",
        "panel": "#14200b",
        "panel_dark": "#080f05",
        "panel_light": "#24320d",
        "display": "#101d09",
        "border": "#668c16",
        "border_glow": "#baff00",
        "text": "#efffd6",
        "muted": "#91a86c",
        "brand": "#baff00",
        "tagline": "#eaff7a",
        "status": "#5dff9a",
        "section": "#c8ff35",
        "track": "#d7ff72",
        "readout": "#aaff00",
        "left": "#aaff00",
        "right": "#00ff88",
        "volume": "#c8ff35",
        "slider_track": "#30421a",
        "slider_fill": "#baff00",
        "slider_fill_end": "#00ff88",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#baff00",
        "button": "#1b2a10",
        "button_border": "#668c16",
        "button_hover": "#344b16",
        "button_hover_border": "#c8ff35",
        "play_start": "#eaff7a",
        "play_middle": "#baff00",
        "play_end": "#00ff88",
        "stop": "#ff5364",
        "spectrum_background": "#070d05",
        "spectrum_grid": "#263d15",
        "vu_background": "#101d09",
        "vu_inactive": "#30421a",
        "vu_low": "#5dff66",
        "vu_mid": "#dfff00",
        "vu_high": "#ff4b38",
        "speaker_housing": "#080f05",
        "speaker_border": "#668c16",
        "speaker_metal": "#617b39",
        "speaker_cone_1": "#d8f5a2",
        "speaker_cone_2": "#719b35",
        "speaker_cone_3": "#304b19",
        "speaker_cone_4": "#080f05",
    },

    "blood_moon": {
        "name": "Blood Moon / Inferno Red",
        "background": "#100508",
        "panel": "#280c12",
        "panel_dark": "#120609",
        "panel_light": "#3b1017",
        "display": "#200910",
        "border": "#9b2638",
        "border_glow": "#ff263f",
        "text": "#ffe9e9",
        "muted": "#b47c83",
        "brand": "#ff263f",
        "tagline": "#ffb347",
        "status": "#ff8866",
        "section": "#ff5264",
        "track": "#ff9b86",
        "readout": "#ffb347",
        "left": "#ff263f",
        "right": "#ff9b35",
        "volume": "#ff5264",
        "slider_track": "#4a1b25",
        "slider_fill": "#ff263f",
        "slider_fill_end": "#ff9b35",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#ff5264",
        "button": "#35121a",
        "button_border": "#9b2638",
        "button_hover": "#5a1725",
        "button_hover_border": "#ff5264",
        "play_start": "#ffd0a1",
        "play_middle": "#ff4b36",
        "play_end": "#c40032",
        "stop": "#ff263f",
        "spectrum_background": "#100508",
        "spectrum_grid": "#4a1820",
        "vu_background": "#200910",
        "vu_inactive": "#4a1b25",
        "vu_low": "#ff8a38",
        "vu_mid": "#ffd166",
        "vu_high": "#ff263f",
        "speaker_housing": "#120609",
        "speaker_border": "#9b2638",
        "speaker_metal": "#89505a",
        "speaker_cone_1": "#ffc1a8",
        "speaker_cone_2": "#a63b43",
        "speaker_cone_3": "#501824",
        "speaker_cone_4": "#120609",
    },

    "arctic_aurora": {
        "name": "Arctic Aurora / Ice Blue",
        "background": "#041017",
        "panel": "#0b202b",
        "panel_dark": "#06131d",
        "panel_light": "#103342",
        "display": "#09202d",
        "border": "#287d91",
        "border_glow": "#54f5ff",
        "text": "#e5fcff",
        "muted": "#83b6c2",
        "brand": "#54f5ff",
        "tagline": "#a4ffe7",
        "status": "#68ffc5",
        "section": "#54f5ff",
        "track": "#a4faff",
        "readout": "#68ffc5",
        "left": "#54f5ff",
        "right": "#72ffbf",
        "volume": "#54f5ff",
        "slider_track": "#1c4655",
        "slider_fill": "#54f5ff",
        "slider_fill_end": "#72ffbf",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#54f5ff",
        "button": "#10303e",
        "button_border": "#287d91",
        "button_hover": "#175064",
        "button_hover_border": "#72ffbf",
        "play_start": "#d5ffff",
        "play_middle": "#54f5ff",
        "play_end": "#72ffbf",
        "stop": "#ff648b",
        "spectrum_background": "#041017",
        "spectrum_grid": "#16404d",
        "vu_background": "#09202d",
        "vu_inactive": "#1c4655",
        "vu_low": "#54f5ff",
        "vu_mid": "#72ffbf",
        "vu_high": "#ff648b",
        "speaker_housing": "#06131d",
        "speaker_border": "#287d91",
        "speaker_metal": "#598c9b",
        "speaker_cone_1": "#c9ffff",
        "speaker_cone_2": "#4b9eae",
        "speaker_cone_3": "#1b5263",
        "speaker_cone_4": "#06131d",
    },

    "gold_rush": {
        "name": "Gold Rush / Luxury Gold",
        "background": "#100d06",
        "panel": "#241b0c",
        "panel_dark": "#100c05",
        "panel_light": "#382a10",
        "display": "#211807",
        "border": "#94702a",
        "border_glow": "#ffd45c",
        "text": "#fff4d6",
        "muted": "#b6a276",
        "brand": "#ffd45c",
        "tagline": "#fff0a6",
        "status": "#aaffbb",
        "section": "#ffd45c",
        "track": "#ffe7a0",
        "readout": "#ffd45c",
        "left": "#ffd45c",
        "right": "#ff9f43",
        "volume": "#ffd45c",
        "slider_track": "#51401e",
        "slider_fill": "#ffd45c",
        "slider_fill_end": "#ff9f43",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#ffd45c",
        "button": "#30230e",
        "button_border": "#94702a",
        "button_hover": "#594018",
        "button_hover_border": "#ffd45c",
        "play_start": "#fff0a6",
        "play_middle": "#ffd45c",
        "play_end": "#ff9f43",
        "stop": "#ff5364",
        "spectrum_background": "#100d06",
        "spectrum_grid": "#443417",
        "vu_background": "#211807",
        "vu_inactive": "#51401e",
        "vu_low": "#aaff88",
        "vu_mid": "#ffd45c",
        "vu_high": "#ff7043",
        "speaker_housing": "#100c05",
        "speaker_border": "#94702a",
        "speaker_metal": "#9d824c",
        "speaker_cone_1": "#fff0bd",
        "speaker_cone_2": "#b38a3d",
        "speaker_cone_3": "#61451c",
        "speaker_cone_4": "#100c05",
    },

    "vaporwave": {
        "name": "Vaporwave / Miami Neon",
        "background": "#10071c",
        "panel": "#20102f",
        "panel_dark": "#10091d",
        "panel_light": "#321440",
        "display": "#1b0e2b",
        "border": "#a13bba",
        "border_glow": "#00ffe1",
        "text": "#fff0ff",
        "muted": "#b18cbd",
        "brand": "#ff65df",
        "tagline": "#00ffe1",
        "status": "#80ffcc",
        "section": "#00ffe1",
        "track": "#ff9be9",
        "readout": "#80ffcc",
        "left": "#00ffe1",
        "right": "#ff65df",
        "volume": "#00ffe1",
        "slider_track": "#46214f",
        "slider_fill": "#00ffe1",
        "slider_fill_end": "#ff65df",
        "slider_handle": "#ffffff",
        "slider_handle_border": "#00ffe1",
        "button": "#301641",
        "button_border": "#a13bba",
        "button_hover": "#552365",
        "button_hover_border": "#ff65df",
        "play_start": "#aafff5",
        "play_middle": "#00ffe1",
        "play_end": "#ff65df",
        "stop": "#ff5577",
        "spectrum_background": "#10071c",
        "spectrum_grid": "#492052",
        "vu_background": "#1b0e2b",
        "vu_inactive": "#46214f",
        "vu_low": "#00ffc3",
        "vu_mid": "#e6ff5c",
        "vu_high": "#ff4b9a",
        "speaker_housing": "#10091d",
        "speaker_border": "#a13bba",
        "speaker_metal": "#80518f",
        "speaker_cone_1": "#f5c4ff",
        "speaker_cone_2": "#a34cbd",
        "speaker_cone_3": "#51205f",
        "speaker_cone_4": "#10071c",
    },
}


def C(key, theme=None):
    """Zentraler Zugriff auf Theme-Farben."""
    theme = theme or ACTIVE_THEME
    palette = COLOR_THEMES.get(
        theme,
        COLOR_THEMES["cyberpunk"]
    )
    return palette.get(key, "#ffffff")


def blend_color(color_a, color_b, amount):
    a = QColor(color_a)
    b = QColor(color_b)
    amount = max(0.0, min(1.0, float(amount)))

    return QColor(
        int(a.red() + (b.red() - a.red()) * amount),
        int(a.green() + (b.green() - a.green()) * amount),
        int(a.blue() + (b.blue() - a.blue()) * amount),
    )


# ============================================================
# FFT ENGINE
# ============================================================

def fft_real(samples):
    """Iterative Radix-2 FFT."""

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
# NEON PANEL
# ============================================================

class NeonPanel(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("neonPanel")
        self.setFrameShape(QFrame.Shape.NoFrame)


# ============================================================
# RGB SPEAKER
# ============================================================

class SpeakerWidget(QWidget):

    def __init__(
        self,
        kind="woofer",
        channel="left",
        parent=None
    ):
        super().__init__(parent)

        self.kind = kind
        self.channel = channel

        self.level = 0.02
        self.phase = 0.0
        self.energy = 0.0

        self.setMinimumSize(125, 155)

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

    def set_level(self, level, phase=0.0, energy=None):

        self.level = max(0.0, min(1.0, float(level)))
        self.phase = float(phase)

        self.energy = (
            self.level if energy is None
            else max(0.0, min(1.0, float(energy)))
        )

        self.update()

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        cx = w / 2
        cy = h / 2

        r = max(25, min(w * 0.39, h * 0.36))

        accent = QColor(C(self.channel))

        pulse = (
            0.5 + 0.5 * math.sin(self.phase)
        ) * self.level

        # Speaker housing
        p.setPen(QPen(QColor(C("speaker_border")), 2))
        p.setBrush(QColor(C("speaker_housing")))

        p.drawRoundedRect(
            QRectF(4, 4, w - 8, h - 8),
            18, 18
        )

        # RGB frame
        frame_color = QColor(
            accent.red(),
            accent.green(),
            accent.blue(),
            100 + int(140 * self.level)
        )

        p.setPen(QPen(frame_color, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)

        p.drawRoundedRect(
            QRectF(10, 10, w - 20, h - 20),
            14, 14
        )

        # Halo
        halo = QRadialGradient(cx, cy, r * 1.65)

        halo.setColorAt(
            0,
            QColor(
                accent.red(),
                accent.green(),
                accent.blue(),
                20 + int(65 * pulse)
            )
        )

        halo.setColorAt(
            0.65,
            QColor(
                accent.red(),
                accent.green(),
                accent.blue(),
                12 + int(35 * pulse)
            )
        )

        halo.setColorAt(1, QColor(0, 0, 0, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(halo))

        p.drawEllipse(
            QRectF(
                cx - r * 1.65,
                cy - r * 1.65,
                r * 3.3,
                r * 3.3
            )
        )

        # Metal ring
        p.setPen(QPen(QColor(C("speaker_metal")), 5))
        p.setBrush(QColor(C("panel_dark")))

        p.drawEllipse(
            QRectF(cx-r, cy-r, 2*r, 2*r)
        )

        # Neon ring
        p.setPen(QPen(accent, 3 + pulse * 3))
        p.setBrush(Qt.BrushStyle.NoBrush)

        p.drawEllipse(
            QRectF(
                cx-r*.91, cy-r*.91,
                r*1.82, r*1.82
            )
        )

        # Speaker cone
        cone_r = r * (
            .69 +
            .055 * self.energy *
            math.sin(self.phase * 1.7)
        )

        gradient = QRadialGradient(
            cx - cone_r*.22,
            cy - cone_r*.28,
            cone_r*1.5
        )

        gradient.setColorAt(0, QColor(C("speaker_cone_1")))
        gradient.setColorAt(.25, QColor(C("speaker_cone_2")))
        gradient.setColorAt(.65, QColor(C("speaker_cone_3")))
        gradient.setColorAt(1, QColor(C("speaker_cone_4")))

        p.setPen(QPen(accent, 1.8))
        p.setBrush(QBrush(gradient))

        p.drawEllipse(
            QRectF(
                cx-cone_r, cy-cone_r,
                cone_r*2, cone_r*2
            )
        )

        # Cone rings
        for factor, alpha in (
            (.86, 150),
            (.72, 95),
            (.56, 55)
        ):

            rr = cone_r * factor

            p.setPen(
                QPen(
                    QColor(
                        accent.red(),
                        accent.green(),
                        accent.blue(),
                        alpha
                    ),
                    1.5
                )
            )

            p.setBrush(Qt.BrushStyle.NoBrush)

            p.drawEllipse(
                QRectF(cx-rr, cy-rr, rr*2, rr*2)
            )

        # Center dust cap
        dust_r = r * (
            .25 if self.kind == "tweeter"
            else .29
        )

        dust = QRadialGradient(
            cx-dust_r*.25,
            cy-dust_r*.3,
            dust_r*1.5
        )

        dust.setColorAt(0, QColor("#ffffff"))
        dust.setColorAt(.3, accent)
        dust.setColorAt(1, QColor(C("panel_dark")))

        p.setPen(QPen(accent, 1.5))
        p.setBrush(QBrush(dust))

        p.drawEllipse(
            QRectF(
                cx-dust_r, cy-dust_r,
                dust_r*2, dust_r*2
            )
        )

        # Screws
        for angle in (45, 135, 225, 315):

            a = math.radians(angle)

            sx = cx + math.cos(a) * r * .96
            sy = cy + math.sin(a) * r * .96

            p.setPen(QPen(QColor(C("muted")), 1))
            p.setBrush(QColor(C("speaker_metal")))

            p.drawEllipse(QPointF(sx, sy), 3, 3)

        p.end()


# ============================================================
# 32-BAND SPECTRUM
# ============================================================

class SpectrumWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.bands = [.02] * 32

        self.setMinimumHeight(105)
        self.setMaximumHeight(145)

    def set_bands(self, bands, hue=None):

        self.bands = [
            max(.02, min(1.0, float(v)))
            for v in bands[:32]
        ]

        self.bands += [.02] * (32 - len(self.bands))

        self.update()

    def paintEvent(self, event):

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        p.setPen(QPen(QColor(C("border")), 1))
        p.setBrush(QColor(C("spectrum_background")))

        p.drawRoundedRect(
            QRectF(0, 0, w, h),
            10, 10
        )

        # Grid
        p.setPen(
            QPen(
                QColor(C("spectrum_grid")),
                1,
                Qt.PenStyle.DotLine
            )
        )

        for i in range(1, 5):
            y = h * i / 5
            p.drawLine(QPointF(7, y), QPointF(w-7, y))

        count = 32
        gap = 3

        bar_width = (
            w - 20 - gap*(count-1)
        ) / count

        bottom = h - 10
        usable = h - 24

        left_color = QColor(C("left"))
        right_color = QColor(C("right"))

        for i, value in enumerate(self.bands):

            x = 10 + i * (bar_width + gap)
            bar_h = max(3, usable * value)

            color = blend_color(
                left_color,
                right_color,
                i / max(1, count - 1)
            )

            grad = QLinearGradient(
                x, bottom-bar_h,
                x, bottom
            )

            grad.setColorAt(0, QColor("#ffffff"))
            grad.setColorAt(.18, color.lighter(125))
            grad.setColorAt(1, color.darker(150))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))

            p.drawRoundedRect(
                QRectF(
                    x, bottom-bar_h,
                    bar_width, bar_h
                ),
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

        self.setMinimumHeight(20)
        self.setMaximumHeight(25)

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

        w = self.width()
        h = self.height()

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(C("vu_background")))

        p.drawRoundedRect(
            QRectF(0, 2, w, h-4),
            5, 5
        )

        segments = 40
        gap = 2

        sw = (
            w - 8 - (segments-1)*gap
        ) / segments

        active = int(self.level * segments)
        peak = int(self.peak * segments)

        for i in range(segments):

            x = 4 + i*(sw+gap)

            if i >= 35:
                color = QColor(C("vu_high"))
            elif i >= 28:
                color = QColor(C("vu_mid"))
            else:
                color = QColor(C("vu_low"))

            p.setBrush(
                color if i < active
                else QColor(C("vu_inactive"))
            )

            p.drawRoundedRect(
                QRectF(x, 5, sw, h-10),
                1.5, 1.5
            )

        if peak > 0:

            x = 4 + min(
                segments-1,
                peak
            )*(sw+gap)

            p.setPen(QPen(QColor("#ffffff"), 2))

            p.drawLine(
                QPointF(x, 3),
                QPointF(x, h-3)
            )

        p.end()


# ============================================================
# MAIN MUSIC PLAYER
# ============================================================

class MusicPlayerWindow(QWidget):

    def __init__(self, host, parent=None):

        super().__init__(
            parent or host,
            Qt.WindowType.Window
        )

        global ACTIVE_THEME

        self.host = host

        self.settings = QSettings(
            "speedy005",
            "OSCamPatchManager"
        )

        # Gespeichertes Theme laden
        saved_theme = self.settings.value(
            "music_player/color_theme",
            ACTIVE_THEME
        )

        if saved_theme in COLOR_THEMES:
            ACTIVE_THEME = saved_theme

        self.setWindowTitle(
            "OSCam Patch Manager Player • NEON BEAST ULTIMATE"
        )

        self.setMinimumSize(850, 680)

        self._phase = 0.0
        self._hue = 190

        self._audio_level = 0.0
        self._audio_peak = 0.0

        self._audio_bands = [.02] * 32
        self._stereo_levels = [0.0, 0.0]

        self._buffer_output = None
        self._buffer_player = None
        self._buffer_signal_connected = False

        self._fft_ready = False
        self._audio_buffer_received = False
        self._last_samples = []

        self._build_ui()

        self._restore_window_geometry()

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._animate_stereo)
        self._timer.start()

        self.set_language()
        self._set_volume(self.volume.value())

    # ========================================================
    # WINDOW GEOMETRY
    # ========================================================

    def _restore_window_geometry(self):

        geometry = self.settings.value(
            "music_player/window_geometry"
        )

        if geometry is not None:

            try:
                if self.restoreGeometry(geometry):
                    return
            except (TypeError, RuntimeError):
                pass

        self.resize(1050, 790)

    def _save_window_geometry(self):

        self.settings.setValue(
            "music_player/window_geometry",
            self.saveGeometry()
        )

        self.settings.sync()

    # ========================================================
    # THEME MANAGEMENT
    # ========================================================

    def _change_theme(self, index):

        global ACTIVE_THEME

        theme_key = self.theme_combo.itemData(index)

        if theme_key not in COLOR_THEMES:
            return

        ACTIVE_THEME = theme_key

        self.settings.setValue(
            "music_player/color_theme",
            ACTIVE_THEME
        )

        self.settings.sync()

        self._apply_style()

        self.left_speaker.update()
        self.right_speaker.update()
        self.spectrum.update()
        self.vu_left.update()
        self.vu_right.update()

        self.theme_combo.setToolTip(
            COLOR_THEMES[ACTIVE_THEME]["name"]
        )

    # ========================================================
    # STYLE
    # ========================================================

    def _apply_style(self):

        self.setStyleSheet(f"""
            QWidget {{
                background-color:{C('background')};
                color:{C('text')};
                font-family:'Segoe UI';
                font-size:9pt;
            }}

            QFrame#chassis {{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 {C('panel')},
                    stop:.45 {C('panel_dark')},
                    stop:1 {C('panel_light')}
                );
                border:2px solid {C('border')};
                border-radius:23px;
            }}

            QFrame#display {{
                background:qlineargradient(
                    x1:0,y1:0,x2:0,y2:1,
                    stop:0 {C('display')},
                    stop:.55 {C('panel_dark')},
                    stop:1 {C('panel_light')}
                );
                border:1px solid {C('border_glow')};
                border-radius:16px;
            }}

            QFrame#glass {{
                background:{C('panel_dark')};
                border:1px solid {C('border')};
                border-radius:12px;
            }}

            QFrame#controlPanel {{
                background:{C('panel')};
                border:1px solid {C('border')};
                border-radius:15px;
            }}

            QFrame#neonLine {{
                background:{C('border_glow')};
                border:none;
                max-height:2px;
                min-height:2px;
            }}

            QLabel#brand {{
                background:transparent;
                color:{C('brand')};
                font-size:24pt;
                font-weight:1000;
                letter-spacing:4px;
            }}

            QLabel#tagline {{
                background:transparent;
                color:{C('tagline')};
                font-size:8pt;
                font-weight:bold;
                letter-spacing:3px;
            }}

            QLabel#status {{
                background:transparent;
                color:{C('status')};
                font-size:9pt;
                font-weight:bold;
            }}

            QLabel#tiny {{
                background:transparent;
                color:{C('muted')};
                font-size:8pt;
                letter-spacing:1px;
            }}

            QLabel#section {{
                background:transparent;
                color:{C('section')};
                font-size:9pt;
                font-weight:bold;
                letter-spacing:2px;
            }}

            QLabel#track {{
                background:transparent;
                color:{C('track')};
                font-size:16pt;
                font-weight:1000;
            }}

            QLabel#readout {{
                background:transparent;
                color:{C('readout')};
                font-size:8pt;
                font-weight:bold;
            }}

            QLabel#leftChannel {{
                background:transparent;
                color:{C('left')};
                font-size:9pt;
                font-weight:bold;
                letter-spacing:3px;
            }}

            QLabel#rightChannel {{
                background:transparent;
                color:{C('right')};
                font-size:9pt;
                font-weight:bold;
                letter-spacing:3px;
            }}

            QLabel#volumeValue {{
                background:transparent;
                color:{C('volume')};
                font-size:10pt;
                font-weight:bold;
            }}

            QPushButton {{
                color:{C('text')};
                background:{C('button')};
                border:1px solid {C('button_border')};
                border-radius:10px;
                padding:10px 14px;
                font-weight:bold;
            }}

            QPushButton:hover {{
                background:{C('button_hover')};
                border:1px solid {C('button_hover_border')};
                color:#ffffff;
            }}

            QPushButton#mainplay {{
                color:#04101b;
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:1,
                    stop:0 {C('play_start')},
                    stop:.5 {C('play_middle')},
                    stop:1 {C('play_end')}
                );
                border:2px solid {C('slider_handle')};
                border-radius:14px;
                font-size:12pt;
                font-weight:1000;
                min-width:135px;
                min-height:45px;
            }}

            QPushButton#mainplay:hover {{
                background:{C('play_start')};
                border:2px solid #ffffff;
            }}

            QPushButton#stopButton {{
                color:{C('stop')};
                border:1px solid {C('stop')};
            }}

            QPushButton#stopButton:hover {{
                background:{C('button_hover')};
                border:1px solid {C('stop')};
            }}

            QComboBox {{
                color:{C('text')};
                background:{C('panel_dark')};
                border:1px solid {C('border')};
                border-radius:9px;
                padding:10px;
                selection-background-color:{C('border')};
            }}

            QComboBox:hover {{
                border:1px solid {C('border_glow')};
            }}

            QComboBox QAbstractItemView {{
                color:{C('text')};
                background:{C('panel')};
                selection-background-color:{C('border')};
                border:1px solid {C('border')};
                padding:5px;
            }}

            QSlider::groove:horizontal {{
                height:7px;
                background:{C('slider_track')};
                border-radius:3px;
            }}

            QSlider::sub-page:horizontal {{
                background:qlineargradient(
                    x1:0,y1:0,x2:1,y2:0,
                    stop:0 {C('slider_fill')},
                    stop:1 {C('slider_fill_end')}
                );
                border-radius:3px;
            }}

            QSlider::handle:horizontal {{
                background:{C('slider_handle')};
                border:3px solid {C('slider_handle_border')};
                width:16px;
                height:16px;
                margin:-7px 0;
                border-radius:9px;
            }}

            QSlider::handle:horizontal:hover {{
                border:4px solid {C('slider_fill_end')};
            }}
        """)

    # ========================================================
    # UI BUILD
    # ========================================================

    def _build_ui(self):

        self._apply_style()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        chassis = QFrame()
        chassis.setObjectName("chassis")

        layout = QVBoxLayout(chassis)
        layout.setContentsMargins(20, 17, 20, 17)
        layout.setSpacing(12)

        # HEADER
        header = QHBoxLayout()
        brand_box = QVBoxLayout()

        brand = QLabel("OSCAM MUSIC PLAYER")
        brand.setObjectName("brand")

        tagline = QLabel(
            "ULTIMATE CYBERPUNK HI-FI EXPERIENCE"
        )
        tagline.setObjectName("tagline")

        brand_box.addWidget(brand)
        brand_box.addWidget(tagline)

        header.addLayout(brand_box)
        header.addStretch()

        status_box = QVBoxLayout()

        self.status_label = QLabel("● SYSTEM ONLINE")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        self.signal_label = QLabel("DSP / STANDBY")
        self.signal_label.setObjectName("tiny")
        self.signal_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        status_box.addWidget(self.status_label)
        status_box.addWidget(self.signal_label)

        header.addLayout(status_box)
        layout.addLayout(header)

        line = QFrame()
        line.setObjectName("neonLine")
        layout.addWidget(line)

        # MAIN DECK
        deck = QHBoxLayout()
        deck.setSpacing(13)

        left_box = QVBoxLayout()

        left_label = QLabel("◈ LEFT CHANNEL")
        left_label.setObjectName("leftChannel")
        left_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.left_speaker = SpeakerWidget("woofer", "left")

        left_box.addWidget(left_label)
        left_box.addWidget(self.left_speaker, 1)

        right_box = QVBoxLayout()

        right_label = QLabel("RIGHT CHANNEL ◈")
        right_label.setObjectName("rightChannel")
        right_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.right_speaker = SpeakerWidget("woofer", "right")

        right_box.addWidget(right_label)
        right_box.addWidget(self.right_speaker, 1)

        # CENTER DISPLAY
        display = QFrame()
        display.setObjectName("display")

        center = QVBoxLayout(display)
        center.setContentsMargins(15, 13, 15, 13)
        center.setSpacing(9)

        reactor = QLabel("◈  AUDIO REACTOR  ◈")
        reactor.setObjectName("section")
        reactor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center.addWidget(reactor)

        self.track_label = QLabel("NEON BEAST // READY")
        self.track_label.setObjectName("track")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label.setWordWrap(True)

        center.addWidget(self.track_label)

        self.track_combo = QComboBox()
        self.track_combo.setMinimumHeight(42)

        self.track_combo.currentIndexChanged.connect(
            self._selection_changed
        )

        center.addWidget(self.track_combo)

        spectrum_title = QLabel("REALTIME FREQUENCY ANALYZER")
        spectrum_title.setObjectName("tiny")
        spectrum_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center.addWidget(spectrum_title)

        self.spectrum = SpectrumWidget()
        center.addWidget(self.spectrum)

        frequency_row = QHBoxLayout()

        for text in ("SUB", "BASS", "LOW", "MID", "HIGH", "AIR"):

            label = QLabel(text)
            label.setObjectName("tiny")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            frequency_row.addWidget(label)

        center.addLayout(frequency_row)

        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)

        center.addWidget(self.progress)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setObjectName("tiny")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        center.addWidget(self.time_label)

        # VU METERS
        meter_panel = QFrame()
        meter_panel.setObjectName("glass")

        meter_layout = QGridLayout(meter_panel)
        meter_layout.setContentsMargins(9, 8, 9, 8)
        meter_layout.setVerticalSpacing(5)

        self.vu_left = StereoMeter("L")
        self.vu_right = StereoMeter("R")

        left_meter_label = QLabel("L")
        right_meter_label = QLabel("R")

        left_meter_label.setObjectName("readout")
        right_meter_label.setObjectName("readout")

        meter_layout.addWidget(left_meter_label, 0, 0)
        meter_layout.addWidget(self.vu_left, 0, 1)
        meter_layout.addWidget(right_meter_label, 1, 0)
        meter_layout.addWidget(self.vu_right, 1, 1)

        center.addWidget(meter_panel)

        deck.addLayout(left_box, 2)
        deck.addWidget(display, 5)
        deck.addLayout(right_box, 2)

        layout.addLayout(deck, 1)

        # TRANSPORT CONTROLS
        controls_panel = QFrame()
        controls_panel.setObjectName("controlPanel")

        controls = QHBoxLayout(controls_panel)
        controls.setContentsMargins(15, 12, 15, 12)
        controls.setSpacing(12)

        self.prev_btn = QPushButton("◀◀")
        self.play_btn = QPushButton("▶ PLAY")
        self.stop_btn = QPushButton("■ STOP")
        self.next_btn = QPushButton("▶▶")

        self.prev_btn.setMinimumSize(62, 48)
        self.next_btn.setMinimumSize(62, 48)
        self.stop_btn.setMinimumSize(85, 48)
        self.play_btn.setMinimumSize(145, 54)

        self.play_btn.setObjectName("mainplay")
        self.stop_btn.setObjectName("stopButton")

        self.prev_btn.setToolTip("Previous track")
        self.next_btn.setToolTip("Next track")
        self.play_btn.setToolTip("Play / Pause")
        self.stop_btn.setToolTip("Stop playback")

        self.prev_btn.clicked.connect(
            lambda: self._step_track(-1)
        )

        self.next_btn.clicked.connect(
            lambda: self._step_track(1)
        )

        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)

        controls.addStretch()
        controls.addWidget(self.prev_btn)
        controls.addWidget(self.play_btn)
        controls.addWidget(self.stop_btn)
        controls.addWidget(self.next_btn)
        controls.addStretch()

        layout.addWidget(controls_panel)

        # MASTER VOLUME
        volume_panel = QFrame()
        volume_panel.setObjectName("glass")

        volume_layout = QHBoxLayout(volume_panel)
        volume_layout.setContentsMargins(15, 10, 15, 10)

        master = QLabel("◖ MASTER VOLUME")
        master.setObjectName("section")

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)

        music_cfg = (
            getattr(self.host, "current_config", {}) or {}
        ).get("music", {})

        try:
            initial_volume = int(music_cfg.get("volume", 20))
        except (TypeError, ValueError):
            initial_volume = 20

        self.volume.setValue(max(0, min(100, initial_volume)))
        self.volume.valueChanged.connect(self._set_volume)

        self.volume_label = QLabel(f"{self.volume.value()} %")
        self.volume_label.setObjectName("volumeValue")

        volume_layout.addWidget(master)
        volume_layout.addWidget(self.volume, 1)
        volume_layout.addWidget(self.volume_label)

        layout.addWidget(volume_panel)

        # THEME SELECTOR
        theme_panel = QFrame()
        theme_panel.setObjectName("glass")

        theme_layout = QHBoxLayout(theme_panel)
        theme_layout.setContentsMargins(15, 8, 15, 8)

        theme_label = QLabel("◈ NEON COLOR THEME")
        theme_label.setObjectName("section")

        self.theme_combo = QComboBox()
        self.theme_combo.setMinimumWidth(230)

        for key, theme in COLOR_THEMES.items():
            self.theme_combo.addItem(theme["name"], key)

        selected_index = self.theme_combo.findData(ACTIVE_THEME)

        if selected_index >= 0:
            self.theme_combo.setCurrentIndex(selected_index)

        self.theme_combo.currentIndexChanged.connect(
            self._change_theme
        )

        self.theme_combo.setToolTip("Neon-Farbdesign auswählen")

        theme_layout.addWidget(theme_label)
        theme_layout.addStretch()
        theme_layout.addWidget(self.theme_combo)

        layout.addWidget(theme_panel)

        # FOOTER
        footer = QLabel(
            "RGB NEON ENGINE  •  LIVE DSP  •  "
            "STEREO DRIVER ARRAY  •  OSCAM"
        )

        footer.setObjectName("tagline")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(footer)

        root.addWidget(chassis)

        self.refresh_tracks()

    # ========================================================
    # LANGUAGE
    # ========================================================

    def set_language(self):

        is_de = str(
            getattr(self.host, "LANG", "de")
        ).lower().startswith("de")

        self.setWindowTitle("OSCam • NEON BEAST ULTIMATE")

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

    # ========================================================
    # TRACK MANAGEMENT
    # ========================================================

    def refresh_tracks(self):

        source = getattr(
            self.host,
            "music_title_combo",
            None
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

                idx = self.track_combo.findText(
                    "🎧 " + Path(wanted).stem
                )

            if idx < 0:
                idx = max(0, source.currentIndex())

            if self.track_combo.count():

                self.track_combo.setCurrentIndex(
                    max(
                        0,
                        min(
                            idx,
                            self.track_combo.count()-1
                        )
                    )
                )

        self.track_combo.blockSignals(False)
        self._update_track_label()

    def _selection_changed(self, index):

        source = getattr(
            self.host,
            "music_title_combo",
            None
        )

        if source is not None and index >= 0:
            source.setCurrentIndex(index)

        self._update_track_label()

        if (
            source is not None
            and index >= 0
            and hasattr(self.host, "_save_music_state")
        ):

            self.host._save_music_state(
                last_track=str(source.currentData() or "")
            )

        self._sync_state()

    def _update_track_label(self):

        text = self.track_combo.currentText().strip()

        self.track_label.setText(
            text if text else "NEON BEAST // READY"
        )

    def _step_track(self, step):

        count = self.track_combo.count()

        if count <= 1:
            return

        index = self.track_combo.currentIndex()

        first = (
            1
            if self.track_combo.itemData(0) == "__random__"
            else 0
        )

        if count <= first:
            return

        if index < first:
            index = first
        else:
            index = first + (
                (index - first + step)
                % (count - first)
            )

        self.track_combo.setCurrentIndex(index)

    # ========================================================
    # HOST PLAYER CONNECTION
    # ========================================================

    def _player(self):

        player = getattr(
            self.host,
            "_background_music_player",
            None
        )

        self._attach_audio_analysis(player)

        return player

    def _attach_audio_analysis(self, player):

        if player is None or player is self._buffer_player:
            return

        self._buffer_player = player
        self._buffer_output = None
        self._buffer_signal_connected = False
        self._audio_buffer_received = False
        self._fft_ready = False

        self._stereo_levels = [0.0, 0.0]
        self._audio_bands = [.02] * 32

        try:
            from PyQt6.QtMultimedia import QAudioBufferOutput

            if not hasattr(player, "setAudioBufferOutput"):
                self.signal_label.setText("DSP / BUFFER UNAVAILABLE")
                return

            self._buffer_output = QAudioBufferOutput(self)

            self._buffer_output.audioBufferReceived.connect(
                self._on_audio_buffer
            )

            player.setAudioBufferOutput(self._buffer_output)

            self._buffer_signal_connected = True

            self.signal_label.setText("DSP / AUDIO CONNECTED")

        except (
            ImportError,
            AttributeError,
            TypeError,
            RuntimeError
        ) as error:

            self._buffer_output = None
            self._buffer_signal_connected = False

            self.signal_label.setText("DSP / AUDIO ERROR")
            print("AudioBufferOutput Fehler:", error)

    # ========================================================
    # LIVE AUDIO ANALYSIS
    # ========================================================

    def _on_audio_buffer(self, buffer):

        try:

            fmt = buffer.format()
            raw = bytes(buffer.data())

            sample_format = fmt.sampleFormat()

            name = getattr(
                sample_format,
                "name",
                str(sample_format)
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

                samples = [
                    (v - 128) / 128.0
                    for v in raw
                ]

            else:

                count = len(raw) // width

                if count == 0:
                    return

                try:

                    from PyQt6.QtMultimedia import QAudioFormat

                    endian = (
                        "<"
                        if fmt.byteOrder()
                        == QAudioFormat.Endian.LittleEndian
                        else ">"
                    )

                except (ImportError, AttributeError):
                    endian = "<"

                unpacked = struct.unpack(
                    endian + code * count,
                    raw[:count * width]
                )

                samples = [
                    max(-1.0, min(1.0, value / scale))
                    for value in unpacked
                ]

            if not samples:
                return

            channels = max(1, int(fmt.channelCount()))

            if channels >= 2 and len(samples) >= channels:

                left = samples[0::channels]
                right = samples[1::channels]

                def rms(values):
                    return math.sqrt(
                        sum(v*v for v in values)
                        / max(1, len(values))
                    )

                l_rms = rms(left)
                r_rms = rms(right)

                self._stereo_levels = [
                    min(1.0, l_rms * 3.5),
                    min(1.0, r_rms * 3.5)
                ]
                self._audio_buffer_received = True
                length = min(len(left), len(right))

                mono = [
                    (left[i] + right[i]) * .5
                    for i in range(length)
                ]

            else:

                mono = samples

                value = math.sqrt(
                    sum(v*v for v in mono)
                    / max(1, len(mono))
                )

                self._stereo_levels = [
                    min(1.0, value * 3.5)
                ] * 2
                self._audio_buffer_received = True
            if not mono:
                return

            rms_value = math.sqrt(
                sum(v*v for v in mono)
                / len(mono)
            )

            self._audio_level = min(1.0, rms_value * 3.5)

            self._audio_peak = min(
                1.0,
                max(abs(v) for v in mono)
            )

            self._last_samples = mono[-512:]

            available = len(self._last_samples)

            if available < 64:
                return

            n = 1 << (
                min(available, 512).bit_length() - 1
            )

            values = self._last_samples[-n:]

            # Hann window
            windowed = [
                values[i] * (
                    .5 - .5 * math.cos(
                        2 * math.pi * i / max(1, n-1)
                    )
                )
                for i in range(n)
            ]

            spectrum = fft_real(windowed)

            if not spectrum:
                return

            # Logarithmische Verteilung
            bands = []
            max_bin = max(2, n // 2)

            for band in range(32):

                low = max(
                    1,
                    int(max_bin ** (band / 32))
                )

                high = max(
                    low + 1,
                    int(max_bin ** ((band + 1) / 32))
                )

                high = min(max_bin, high)

                magnitudes = [
                    abs(spectrum[k]) / max(1, n / 2)
                    for k in range(low, high)
                    if k < len(spectrum)
                ]

                energy = (
                    math.sqrt(
                        sum(v*v for v in magnitudes)
                        / len(magnitudes)
                    )
                    if magnitudes else 0.0
                )

                bands.append(
                    max(.02, min(1.0, energy * 4.5))
                )

            self._audio_bands = bands
            self._fft_ready = True

        except (
            ValueError,
            TypeError,
            BufferError,
            struct.error,
            RuntimeError,
            ZeroDivisionError
        ):
            return

    # ========================================================
    # PLAYBACK CONTROLS
    # ========================================================

    def _toggle_play(self):

        button = getattr(
            self.host,
            "music_button",
            None
        )

        if button is None:
            return

        # Zentralen OSCam-Button auslösen
        button.click()

        self._sync_state()

    def _stop(self):

        player = self._player()

        if player is not None:
            player.stop()

        button = getattr(
            self.host,
            "music_button",
            None
        )

        if button is not None and button.isChecked():
            button.setChecked(False)

        self._sync_state()

    def _set_volume(self, value):

        value = max(0, min(100, int(value)))

        if hasattr(self.host, "_save_music_state"):
            self.host._save_music_state(volume=value)

        output = getattr(
            self.host,
            "_background_music_output",
            None
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

    # ========================================================
    # PLAYER STATE
    # ========================================================

    def _sync_state(self):

        player = getattr(
            self.host,
            "_background_music_player",
            None
        )

        button = getattr(
            self.host,
            "music_button",
            None
        )

        playing = bool(button and button.isChecked())

        is_de = str(
            getattr(self.host, "LANG", "de")
        ).lower().startswith("de")

        self.play_btn.setText(
            (
                "Ⅱ PAUSE" if playing else "▶ ABSPIELEN"
            )
            if is_de
            else (
                "Ⅱ PAUSE" if playing else "▶ PLAY"
            )
        )

        if player is None:

            self.progress.setValue(0)
            self.time_label.setText("00:00 / 00:00")

            return

        try:

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

        except (AttributeError, RuntimeError):
            pass

    # ========================================================
    # RGB ANIMATION ENGINE
    # ========================================================

    def _animate_stereo(self):

        self._phase += .22

        player = getattr(
            self.host,
            "_background_music_player",
            None
        )

        # Audioanalyse automatisch verbinden
        self._attach_audio_analysis(player)

        # Tatsächlichen Player-Status abfragen
        try:
            from PyQt6.QtMultimedia import QMediaPlayer

            playing = (
                player is not None
                and player.playbackState()
                == QMediaPlayer.PlaybackState.PlayingState
            )

        except (AttributeError, RuntimeError):
            playing = False

        if playing:

            if (
                self._buffer_signal_connected
                and self._audio_buffer_received
            ):

                left = self._stereo_levels[0]
                right = self._stereo_levels[1]

                bands = self._audio_bands

                self.signal_label.setText("DSP / LIVE AUDIO")
                self.status_label.setText("● AUDIO STREAM ACTIVE")

                sub = sum(bands[:4]) / 4
                bass = sum(bands[4:9]) / 5
                mid = sum(bands[9:21]) / 12
                high = sum(bands[21:]) / 11

            else:

                # Keine künstliche Animation!
                left = 0.0
                right = 0.0

                bands = [.02] * 32

                sub = 0.0
                bass = 0.0
                mid = 0.0
                high = 0.0

                self.signal_label.setText("DSP / WAITING FOR AUDIO")
                self.status_label.setText("● WAITING FOR SIGNAL")

            # LEFT SPEAKER
            self.left_speaker.set_level(
                left,
                self._phase,
                sub
            )

            # RIGHT SPEAKER
            self.right_speaker.set_level(
                right,
                self._phase,
                sub
            )

            # REAL STEREO VU
            self.vu_left.set_level(left)
            self.vu_right.set_level(right)

            # REAL FFT
            self.spectrum.set_bands(bands)

        else:

            # Bei Pause und Stopp alles zurücksetzen
            self._stereo_levels = [0.0, 0.0]
            self._audio_level = 0.0
            self._audio_peak = 0.0

            self._audio_bands = [.02] * 32
            self._audio_buffer_received = False
            self._fft_ready = False

            self.left_speaker.set_level(0.0, self._phase, 0.0)
            self.right_speaker.set_level(0.0, self._phase, 0.0)

            self.vu_left.reset()
            self.vu_right.reset()

            self.spectrum.set_bands([.02] * 32)

            self.signal_label.setText("DSP / STANDBY")
            self.status_label.setText("● SYSTEM ONLINE")

        self._sync_state()

    # ========================================================
    # WINDOW EVENTS
    # ========================================================

    def showEvent(self, event):

        self.refresh_tracks()
        self.set_language()

        super().showEvent(event)

    def closeEvent(self, event):

        # Fenstergröße und Position speichern.
        self._save_window_geometry()

        # Nur den Visual Player Timer stoppen.
        # Die OSCam-Wiedergabe bleibt zentral aktiv.

        if hasattr(self, "_timer"):
            self._timer.stop()

        super().closeEvent(event)

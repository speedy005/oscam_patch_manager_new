"""
OSCam Music Player – eigenständiges Player-Fenster für den OSCam Patch Manager.
Dieses Modul wird von der Haupt-GUI importiert; die Wiedergabe bleibt dort zentral.
"""
import math
import random

from PyQt6.QtCore import Qt, QTimer, QSettings, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QRadialGradient
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame, QSizePolicy
)


class SpeakerWidget(QWidget):
    """Gezeichnete, dezent pulsierende Lautsprechermembran."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.level = 0.12
        self.phase = 0.0
        self.setMinimumSize(112, 158)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_level(self, level, phase):
        self.level = max(0.0, min(1.0, level)); self.phase = phase; self.update()

    def paintEvent(self, event):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height(); cx, cy = w/2, h/2
        r = min(w*.43, h*.43); pulse = (0.5 + 0.5*math.sin(self.phase))*self.level
        p.setPen(QPen(QColor('#285d32'), 2)); p.setBrush(QColor('#0b120e'))
        p.drawRoundedRect(QRectF(3, 3, w-6, h-6), 12, 12)
        p.setPen(QPen(QColor(57,255,85,90+int(100*pulse)), 5+2*pulse)); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(cx-r, cy-r, 2*r, 2*r))
        grad=QRadialGradient(cx-r*.22, cy-r*.25, r*1.25)
        grad.setColorAt(0,QColor('#49634c')); grad.setColorAt(.38,QColor('#1d2d22')); grad.setColorAt(1,QColor('#080d0a'))
        p.setPen(QPen(QColor('#72ff7c'),1.5)); p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(cx-r*.82,cy-r*.82,r*1.64,r*1.64))
        p.setPen(QPen(QColor('#4ebd5b'),2)); p.setBrush(QColor('#111a14'))
        p.drawEllipse(QRectF(cx-r*.55,cy-r*.55,r*1.1,r*1.1))
        p.setPen(QPen(QColor('#8aff91'),1.5)); p.setBrush(QColor('#263b2b'))
        p.drawEllipse(QRectF(cx-r*.25,cy-r*.25,r*.5,r*.5)); p.end()


class MusicPlayerWindow(QWidget):
    def __init__(self, host, parent=None):
        super().__init__(parent or host, Qt.WindowType.Window)
        self.host = host
        self.settings = QSettings("speedy005", "OSCamPatchManager")  # Legacy fallback only
        self.setWindowTitle("OSCam • Cyber Music Player")
        self.setMinimumSize(680, 500)
        self.resize(760, 550)
        self._phase = 0.0
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(160)
        self._timer.timeout.connect(self._animate_stereo)
        self._timer.start()
        self.set_language()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget { background:#080d0a; color:#d9ffe0; font-family:'Segoe UI'; font-size:10pt; }
            QFrame#panel { background:#111914; border:2px solid #397c43; border-radius:16px; }
            QFrame#display { background:#050907; border:1px solid #4cff61; border-radius:9px; }
            QLabel#brand { color:#73ff7d; font-size:19pt; font-weight:900; }
            QLabel#track { color:#f1ff64; font-size:13pt; font-weight:800; }
            QPushButton { color:#eaff00; background:#1c2a20; border:1px solid #4cff61; border-radius:8px; padding:9px 13px; font-weight:bold; }
            QPushButton:hover { background:#315b38; color:white; }
            QPushButton#mainplay { color:#071009; background:#72ff79; font-size:11pt; min-width:118px; }
            QComboBox { background:#111e15; border:1px solid #4b9b55; border-radius:6px; padding:7px; }
            QSlider::groove:horizontal { height:7px; background:#263d2b; border-radius:3px; }
            QSlider::handle:horizontal { background:#75ff80; width:16px; margin:-5px 0; border-radius:8px; }
        """)
        root=QVBoxLayout(self); root.setContentsMargins(14,14,14,14)
        panel=QFrame(); panel.setObjectName("panel")
        layout=QVBoxLayout(panel); layout.setContentsMargins(16,14,16,16); layout.setSpacing(10)
        brand=QLabel("◉  OSCAM  /  CYBER STEREO  ◉"); brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(brand)
        sub=QLabel("MATRIX EDITION  •  HI-FI DIGITAL SOUND SYSTEM")
        sub.setStyleSheet("color:#83c98b;font-size:8pt;font-weight:bold;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(sub)
        deck=QHBoxLayout(); deck.setSpacing(10)
        self.left_speaker=SpeakerWidget(); self.right_speaker=SpeakerWidget()
        deck.addWidget(self.left_speaker,2)
        display=QFrame(); display.setObjectName("display")
        center=QVBoxLayout(display); center.setContentsMargins(12,12,12,12); center.setSpacing(8)
        status=QLabel("● POWER ON     ▰ DIGITAL RECEIVER")
        status.setStyleSheet("color:#83c98b;font-size:8pt;font-weight:bold;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter); center.addWidget(status)
        self.track_label=QLabel("Bereit für den nächsten Build-Sound")
        self.track_label.setObjectName("track"); self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center.addWidget(self.track_label)
        self.track_combo=QComboBox(); self.track_combo.currentIndexChanged.connect(self._selection_changed)
        center.addWidget(self.track_combo)
        self.eq_bars=[]; eq=QHBoxLayout(); eq.setSpacing(3)
        for i in range(18):
            bar=QFrame(); bar.setMinimumWidth(4); bar.setFixedHeight(30)
            bar.setStyleSheet("background:#24472b;border:1px solid #397c43;border-radius:2px;")
            self.eq_bars.append(bar); eq.addWidget(bar)
        center.addLayout(eq)
        self.progress=QSlider(Qt.Orientation.Horizontal); self.progress.setRange(0,1000)
        self.progress.sliderMoved.connect(self._seek); center.addWidget(self.progress)
        self.time_label=QLabel("00:00  /  00:00"); self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setStyleSheet("color:#83c98b;font-size:8pt;"); center.addWidget(self.time_label)
        deck.addWidget(display,5); deck.addWidget(self.right_speaker,2); layout.addLayout(deck,1)
        controls=QHBoxLayout(); self.prev_btn=QPushButton("◀◀")
        self.play_btn=QPushButton("▶  PLAY"); self.play_btn.setObjectName("mainplay")
        self.stop_btn=QPushButton("■  STOP"); self.next_btn=QPushButton("▶▶")
        self.prev_btn.clicked.connect(lambda:self._step_track(-1)); self.next_btn.clicked.connect(lambda:self._step_track(1))
        self.play_btn.clicked.connect(self._toggle_play); self.stop_btn.clicked.connect(self._stop)
        for b in (self.prev_btn,self.play_btn,self.stop_btn,self.next_btn): controls.addWidget(b)
        layout.addLayout(controls)
        volume=QHBoxLayout(); volume.addWidget(QLabel("🔊  MASTER VOLUME"))
        self.volume=QSlider(Qt.Orientation.Horizontal); self.volume.setRange(0,100)
        music_cfg=(getattr(self.host,"current_config",{}) or {}).get("music",{})
        self.volume.setValue(max(0,min(100,int(music_cfg.get("volume",20)))))
        self.volume.valueChanged.connect(self._set_volume); volume.addWidget(self.volume,1)
        self.volume_label=QLabel(f"{self.volume.value()} %"); volume.addWidget(self.volume_label)
        layout.addLayout(volume); root.addWidget(panel); self.refresh_tracks()

    def set_language(self):
        is_de = str(getattr(self.host, "LANG", "de")).lower().startswith("de")
        self.setWindowTitle("OSCam • Cyber Music Player")
        self.track_label.setText(
            "Bereit für den nächsten Build-Sound" if is_de
            else "Ready for your next build session"
        )
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
        if source is not None and index >= 0:
            self.host._save_music_state(last_track=str(source.currentData() or ""))

    def _player(self):
        return getattr(self.host, "_background_music_player", None)

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
        # Index 0 is random; next/previous cycles through the actual tracks.
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
        self.play_btn.setText(
            ("Ⅱ  PAUSE" if playing else "▶  ABSPIELEN")
            if str(getattr(self.host, "LANG", "de")).lower().startswith("de")
            else ("Ⅱ  PAUSE" if playing else "▶  PLAY")
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
        self._phase += 0.24
        button=getattr(self.host,"music_button",None)
        playing=bool(button and button.isChecked())
        level=random.uniform(.45,1.0) if playing else .08
        self.left_speaker.set_level(level,self._phase)
        self.right_speaker.set_level(level*random.uniform(.8,1.0),self._phase+1.2)
        for bar in self.eq_bars:
            height=random.randint(8,42) if playing else 8
            bar.setFixedHeight(height)
            bar.setStyleSheet("background:#72ff79;border:1px solid #397c43;border-radius:2px;" if playing else "background:#24472b;border:1px solid #397c43;border-radius:2px;")
        self._sync_state()

    def showEvent(self, event):
        self.refresh_tracks()
        self.set_language()
        super().showEvent(event)

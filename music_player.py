"""
OSCam Music Player – eigenständiges Player-Fenster für den OSCam Patch Manager.
Dieses Modul wird von der Haupt-GUI importiert; die Wiedergabe bleibt dort zentral.
"""
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QComboBox, QFrame
)


class MusicPlayerWindow(QWidget):
    def __init__(self, host, parent=None):
        super().__init__(parent or host, Qt.WindowType.Window)
        self.host = host
        self.setWindowTitle("OSCam • Cyber Music Player")
        self.setMinimumWidth(430)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._sync_state)
        self._timer.start()
        self.set_language()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background: #090d0b; color: #d8ffe0;
                font-family: 'Segoe UI'; font-size: 10pt;
            }
            QFrame#panel {
                background: #111a15; border: 1px solid #39ff55;
                border-radius: 12px;
            }
            QLabel#brand {
                color: #63ff72; font-size: 17pt; font-weight: 900;
            }
            QLabel#track {
                color: #f0ff4a; font-size: 12pt; font-weight: 700;
            }
            QPushButton {
                color: #eaff00; background: #202b24;
                border: 1px solid #39ff55; border-radius: 8px;
                padding: 8px 12px; font-weight: bold;
            }
            QPushButton:hover { background: #304b36; color: white; }
            QComboBox, QSlider {
                background: #17221b; border: 1px solid #397d43;
                border-radius: 6px; padding: 6px;
            }
            QSlider::groove:horizontal {
                height: 6px; background: #304536; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #70ff79; width: 14px; margin: -5px 0;
                border-radius: 7px;
            }
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        brand = QLabel("◉ OSCAM  /  CYBER PLAYER")
        brand.setObjectName("brand")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(brand)

        self.track_label = QLabel("Bereit für den nächsten Build-Sound")
        self.track_label.setObjectName("track")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.track_label)

        self.track_combo = QComboBox()
        self.track_combo.currentIndexChanged.connect(self._selection_changed)
        layout.addWidget(self.track_combo)

        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderMoved.connect(self._seek)
        layout.addWidget(self.progress)

        self.time_label = QLabel("00:00  /  00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        controls = QHBoxLayout()
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶  PLAY")
        self.stop_btn = QPushButton("■  STOP")
        self.next_btn = QPushButton("⏭")
        self.prev_btn.clicked.connect(lambda: self._step_track(-1))
        self.next_btn.clicked.connect(lambda: self._step_track(1))
        self.play_btn.clicked.connect(self._toggle_play)
        self.stop_btn.clicked.connect(self._stop)
        for button in (self.prev_btn, self.play_btn, self.stop_btn, self.next_btn):
            controls.addWidget(button)
        layout.addLayout(controls)

        volume_row = QHBoxLayout()
        volume_row.addWidget(QLabel("🔊"))
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(20)
        self.volume.valueChanged.connect(self._set_volume)
        volume_row.addWidget(self.volume, 1)
        self.volume_label = QLabel("20 %")
        volume_row.addWidget(self.volume_label)
        layout.addLayout(volume_row)

        root.addWidget(panel)
        self.refresh_tracks()

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
        self.track_combo.blockSignals(True)
        self.track_combo.clear()
        if source is not None:
            for i in range(source.count()):
                self.track_combo.addItem(source.itemText(i), source.itemData(i))
            self.track_combo.setCurrentIndex(max(0, source.currentIndex()))
        self.track_combo.blockSignals(False)

    def _selection_changed(self, index):
        source = getattr(self.host, "music_title_combo", None)
        if source is not None and index >= 0:
            source.setCurrentIndex(index)
        self._sync_state()

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

    def showEvent(self, event):
        self.refresh_tracks()
        self.set_language()
        super().showEvent(event)

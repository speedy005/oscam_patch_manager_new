"""Live system dashboard for OSCam Patch Manager."""

import platform
import psutil

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QGroupBox, QLabel,
    QProgressBar, QVBoxLayout
)


class SystemDashboardDialog(QDialog):

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)

        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self.last_net = psutil.net_io_counters()

        self.setWindowTitle(self.tr("Live-System-Dashboard", "Live System Dashboard"))
        self.resize(760, 520)
        self.setMinimumSize(650, 440)

        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.refresh_data)

        self.build_ui()
        self.apply_theme()
        self.refresh_data()
        self.timer.start()

    def tr(self, de, en):
        return de if self.language == "de" else en

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        title = QLabel(self.tr("SYSTEMÜBERWACHUNG", "SYSTEM MONITOR"))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        root.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)
        root.addLayout(grid)

        self.cpu = self.add_meter(grid, 0, 0, self.tr("Prozessor", "Processor"))
        self.ram = self.add_meter(grid, 0, 1, self.tr("Arbeitsspeicher", "Memory"))
        self.disk = self.add_meter(grid, 1, 0, self.tr("Systemlaufwerk", "System disk"))

        network = QGroupBox(self.tr("Netzwerk", "Network"))
        network_layout = QVBoxLayout(network)
        self.download = QLabel("↓ 0 B/s")
        self.upload = QLabel("↑ 0 B/s")
        self.download.setStyleSheet("font-size: 17px; font-weight: bold;")
        self.upload.setStyleSheet("font-size: 17px; font-weight: bold;")
        network_layout.addWidget(self.download)
        network_layout.addWidget(self.upload)
        grid.addWidget(network, 1, 1)

        details = QGroupBox(self.tr("Systeminformationen", "System information"))
        details_layout = QVBoxLayout(details)
        self.temperature = QLabel()
        self.platform = QLabel(f"{platform.system()} {platform.release()}")
        details_layout.addWidget(self.temperature)
        details_layout.addWidget(self.platform)
        root.addWidget(details)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.status)

    def add_meter(self, grid, row, column, title):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)

        value = QLabel("0 %")
        value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value.setStyleSheet("font-size: 23px; font-weight: bold;")

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(False)
        bar.setMinimumHeight(18)

        layout.addWidget(value)
        layout.addWidget(bar)
        grid.addWidget(box, row, column)

        return value, bar

    @staticmethod
    def set_meter(meter, value):
        label, bar = meter
        bar.setValue(max(0, min(100, round(value))))
        label.setText(f"{value:.1f} %")

    @staticmethod
    def format_rate(value):
        for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
            if value < 1024 or unit == "GB/s":
                return f"{value:.1f} {unit}"
            value /= 1024

    def read_temperature(self):
        try:
            sensors = psutil.sensors_temperatures() or {}
            values = [
                item.current
                for entries in sensors.values()
                for item in entries
                if item.current is not None
            ]
            if values:
                return f"{self.tr('Temperatur', 'Temperature')}: {max(values):.1f} °C"
        except (AttributeError, OSError, NotImplementedError):
            pass

        return self.tr(
            "Temperatur: Sensor nicht verfügbar",
            "Temperature: sensor unavailable"
        )

    def refresh_data(self):
        try:
            self.set_meter(self.cpu, psutil.cpu_percent())
            self.set_meter(self.ram, psutil.virtual_memory().percent)
            self.set_meter(self.disk, psutil.disk_usage("/").percent)

            current = psutil.net_io_counters()
            elapsed = 2.0

            down = max(0, current.bytes_recv - self.last_net.bytes_recv) / elapsed
            up = max(0, current.bytes_sent - self.last_net.bytes_sent) / elapsed
            self.last_net = current

            self.download.setText(f"↓ {self.format_rate(down)}")
            self.upload.setText(f"↑ {self.format_rate(up)}")
            self.temperature.setText(self.read_temperature())

            self.status.setText(self.tr(
                "Live-Aktualisierung alle 2 Sekunden",
                "Live refresh every 2 seconds"
            ))
        except (OSError, RuntimeError) as exc:
            self.status.setText(
                self.tr(f"Fehler: {exc}", f"Error: {exc}")
            )

    def apply_theme(self):
        bg = self.colors.get("bg", "#1D1D1D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        window_bg = self.colors.get("window_bg", "#2F2F2F")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {fg}; }}
            QLabel {{ color: {fg}; background: transparent; }}
            QGroupBox {{
                color: {fg};
                border: 1px solid {hover};
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }}
            QProgressBar {{
                border: 1px solid {hover};
                border-radius: 6px;
                background: {bg};
            }}
            QProgressBar::chunk {{
                background: {hover};
                border-radius: 5px;
            }}
        """)

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

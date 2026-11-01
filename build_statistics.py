"""Read-only build statistics for OSCam Patch Manager."""

import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame,
)


class BuildStatisticsDialog(QDialog):
    SUCCESS = "success"
    FAILED = "failed"
    INCOMPLETE = "incomplete"

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)
        self.is_de = str(language).lower().startswith("de")
        self.colors = colors or {}
        self.log_dir = Path(__file__).resolve().parent / "build_logs"
        self.records = []

        self.setWindowTitle(self.tr("Build-Statistik", "Build statistics"))
        self.resize(1050, 680)
        self.setMinimumSize(760, 500)

        self._build_ui()
        self._apply_theme()
        self.refresh_statistics()

    def tr(self, de, en):
        return de if self.is_de else en

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(self.tr(
            "BUILD-STATISTIK – Übersicht und Verlauf",
            "BUILD STATISTICS – Overview and history"
        ))
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(self.tr(
            "Leseansicht der vorhandenen Build-Logs. Es werden keine Builds gestartet oder Logs verändert.",
            "Read-only view of existing build logs. No builds are started or logs modified."
        ))
        description.setWordWrap(True)
        layout.addWidget(description)

        grid = QGridLayout()
        grid.setSpacing(10)
        self.stat_labels = {}

        definitions = [
            ("total", "Gesamt", "Total"),
            ("success", "Erfolgreich", "Successful"),
            ("failed", "Fehlgeschlagen", "Failed"),
            ("incomplete", "Unvollständig", "Incomplete"),
            ("rate", "Erfolgsquote", "Success rate"),
        ]

        for index, (key, de, en) in enumerate(definitions):
            frame = QFrame()
            frame.setObjectName("statCard")
            card = QVBoxLayout(frame)
            card.setContentsMargins(12, 9, 12, 9)

            caption = QLabel(self.tr(de, en))
            value = QLabel("–")
            value.setStyleSheet("font-size: 23px; font-weight: bold;")

            card.addWidget(caption)
            card.addWidget(value)
            grid.addWidget(frame, 0, index)
            self.stat_labels[key] = value

        layout.addLayout(grid)

        controls = QHBoxLayout()
        controls.addWidget(QLabel(self.tr("Variante:", "Variant:")))

        self.variant_combo = QComboBox()
        self.variant_combo.addItem(self.tr("Alle", "All"), "all")
        self.variant_combo.addItem("S3", "s3")
        self.variant_combo.addItem("S4", "s4")
        self.variant_combo.addItem("NCAM", "ncam")
        self.variant_combo.currentIndexChanged.connect(self._render)
        controls.addWidget(self.variant_combo)
        controls.addStretch(1)

        refresh = QPushButton(self.tr("Aktualisieren", "Refresh"))
        refresh.clicked.connect(self.refresh_statistics)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self.tr("Datum / Start", "Date / start"),
            self.tr("Variante", "Variant"),
            self.tr("Ergebnis", "Result"),
            self.tr("Log-Sitzung", "Log session"),
            self.tr("Logdatei", "Log file"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.verticalHeader().setVisible(False)

        header = self.table.horizontalHeader()
        for column in range(4):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel()
        footer.addWidget(self.status_label, 1)

        close = QPushButton(self.tr("Schließen", "Close"))
        close.clicked.connect(self.close)
        footer.addWidget(close)
        layout.addLayout(footer)

    def _apply_theme(self):
        bg = self.colors.get(
            "window_bg", self.colors.get("bg", "#20242b")
        )
        panel = self.colors.get("bg", bg)
        fg = self.colors.get("fg", "#eeeeee")
        hover = self.colors.get("hover", "#3b4655")
        active = self.colors.get("active", "#52657a")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {fg}; }}
            QLabel {{ color: {fg}; }}
            QFrame#statCard {{
                background-color: {panel};
                border: 1px solid {hover};
                border-radius: 7px;
            }}
            QComboBox, QTableWidget {{
                background-color: {panel};
                color: {fg};
                border: 1px solid {hover};
                border-radius: 5px;
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {hover};
                color: {fg};
                padding: 6px;
                border: 1px solid {active};
            }}
            QPushButton {{
                background-color: {hover};
                color: {fg};
                border: 1px solid {active};
                border-radius: 5px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{ background-color: {active}; }}
        """)

    @staticmethod
    def _variant(filename):
        name = filename.lower()
        if name.startswith("ncam"):
            return "NCAM"
        if name.startswith("s4"):
            return "S4"
        if name.startswith("s3"):
            return "S3"
        return "Other"

    @staticmethod
    def _duration(seconds):
        if seconds is None:
            return "–"
        minutes, secs = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours} h {minutes:02d} min"
        if minutes:
            return f"{minutes} min {secs} s"
        return f"{secs} s"

    def _read_log(self, path):
        try:
            content = path.read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            content = ""

        start = None
        match = re.search(r"(?m)^Start:\s*(\S+)", content)
        if match:
            try:
                start = datetime.fromisoformat(match.group(1))
            except ValueError:
                pass

        end = None
        match = re.search(
            r"(?m)^Script done on "
            r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2})",
            content
        )
        if match:
            try:
                end = datetime.strptime(
                    match.group(1), "%Y-%m-%d %H:%M:%S%z"
                )
            except ValueError:
                pass

        duration = None
        if start and end:
            try:
                seconds = int((end - start).total_seconds())
                if seconds >= 0:
                    duration = seconds
            except TypeError:
                pass

        finish = re.search(
            r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", content
        )

        if finish:
            status = (
                self.SUCCESS if int(finish.group(1)) == 0
                else self.FAILED
            )
        elif "numeric argument required" in content:
            status = self.FAILED
        elif re.search(
            r"SIMPLEBUILD_FINISHED:exit=\s*(?:\r?$)",
            content, re.M
        ):
            status = self.FAILED
        else:
            # The outer terminal exit code alone is not a build result.
            status = self.INCOMPLETE

        return {
            "filename": path.name,
            "variant": self._variant(path.name),
            "start": start,
            "duration": duration,
            "status": status,
        }

    def refresh_statistics(self):
        self.records = []

        if self.log_dir.is_dir():
            for path in self.log_dir.glob("*.log"):
                self.records.append(self._read_log(path))

        self.records.sort(
            key=lambda item: item["start"] or datetime.min,
            reverse=True
        )
        self._render()

    def _render(self, *_):
        selected = self.variant_combo.currentData()
        records = [
            item for item in self.records
            if selected == "all"
            or item["variant"].lower() == selected
        ]

        counts = {
            status: sum(item["status"] == status for item in records)
            for status in (
                self.SUCCESS, self.FAILED, self.INCOMPLETE
            )
        }

        completed = counts[self.SUCCESS] + counts[self.FAILED]
        rate = (
            f"{counts[self.SUCCESS] / completed * 100:.1f}%"
            if completed else "–"
        )

        self.stat_labels["total"].setText(str(len(records)))
        self.stat_labels["success"].setText(str(counts[self.SUCCESS]))
        self.stat_labels["failed"].setText(str(counts[self.FAILED]))
        self.stat_labels["incomplete"].setText(
            str(counts[self.INCOMPLETE])
        )
        self.stat_labels["rate"].setText(rate)

        labels = {
            self.SUCCESS: self.tr("Erfolgreich", "Successful"),
            self.FAILED: self.tr("Fehlgeschlagen", "Failed"),
            self.INCOMPLETE: self.tr("Unvollständig", "Incomplete"),
        }

        self.table.setRowCount(len(records))

        for row, record in enumerate(records):
            start = record["start"]
            date_text = (
                start.astimezone().strftime("%d.%m.%Y %H:%M:%S")
                if start else "–"
            )

            values = [
                date_text,
                record["variant"],
                labels[record["status"]],
                self._duration(record["duration"]),
                record["filename"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 2:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                    )
                self.table.setItem(row, column, item)

        self.status_label.setText(self.tr(
            f"{len(records)} Logdateien | Laufzeit = Log-Sitzungsdauer, "
            "nicht zwingend reine Build-Zeit",
            f"{len(records)} log files | Duration = log session time, "
            "not necessarily pure build time"
        ))

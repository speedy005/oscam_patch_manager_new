"""Animated Cyber Terminal for OSCam Patch Manager."""

import random
import psutil

from datetime import datetime
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton
)


class CyberTerminalDialog(QDialog):

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)

        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self.running = True
        self.message_index = 0

        self.messages = [
            ("SYSTEM", "Systemüberwachung initialisiert", "System monitoring initialized"),
            ("CPU", "Prozessorstatus wird geprüft", "Checking processor status"),
            ("MEMORY", "Arbeitsspeicher wird analysiert", "Analyzing memory"),
            ("NETWORK", "Netzwerkstatus wird aktualisiert", "Updating network status"),
            ("SCAN", "Simulierter Cyber-Scan gestartet", "Simulated cyber scan started"),
            ("SCAN", "Simulierter Scan: lokale Statusprüfung", "Simulated scan: local status check"),
            ("SECURITY", "Keine externe Verbindung aufgebaut", "No external connection established"),
            ("SYSTEM", "System läuft ordnungsgemäß", "System operating normally"),
            ("SCAN", "Simulierter Scan abgeschlossen", "Simulated scan completed"),
        ]

        self.setWindowTitle(self.tr("Cyber-Terminal", "Cyber Terminal"))
        self.resize(850, 570)
        self.setMinimumSize(650, 420)

        self.build_ui()
        self.apply_theme()

        self.timer = QTimer(self)
        self.timer.setInterval(1100)
        self.timer.timeout.connect(self.add_event)
        self.timer.start()

        self.add_line("BOOT", "Cyber Terminal gestartet", "Cyber Terminal started")

    def tr(self, de, en):
        return de if self.language == "de" else en

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        title = QLabel(self.tr("CYBER-TERMINAL", "CYBER TERMINAL"))
        title.setStyleSheet("font-size: 23px; font-weight: bold;")
        root.addWidget(title)

        self.status = QLabel()
        root.addWidget(self.status)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.output.setFontFamily("Consolas")
        self.output.setStyleSheet("font-size: 12px;")
        root.addWidget(self.output, 1)

        buttons = QHBoxLayout()

        self.pause_button = QPushButton(self.tr("PAUSE", "PAUSE"))
        self.pause_button.clicked.connect(self.toggle_running)

        clear_button = QPushButton(self.tr("LEEREN", "CLEAR"))
        clear_button.clicked.connect(self.output.clear)

        close_button = QPushButton(self.tr("SCHLIESSEN", "CLOSE"))
        close_button.clicked.connect(self.close)

        buttons.addWidget(self.pause_button)
        buttons.addWidget(clear_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        root.addLayout(buttons)

        self.update_status()

    def apply_theme(self):
        bg = self.colors.get("bg", "#101810")
        fg = self.colors.get("fg", "#39FF14")
        hover = self.colors.get("hover", "#00FF41")
        window_bg = self.colors.get("window_bg", "#1A241A")

        self.terminal_bg = bg
        self.terminal_fg = fg
        self.terminal_hover = hover

        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {fg}; }}
            QLabel {{ color: {fg}; }}
            QTextEdit {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {hover};
                border-radius: 7px;
                padding: 8px;
            }}
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {hover};
                border-radius: 6px;
                padding: 7px 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover};
                color: {bg};
            }}
        """)

    def update_status(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        state = self.tr("AKTIV", "ACTIVE") if self.running else self.tr("PAUSIERT", "PAUSED")

        self.status.setText(
            f"● {state}   |   CPU: {cpu:.1f}%   |   RAM: {ram:.1f}%"
        )

    def add_line(self, category, german, english):
        message = german if self.language == "de" else english
        timestamp = datetime.now().strftime("%H:%M:%S")

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        category_format = QTextCharFormat()
        category_format.setForeground(QColor(self.terminal_hover))
        category_format.setFontWeight(700)

        message_format = QTextCharFormat()
        message_format.setForeground(QColor(self.terminal_fg))

        cursor.insertText(f"[{timestamp}] ", message_format)
        cursor.insertText(f"[{category:<8}] ", category_format)
        cursor.insertText(message + "\n", message_format)

        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

        if self.output.document().blockCount() > 400:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

    def add_event(self):
        category, german, english = self.messages[
            self.message_index % len(self.messages)
        ]
        self.message_index += 1

        self.add_line(category, german, english)
        self.update_status()

    def toggle_running(self):
        self.running = not self.running

        if self.running:
            self.timer.start()
            self.pause_button.setText(self.tr("PAUSE", "PAUSE"))
            self.add_line("SYSTEM", "Terminal fortgesetzt", "Terminal resumed")
        else:
            self.timer.stop()
            self.pause_button.setText(self.tr("FORTSETZEN", "RESUME"))
            self.add_line("SYSTEM", "Terminal pausiert", "Terminal paused")

        self.update_status()

    def closeEvent(self, event):
        self.timer.stop()
        super().closeEvent(event)

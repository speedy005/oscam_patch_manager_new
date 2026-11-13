"""Central OSCam Control Center window for OSCam Patch Manager."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt


class CyberCenterDialog(QDialog):
    """Central launcher for the OSCam Control Center modules."""

    MODULES = [
        ("dashboard", "Live-System-Dashboard", "Live system dashboard",
         "CPU, RAM, Festplatte und Netzwerk", "CPU, RAM, disk and network"),
        ("terminal", "Cyber-Terminal", "Cyber terminal",
         "Animierte Systemmeldungen und Status", "Animated system messages and status"),
        ("timemachine", "Update-Zeitmaschine", "Update time machine",
         "Update-Verlauf und Wiederherstellung", "Update history and restore"),
        ("statistics", "Build-Statistik", "Build statistics",
         "Erfolge, Fehler und Build-Zeiten", "Successes, errors and build times"),
        ("notifications", "Smart-Benachrichtigungen", "Smart notifications",
         "Hinweise zu Updates und neuen Commits", "Notices about updates and new commits"),
        ("backup", "Backup-Explorer", "Backup explorer",
         "Backups durchsuchen und wiederherstellen", "Browse and restore backups"),
        ("startup", "Premium-Startanimation", "Premium startup animation",
         "Animierter Systemstart und Systemcheck", "Animated startup and system check"),
        ("compatibility", "Patch-Kompatibilitätsprüfung", "Patch Compatibility Scanner",
         "Patches auf doppelte Änderungen und Konflikte prüfen", "Check patches for duplicate changes and conflicts"),
        ("radar", "Patch Radar – Ampelsystem", "Patch Radar – Traffic Lights",
         "Patch-Varianten automatisch auf Konflikte prüfen", "Automatically scan patch variants for conflicts"),
    ]

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)

        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}

        self.setWindowTitle("OSCam Control Center")
        self.setMinimumSize(760, 540)
        self.resize(900, 620)

        self._build_ui()
        self._apply_theme()

    def _tr(self, german, english):
        return german if self.language == "de" else english

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        title = QLabel("OSCAM CONTROL CENTER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 25px; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel(self._tr(
            "Deine zentrale Kommandozentrale",
            "Your central command center"
        ))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 13px;")
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(14)

        self.module_buttons = {}

        for index, module in enumerate(self.MODULES):
            key, de_title, en_title, de_desc, en_desc = module

            card = QFrame()
            card.setObjectName("cyberCard")
            card.setToolTip(self._tr(
                f"{de_title}\\n{de_desc}",
                f"{en_title}\\n{en_desc}"
            ))

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 14, 14, 14)
            card_layout.setSpacing(9)

            heading = QLabel(self._tr(de_title, en_title))
            heading.setWordWrap(True)
            heading.setStyleSheet("font-size: 15px; font-weight: bold;")

            description = QLabel(self._tr(de_desc, en_desc))
            description.setWordWrap(True)
            description.setStyleSheet("font-size: 12px;")

            button = QPushButton(self._tr("Modul öffnen", "Open module"))
            button.setObjectName("moduleButton")
            button.setMinimumHeight(34)
            button.setToolTip(self._tr(
                f"{de_title} öffnen – {de_desc}",
                f"Open {en_title} – {en_desc}"
            ))
            button.clicked.connect(
                lambda checked=False, module_key=key:
                self._open_module(module_key)
            )

            card_layout.addWidget(heading)
            card_layout.addWidget(description)
            card_layout.addStretch(1)
            card_layout.addWidget(button)

            grid.addWidget(card, index // 2, index % 2)
            self.module_buttons[key] = button

        layout.addLayout(grid, 1)

        footer = QLabel(self._tr(
            "Alle neun Module sind direkt über diese Zentrale erreichbar.",
            "All nine modules are available directly from this control center."
        ))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)
        layout.addWidget(footer)

        close_button = QPushButton(self._tr("Schließen", "Close"))
        close_button.setObjectName("closeButton")
        close_button.setMinimumHeight(34)
        close_button.setToolTip(self._tr(
            "OSCam Control Center schließen",
            "Close OSCam Control Center"
        ))
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

    def _apply_theme(self):
        bg = self.colors.get("bg", "#1D1D1D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        active = self.colors.get("active", "#000000")
        window_bg = self.colors.get("window_bg", "#2F2F2F")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {window_bg};
                color: {fg};
            }}
            QLabel {{
                color: {fg};
                background: transparent;
            }}
            QFrame#cyberCard {{
                background-color: {bg};
                border: 1px solid {hover};
                border-radius: 10px;
            }}
            QFrame#cyberCard:hover {{
                background-color: {window_bg};
                border: 2px solid {fg};
            }}
            QPushButton {{
                color: {fg};
                background-color: {bg};
                border: 1px solid {hover};
                border-radius: 7px;
                padding: 6px 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: {active};
                background-color: {hover};
            }}
            QPushButton:pressed {{
                background-color: {active};
                color: {fg};
                border: 2px solid {fg};
            }}
            QToolTip {{
                color: {fg};
                background-color: {bg};
                border: 1px solid {hover};
                padding: 7px 9px;
                border-radius: 5px;
                font-size: 10pt;
            }}
        """)

    def _open_module(self, module_key):
        if module_key == "radar":
            from patch_radar import PatchRadarDialog

            if not hasattr(self, "_patch_radar_window") or self._patch_radar_window is None:
                self._patch_radar_window = PatchRadarDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._patch_radar_window.refresh_scan()
            self._patch_radar_window.show()
            self._patch_radar_window.raise_()
            self._patch_radar_window.activateWindow()
            return

        if module_key == "compatibility":
            from patch_compatibility_scanner import PatchCompatibilityDialog

            if not hasattr(self, "_compatibility_window") or self._compatibility_window is None:
                self._compatibility_window = PatchCompatibilityDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._compatibility_window.show()
            self._compatibility_window.raise_()
            self._compatibility_window.activateWindow()
            return
        if module_key == "startup":
            from startup_settings import StartupSettingsDialog

            dialog = StartupSettingsDialog(
                self,
                language=self.language,
                colors=self.colors,
            )
            dialog.exec()
            return

        if module_key == "dashboard":
            from system_dashboard import SystemDashboardDialog

            if not hasattr(self, "_dashboard_window") or self._dashboard_window is None:
                self._dashboard_window = SystemDashboardDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._dashboard_window.show()
            self._dashboard_window.raise_()
            self._dashboard_window.activateWindow()
            return

        if module_key == "terminal":
            from cyber_terminal import CyberTerminalDialog

            if not hasattr(self, "_terminal_window") or self._terminal_window is None:
                self._terminal_window = CyberTerminalDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._terminal_window.show()
            self._terminal_window.raise_()
            self._terminal_window.activateWindow()
            return

        if module_key == "timemachine":
            from update_timemachine import UpdateTimeMachineDialog

            if not hasattr(self, "_timemachine_window") or self._timemachine_window is None:
                self._timemachine_window = UpdateTimeMachineDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._timemachine_window.show()
            self._timemachine_window.raise_()
            self._timemachine_window.activateWindow()
            return

        if module_key == "backup":
            from backup_explorer import BackupExplorerDialog

            if not hasattr(self, "_backup_explorer_window") or self._backup_explorer_window is None:
                self._backup_explorer_window = BackupExplorerDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._backup_explorer_window.refresh_backups()
            self._backup_explorer_window.show()
            self._backup_explorer_window.raise_()
            self._backup_explorer_window.activateWindow()
            return

        if module_key == "notifications":
            from smart_notifications import SmartNotificationsDialog

            if not hasattr(self, "_notifications_window") or self._notifications_window is None:
                self._notifications_window = SmartNotificationsDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._notifications_window.refresh_notifications()
            self._notifications_window.show()
            self._notifications_window.raise_()
            self._notifications_window.activateWindow()
            return

        if module_key == "statistics":
            from build_statistics import BuildStatisticsDialog

            if not hasattr(self, "_statistics_window") or self._statistics_window is None:
                self._statistics_window = BuildStatisticsDialog(
                    self,
                    language=self.language,
                    colors=self.colors,
                )

            self._statistics_window.refresh_statistics()
            self._statistics_window.show()
            self._statistics_window.raise_()
            self._statistics_window.activateWindow()
            return

        titles = {
            key: self._tr(de_title, en_title)
            for key, de_title, en_title, _, _ in self.MODULES
        }
        QMessageBox.information(
            self,
            "OSCam Control Center",
            self._tr(
                f"Das Modul „{titles[module_key]}“ wird in einem der nächsten Schritte integriert.",
                f"The module “{titles[module_key]}” will be integrated in a later step."
            )
        )

"""Central OSCam Control Center window for OSCam Patch Manager."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QLabel, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QSettings, QTimer
from pathlib import Path
import os
import psutil


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
        self.setMinimumSize(900, 680)
        self.resize(1120, 820)

        # Restore the last OSCam Control Center window size.
        self.settings = QSettings(
            "OSCamPatchManager", "OSCamPatchManager"
        )
        saved_size = self.settings.value("cyber_center/window_size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            if saved_size.width() >= 760 and saved_size.height() >= 540:
                self.resize(saved_size)

        self._build_ui()
        self._apply_theme()

        self._system_timer = QTimer(self)
        self._system_timer.timeout.connect(self._refresh_system_tile)
        self._system_timer.start(2000)

        self._scan_timer = QTimer(self)
        self._scan_timer.timeout.connect(self._refresh_scan_tiles)
        self._scan_timer.start(30000)

        self._refresh_system_tile()
        self._refresh_scan_tiles()

    def _tr(self, german, english):
        return german if self.language == "de" else english

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        header.setSpacing(12)

        brand = QVBoxLayout()
        brand.setSpacing(4)

        title = QLabel("OSCAM CONTROL CENTER")
        title.setObjectName("mainTitle")
        title.setStyleSheet("font-size: 32px; font-weight: 900; letter-spacing: 2px;")

        subtitle = QLabel(self._tr(
            "CYBER OPERATIONS  •  DEINE ZENTRALE KOMMANDOZENTRALE",
            "CYBER OPERATIONS  •  YOUR CENTRAL COMMAND CENTER"
        ))
        subtitle.setObjectName("subtitle")

        brand.addWidget(title)
        brand.addWidget(subtitle)
        header.addLayout(brand)
        header.addStretch(1)

        module_count = QLabel("09 MODULE")
        module_count.setObjectName("moduleCount")
        module_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(module_count)

        layout.addLayout(header)

        separator = QFrame()
        separator.setObjectName("cyberSeparator")
        separator.setFixedHeight(2)
        layout.addWidget(separator)

        # Overview tiles – descriptive categories, no fabricated live values.
        overview = QGridLayout()
        overview.setSpacing(12)

        overview_items = [
            ("system", self._tr("SYSTEMÜBERSICHT", "SYSTEM OVERVIEW"), "01"),
            ("patches", self._tr("PATCH-MANAGEMENT", "PATCH MANAGEMENT"), "02"),
            ("backups", self._tr("SICHERUNG", "BACKUP & RESTORE"), "03"),
            ("builds", self._tr("AUSWERTUNG", "ANALYTICS"), "04"),
        ]

        self.overview_values = {}
        self.overview_details = {}

        for index, (key, heading_text, number) in enumerate(overview_items):
            tile = QFrame()
            tile.setObjectName("infoCard")

            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(14, 12, 14, 12)
            tile_layout.setSpacing(5)

            number_label = QLabel(number)
            number_label.setObjectName("infoNumber")

            heading = QLabel(heading_text)
            heading.setObjectName("infoHeading")
            heading.setWordWrap(True)

            value = QLabel("—")
            value.setObjectName("infoValue")
            value.setWordWrap(True)

            detail = QLabel(self._tr("Daten werden geladen …", "Loading data …"))
            detail.setObjectName("infoDescription")
            detail.setWordWrap(True)

            tile_layout.addWidget(number_label)
            tile_layout.addWidget(heading)
            tile_layout.addWidget(value)
            tile_layout.addWidget(detail)

            self.overview_values[key] = value
            self.overview_details[key] = detail
            overview.addWidget(tile, 0, index)

        layout.addLayout(overview)

        section_header = QHBoxLayout()

        section_title = QLabel(self._tr(
            "MODULE & FUNKTIONEN",
            "MODULES & FEATURES"
        ))
        section_title.setObjectName("sectionTitle")

        section_hint = QLabel(self._tr(
            "Wähle ein Modul zum Öffnen",
            "Select a module to open"
        ))
        section_hint.setObjectName("sectionHint")

        section_header.addWidget(section_title)
        section_header.addStretch(1)
        section_header.addWidget(section_hint)
        layout.addLayout(section_header)

        # Module cards
        grid = QGridLayout()
        grid.setSpacing(14)

        self.module_buttons = {}

        for index, module in enumerate(self.MODULES):
            key, de_title, en_title, de_desc, en_desc = module

            card = QFrame()
            card.setObjectName("cyberCard")
            card.setMinimumHeight(158)
            card.setToolTip(self._tr(
                f"{de_title}\n{de_desc}",
                f"{en_title}\n{en_desc}"
            ))

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 13, 16, 14)
            card_layout.setSpacing(8)

            top_row = QHBoxLayout()

            number = QLabel(f"{index + 1:02d}")
            number.setObjectName("cardNumber")

            category = QLabel(self._tr("OSCAM MODULE", "OSCAM MODULE"))
            category.setObjectName("cardCategory")

            top_row.addWidget(number)
            top_row.addStretch(1)
            top_row.addWidget(category)

            heading = QLabel(self._tr(de_title, en_title))
            heading.setObjectName("cardHeading")
            heading.setWordWrap(True)

            description = QLabel(self._tr(de_desc, en_desc))
            description.setObjectName("cardDescription")
            description.setWordWrap(True)

            button = QPushButton(self._tr(
                "MODUL ÖFFNEN  →",
                "OPEN MODULE  →"
            ))
            button.setObjectName("moduleButton")
            button.setMinimumHeight(36)
            button.setToolTip(self._tr(
                f"{de_title} öffnen – {de_desc}",
                f"Open {en_title} – {en_desc}"
            ))
            button.clicked.connect(
                lambda checked=False, module_key=key:
                self._open_module(module_key)
            )

            card_layout.addLayout(top_row)
            card_layout.addWidget(heading)
            card_layout.addWidget(description)
            card_layout.addStretch(1)
            card_layout.addWidget(button)

            grid.addWidget(card, index // 3, index % 3)
            self.module_buttons[key] = button

        layout.addLayout(grid, 1)

        footer_row = QHBoxLayout()

        footer = QLabel(self._tr(
            "OSCam Patch Manager  •  Alle neun Module an einem Ort",
            "OSCam Patch Manager  •  All nine modules in one place"
        ))
        footer.setObjectName("footerLabel")

        close_button = QPushButton(self._tr("SCHLIESSEN", "CLOSE"))
        close_button.setObjectName("closeButton")
        close_button.setMinimumSize(130, 38)
        close_button.setToolTip(self._tr(
            "OSCam Control Center schließen",
            "Close OSCam Control Center"
        ))
        close_button.clicked.connect(self.close)

        footer_row.addWidget(footer)
        footer_row.addStretch(1)
        footer_row.addWidget(close_button)
        layout.addLayout(footer_row)

    def _apply_theme(self):
        bg = self.colors.get("bg", "#14201D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        active = self.colors.get("active", "#101815")
        window_bg = self.colors.get("window_bg", "#0D1513")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {window_bg};
                color: {fg};
            }}

            QLabel {{
                color: {fg};
                background: transparent;
            }}

            QLabel#mainTitle {{
                color: {fg};
                font-size: 27px;
                font-weight: 900;
                letter-spacing: 2px;
            }}

            QLabel#subtitle {{
                color: #8DA69A;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }}

            QLabel#moduleCount {{
                color: {fg};
                background-color: {bg};
                border: 1px solid {hover};
                border-radius: 8px;
                padding: 11px 16px;
                font-size: 12px;
                font-weight: bold;
            }}

            QFrame#cyberSeparator {{
                background-color: {hover};
                border: none;
                max-height: 2px;
            }}

            QFrame#infoCard {{
                background-color: #17231F;
                border: 1px solid #30443A;
                border-radius: 9px;
            }}

            QFrame#infoCard:hover {{
                border: 1px solid {hover};
                background-color: #1B2B24;
            }}

            QLabel#infoNumber {{
                color: {hover};
                font-size: 10px;
                font-weight: bold;
            }}

            QLabel#infoHeading {{
                color: {fg};
                font-size: 11px;
                font-weight: 900;
            }}

            QLabel#infoValue {{
                color: {hover};
                font-size: 21px;
                font-weight: 900;
            }}

            QLabel#infoDescription {{
                color: #9CB0A4;
                font-size: 10px;
            }}

            QLabel#sectionTitle {{
                color: {fg};
                font-size: 14px;
                font-weight: 900;
                letter-spacing: 1px;
            }}

            QLabel#sectionHint {{
                color: #81968A;
                font-size: 10px;
            }}

            QFrame#cyberCard {{
                background-color: {bg};
                border: 1px solid #30443A;
                border-radius: 10px;
            }}

            QFrame#cyberCard:hover {{
                background-color: #1B2B24;
                border: 1px solid {hover};
            }}

            QLabel#cardNumber {{
                color: {hover};
                font-size: 19px;
                font-weight: 900;
            }}

            QLabel#cardCategory {{
                color: #81968A;
                font-size: 9px;
                font-weight: bold;
                letter-spacing: 1px;
            }}

            QLabel#cardHeading {{
                color: {fg};
                font-size: 14px;
                font-weight: 900;
            }}

            QLabel#cardDescription {{
                color: #A7B8AE;
                font-size: 10px;
            }}

            QPushButton {{
                color: {fg};
                background-color: #1B2B24;
                border: 1px solid #526B5B;
                border-radius: 7px;
                padding: 7px 11px;
                font-size: 10px;
                font-weight: bold;
            }}

            QPushButton#moduleButton {{
                text-align: left;
                padding-left: 12px;
            }}

            QPushButton:hover {{
                color: {active};
                background-color: {hover};
                border: 1px solid {hover};
            }}

            QPushButton:pressed {{
                background-color: {active};
                color: {fg};
                border: 2px solid {fg};
            }}

            QPushButton#closeButton {{
                background-color: transparent;
                border: 1px solid #526B5B;
            }}

            QLabel#footerLabel {{
                color: #81968A;
                font-size: 10px;
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

    def _refresh_system_tile(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory().percent
            self.overview_values["system"].setText(
                f"CPU {cpu:.0f}%  |  RAM {ram:.0f}%"
            )
            self.overview_details["system"].setText(
                self._tr("Live-Auslastung", "Live utilization")
            )
        except Exception as exc:
            self.overview_values["system"].setText("—")
            self.overview_details["system"].setText(str(exc))

    def _refresh_scan_tiles(self):
        root = Path(__file__).resolve().parent

        # Patch-Auswertung mit derselben Logik wie Patch Radar.
        try:
            from itertools import combinations
            from patch_compatibility_scanner import _parse_patch, _overlap

            variants = [
                ("S3", "s3/support/patches"),
                ("S3 Speedy005", "s3_speedy005/support/patches"),
                ("NCam Bonecrew", "s3_ncam_bonecrew/support/patches"),
                ("S4", "s4/data/patches"),
            ]
            parsed = []
            patch_total = 0
            patch_errors = 0

            for variant, relative in variants:
                folder = root / relative
                if not folder.is_dir():
                    patch_errors += 1
                    continue
                try:
                    files = sorted(
                        item for item in folder.iterdir()
                        if item.is_file()
                        and item.suffix.lower() in (".patch", ".diff")
                    )
                except OSError:
                    patch_errors += 1
                    continue

                patch_total += len(files)
                for path in files:
                    try:
                        parsed.append({
                            "variant": variant,
                            "entries": _parse_patch(path),
                        })
                    except Exception:
                        patch_errors += 1

            conflicts = 0
            duplicates = 0
            for first, second in combinations(parsed, 2):
                if first["variant"] == second["variant"]:
                    continue
                for file_a in first["entries"]:
                    for file_b in second["entries"]:
                        if file_a["path"] != file_b["path"]:
                            continue
                        for hunk_a in file_a["hunks"]:
                            for hunk_b in file_b["hunks"]:
                                if hunk_a["changes"] and hunk_a["changes"] == hunk_b["changes"]:
                                    duplicates += 1
                                elif _overlap(hunk_a, hunk_b):
                                    conflicts += 1

            self.overview_values["patches"].setText(
                self._tr(f"{patch_total} Dateien", f"{patch_total} files")
            )
            detail = self._tr(
                f"{conflicts} Konflikte · {duplicates} Duplikate",
                f"{conflicts} conflicts · {duplicates} duplicates"
            )
            if patch_errors:
                detail += self._tr(
                    f" · {patch_errors} Scanfehler",
                    f" · {patch_errors} scan errors"
                )
            self.overview_details["patches"].setText(detail)
        except Exception as exc:
            self.overview_values["patches"].setText("—")
            self.overview_details["patches"].setText(str(exc))

        # Backup-Auswertung anhand der Verzeichnisse des Backup Explorers.
        try:
            backup_sources = (
                "backup", "backups", "patch_sicherungen", "s4/data/backups"
            )
            backup_count = 0
            backup_bytes = 0

            for relative in backup_sources:
                folder = root / relative
                if not folder.is_dir():
                    continue
                for current, directories, filenames in os.walk(folder):
                    current_path = Path(current)
                    depth = len(current_path.relative_to(folder).parts)
                    if depth >= 8:
                        directories[:] = []
                    for filename in filenames:
                        file_path = current_path / filename
                        try:
                            if file_path.is_file():
                                backup_count += 1
                                backup_bytes += file_path.stat().st_size
                        except OSError:
                            pass

            size_mb = backup_bytes / (1024 * 1024)
            self.overview_values["backups"].setText(
                self._tr(f"{backup_count} Dateien", f"{backup_count} files")
            )
            self.overview_details["backups"].setText(
                self._tr(f"{size_mb:.1f} MB belegt", f"{size_mb:.1f} MB used")
            )
        except Exception as exc:
            self.overview_values["backups"].setText("—")
            self.overview_details["backups"].setText(str(exc))

        # Build-Status nach denselben Regeln wie BuildStatisticsDialog.
        try:
            import re
            log_dir = root / "build_logs"
            logs = list(log_dir.glob("*.log")) if log_dir.is_dir() else []
            latest_status = self._tr("Keine Builds", "No builds")

            if logs:
                latest = max(logs, key=lambda item: item.stat().st_mtime)
                content = latest.read_text(encoding="utf-8", errors="replace")
                finish = re.search(
                    r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", content
                )

                if finish:
                    successful = int(finish.group(1)) == 0
                    latest_status = self._tr(
                        "Letzter Build: Erfolg" if successful else "Letzter Build: Fehler",
                        "Latest build: success" if successful else "Latest build: failed"
                    )
                elif "numeric argument required" in content or re.search(
                    r"SIMPLEBUILD_FINISHED:exit=\s*(?:\r?$)", content, re.M
                ):
                    latest_status = self._tr(
                        "Letzter Build: Fehler", "Latest build: failed"
                    )
                else:
                    latest_status = self._tr(
                        "Letzter Build: unvollständig",
                        "Latest build: incomplete"
                    )

            self.overview_values["builds"].setText(
                self._tr(f"{len(logs)} Build-Logs", f"{len(logs)} build logs")
            )
            self.overview_details["builds"].setText(latest_status)
        except Exception as exc:
            self.overview_values["builds"].setText("—")
            self.overview_details["builds"].setText(str(exc))

    def closeEvent(self, event):
        # Save the current window size for the next launch.
        self.settings.setValue("cyber_center/window_size", self.size())
        self.settings.sync()
        super().closeEvent(event)

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

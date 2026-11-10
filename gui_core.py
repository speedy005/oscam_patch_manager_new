"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerCoreMixin:
    """Patch Manager Core"""

    def __init__(self):
        super().__init__()

    def pbar_idle(self):
        """
        Pulsier-Logik für die ProgressBar im Leerlauf.
        Features: Akku-Erkennung, Sleep-Timer (10 Min), Dynamic Style.
        """
        import psutil
        from PyQt6.QtCore import QVariantAnimation, QEasingCurve, QTimer

        pb = getattr(self, "progress_bar", None)
        if not pb or pb.value() > 0:
            return

        # 1. Energie-Status & Geschwindigkeit festlegen
        battery = psutil.sensors_battery()
        is_on_battery = battery.power_plugged is False if battery else False
        duration = 2800 if is_on_battery else 1500  # Langsamer im Akku-Modus

        # 2. Alte Animation & Timer säubern
        if hasattr(self, "_idle_anim"):
            self._idle_anim.stop()
        if hasattr(self, "_idle_sleep_timer"):
            self._idle_sleep_timer.stop()

        # 3. Sleep-Timer: Schaltet Animation nach 10 Min Inaktivität aus
        self._idle_sleep_timer = QTimer(self)
        self._idle_sleep_timer.setSingleShot(True)
        self._idle_sleep_timer.timeout.connect(
            lambda: self._idle_anim.stop() if hasattr(self, "_idle_anim") else None
        )
        self._idle_sleep_timer.start(600000)  # 10 Minuten (600.000 ms)

        # 4. Animation erstellen
        self._idle_anim = QVariantAnimation(self)
        self._idle_anim.setStartValue(30)  # Start-Helligkeit
        self._idle_anim.setEndValue(85)  # Ziel-Helligkeit
        self._idle_anim.setDuration(duration)
        self._idle_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._idle_anim.setLoopCount(-1)

        def update_style(value):
            if pb.value() == 0:
                color = current_diff_colors.get("fg", "#00FF00")
                pb.setStyleSheet(
                    f"""
                    QProgressBar {{
                        border: 1px solid {color};
                        border-radius: 8px;
                        background-color: #000;
                        text-align: center;
                        color: {color};
                        font-weight: bold;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        opacity: {value / 100.0};
                        border-radius: 7px;
                    }}
                """
                )
            else:
                self._idle_anim.stop()  # Sofort-Stop bei Fortschritt

        self._idle_anim.valueChanged.connect(update_style)
        self._idle_anim.start()

    def apply_global_button_style(self, text_color=None):
        """Wendet das aktuelle Farbschema auf alle QPushButtons an; Stats bleibt unberührt."""
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt

        global current_diff_colors
        colors = globals().get("current_diff_colors", {}) or {}
        # Ein explizit übergebener Textfarbwert wird absichtlich ignoriert, wenn
        # ein gültiges Theme existiert: so gewinnt immer das ausgewählte Schema.
        fg = colors.get("fg", colors.get("text", text_color or "#FFFFFF"))
        bg = colors.get("bg", "#2F2F2F")
        hover = colors.get("hover", "#444444")
        active = colors.get("active", "#222222")
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")

        # Widget-Attribute finden, damit Tooltips bei jedem Sprachwechsel neu
        # gesetzt werden und keine Texte der vorherigen Sprache zurückbleiben.
        attr_by_id = {}
        try:
            for attr_name, value in vars(self).items():
                if isinstance(value, QPushButton):
                    attr_by_id[id(value)] = attr_name
        except Exception:
            pass

        tooltip_texts = {
            "btn_patch_online": (
                "Lädt verfügbare Patches aus dem Git-Repository und zeigt deren Versionen an."
                if is_de else
                "Loads available patches from the Git repository and shows their versions."
            ),
            "telemetry_cb": (
                "Anonyme Nutzungsstatistik aktivieren oder deaktivieren."
                if is_de else
                "Enable or disable anonymous usage statistics."
            ),
            "log_button": (
                "Speichert den aktuellen Log-/Protokollinhalt in einer Datei."
                if is_de else
                "Saves the current log output to a file."
            ),
            "btn_modifier": (
                "Ändert den Namen des Patch-Autors."
                if is_de else
                "Changes the patch author name."
            ),
            "btn_repo_url": (
                "Zeigt oder ändert die URL des OSCam-Emu-Repositories."
                if is_de else
                "Shows or changes the OSCam-Emu repository URL."
            ),
            "btn_open_work": (
                "Öffnet den Arbeitsordner."
                if is_de else "Opens the working folder."
            ),
            "btn_open_temp": (
                "Öffnet den lokalen temporären Git-Clone."
                if is_de else "Opens the local temporary Git clone."
            ),
            "btn_open_emu": (
                "Öffnet das OSCam-Emu-Repository."
                if is_de else "Opens the OSCam-Emu repository."
            ),
            "btn_check_tools": (
                "Prüft Compiler und benötigte Abhängigkeiten."
                if is_de else "Checks compilers and required dependencies."
            ),
            "btn_check_commit": (
                "Prüft den aktuellen Git-Commit."
                if is_de else "Checks the current Git commit."
            ),
            "header_btn_s3_ncam": (
                "Wählt den Patch-Ordner für S3/NCam aus."
                if is_de else "Selects the S3/NCam patch folder."
            ),
            "header_btn_s4": (
                "Wählt den S4-Patch-Ordner aus."
                if is_de else "Selects the S4 patch folder."
            ),
            "header_btn_patch_ncam": (
                "Kopiert den Patch in den konfigurierten S3/NCam-Ordner."
                if is_de else "Copies the patch to the configured S3/NCam folder."
            ),
            "header_btn_patch_s4": (
                "Kopiert den Patch in den konfigurierten S4-Ordner."
                if is_de else "Copies the patch to the configured S4 folder."
            ),
            "btn_s3": (
                "Linksklick: S3 öffnen/starten. Rechtsklick: Installationspfad ändern."
                if is_de else "Left-click: open/start S3. Right-click: change installation path."
            ),
            "btn_s4": (
                "Linksklick: S4 öffnen/starten. Rechtsklick: Installationspfad ändern."
                if is_de else "Left-click: open/start S4. Right-click: change installation path."
            ),
            "btn_ncam": (
                "Linksklick: NCam öffnen/starten. Rechtsklick: Installationspfad ändern."
                if is_de else "Left-click: open/start NCam. Right-click: change installation path."
            ),
            "info_button": (
                "Zeigt Informationen zum Programm."
                if is_de else "Shows information about the application."
            ),
            "matrix_btn": (
                "Schaltet den Matrix-Modus um."
                if is_de else "Toggles Matrix mode."
            ),
            "oscam_source_button": (
                "Öffnet oder ändert die OSCam-Quellrepository-URL."
                if is_de else "Opens or changes the OSCam source repository URL."
            ),
            "patch_emu_git_button": (
                "Verwaltet das OSCam-Emu-Git-Repository und den Patch."
                if is_de else "Manages the OSCam-Emu Git repository and patch."
            ),
            "github_upload_patch_button": (
                "Lädt den aktuellen Patch zu GitHub hoch."
                if is_de else "Uploads the current patch to GitHub."
            ),
            "clean_emu_button": (
                "Bereinigt das lokale OSCam-Emu-Git-Repository."
                if is_de else "Cleans the local OSCam-Emu Git repository."
            ),
        }

        for btn in self.findChildren(QPushButton):
            try:
                attr_name = attr_by_id.get(id(btn), "")
                label = btn.text().replace("&", "").replace("\n", " ").strip()
                label = " ".join(label.split())
                if attr_name in tooltip_texts:
                    tooltip = tooltip_texts[attr_name]
                elif label:
                    tooltip = (f"Aktion: {label}" if is_de else f"Action: {label}")
                else:
                    tooltip = ("Aktion ausführen" if is_de else "Perform action")
                btn.setToolTip(tooltip)
                btn.setToolTipDuration(10000)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                # Ein einheitliches Theme für alle Buttons. Stats bleibt ein
                # Toggle: aktiv rote Schrift, inaktiv die Theme-Textfarbe.
                if btn is getattr(self, "telemetry_cb", None):
                    btn.setStyleSheet(f"""
                        QPushButton {{ color: {fg}; background-color: {bg};
                            border: 2px solid {fg}; border-radius: 8px;
                            padding: 3px 8px; font-weight: bold; }}
                        QPushButton:hover {{ color: {fg}; background-color: {hover};
                            border: 2px solid {fg}; }}
                        QPushButton:checked {{ color: #FF0000; background-color: {bg};
                            border: 2px solid #FF0000; }}
                        QPushButton:checked:hover {{ color: #FF0000;
                            background-color: {hover}; border: 2px solid #FF0000; }}
                        QPushButton:pressed {{ background-color: {active}; }}
                        QPushButton:disabled {{ color: #777777; background-color: {active}; }}
                        QToolTip {{ color: {fg}; background-color: {bg};
                            border: 2px solid {fg}; padding: 5px; }}
                    """)
                else:
                    btn.setStyleSheet(f"""
                        QPushButton {{ color: {fg}; background-color: {bg};
                            border: 2px solid {fg}; border-radius: 8px;
                            padding: 5px; font-weight: bold; }}
                        QPushButton:hover {{ color: {fg}; background-color: {hover};
                            border: 2px solid {fg}; }}
                        QPushButton:pressed {{ color: {fg}; background-color: {active};
                            border: 2px solid {fg}; }}
                        QPushButton:disabled {{ color: #777777; background-color: {active}; }}
                        QToolTip {{ color: {fg}; background-color: {bg};
                            border: 2px solid {fg}; padding: 5px; }}
                    """)
            except RuntimeError:
                continue



    def force_user_leds_static(self):
        """User-LEDs statisch setzen (NUR User-LEDs, Farbe passt sich dem Theme an!)"""
        global current_diff_colors

        # 1. Aktuelle Akzentfarbe (z.B. Gold oder Matrix-Grün) holen
        fg = current_diff_colors.get("fg", "#EAFF00")

        # 2. Status prüfen: Sollen die LEDs leuchten (AN) oder schlafen (AUS)?
        is_enabled = getattr(self, "current_config", {}).get("led_enabled", True)

        if not is_enabled:
            # Falls AUS: Akzentfarbe auf 20% Helligkeit dimmen (deine neue Funktion!)
            target_color = self.adjust_color(fg, 0.2)
            border_color = "#111"
        else:
            # Falls AN: Volle Akzentfarbe (aber statisch, kein Blinken)
            target_color = fg
            border_color = "#555"

        # 3. Timer sofort stoppen (Wichtig gegen Ghost-Blinking)
        if hasattr(self, "blink_timer"):
            self.blink_timer.stop()

        # 4. Stylesheet auf alle User-LEDs anwenden
        for led in getattr(self, "user_leds", []):
            try:
                led.setStyleSheet(
                    f"""
                    QLabel {{
                        background-color: {target_color};
                        border: 1px solid {border_color};
                        border-radius: 4px;
                    }}
                """
                )
            except:
                continue

        # Internen Status zurücksetzen
        self._blink_state = False

    def toggle_theme(self):
        """
        Schaltet zwischen Light, Dark und Matrix Mode um, aktualisiert die UI
        und speichert die Auswahl dauerhaft in der Config-Datei.
        """

        # --- Final Label ausblenden, falls sichtbar ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        import json

        # Aktuellen Modus aus den globalen Variablen holen (geladen durch load_config)
        current_mode = globals().get("THEME_MODE", "standard")
        lang = getattr(self, "LANG", "de").lower()

        # 1. Logik für den Wechsel (Rotation: Standard -> Dark -> Matrix -> zurück)
        if current_mode == "standard":
            new_mode = "dark"
        elif current_mode == "dark":
            new_mode = "matrix"
        else:
            new_mode = "standard"

        # 2. Globale Variable sofort aktualisieren
        globals()["THEME_MODE"] = new_mode

        # 3. THEMEN ANWENDEN
        if new_mode == "standard":
            # --- LIGHT MODE ---
            self.setStyleSheet("background-color: #F5F5F5; color: #222;")
            self.info_text.setStyleSheet(
                "background-color: #FFFFFF; color: #222; border: 1px solid #CCC; border-radius: 5px;"
            )
            if hasattr(self, "header_widget"):
                self.header_widget.setStyleSheet(
                    "background-color: #E0E0E0; border: 1px solid #BBB; border-radius: 10px;"
                )
            self.btn_theme.setStyleSheet(
                "background-color: #DDD; color: #222; border: 1px solid #BBB; border-radius: 4px; font-size: 10px;"
            )
            self.btn_theme.setText("☀️ Light Mode")

            pbar = getattr(self, "progress_bar", None)
            if pbar:
                pbar.setStyleSheet(
                    "QProgressBar { text-align: center; border: 1px solid #BBB; border-radius: 5px; background-color: #EEE; color: #222; }"
                )
                pbar.setFormat("Helles Design" if lang == "de" else "Light Mode")

        elif new_mode == "dark":
            # --- DARK MODE ---
            self.setStyleSheet("background-color: #2F2F2F; color: #EEE;")
            self.info_text.setStyleSheet(
                "background-color: #000000; color: #FFFFFF; border: 1px solid #444; border-radius: 5px;"
            )
            if hasattr(self, "header_widget"):
                self.header_widget.setStyleSheet(
                    "background-color: #2F2F2F; border: 1px solid #444; border-radius: 10px;"
                )
            self.btn_theme.setStyleSheet(
                "background-color: #3D3D3D; color: #EEE; border: 1px solid #555; border-radius: 4px; font-size: 10px;"
            )
            self.btn_theme.setText("🌓 Dark Mode")

            pbar = getattr(self, "progress_bar", None)
            if pbar:
                rainbow = (
                    "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                    "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF)"
                )
                pbar.setStyleSheet(
                    f"QProgressBar {{ text-align: center; border: 2px solid #222; border-radius: 6px; background-color: #111; color: black; font-weight: bold; }}"
                    f"QProgressBar::chunk {{ background: {rainbow}; border-radius: 4px; }}"
                )
                pbar.setFormat("Dunkles Design" if lang == "de" else "Dark Mode")

        elif new_mode == "matrix":
            # --- MATRIX MODE ---
            # Klassisches Hacker-Grün auf Schwarz
            self.setStyleSheet("background-color: #000000; color: #00FF00;")
            self.info_text.setStyleSheet(
                "background-color: #000000; color: #00FF00; border: 1px solid #00FF00; border-radius: 5px; font-family: 'Courier New';"
            )
            if hasattr(self, "header_widget"):
                self.header_widget.setStyleSheet(
                    "background-color: #000000; border: 1px solid #00FF00; border-radius: 10px;"
                )
            self.btn_theme.setStyleSheet(
                "background-color: #000000; color: #00FF00; border: 1px solid #00FF00; border-radius: 4px; font-size: 10px;"
            )
            self.btn_theme.setText("📟 Matrix Mode")

            pbar = getattr(self, "progress_bar", None)
            if pbar:
                pbar.setStyleSheet(
                    "QProgressBar { text-align: center; border: 1px solid #00FF00; border-radius: 5px; background-color: #000; color: #00FF00; }"
                    "QProgressBar::chunk { background-color: #008800; }"
                )
                pbar.setFormat("SYSTEM MATRIX..." if lang == "de" else "MATRIX ACTIVE")

        # 4. SPEICHERN IN DATEI (Persistenz)
        try:
            # Nutzt die CONFIG_FILE Konstante aus dem globalen Scope
            config_path = globals().get("CONFIG_FILE", "config.json")
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)

                cfg["theme_mode"] = new_mode

                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Themes: {e}")


    def show_info(self):
        """Zeigt das Info-Fenster mit sprachabhängigen Texten und Theme-Farben."""
        from PyQt6.QtWidgets import (
            QApplication,
            QDialog,
            QVBoxLayout,
            QHBoxLayout,
            QFormLayout,
            QLabel,
            QGroupBox,
            QPushButton,
            QStyle,
        )
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import Qt

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        t = TEXTS.get(lang, TEXTS.get("en", {}))

        # --------------------------------------------------
        # Info-Button: Tooltip sicherstellen
        # --------------------------------------------------
        info_btn = getattr(self, "btn_info", None)

        if info_btn is not None:
            info_btn.setToolTip(
                "Zeigt Informationen über das OSCam Toolkit an."
                if is_de
                else "Displays information about the OSCam Toolkit."
            )
            info_btn.setToolTipDuration(10000)

            # Sicherstellen, dass der Button die Methode öffnet.
            try:
                info_btn.clicked.disconnect(self.show_info)
            except (TypeError, RuntimeError):
                pass

            info_btn.clicked.connect(self.show_info)

        # --------------------------------------------------
        # Dialog erstellen
        # --------------------------------------------------
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle(
            t.get("info_title", "About OSCam Emu Toolkit")
        )
        info_dialog.resize(450, 410)
        info_dialog.setMinimumHeight(390)
        info_dialog.setMaximumHeight(450)

        # --------------------------------------------------
        # Farben aus dem aktuellen Theme laden
        # --------------------------------------------------
        colors = globals().get("current_diff_colors", {})

        bg_color = colors.get("bg", "#FFFFFF")
        text_color = colors.get("text", "#000000")
        border_col = colors.get("border", "#888888")
        active_color = colors.get("active", "#e0e0e0")

        info_dialog.setStyleSheet(
            f"""
            QDialog {{
                background-color: {bg_color};
            }}
            """
        )

        layout = QVBoxLayout(info_dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --------------------------------------------------
        # Header
        # --------------------------------------------------
        header_layout = QHBoxLayout()

        icon_label = QLabel()
        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxInformation
        )
        icon_label.setPixmap(icon.pixmap(64, 64))

        title_vbox = QVBoxLayout()

        title_label = QLabel("OSCam Emu Patch Manager")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #0000FF;")

        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setStyleSheet("color: #666666;")

        title_vbox.addWidget(title_label)
        title_vbox.addWidget(version_label)

        header_layout.addWidget(icon_label)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # --------------------------------------------------
        # Credits / Authors
        # --------------------------------------------------
        credits_title = t.get("credits_label", "Credits / Authors")
        credits_group = QGroupBox(credits_title)

        credits_group.setStyleSheet(
            f"""
            QGroupBox {{
                color: {text_color};
                border: 1px solid {border_col};
                margin-top: 10px;
                font-weight: bold;
            }}
            """
        )

        credits_layout = QFormLayout(credits_group)

        author_label = QLabel(
            "Hauptautor:" if is_de else "Main Author:"
        )
        author_val = QLabel("<b>speedy005</b>")
        author_val.setStyleSheet("color: #008000;")

        emu_label = QLabel(
            "Emu-Patch:" if is_de else "Emu Patch:"
        )
        emu_val = QLabel("OSCam-Emu Team")
        emu_val.setStyleSheet("color: #0000FF;")

        license_label = QLabel("Lizenz:" if is_de else "License:")
        lic_val = QLabel("MIT License")
        lic_val.setStyleSheet("color: #FF0000;")

        for label in (author_label, emu_label, license_label):
            label.setStyleSheet(f"color: {text_color};")

        credits_layout.addRow(author_label, author_val)
        credits_layout.addRow(emu_label, emu_val)
        credits_layout.addRow(license_label, lic_val)

        layout.addWidget(credits_group)

        # --------------------------------------------------
        # OSCam-Quellrepository
        # --------------------------------------------------
        source_title = (
            "OSCam-Quellrepository"
            if is_de
            else "OSCam source repository"
        )

        source_group = QGroupBox(source_title)
        source_group.setStyleSheet(
            f"""
            QGroupBox {{
                color: {text_color};
                border: 1px solid {border_col};
                margin-top: 10px;
                font-weight: bold;
            }}
            """
        )

        source_layout = QVBoxLayout(source_group)

        try:
            active_source = get_selected_stream_repo_name()
        except Exception:
            active_source = "Unbekannt" if is_de else "Unknown"

        try:
            active_url = get_selected_stream_repo_url()
        except Exception:
            active_url = ""

        source_label = QLabel(f"{active_source}\n{active_url}")
        source_label.setWordWrap(True)
        source_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        source_label.setStyleSheet(f"color: {text_color};")

        source_layout.addWidget(source_label)
        layout.addWidget(source_group)

        # --------------------------------------------------
        # Copyright
        # --------------------------------------------------
        copy_label = QLabel(
            "© 2026 speedy005 - Alle Rechte vorbehalten."
            if is_de
            else "© 2026 speedy005 - All rights reserved."
        )
        copy_label.setFont(QFont("Arial", 8))
        copy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy_label.setStyleSheet(f"color: {text_color};")

        layout.addWidget(copy_label)

        # --------------------------------------------------
        # Schließen-Button
        # --------------------------------------------------
        close_btn = QPushButton(t.get("close", "Schließen" if is_de else "Close"))
        close_btn.setMinimumHeight(50)

        button_radius = getattr(self, "BUTTON_RADIUS", 8)

        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                border-radius: {button_radius}px;
                background-color: {active_color};
                color: #0000FF;
                font-weight: bold;
                border: 1px solid {border_col};
                padding: 6px;
            }}
            QPushButton:hover {{
                border: 1px solid #0000FF;
            }}
            """
        )

        close_btn.clicked.connect(info_dialog.accept)
        layout.addWidget(close_btn)

        # Dialog modal anzeigen
        info_dialog.exec()



    def resizeEvent(self, event):
        """
        Zentrale Steuerung für die UI-Skalierung bei Auflösungsänderung.
        Passt Header, Logo, Schriftgrößen und Overlay an.
        """
        QWidget.resizeEvent(self, event)

        # Responsive Breiten für Status- und Einstellungsleiste:
        # feste Pixelbreiten waren auf schmalen Fenstern unnötig platzintensiv.
        try:
            compact = self.width() < 1150
            if hasattr(self, "status_info_label"):
                self.status_info_label.setFixedWidth(145 if compact else 220)
                self.status_info_label.setStyleSheet(
                    "color: #FF0000; font-size: %dpx; font-weight: bold; border: none; background: transparent;"
                    % (16 if compact else 22)
                )
            if hasattr(self, "btn_matrix"):
                self.btn_matrix.setFixedWidth(180 if compact else 300)
            if hasattr(self, "btn_theme"):
                self.btn_theme.setFixedWidth(130 if compact else 200)
            if hasattr(self, "slider_speed"):
                self.slider_speed.setFixedWidth(75 if compact else 110)
            if hasattr(self, "lbl_speed_val"):
                self.lbl_speed_val.setFixedWidth(65 if compact else 85)
            if hasattr(self, "language_box"):
                self.language_box.setFixedWidth(65 if compact else 80)
            if hasattr(self, "color_label"):
                self.color_label.setFixedWidth(85 if compact else 120)
            if hasattr(self, "color_box"):
                self.color_box.setFixedWidth(95 if compact else 120)
            if hasattr(self, "commit_label"):
                self.commit_label.setFixedWidth(100 if compact else 140)
            if hasattr(self, "commit_spin"):
                self.commit_spin.setFixedWidth(65 if compact else 75)
            if hasattr(self, "btn_check_tools"):
                self.btn_check_tools.setFixedWidth(165 if compact else 220)
        except RuntimeError:
            # Widgets können während des Schließens bereits zerstört sein.
            pass

        # Buttonhöhen und Beschriftungen bei jeder Fenstergrößenänderung neu berechnen.
        QTimer.singleShot(0, self._fit_all_button_texts)

        # 1. Header-Steuerelemente responsiv anpassen
        if hasattr(self, "header_widget"):
            QTimer.singleShot(0, self._fit_header_controls)

        # 2. Dynamische Schriftgrößen berechnen
        dynamic_size = max(10, int(self.width() / 90))

        button_font = QFont(
            "Arial", dynamic_size, QFont.Weight.Bold
        )
        label_font = QFont(
            "Arial", max(9, dynamic_size - 1)
        )
        clock_font = QFont(
            "Arial",
            max(12, int(dynamic_size * 0.9)),
            QFont.Weight.Bold,
        )

        # 3. Alle Buttons aktualisieren
        for btn in getattr(self, "all_buttons", []):
            btn.setFont(button_font)

            if not btn.icon().isNull():
                icon_dim = int(dynamic_size * 2.0)
                btn.setIconSize(QSize(icon_dim, icon_dim))

        # 4. Aktions-Grid aktualisieren
        for btn in getattr(self, "buttons", {}).values():
            btn.setFont(button_font)

        # 5. Uhr aktualisieren
        
        # Uhr und Datum immer gleich groß und fett
        clock_date_font = QFont(
            "Segoe UI",
            max(12, int(dynamic_size * 0.9)),
            QFont.Weight.Bold,
        )

        if hasattr(self, "digital_clock"):
            self.digital_clock.setFont(clock_date_font)

        if hasattr(self, "date_label"):
            self.date_label.setFont(clock_date_font)


        # 6. Header-Labels aktualisieren
        if hasattr(self, "lang_label"):
            self.lang_label.setFont(label_font)

        if hasattr(self, "color_label"):
            self.color_label.setFont(label_font)

        if hasattr(self, "commit_label"):
            self.commit_label.setFont(label_font)

        # 7. Logo einmal nach der Layout-Aktualisierung skalieren
        if (
            hasattr(self, "logo_label")
            and getattr(self, "original_pixmap", None) is not None
        ):
            QTimer.singleShot(0, self._fit_header_logo)

        # 8. Info-Text aktualisieren
        if hasattr(self, "info_text"):
            text_font = QFont(
                "Courier", max(10, dynamic_size)
            )
            self.info_text.setFont(text_font)

        # 9. Lade-Overlay auf Fenstergröße halten
        if getattr(self, "loading_overlay", None):
            self.loading_overlay.setGeometry(self.rect())


    def checkout_streamboard_revision(self):
        """
        Wählt eine beliebige Streamboard-Git-Revision aus und checkt sie
        im lokalen STREAMREPO als detached HEAD aus.

        Wichtig:
        - Es werden keine untracked Dateien gelöscht.
        - Bei einem nicht sauberen Working Tree wird der Vorgang abgebrochen.
        - Ein Commit kann aus der Liste gewählt oder als SHA manuell eingegeben werden.
        - Die Auswahl wird in self.selected_streamboard_commit gespeichert und
          anschließend von create_patch() als Patch-Basis verwendet.
        """
        import os
        import re
        import subprocess

        from PyQt6.QtWidgets import (
            QApplication,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"

        texts = getattr(self, "TEXT", {}) or {}

        def tr(key, de_fallback, en_fallback):
            return texts.get(key) or (
                de_fallback if is_de else en_fallback
            )

        stream_dir = os.path.abspath(
            globals().get("STREAMREPO", "")
        )
        stream_choices = dict(STREAM_REPO_CHOICES)
        stream_url = str(get_selected_stream_repo_url()).strip()

        
        if stream_url not in stream_choices.values():
            stream_choices[tr(
                "current_source",
                "Aktuelle Quelle",
                "Current Source"
            )] = stream_url


        if not stream_dir:
            QMessageBox.critical(
                self,
                "Streamboard",
                "STREAMREPO ist nicht definiert."
                if is_de else
                "STREAMREPO is not defined."
            )
            return False

        try:
            git = find_git_executable()
        except Exception:
            git = None

        if not git:
            QMessageBox.critical(
                self,
                "Git",
                "Git wurde nicht gefunden."
                if is_de else
                "Git was not found."
            )
            return False

        def git_run(args, cwd=stream_dir, check=True, timeout=1200):
            result = subprocess.run(
                [git] + list(args),
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            if check and result.returncode != 0:
                raise RuntimeError(err or out or "Git command failed")
            return out

        try:
            # Repository bei Bedarf anlegen/klonen.
            if not os.path.isdir(stream_dir) or not os.path.isdir(
                os.path.join(stream_dir, ".git")
            ):
                ensure_git_repository(
                    stream_dir,
                    stream_url,
                    description="Streamboard",
                    clone_timeout=1200,
                )

            # Sicherheitsprüfung: niemals uncommitted Änderungen überschreiben.
            status = git_run(["status", "--porcelain"], timeout=60)
            if status:
                QMessageBox.warning(
                    self,
                    "Streamboard",
                    (
                        "Das Streamboard-Arbeitsverzeichnis enthält lokale Änderungen.\n\n"
                        "Bitte zuerst committen/stashen oder den Ordner bereinigen.\n"
                        "Es werden von diesem Dialog keine Dateien gelöscht."
                    ) if is_de else (
                        "The Streamboard working tree contains local changes.\n\n"
                        "Please commit/stash them or clean the repository first.\n"
                        "This dialog will not delete any files."
                    )
                )
                return False

            # Commit-Liste aus dem aktuell ausgewählten Repository laden.
            git_run(
                [
                    "fetch",
                    stream_url,
                    "refs/heads/master:refs/remotes/revision-picker/master",
                ],
                timeout=1200,
            )

            # Aktuellen Remote-Master direkt vom Server bestimmen.
            remote_head = ""
            try:
                remote_head = git_run(
                    ["ls-remote", "--exit-code", stream_url, "refs/heads/master"],
                    cwd=stream_dir,
                    timeout=120,
                ).split()[0]
            except Exception:
                remote_head = ""

            # Letzte 100 Commits aus dem ausgewählten Repository.
            log_output = git_run(
                [
                    "log",
                    "revision-picker/master",
                    "-100",
                    "--date=format:%Y-%m-%d %H:%M",
                    "--format=%H%x09%ad%x09%s",
                ],
                timeout=120,
            )

            commits = []
            seen = set()
            for line in log_output.splitlines():
                parts = line.split("\t", 2)
                if len(parts) != 3:
                    continue
                sha, date_text, subject = parts
                sha = sha.strip()
                if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
                    continue
                if sha in seen:
                    continue
                seen.add(sha)
                commits.append((sha, date_text, subject))

            if remote_head and remote_head not in seen:
                try:
                    git_run(["fetch", stream_url, remote_head], timeout=1200)
                    subject = git_run(
                        ["show", "-s", "--format=%s", remote_head],
                        timeout=60,
                    )
                    date_text = git_run(
                        ["show", "-s", "--date=format:%Y-%m-%d %H:%M", "--format=%ad", remote_head],
                        timeout=60,
                    )
                    commits.insert(0, (remote_head, date_text, subject))
                    seen.add(remote_head)
                except Exception:
                    pass

            dialog = QDialog(self)
            dialog.setModal(True)
            dialog.resize(900, 620)
            
            dialog.setWindowTitle(
                tr(
                    "select_revision",
                    "Streamboard Git-Revision auswählen",
                    "Select Streamboard Git Revision"
                )
            )


            layout = QVBoxLayout(dialog)

            info = QLabel(
                (
                    "Wähle einen Commit aus oder gib einen vollständigen Git-SHA ein.\n"
                    "Der ausgewählte Commit wird detached ausgecheckt und für die Patch-Erstellung verwendet."
                ) if is_de else (
                    "Select a commit or enter a full Git SHA.\n"
                    "The selected commit will be checked out detached and used as the patch base."
                )
            )
            info.setWordWrap(True)
            layout.addWidget(info)
            repo_label = QLabel(
                "Repository für Commit-Liste:" if is_de else
                "Repository for commit list:"
            )
            layout.addWidget(repo_label)

            repo_combo = QComboBox(dialog)
            repo_names = list(stream_choices.keys())
            selected_repo_name = next(
                (
                    name for name, url in stream_choices.items()
                    if url == stream_url
                ),
                repo_names[0] if repo_names else "",
            )
            repo_combo.addItems(repo_names)
            if selected_repo_name:
                repo_combo.setCurrentText(selected_repo_name)
            layout.addWidget(repo_combo)
            current = getattr(self, "selected_streamboard_commit", "")
            if current:
                current_label = QLabel(
                    f"Aktuell ausgewählt: {current}" if is_de else
                    f"Currently selected: {current}"
                )
                layout.addWidget(current_label)

            commit_list = QListWidget(dialog)
            layout.addWidget(commit_list)

            for sha, date_text, subject in commits:
                item = QListWidgetItem(
                    f"{date_text}  {sha[:12]}  {subject}"
                )
                item.setData(0x0100, sha)
                commit_list.addItem(item)

            sha_edit = QLineEdit(dialog)
            sha_edit.setPlaceholderText(
                "Vollständigen 40-stelligen Commit-SHA eingeben"
                if is_de else
                "Enter full 40-character commit SHA"
            )
            layout.addWidget(sha_edit)

            refresh_button = QPushButton(
                "Commit-Liste aktualisieren" if is_de else "Refresh commit list"
            )
            layout.addWidget(refresh_button)

            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel,
                parent=dialog,
            )

            buttons.button(
                QDialogButtonBox.StandardButton.Ok
            ).setText("OK" if is_de else "OK")

            buttons.button(
                QDialogButtonBox.StandardButton.Cancel
            ).setText("Abbrechen" if is_de else "Cancel")

            layout.addWidget(buttons)

            layout.addWidget(buttons)

            def use_list_selection():
                item = commit_list.currentItem()
                if item is not None:
                    sha_edit.setText(str(item.data(0x0100)))

            commit_list.itemDoubleClicked.connect(
                lambda _item: use_list_selection()
            )
            commit_list.currentItemChanged.connect(
                lambda _current, _previous: use_list_selection()
            )

            # Refresh schließt den Dialog nicht. Die Liste wird neu aufgebaut.
            
            def refresh_list():
                try:
                    if git_run(["status", "--porcelain"], timeout=60):
                        
                        QMessageBox.warning(
                            dialog,
                            "Streamboard",
                            tr(
                                "working_tree_not_clean",
                                "Arbeitsverzeichnis ist nicht sauber.",
                                "Working tree is not clean."
                            )
                        )

                        return

                    selected_name = repo_combo.currentText()
                    selected_url = str(
                        stream_choices.get(selected_name, "")
                    ).strip()

                    
                    if not selected_url:
                        raise RuntimeError(
                            tr(
                                "no_repository_url",
                                "Für die ausgewählte Quelle ist keine URL definiert.",
                                "No URL is defined for the selected source."
                            )
                        )


                    remote_ref = "refs/remotes/revision-picker/master"

                    
                    git_run(
                        [
                            "fetch",
                            "--force",
                            selected_url,
                            f"+refs/heads/master:{remote_ref}",
                        ],
                        timeout=1200,
                    )


                    fresh = git_run(
                        [
                            "log",
                            remote_ref,
                            "-100",
                            "--date=format:%Y-%m-%d %H:%M",
                            "--format=%H%x09%ad%x09%s",
                        ],
                        timeout=120,
                    )

                    commit_list.clear()
                    sha_edit.clear()
                    local_seen = set()

                    for line in fresh.splitlines():
                        parts = line.split("\t", 2)
                        if len(parts) != 3:
                            continue

                        sha, date_text, subject = parts
                        sha = sha.lower()

                        if not re.fullmatch(r"[0-9a-f]{40}", sha):
                            continue
                        if sha in local_seen:
                            continue

                        local_seen.add(sha)
                        refreshed_item = QListWidgetItem(
                            f"{date_text}  {sha[:12]}  {subject}"
                        )
                        refreshed_item.setData(0x0100, sha)
                        commit_list.addItem(refreshed_item)

                except Exception as exc:
                    QMessageBox.critical(
                        dialog,
                        "Git",
                        str(exc),
                    )

            refresh_button.clicked.connect(refresh_list)
            repo_combo.currentTextChanged.connect(
                lambda _name: refresh_list()
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False
            stream_url = str(
                stream_choices.get(repo_combo.currentText(), "")
            ).strip()

            
            if not stream_url:
                QMessageBox.warning(
                    self,
                    "Streamboard",
                    tr(
                        "no_repository_url",
                        "Für das ausgewählte Repository fehlt die URL.",
                        "The selected repository has no URL."
                    )
                )
                return False

                
            selected = sha_edit.text().strip()
            if not selected:
                QMessageBox.warning(
                    self,
                    "Streamboard",
                    "Bitte einen Commit auswählen oder eine SHA eingeben."
                    if is_de else
                    "Please select a commit or enter a SHA."
                )
                return False

            if not re.fullmatch(r"[0-9a-fA-F]{40}", selected):
                QMessageBox.warning(
                    self,
                    "Streamboard",
                    "Es muss eine vollständige 40-stellige Git-SHA eingegeben werden."
                    if is_de else
                    "A complete 40-character Git SHA is required."
                )
                return False

            selected = selected.lower()

            # Commit bei manueller Eingabe explizit vom Streamboard-Server holen.
            local_selected = git_run(
                ["rev-parse", "--verify", selected + "^{commit}"],
                check=False,
                timeout=60,
            )
            if local_selected != selected:
                git_run(
                    ["fetch", stream_url, selected],
                    timeout=1200,
                )
                local_selected = git_run(
                    ["rev-parse", "--verify", selected + "^{commit}"],
                    check=False,
                    timeout=60,
                )

            if local_selected != selected:
                raise RuntimeError(
                    "Der gewünschte Commit konnte nicht aus Streamboard geladen werden."
                    if is_de else
                    "The requested commit could not be fetched from Streamboard."
                )

            # Exakt diesen Commit auschecken. Kein Reset --hard und kein git clean.
            git_run(
                ["checkout", "--detach", selected],
                timeout=1200,
            )

            checked_out = git_run(
                ["rev-parse", "HEAD"],
                timeout=60,
            )
            if checked_out != selected:
                raise RuntimeError(
                    "Der ausgewählte Commit konnte nicht exakt ausgecheckt werden."
                    if is_de else
                    "The selected commit could not be checked out exactly."
                )

            self.selected_streamboard_commit = selected
            self.selected_streamboard_commit_repo_url = stream_url
            self.display_streamboard_commit = selected
            self.update_revision_button_labels()
            # Commit und Herkunft für bestehende Helfer verfügbar machen.
            globals()["SELECTED_STREAMBOARD_COMMIT"] = selected
            globals()["SELECTED_STREAMBOARD_COMMIT_REPO_URL"] = stream_url

            # Button/Status optisch aktualisieren, falls vorhanden.
            status_text = (
                f"Streamboard Basis: {selected[:12]}"
                if is_de else
                f"Streamboard base: {selected[:12]}"
            )
            try:
                if hasattr(self, "info_text"):
                    self.info_text.append(
                        f"<b>✅ {status_text}</b>"
                    )
                    self.info_text.ensureCursorVisible()
            except Exception:
                pass

            try:
                QApplication.processEvents()
            except Exception:
                pass

            QMessageBox.information(
                self,
                "Streamboard",
                (
                    f"Commit erfolgreich ausgewählt:\n\n{selected}\n\n"
                    "Dieser Commit wird bei der nächsten Patch-Erstellung als Basis verwendet."
                ) if is_de else (
                    f"Commit selected successfully:\n\n{selected}\n\n"
                    "This commit will be used as the base for the next patch."
                )
            )
            return True

        except Exception as exc:
            print("[STREAMBOARD CHECKOUT] Fehler:", repr(exc), flush=True)
            try:
                QMessageBox.critical(
                    self,
                    "Streamboard Git",
                    f"Fehler:\n{exc}"
                )
            except Exception:
                pass
            return False

    def checkout_emu_revision(self):
        """
        Wählt eine beliebige OSCam-Emu-Git-Revision aus und checkt sie
        im lokalen PATCH_EMU_GIT_DIR als detached HEAD aus.

        Das Verhalten entspricht dem Streamboard-Revisionsdialog:
        - letzte 100 Commits anzeigen
        - Commit per Liste oder vollständiger SHA auswählen
        - Commit-Liste aktualisieren
        - Auswahl in self.selected_emu_commit speichern
        - Auswahl wird beim nächsten Patchlauf als exakte OSCam-Emu-Basis verwendet
        """
        import os
        import re
        import subprocess

        from PyQt6.QtWidgets import (
            QApplication,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QLabel,
            QLineEdit,
            QListWidget,
            QListWidgetItem,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
        )

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"

        texts = getattr(self, "TEXT", {}) or {}

        def tr(key, de_fallback, en_fallback):
            return texts.get(key) or (
                de_fallback if is_de else en_fallback
            )

        emu_dir = os.path.abspath(
            globals().get("PATCH_EMU_GIT_DIR", "")
        )

        # Die aktive OSCam-Emu-URL kommt aus der bestehenden GUI-Konfiguration.
        try:
            emu_url, emu_branch = get_emu_repository_config()
        except Exception:
            emu_url = globals().get(
                "EMUREPO_URL",
                "https://github.com/oscam-mirror/oscam-emu.git"
            )
            emu_branch = "master"

        emu_url = str(emu_url or "").strip()
        emu_branch = str(emu_branch or "master").strip() or "master"
        emu_repo_choices = {
            "OSCam-EMU Mirror": "https://github.com/oscam-mirror/oscam-emu.git",
            "speedy005 OSCam-EMU": "https://github.com/speedy005/Oscam-emu.git",
        }

        
        if emu_url not in emu_repo_choices.values():
            emu_repo_choices[tr(
                "current_source",
                "Aktuelle Quelle",
                "Current Source"
            )] = emu_url

        if not emu_dir:
            QMessageBox.critical(
                self,
                "OSCam-Emu",
                "PATCH_EMU_GIT_DIR ist nicht definiert."
                if is_de else
                "PATCH_EMU_GIT_DIR is not defined."
            )
            return False

        try:
            git = find_git_executable()
        except Exception:
            git = None

        if not git:
            QMessageBox.critical(
                self,
                "Git",
                "Git wurde nicht gefunden."
                if is_de else
                "Git was not found."
            )
            return False

        def git_run(args, cwd=emu_dir, check=True, timeout=1200):
            result = subprocess.run(
                [git] + list(args),
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            if check and result.returncode != 0:
                raise RuntimeError(err or out or "Git command failed")
            return out

        try:
            # Repository bei Bedarf mit der aktuell konfigurierten URL anlegen.
            if not os.path.isdir(emu_dir) or not os.path.isdir(
                os.path.join(emu_dir, ".git")
            ):
                ensure_git_repository(
                    emu_dir,
                    emu_url,
                    description="OSCam-Emu",
                    clone_timeout=1200,
                )

            # Das lokale OSCam-Emu-Repository immer an die aktuell über
            # "Repo URL" ausgewählte Quelle anbinden.
            #
            # WICHTIG: sync_emu_origin() ist ein lokaler Helfer innerhalb
            # von create_patch() und steht in diesem GUI-Dialog nicht zur
            # Verfügung. Deshalb wird die Origin-URL hier direkt
            # synchronisiert. So entsteht kein "name ... is not defined".
            current_origin = git_run(
                ["remote", "get-url", "origin"],
                check=False,
                timeout=60,
            ).strip()

            if not current_origin:
                git_run(
                    ["remote", "add", "origin", emu_url],
                    timeout=60,
                )
            elif current_origin.rstrip("/") != emu_url.rstrip("/"):
                git_run(
                    ["remote", "set-url", "origin", emu_url],
                    timeout=60,
                )

            # Keine lokalen Änderungen überschreiben.
            status = git_run(["status", "--porcelain"], timeout=60)
            if status:
                QMessageBox.warning(
                    self,
                    "OSCam-Emu",
                    (
                        "Das OSCam-Emu-Arbeitsverzeichnis enthält lokale Änderungen.\n\n"
                        "Bitte zuerst committen/stashen oder den Ordner bereinigen.\n"
                        "Es werden von diesem Dialog keine Dateien gelöscht."
                    ) if is_de else (
                        "The OSCam-Emu working tree contains local changes.\n\n"
                        "Please commit/stash them or clean the repository first.\n"
                        "This dialog will not delete any files."
                    )
                )
                return False

            # Den konfigurierten Branch aktualisieren und als Remote-Referenz bereitstellen.
            git_run(["fetch", "origin", emu_branch], timeout=1200)

            remote_ref = f"origin/{emu_branch}"
            if not git_run(
                ["rev-parse", "--verify", remote_ref],
                check=False,
                timeout=60,
            ):
                raise RuntimeError(
                    f"OSCam-Emu Branch konnte nicht gefunden werden: {emu_branch}"
                )

            commits_raw = git_run(
                [
                    "log",
                    remote_ref,
                    "-100",
                    "--date=format:%Y-%m-%d %H:%M",
                    "--format=%H%x09%ad%x09%s",
                ],
                timeout=120,
            )

            commits = []
            for line in commits_raw.splitlines():
                parts = line.split("\t", 2)
                if len(parts) != 3:
                    continue
                sha, date_text, subject = parts
                if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
                    continue
                commits.append((sha.lower(), date_text, subject))

            
            dialog = QDialog(self)
            dialog.setWindowTitle(
                tr(
                    "select_revision",
                    "OSCam-Emu Revision auswählen",
                    "Select OSCam-Emu Revision"
                )
            )
            dialog.resize(850, 600)

            layout = QVBoxLayout(dialog)
            repo_label = QLabel(
                tr(
                    "select_repository",
                    "Git-Repository für die Commit-Liste:",
                    "Git repository for the commit list:"
                )
            )
            layout.addWidget(repo_label)


            repo_combo = QComboBox(dialog)

            for repo_name, repo_url in emu_repo_choices.items():
                repo_combo.addItem(repo_name, repo_url)

            current_index = repo_combo.findData(emu_url)
            if current_index >= 0:
                repo_combo.setCurrentIndex(current_index)

            layout.addWidget(repo_combo)
            info = QLabel(
                (
                    "Wähle einen OSCam-Emu-Commit aus oder gib einen vollständigen "
                    "40-stelligen Git-SHA ein."
                ) if is_de else (
                    "Select an OSCam-Emu commit or enter a full 40-character Git SHA."
                )
            )
            info.setWordWrap(True)
            layout.addWidget(info)

            current = getattr(self, "selected_emu_commit", "")
            if current:
                current_label = QLabel(
                    f"Aktuell ausgewählt: {current}"
                    if is_de else
                    f"Currently selected: {current}"
                )
                layout.addWidget(current_label)

            commit_list = QListWidget(dialog)
            layout.addWidget(commit_list)

            for sha, date_text, subject in commits:
                item = QListWidgetItem(
                    f"{date_text}  {sha[:12]}  {subject}"
                )
                item.setData(0x0100, sha)
                commit_list.addItem(item)

            sha_edit = QLineEdit(dialog)
            sha_edit.setPlaceholderText(
                "Vollständigen 40-stelligen Commit-SHA eingeben"
                if is_de else
                "Enter full 40-character commit SHA"
            )
            layout.addWidget(sha_edit)

            refresh_button = QPushButton(
                "Commit-Liste aktualisieren"
                if is_de else
                "Refresh commit list"
            )
            layout.addWidget(refresh_button)

            
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel,
                parent=dialog,
            )

            buttons.button(
                QDialogButtonBox.StandardButton.Ok
            ).setText("OK" if is_de else "OK")

            buttons.button(
                QDialogButtonBox.StandardButton.Cancel
            ).setText("Abbrechen" if is_de else "Cancel")

            layout.addWidget(buttons)


            def use_list_selection():
                item = commit_list.currentItem()
                if item is not None:
                    sha_edit.setText(str(item.data(0x0100)))

            commit_list.itemDoubleClicked.connect(
                lambda _item: use_list_selection()
            )
            commit_list.currentItemChanged.connect(
                lambda _current, _previous: use_list_selection()
            )

            
            def refresh_list():
                try:
                    if git_run(["status", "--porcelain"], timeout=60):
                        
                        QMessageBox.warning(
                            dialog,
                            "OSCam-Emu",
                            tr(
                                "working_tree_not_clean",
                                "Arbeitsverzeichnis ist nicht sauber.",
                                "Working tree is not clean."
                            )
                        )

                        return

                    selected_url = str(
                        repo_combo.currentData() or ""
                    ).strip()

                    
                    if not selected_url:
                        raise RuntimeError(
                            tr(
                                "no_repository_url",
                                "Keine Repository-URL ausgewählt.",
                                "No repository URL selected."
                            )
                        )


                    remote_ref = "refs/remotes/revision-picker/emu"

                    
                    git_run(
                        [
                            "fetch",
                            "--force",
                            selected_url,
                            f"+refs/heads/{emu_branch}:{remote_ref}",
                        ],
                        timeout=1200,
                    )


                    fresh = git_run(
                        [
                            "log",
                            remote_ref,
                            "-100",
                            "--date=format:%Y-%m-%d %H:%M",
                            "--format=%H%x09%ad%x09%s",
                        ],
                        timeout=120,
                    )

                    commit_list.clear()
                    sha_edit.clear()
                    local_seen = set()

                    for line in fresh.splitlines():
                        parts = line.split("\t", 2)
                        if len(parts) != 3:
                            continue

                        sha, date_text, subject = parts
                        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
                            continue

                        sha = sha.lower()
                        if sha in local_seen:
                            continue
                        local_seen.add(sha)

                        item = QListWidgetItem(
                            f"{date_text}  {sha[:12]}  {subject}"
                        )
                        item.setData(0x0100, sha)
                        commit_list.addItem(item)

                except Exception as exc:
                    QMessageBox.critical(
                        dialog,
                        "Git",
                        str(exc),
                    )

            refresh_button.clicked.connect(refresh_list)
            repo_combo.currentIndexChanged.connect(
                lambda _index: refresh_list()
            )

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return False

            selected = sha_edit.text().strip().lower()

            selected_emu_url = str(
                repo_combo.currentData() or ""
            ).strip()

                
            if not selected_emu_url:
                QMessageBox.warning(
                    self,
                    "OSCam-Emu",
                    tr(
                        "select_repository_prompt",
                        "Bitte ein Repository auswählen.",
                        "Please select a repository."
                    )
                )
                return False

                

            if not selected:
                QMessageBox.warning(
                    self,
                    "OSCam-Emu",
                    "Bitte einen Commit auswählen oder eine SHA eingeben."
                    if is_de else
                    "Please select a commit or enter a SHA."
                )
                return False

            if not re.fullmatch(r"[0-9a-f]{40}", selected):
                QMessageBox.warning(
                    self,
                    "OSCam-Emu",
                    "Es muss eine vollständige 40-stellige Git-SHA eingegeben werden."
                    if is_de else
                    "A complete 40-character Git SHA is required."
                )
                return False

            # Manuell eingegebene SHA bei Bedarf direkt vom aktiven OSCam-Emu-Remote holen.
            local_selected = git_run(
                ["rev-parse", "--verify", selected + "^{commit}"],
                check=False,
                timeout=60,
            )

            
            if local_selected != selected:
                git_run(
                    ["fetch", selected_emu_url, selected],
                    timeout=1200,
                )


            if local_selected != selected:
                raise RuntimeError(
                    "Der gewünschte OSCam-Emu-Commit konnte nicht aus dem Repository geladen werden."
                    if is_de else
                    "The requested OSCam-Emu commit could not be fetched from the repository."
                )

            # Exakt diesen Commit auschecken.
            git_run(
                ["checkout", "--detach", selected],
                timeout=1200,
            )

            checked_out = git_run(
                ["rev-parse", "HEAD"],
                check=False,
                timeout=60,
            )

            if checked_out != selected:
                raise RuntimeError(
                    "Der ausgewählte OSCam-Emu-Commit konnte nicht exakt ausgecheckt werden."
                    if is_de else
                    "The selected OSCam-Emu commit could not be checked out exactly."
                )

            # Commit und das dazugehörige Repository gemeinsam merken.
            # Eine Revision darf später niemals versehentlich mit einer
            # anderen OSCam-Emu-Repo-URL verwendet werden.
            self.selected_emu_commit = selected
            self.selected_emu_commit_repo_url = selected_emu_url
            self.display_emu_commit = selected
            globals()["SELECTED_EMU_COMMIT"] = selected
            globals()["SELECTED_EMU_COMMIT_REPO_URL"] = selected_emu_url
            self.update_revision_button_labels()

            status_text = (
                f"OSCam-Emu Basis: {selected[:12]}"
                if is_de else
                f"OSCam-Emu base: {selected[:12]}"
            )

            try:
                if hasattr(self, "info_text"):
                    self.info_text.append(f"<b>✅ {status_text}</b>")
                    self.info_text.ensureCursorVisible()
                QApplication.processEvents()
            except Exception:
                pass

            QMessageBox.information(
                self,
                "OSCam-Emu",
                (
                    f"Commit erfolgreich ausgewählt:\n\n{selected}\n\n"
                    "Dieser Commit wird bei der nächsten Patch-Erstellung als OSCam-Emu-Basis verwendet."
                ) if is_de else (
                    f"Commit selected successfully:\n\n{selected}\n\n"
                    "This commit will be used as the OSCam-Emu base for the next patch."
                )
            )
            return True

        except Exception as exc:
            print("[OSCAM-EMU CHECKOUT] Fehler:", repr(exc), flush=True)
            try:
                QMessageBox.critical(
                    self,
                    "OSCam-Emu Git",
                    f"Fehler:\n{exc}"
                )
            except Exception:
                pass
            return False

    def set_active_button(self, active_key):
        self.active_button_key = active_key

        # 1. Sicherstellen, dass wir die richtige Textfarbe aus dem aktuellen Theme haben
        # Wir probieren 'fg', falls das fehlt 'text', sonst weiß als Notlösung.
        text_color = current_diff_colors.get(
            "fg", current_diff_colors.get("text", "#FFFFFF")
        )

        # 2. Die Hover-Farbe für den inaktiven Zustand holen
        hover_color = current_diff_colors.get("hover", current_diff_colors["bg"])

        for key, btn in self.buttons.items():
            if key == active_key:
                # AKTIVER BUTTON: Giftgrün (wie in deinem Original)
                # Tipp: Du könntest hier auch current_diff_colors['active'] nutzen!
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: #00FF00; 
                        color: #000000; 
                        border-radius: {self.BUTTON_RADIUS}px; 
                        min-height: {self.BUTTON_HEIGHT}px;
                        font-weight: bold;
                        border: 2px solid white;
                    }}
                """
                )
            else:
                # INAKTIVE BUTTONS: Nutzen das aktuelle Farbschema (Theme)
                # Wir bauen hier auch den Hover-Effekt wieder ein, damit er nicht verloren geht!
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {current_diff_colors['bg']}; 
                        color: {text_color}; 
                        border-radius: {self.BUTTON_RADIUS}px; 
                        min-height: {self.BUTTON_HEIGHT}px;
                    }}
                    QPushButton:hover {{
                        background-color: {hover_color};
                    }}
                """
                )

    def repaint_ui_colors(self):
        """
        Wendet das aktuell gewählte Farbschema auf die normalen GUI-Elemente an.

        Individuelle Buttons wie:
        - Grid-Buttons
        - S3
        - S4
        - NCam

        werden nicht überschrieben.

        Zusätzlich wird die Farbauswahl-ComboBox (color_box)
        vollständig an das aktuell gewählte Farbschema angepasst.
        """

        from PyQt6.QtWidgets import (
            QPushButton,
            QCheckBox,
            QComboBox,
            QListView,
        )
        from PyQt6.QtGui import QColor

        global current_diff_colors

        # ============================================================
        # 1. AKTUELLE THEME-FARBEN
        # ============================================================

        text_color = current_diff_colors.get(
            "fg",
            current_diff_colors.get(
                "text",
                "#FFFFFF"
            )
        )

        bg_color = current_diff_colors.get(
            "bg",
            "#2F2F2F"
        )

        hover_color = current_diff_colors.get(
            "hover",
            "#444444"
        )

        active_color = current_diff_colors.get(
            "active",
            "#666666"
        )

        # ============================================================
        # 2. INDIVIDUELLE BUTTONS SCHÜTZEN
        # ============================================================

        protected_buttons = {
            "btn_s3",
            "btn_s4",
            "btn_ncam",
        }

        # ============================================================
        # 3. GRID-BUTTONS SCHÜTZEN
        # ============================================================

        grid_buttons = set()

        if hasattr(self, "buttons") and isinstance(
            self.buttons,
            dict
        ):
            try:
                grid_buttons = {
                    btn
                    for btn in self.buttons.values()
                    if btn is not None
                }

            except Exception:
                grid_buttons = set()

        # ============================================================
        # 4. NORMALE BUTTONS
        # ============================================================

        for btn in self.findChildren(QPushButton):

            try:

                # Alle Buttons erhalten dasselbe aktive Farbschema.
                # Der Stats-Button wird weiter unten mit seinem Toggle-Zustand gestylt.
                btn.setGraphicsEffect(None)
                if not btn.toolTip().strip():
                    label = btn.text().replace("&", "").strip() or btn.objectName() or "Button"
                    btn.setToolTip(label)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)

                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {bg_color};
                        color: {text_color};
                        border-radius: 10px;
                        font-weight: 700;
                        padding: 2px 6px;
                        border: 1px solid {text_color};
                        min-height: 35px;
                    }}

                    QPushButton:hover {{
                        background-color: {hover_color};
                        color: {text_color};
                        border: 1px solid {text_color};
                    }}

                    QPushButton:pressed {{
                        background-color: {active_color};
                        color: {text_color};
                        border: 2px solid {text_color};
                    }}

                    QPushButton:disabled {{
                        background-color: {active_color};
                        color: #777777;
                        border: 1px solid #555555;
                    }}
                    """
                )

            except RuntimeError:
                continue

        # ============================================================
        # 5. STATS-TOGGLE: aktiviert = rote Schrift, deaktiviert = Theme
        # ============================================================
        cb = getattr(self, "telemetry_cb", None)
        if cb:
            try:
                if not cb.toolTip().strip():
                    cb.setToolTip("Anonyme Nutzungsstatistik aktivieren oder deaktivieren.")
                cb.setStyleSheet(f"""
                    QPushButton {{ background-color: {bg_color}; color: {text_color};
                                  border-radius: 10px; font-weight: 700; padding: 2px 12px;
                                  border: 1px solid {text_color}; min-height: 35px; }}
                    QPushButton:hover {{ background-color: {hover_color}; color: {text_color};
                                         border: 2px solid {text_color}; }}
                    QPushButton:checked {{ color: #FF0000; background-color: {bg_color};
                                           border: 2px solid #FF0000; }}
                    QPushButton:checked:hover {{ color: #FF0000; background-color: {hover_color};
                                                 border: 2px solid #FF0000; }}
                    QPushButton:pressed {{ background-color: {active_color}; }}
                """)
            except RuntimeError:
                pass

        # ============================================================
        # 6. FARB-AUSWAHLBOX / COMBOBOX
        # ============================================================

        color_box = getattr(
            self,
            "color_box",
            None
        )

        if color_box:

            try:

                # ----------------------------------------------------
                # Haupt-ComboBox
                # ----------------------------------------------------

                color_box.setStyleSheet(
                    f"""
                    QComboBox {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {text_color};
                        border-radius: 8px;
                        padding: 5px 10px;
                        min-height: 35px;
                        font-weight: 700;
                    }}

                    QComboBox:hover {{
                        background-color: {hover_color};
                        color: {text_color};
                        border: 1px solid {text_color};
                    }}

                    QComboBox:focus {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {text_color};
                    }}

                    QComboBox:on {{
                        background-color: {bg_color};
                        color: {text_color};
                    }}

                    QComboBox:disabled {{
                        background-color: {active_color};
                        color: #777777;
                        border: 1px solid #555555;
                    }}

                    QComboBox::drop-down {{
                        background-color: {bg_color};
                        border: none;
                        width: 30px;
                        subcontrol-origin: padding;
                        subcontrol-position: top right;
                    }}

                    QComboBox::drop-down:hover {{
                        background-color: {hover_color};
                    }}

                    QComboBox::down-arrow {{
                        width: 10px;
                        height: 10px;
                    }}

                    QComboBox QAbstractItemView {{
                        background-color: {bg_color};
                        color: {text_color};
                        border: 1px solid {text_color};
                        selection-background-color: {hover_color};
                        selection-color: {text_color};
                        outline: none;
                        padding: 2px;
                    }}

                    QComboBox QAbstractItemView::item {{
                        background-color: {bg_color};
                        color: {text_color};
                        padding: 7px 10px;
                        min-height: 25px;
                    }}

                    QComboBox QAbstractItemView::item:hover {{
                        background-color: {hover_color};
                        color: {text_color};
                    }}

                    QComboBox QAbstractItemView::item:selected {{
                        background-color: {hover_color};
                        color: {text_color};
                    }}

                    QComboBox QAbstractItemView::item:selected:hover {{
                        background-color: {active_color};
                        color: {text_color};
                    }}
                    """
                )

                # ----------------------------------------------------
                # Wichtig:
                #
                # Bei bestimmten Qt-Styles wird das Popup als separates
                # View-Widget behandelt. Deshalb setzen wir zusätzlich
                # den View direkt.
                # ----------------------------------------------------

                try:

                    view = color_box.view()

                    if view:

                        view.setStyleSheet(
                            f"""
                            QListView {{
                                background-color: {bg_color};
                                color: {text_color};
                                border: 1px solid {text_color};
                                outline: none;
                                padding: 2px;
                            }}

                            QListView::item {{
                                background-color: {bg_color};
                                color: {text_color};
                                padding: 7px 10px;
                                min-height: 25px;
                            }}

                            QListView::item:hover {{
                                background-color: {hover_color};
                                color: {text_color};
                            }}

                            QListView::item:selected {{
                                background-color: {hover_color};
                                color: {text_color};
                            }}

                            QListView::item:selected:hover {{
                                background-color: {active_color};
                                color: {text_color};
                            }}
                            """
                        )

                except (
                    RuntimeError,
                    AttributeError
                ):
                    pass

            except RuntimeError:
                pass

        # ============================================================
        # 7. PROGRESS BAR
        # ============================================================

        pb = getattr(
            self,
            "progress_bar",
            None
        )

        if pb:

            try:

                if pb.value() == 0:

                    if hasattr(
                        self,
                        "pbar_idle"
                    ):
                        self.pbar_idle()

                else:

                    if hasattr(
                        self,
                        "_idle_anim"
                    ):
                        self._idle_anim.stop()

                    pb.setStyleSheet(
                        f"""
                        QProgressBar {{
                            border: 1px solid {text_color};
                            border-radius: 7px;
                            background-color: {bg_color};
                            text-align: center;
                            color: {text_color};
                            font-weight: 700;
                        }}

                        QProgressBar::chunk {{
                            background-color: {active_color};
                            border-radius: 6px;
                        }}
                        """
                    )

            except RuntimeError:
                pass

        # ============================================================
        # 8. LABELS & HEADER
        # ============================================================

        labels = [
            "lang_label",
            "color_label",
            "commit_label",
            "controls_header",
            "github_header",
            "header_label",
            "status_label",
        ]

        for lbl_name in labels:

            lbl = getattr(
                self,
                lbl_name,
                None
            )

            if not lbl:
                continue

            try:

                is_header = (
                    "header"
                    in lbl_name
                )

                label_bg = (
                    bg_color
                    if is_header
                    else "transparent"
                )

                lbl.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {text_color};
                        font-weight: 700;
                        font-size: 18px;
                        background-color: {label_bg};
                        border: none;
                    }}
                    """
                )

            except RuntimeError:
                pass

        # ============================================================
        # 9. HAUPTFENSTER-HINTERGRUND
        # ============================================================

        try:

            self.setAutoFillBackground(
                True
            )

            palette = self.palette()

            palette.setColor(
                self.backgroundRole(),
                QColor(bg_color)
            )

            self.setPalette(
                palette
            )

        except (
            RuntimeError,
            AttributeError,
            TypeError
        ):
            pass

        # ============================================================
        # 10. PROGRESSBAR IDLE NACH THEME-ÄNDERUNG
        # ============================================================

        try:

            if (
                pb
                and pb.value() == 0
                and hasattr(
                    self,
                    "pbar_idle"
                )
            ):
                self.pbar_idle()

        except RuntimeError:
            pass

        # ============================================================
        # 11. GUI NEU ZEICHNEN
        # ============================================================

        try:

            self.update()
            self.repaint()

        except RuntimeError:
            pass

    def run_action(self, action_func):
        """
        Führt eine Aktion aus, zeigt Fortschritt in der ProgressBar und Meldungen im Info-Widget.
        action_func: Funktion, die (info_widget, progress_callback) als Parameter akzeptiert
        """
        lang = getattr(self, "LANG", LANG)  # aktuelle GUI-Sprache

        try:
            # Progress starten
            self.progress.setValue(0)
            self.progress.setStyleSheet(
                f"QProgressBar::chunk {{background-color:{current_diff_colors['bg']};}}"
            )

            # Aktion ausführen
            action_func(
                info_widget=self.info_text, progress_callback=self.progress.setValue
            )

            # Fortschritt abschließen
            self.progress.setValue(100)

        except Exception as e:
            # Fehler im Info-Widget ausgeben, sprachabhängig
            error_text = (
                TEXTS[lang]
                .get("generic_error", "❌ Fehler: {error}")
                .format(error=str(e))
            )
            self.append_info(self.info_text, error_text, "error")
            self.progress.setValue(0)



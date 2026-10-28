"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerCoreMixin:
    """Patch Manager Core"""

    def __init__(self):
        # 1. IMPORTS & INITIALER SCHUTZ
        from PyQt6.QtGui import QFont, QFontMetrics
        from PyQt6.QtGui import QColor, QFont, QTextCursor, QIcon
        from PyQt6.QtCore import Qt, QTimer, QDateTime, QSize, QUrl
        from PyQt6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QComboBox
        import subprocess, platform, shutil, os, re, sys

        # Build-Log-Verzeichnis bereits beim Programmstart anlegen. So ist
        # sichtbar, ob genau diese gui.py ausgeführt wird, auch wenn später
        # kein S3/S4/NCam-Terminal gestartet werden kann.
        try:
            self.build_log_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "build_logs"
            )
            os.makedirs(self.build_log_dir, exist_ok=True)
        except OSError as log_setup_error:
            self.build_log_dir = None
            print(f"[BUILD-LOG] Verzeichnis konnte nicht angelegt werden: {log_setup_error}")

        self.is_loading = True  # Schutz vor Timer während Setup

        # 2. ATTR-BOOTSTRAP
        self.btn_matrix = None
        self.slider_speed = None
        self.color_box = None
        self.status_leds = []  # System-Status LEDs
        self.user_leds = []  # User-Blink-LEDs
        self.all_buttons = []
        self.option_buttons = {}
        self.buttons = {}

        # Keine feste Revision beim Programmstart.
        # Create Patch verwendet dadurch automatisch den aktuellen
        # Streamboard-HEAD und den aktuellen Stand des gewählten
        # OSCam-Emu-Repositories, solange der Benutzer nichts auswählt.
        self.selected_streamboard_commit = None
        self.selected_emu_commit = None
        self.selected_emu_commit_repo_url = ""
        # Nur Anzeige des zuletzt tatsächlich gebauten Patches.
        # Diese Werte sind KEINE feste Auswahl und werden bei Create Patch
        # nicht als Basis erzwungen.
        self.display_streamboard_commit = None
        self.display_emu_commit = None
        globals()["SELECTED_STREAMBOARD_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT_REPO_URL"] = ""

        self._blink_state = True

        # QWidget wird einmalig in PatchManagerGUI.__init__ initialisiert.
        # Ein zweiter Aufruf aus dem Mixin kann bei PyQt/SIP rekursiv
        # erneut in diese __init__-Methode gelangen.
        self.current_config = self.load_config_from_file()
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = "S3 Simplebuild (Original)"
        self.s3_repo_combo = None
        self.s3_install_worker = None
        self.sound_manager = SystemSoundManager(self, volume=0.45)
        set_active_sound_manager(self.sound_manager)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.sound_manager.shutdown)
        self.sound_manager.play_login()
        # Globalen Klicksound-Filter registrieren
        self.button_click_sound_filter = ButtonClickSoundFilter(
            self.sound_manager,
            self
        )

        QApplication.instance().installEventFilter(
            self.button_click_sound_filter
        )
        # --- TIMER-SEKTION ---
        # 3. INFOSCREEN & REDIRECTOR FIX
        self.current_rev = getattr(
            self, "current_rev", "11943"
        )  # Falls nicht schon gesetzt
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        try:
            self.stdout_redir = StreamToGui()
            self.stdout_redir.callback = lambda msg: self.append_info(
                self.info_text, msg, "info"
            )
            sys.stdout = self.stdout_redir
            self.stderr_redir = StreamToGui()
            self.stderr_redir.callback = lambda msg: self.append_info(
                self.info_text, msg, "error"
            )
            sys.stderr = self.stderr_redir
        except Exception:
            pass

        
        # S3-Repository-Auswahl und Worker initialisieren
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        
        self.current_config = self.load_config_from_file()

        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_install_worker = None

        # Die ComboBox hier erstellen und NICHT wieder auf None setzen.
        self.s3_repo_combo = QComboBox()

        for name, url in self.s3_repository_options.items():
            self.s3_repo_combo.addItem(name, url)

        index = self.s3_repo_combo.findText(self.selected_s3_repository)
        if index >= 0:
            self.s3_repo_combo.setCurrentIndex(index)

        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )


        # ComboBox erst nach der Initialisierung erstellen
        self.s3_repo_combo = QComboBox()

        for name, url in self.s3_repository_options.items():
            self.s3_repo_combo.addItem(name, url)

        index = self.s3_repo_combo.findText(
            self.selected_s3_repository
        )

        if index >= 0:
            self.s3_repo_combo.setCurrentIndex(index)

        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_repo_combo = None
        self.s3_install_worker = None

        ## --- Pfad für Standard S3 ---
        stored_s3 = self.current_config.get("s3_custom_path", "/opt/s3")
        self.S3_PATH = os.path.normpath(stored_s3)

        # --- Pfad für NCam Bonecrew (EIGENE VARIABLE!) ---
        stored_ncam = self.current_config.get(
            "ncam_custom_path", "/opt/s3_ncam_bonecrew_test"
        )
        self.NCAM_PATH = os.path.normpath(stored_ncam)

        # --- NEU: SOFORT-CHECK BEIM START ---
        # Wir triggern die Prüfung kurz nach dem Start, damit der Button
        # von "Install" auf "OK" springt, falls S3 gefunden wurde.
        QTimer.singleShot(100, self.update_ui_texts)

        stored_lang = str(self.current_config.get("language", "de")).lower()
        self.LANG = stored_lang if stored_lang in ["en", "de"] else "de"

        # TEXT muss VOR init_ui() verfügbar sein.
        # init_ui() erzeugt bereits Buttons/Labels und verwendet dafür
        # self.TEXT.get(...). update_language() wird erst nach init_ui()
        # aufgerufen und kann daher nicht die Erstinitialisierung übernehmen.
        self.TEXT = TEXTS.get(
            self.LANG,
            TEXTS.get("en", {})
        )

        self.patch_modifier = self.current_config.get("patch_modifier", "Default")
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.PLUGIN_DIR = self.base_dir  # Plugin-Verzeichnis

        stored_work_dir = self.current_config.get("work_dir", self.base_dir)
        if not isinstance(stored_work_dir, str) or not stored_work_dir.strip():
            stored_work_dir = self.base_dir

        self.WORK_DIR = os.path.normpath(stored_work_dir)
        self.TEMP_REPO = os.path.join(self.base_dir, "streamboard-git")  # Temp-Repo Ordner
        self.PATCH_EMU_GIT_DIR = os.path.join(
            self.base_dir, "oscam-emu-git"
        )  # Emu-Git Ordner
        current_path = self.current_config.get(
            "s3_patch_path", globals().get("OLD_PATCH_DIR", "./")
        )
        self.OLD_PATCH_DIR = os.path.normpath(current_path)
        self.OLD_PATCH_FILE = os.path.join(self.OLD_PATCH_DIR, "oscam-emu.patch")
        self.ALT_PATCH_FILE = os.path.join(self.OLD_PATCH_DIR, "oscam-emu.altpatch")
        # --- Direkt nach ALT_PATCH_FILE einfügen ---
        target_dirs = [
            self.PLUGIN_DIR,
            self.TEMP_REPO,
            self.PATCH_EMU_GIT_DIR,
            self.OLD_PATCH_DIR,
        ]

        for d in target_dirs:
            if d and not os.path.exists(d):
                try:
                    os.makedirs(d, exist_ok=True)
                except:
                    pass

        # Basis-Variablen
        self.active_button_key = ""
        self.main_grid_layout = None
        self.latest_version = (
            globals().get("APP_VERSION", "1.0.0").replace("v", "").strip()
        )
        self.BUTTON_RADIUS = 5

        # 5. HAUPT-UI AUFBAUEN
        self.live_indicator = QLabel()
        # Initialer Text
        self.live_indicator.setText(
            "<span style='color:#ff0000;'>●</span> <span style='color:#ffffff;'>LIVE | System Monitor</span>"
        )
        self.live_indicator.setStyleSheet(
            """
            font-weight: bold; 
            font-family: 'Courier New', monospace;
            font-size: 22px;
            background: transparent;
        """
        )

        self.init_ui()
        self._fit_all_button_texts()
        # 6. TIMER VORBEREITEN (Nur für User-LEDs, nicht starten)
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.animate_status_bar)

        # 7. THEME & FARBEN
        saved_color = self.current_config.get("color", "Classics")
        if hasattr(self, "color_box") and self.color_box:
            self.color_box.blockSignals(True)
            index = self.color_box.findText(saved_color)
            if index != -1:
                self.color_box.setCurrentIndex(index)
            self.color_box.blockSignals(False)
            self.color_box.currentIndexChanged.connect(self.change_colors)
        self.color_box.setToolTip(
            "Farbschema der Oberfläche auswählen"
            if str(getattr(self, "LANG", self.cfg.get("language", "de"))).lower() in ("de", "0")
            else "Choose the interface color theme"
        )
        self.color_box.setToolTipDuration(10000)

        self.update_language()
        #self.change_colors()

        # Theme-Status ohne Blinken anwenden
        target_theme = self.current_config.get("theme_mode", "standard")
        if hasattr(self, "toggle_matrix"):
            self.toggle_matrix(force_state=target_theme)

        # ----------------------------
        # 8. FINALER SLIDER- & LED-FIX
        # ----------------------------
        current_speed = self.current_config.get("blink_speed", 0)

        if hasattr(self, "slider_speed") and self.slider_speed:
            self.slider_speed.blockSignals(True)
            self.slider_speed.setValue(current_speed)
            self.slider_speed.blockSignals(False)

            if hasattr(self, "update_label_only"):
                self.update_label_only(current_speed)

            if hasattr(self, "update_blink_speed"):
                self.slider_speed.valueChanged.connect(self.update_blink_speed)

        # System-Status LEDs immer statisch setzen
        if hasattr(self, "set_system_leds_static"):
            self.set_system_leds_static()

        # User-LED Timer beim Start stoppen
        if hasattr(self, "blink_timer"):
            self.blink_timer.stop()

        if hasattr(self, "update_blink_speed"):
            self.update_blink_speed(current_speed)

        if hasattr(self, "update_plugin_button_state"):
            self.update_plugin_button_state()

        # --- LED STATUS WIEDERHERSTELLEN ---
        # 1. Den Wert aus der geladenen Config holen (Standard: True)
        saved_led_enabled = self.current_config.get("led_enabled", True)

        # 2. Die Checkbox visuell synchronisieren (ohne Signale zu feuern)
        if hasattr(self, "led_checkbox"):
            self.led_checkbox.blockSignals(True)
            self.led_checkbox.setChecked(saved_led_enabled)
            self.led_checkbox.blockSignals(False)

        # 3. Die tatsächliche Blink-Logik/Timer starten oder stoppen
        # WICHTIG: Wir blockieren kurzzeitig das Speichern, damit beim Start
        # nicht unnötig in die config.json geschrieben wird (Performance & Loop-Schutz)
        self._block_config_save = True
        self.toggle_leds(saved_led_enabled)
        self._block_config_save = False

        # 4. Falls die LEDs aus sind, sofort den dunklen Zustand erzwingen
        if not saved_led_enabled:
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()

        lang = getattr(self, "LANG", "de").lower()
        init_msg = (
            "Initialisiere Generator..."
            if lang == "de"
            else "Initializing Generator..."
        )

        # Styling: Rot (#FF0000), Schriftstärke 900 (Extra Bold)
        self.info_text.setHtml(
            f"<div style='margin: 20px; font-family: sans-serif; text-align: center;'>"
            f"<b style='color:#FF0000; font-size:22pt; font-weight:900;'>{init_msg}</b>"
            f"</div>"
        )
        # Ganz am Ende der __init__ einfügen:

        # 1. Wert aus Config holen
        saved_led_enabled = self.current_config.get("led_enabled", True)

        # 2. Checkbox finden und setzen (WICHTIG: Name prüfen!)
        # Falls die Checkbox bei dir anders heißt, hier anpassen:
        target_cb = getattr(self, "led_checkbox", None)
        if target_cb:
            target_cb.blockSignals(True)
            target_cb.setChecked(saved_led_enabled)
            target_cb.blockSignals(False)

        # 3. Die Logik final erzwingen
        self.toggle_leds(saved_led_enabled)

        # 4. Falls der Timer trotzdem läuft, obwohl er aus sein soll:
        if not saved_led_enabled and hasattr(self, "blink_timer"):
            self.blink_timer.stop()
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()

        # 1. Willkommens-Info (500ms)
        # QTimer.singleShot(500, self.show_welcome_info)

        # 2. System-Check (2000ms) - Injiziert sich in den Anker
        QTimer.singleShot(2000, lambda: self.run_full_system_check(clear_log=False))

        # Die Update-Prüfung wird einmalig nach Abschluss des Systemchecks
        # in _system_check_finished() gestartet. Kein paralleler Timer, damit
        # keine doppelten Meldungen oder konkurrierenden Infoscreen-Updates entstehen.

        # 4. OSCam Monitor (8500ms)
        QTimer.singleShot(4500, self.start_oscam_update_check)
        self.init_button_signals()

        self.is_loading = False  # Initialisierung abgeschlossen

        # Ein einheitlicher Startmodus: startup.py zeigt das Hauptfenster
        # maximiert. Nicht nachträglich in exklusiven Vollbildmodus wechseln,
        # da dies auf Windows wie ein zweites/anderes Fenster wirken kann.
        QTimer.singleShot(0, self.showMaximized)

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

    def choose_oscam_source(self):
        """Öffnet eine separate Auswahlbox für das OSCam-Quellrepository."""
        from PyQt6.QtWidgets import QInputDialog
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        names = list(STREAM_REPO_CHOICES.keys())
        current = get_selected_stream_repo_name()
        selected, accepted = QInputDialog.getItem(
            self,
            "OSCam-Quelle auswählen" if is_de else "Select OSCam source",
            "Repository für Patch-Erstellung:" if is_de else "Repository for patch creation:",
            names,
            names.index(current) if current in names else 0,
            False,
        )
        if not accepted or selected not in STREAM_REPO_CHOICES:
            return
        try:
            config_path = globals().get("CONFIG_FILE", "config.json")
            config = {}
            if os.path.isfile(config_path):
                with open(config_path, "r", encoding="utf-8") as handle:
                    loaded = json.load(handle)
                    if isinstance(loaded, dict):
                        config = loaded
            config["oscam_source"] = selected
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=4, ensure_ascii=False)
            # Aktuelle Laufzeit-Workflows verwenden ebenfalls die Auswahl.
            globals()["STREAMREPO_URL"] = STREAM_REPO_CHOICES[selected]
            self.oscam_source_button.setText("Oscam Git URL")
            message = f"OSCam-Quelle eingestellt: {selected}\n{STREAM_REPO_CHOICES[selected]}"
            if hasattr(self, "append_info"):
                self.append_info(self.info_text, message, "success")
            elif hasattr(self, "info_text"):
                self.info_text.append(message)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "OSCam-Quelle",
                f"Einstellung konnte nicht gespeichert werden:\n{exc}",
            )

    def _play_sys_sound(self, sound_type="standard"):
        """Spielt Systemfeedback über den gemeinsamen Windows/Linux-Backend."""
        manager = getattr(self, "sound_manager", None) or get_active_sound_manager()
        if manager is None:
            return False
        kind = str(sound_type).lower()
        if kind in ("error", "critical", "failure"):
            return manager.play_error()
        if kind in ("warning", "exclamation"):
            return manager.play_warning()
        if kind in ("click", "button"):
            return manager.play("click")
        return manager.play_info()

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

    def change_colors(self):
        """
        Aktualisiert das komplette Farbschema der GUI.

        Funktionen:
        - Liest die aktuell gewählte Farbe sicher aus der Config/ComboBox.
        - Aktualisiert current_diff_colors zentral.
        - Repaintet die normalen Buttons.
        - Schützt S3/S4/NCam-Installationsbuttons vor Theme-Überschreibung.
        - Aktualisiert Checkbox, Header, Badges und Status.
        - Setzt den LED-Zustand nach dem Repaint erneut.
        - Synchronisiert theme_mode mit dem gewählten Theme.
        - Speichert die Änderung zentral.
        """

        from PyQt6.QtWidgets import QPushButton

        global current_diff_colors, current_color_name

        # ============================================================
        # 0. FINAL LABEL AUSBLENDEN
        # ============================================================
        try:
            if hasattr(self, "hide_final_label"):
                self.hide_final_label()
            elif getattr(self, "final_label", None):
                self.final_label.hide()
        except RuntimeError:
            pass

        # ============================================================
        # 1. CONFIG SICHER ERMITTELN
        # ============================================================
        config_obj = getattr(
            self,
            "cfg",
            getattr(self, "current_config", {})
        )

        if not isinstance(config_obj, dict):
            config_obj = {}

        saved_color = config_obj.get("color", "Classics")

        # ============================================================
        # 2. AKTUELLE FARBE ERMITTELN
        # ============================================================
        color_from_combo = ""

        try:
            if hasattr(self, "color_box") and self.color_box:
                color_from_combo = self.color_box.currentText().strip()
        except RuntimeError:
            color_from_combo = ""

        # Während des Startvorgangs niemals eine leere/noch nicht
        # initialisierte ComboBox verwenden.
        if getattr(self, "is_loading", False):
            current_color_name = saved_color
        elif color_from_combo:
            current_color_name = color_from_combo
        else:
            current_color_name = saved_color

        # ============================================================
        # 3. THEME SUCHEN
        # ============================================================
        base_colors = DIFF_COLORS.get(current_color_name)

        # Fallback, falls Theme-Key nicht existiert
        if not base_colors:
            base_colors = DIFF_COLORS.get(
                saved_color,
                DIFF_COLORS.get(
                    "Classics",
                    {
                        "bg": "#2F2F2F",
                        "fg": "#FFFFFF",
                        "hover": "#444444",
                        "active": "#222222",
                    },
                ),
            )

        # ============================================================
        # 4. FARBEN ZENTRAL AUFBAUEN
        # ============================================================
        bg = base_colors.get("bg", "#2F2F2F")
        fg = base_colors.get(
            "fg",
            base_colors.get("text", "#FFFFFF")
        )

        hover = base_colors.get("hover")

        if not hover:
            if hasattr(self, "adjust_color"):
                hover = self.adjust_color(bg, 1.20)
            else:
                hover = bg

        active = base_colors.get("active")

        if not active:
            if hasattr(self, "adjust_color"):
                active = self.adjust_color(bg, 0.80)
            else:
                active = bg

        current_diff_colors = {
            **base_colors,
            "bg": bg,
            "fg": fg,
            "text": base_colors.get("text", fg),
            "hover": hover,
            "active": active,
        }

        # ============================================================
        # 5. SOUND
        # ============================================================
        try:
            safe_play_func = globals().get("safe_play")
            if safe_play_func:
                safe_play_func("dialog-information.oga")
        except Exception:
            pass

        # ============================================================
        # 6. ALLGEMEINES REPAINT
        # ============================================================
        try:
            if hasattr(self, "repaint_ui_colors"):
                self.repaint_ui_colors()
        except Exception:
            pass


        # ============================================================
        # 7/8. KEINE Sonderfarbe für aktive Grid-Buttons:
        # Alle Buttons bleiben im ausgewählten Farbschema.
        # ============================================================

        # ============================================================
        # 9. INSTALLATIONSBUTTONS EXPLIZIT SCHÜTZEN
        #
        # Ihre individuelle Farbe bleibt erhalten.
        # ============================================================
        for attr_name in ("btn_s3", "btn_s4", "btn_ncam"):

            btn = getattr(self, attr_name, None)

            if not btn:
                continue

            try:
                # Vorhandenes individuelles Styling NICHT verändern.
                # Falls der Button noch keinen Style besitzt,
                # bekommt er einen neutralen Fallback.
                if not btn.styleSheet().strip():

                    btn.setStyleSheet(
                        f"""
                        QPushButton {{
                            text-align: left;
                            padding-left: 8px;
                            font-weight: bold;
                            background-color: {bg};
                            color: {fg};
                            border: 2px solid {fg};
                            border-radius: 8px;
                        }}
                        """
                    )


            except RuntimeError:
                pass

        # ============================================================
        # 10. TELEMETRIE CHECKBOX
        # ============================================================
        telemetry_cb = getattr(self, "telemetry_cb", None)

        if telemetry_cb:

            try:
                telemetry_cb.setStyleSheet(
                    f"""
                    QCheckBox {{
                        background-color: {bg};
                        color: {fg};
                        border: 2px solid {fg};
                        border-radius: 4px;
                        padding: 5px 10px;
                        font-weight: 700;
                    }}

                    QCheckBox:hover {{
                        background-color: {hover};
                    }}

                    QCheckBox::indicator {{
                        width: 16px;
                        height: 16px;
                        border: 2px solid {fg};
                        border-radius: 3px;
                        background-color: transparent;
                    }}

                    QCheckBox::indicator:hover {{
                        border: 1px solid white;
                    }}

                    QCheckBox::indicator:checked {{
                        background-color: {fg};
                        border: 1px solid white;
                    }}
                    """
                )

            except RuntimeError:
                pass

        # ============================================================
        # 11. HEADER CONTAINER
        # ============================================================
        header_container = getattr(self, "header_container", None)

        if header_container:

            try:
                header_container.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: {bg};
                        border: 1px solid #444444;
                        border-radius: 8px;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 12. BADGES
        # ============================================================
        badge_style = f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid #444444;
                border-radius: 6px;
            }}

            QFrame:hover {{
                border: 2px solid {fg};
            }}
        """

        left_badge = getattr(self, "left_badge", None)

        if left_badge:
            try:
                left_badge.setStyleSheet(badge_style)
            except RuntimeError:
                pass

        right_badge = getattr(self, "right_badge", None)

        if right_badge:
            try:
                right_badge.setStyleSheet(
                    f"""
                    QFrame {{
                        background-color: transparent;
                        border: 1px solid #444444;
                        border-radius: 6px;
                    }}

                    QFrame:hover {{
                        border: 2px solid {fg};
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 13. HEADER LABEL
        # ============================================================
        header_label = getattr(self, "header_label", None)

        if header_label:

            try:
                header_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {fg};
                        font-weight: bold;
                        font-size: 15px;
                        background: transparent;
                        border: none;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 14. STATUS LABEL
        # ============================================================
        status_label = getattr(self, "status_label", None)

        if status_label:

            try:
                status_label.setStyleSheet(
                    f"""
                    QLabel {{
                        color: {fg};
                        font-weight: bold;
                        font-size: 18px;
                        background: transparent;
                        border: none;
                    }}
                    """
                )
            except RuntimeError:
                pass

        # ============================================================
        # 15. LED-STATUS ERZWINGEN
        #
        # MUSS NACH DEM REPAINT KOMMEN.
        # ============================================================
        is_led_enabled = config_obj.get("led_enabled", True)

        blink_timer = getattr(self, "blink_timer", None)

        if blink_timer:

            try:
                blink_timer.stop()
            except RuntimeError:
                pass

        # LEDs zuerst in definierten statischen Zustand bringen
        try:
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()
        except Exception:
            pass

        # Danach Blinkbetrieb wieder aktivieren
        if is_led_enabled:

            try:
                slider = getattr(self, "slider_speed", None)

                speed_val = slider.value() if slider else 500

                if 10 <= speed_val < 950 and blink_timer:
                    blink_timer.start(speed_val)

            except (RuntimeError, ValueError, TypeError):
                pass

        # ============================================================
        # 16. CONFIG AKTUALISIEREN
        # ============================================================
        old_color = config_obj.get("theme_color", config_obj.get("color"))

        config_changed = old_color != current_color_name

        if config_changed:
            # Keep both keys synchronized: older code reads "color", while
            # the settings selector reads "theme_color".
            config_obj["color"] = current_color_name
            config_obj["theme_color"] = current_color_name

            # Nur bei tatsächlicher Farbänderung Theme-Modus neu setzen
            if "matrix" in str(current_color_name).lower():
                config_obj["theme_mode"] = "matrix"
            else:
                config_obj["theme_mode"] = "standard"


        # ============================================================
        # 17. INSTANZEN SYNCHRONISIEREN
        # ============================================================
        try:
            if hasattr(self, "cfg"):
                self.cfg = config_obj

            if hasattr(self, "current_config"):
                self.current_config = config_obj

        except Exception:
            pass

        # ============================================================
        # 18. SPEICHERN
        #
        # Während des Startvorgangs nicht unnötig speichern.
        # ============================================================
        if not getattr(self, "is_loading", False):

            try:
                save_config_func = globals().get("save_config")

                if save_config_func:
                    save_config_func(
                        config_obj,
                        gui_instance=self,
                        silent=True
                    )

            except Exception as e:
                print(f"[change_colors] Config konnte nicht gespeichert werden: {e}")

        # ============================================================
        # 18b. FARBMELDUNG IM GROSSEN INFOSCREEN
        #
        # Nur bei einer tatsächlichen Änderung melden.
        # Die Meldung wird ANGEHÄNGT und überschreibt keine
        # vorhandenen Infoscreen-Meldungen.
        # ============================================================
        if config_changed and not getattr(self, "is_loading", False):

            try:
                info_widget = getattr(self, "info_text", None)

                if info_widget is not None and hasattr(self, "append_info"):

                    lang = str(getattr(self, "LANG", "de")).lower()

                    if lang.startswith("de"):
                        color_msg = (
                            f"🎨 Farbe eingestellt: <b>{current_color_name}</b>"
                        )
                    else:
                        color_msg = (
                            f"🎨 Color selected: <b>{current_color_name}</b>"
                        )

                    # WICHTIG:
                    # Den bereits aufgebauten großen Infoscreen niemals neu setzen
                    # oder leeren. Der komplette System-Check-Block (Copyright,
                    # LIVE/System Monitor, Autor/Version, Hauptmerkmale,
                    # Systemdaten, Tools, Netzwerk, Repositories, Statistik
                    # und "System-Check OK. Bereit.") bleibt erhalten.
                    #
                    # Vor dem Anhängen merken wir uns den aktuellen HTML-Inhalt.
                    # append_info fügt anschließend ausschließlich am Ende ein.
                    existing_html = info_widget.toHtml()

                    self.append_info(
                        info_widget,
                        color_msg,
                        "info"
                    )

                    # Sicherheitsprüfung: Falls eine unerwartete UI-Aktion
                    # den Inhalt verändert hätte, den vollständigen bisherigen
                    # Infoscreen wiederherstellen und die Farbm­eldung danach
                    # erneut anhängen.
                    if existing_html and not info_widget.toHtml().startswith(
                        existing_html[:80]
                    ):
                        info_widget.setHtml(existing_html)
                        self.append_info(
                            info_widget,
                            color_msg,
                            "info"
                        )

            except Exception as e:
                print(f"[change_colors] Farbmeldung im Infoscreen fehlgeschlagen: {e}")

        # ============================================================
        # 19. BUTTON-TEXTE NACH THEME/STYLE SICHER ANPASSEN
        # ============================================================
        try:
            from PyQt6.QtCore import QTimer

            if hasattr(self, "_fit_all_button_texts"):

                # Nach dem ersten Theme-Repaint
                QTimer.singleShot(
                    100,
                    self._fit_all_button_texts
                )

                # Nach Sprach-/Layout-Updates
                QTimer.singleShot(
                    500,
                    self._fit_all_button_texts
                )

                # Nach vollständiger GUI-Initialisierung
                QTimer.singleShot(
                    1000,
                    self._fit_all_button_texts
                )

        except Exception as e:
            print(f"[change_colors] Button-Text-Anpassung fehlgeschlagen: {e}")

        # Letzter Schritt: sämtliche Buttons (einschließlich S3/S4/NCam und
        # Stats) erhalten das ausgewählte Theme, dessen Hover-Farbe und Tooltips.
        try:
            self.apply_global_button_style()
        except Exception as exc:
            print(f"[change_colors] Button-Theme/Tooltips konnten nicht aktualisiert werden: {exc}")

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

    def change_emu_repo(self):
        """Wählt das OSCam-Emu-Git-Repository für die nächste Patch-Erstellung."""
        from PyQt6.QtWidgets import QInputDialog, QApplication, QMessageBox
        from PyQt6.QtCore import QTimer
        import re

        presets=[
            "https://github.com/oscam-mirror/oscam-emu.git",
            "https://github.com/speedy005/Oscam-emu.git",
        ]
        current=str(getattr(self,"EMUREPO",None) or globals().get("EMUREPO",presets[0])).strip()
        if current and current not in presets:
            presets.insert(0,current)

        is_de=str(getattr(self,"LANG","de")).lower()[:2]=="de"
        dialog=QInputDialog(self)
        dialog.setWindowTitle("OSCam-Emu Git auswählen" if is_de else "Select OSCam-Emu Git")
        dialog.setLabelText("Repository-URL auswählen oder eigene Git-URL eingeben:" if is_de else "Select a repository URL or enter your own Git URL:")
        dialog.setComboBoxItems(presets)
        dialog.setComboBoxEditable(True)
        dialog.setTextValue(current or presets[0])
        dialog.setOkButtonText("Übernehmen" if is_de else "Apply")
        dialog.setCancelButtonText("Abbrechen" if is_de else "Cancel")

        if not dialog.exec():
            return False
        new_url=(dialog.textValue() or "").strip()
        valid=bool(re.match(r"^(https?://|ssh://|git@|file://|/|[A-Za-z]:[\\/])",new_url))
        if not valid:
            QMessageBox.warning(self,"OSCam-Emu Git",
                "Bitte eine gültige Git-Repository-URL eingeben." if is_de else
                "Please enter a valid Git repository URL.")
            return False

        # Die Auswahl sofort als aktive Patch-Quelle merken.
        # create_patch() darf hier NICHT wieder auf eine alte
        # emu_repo_url aus der geladenen Config zurückfallen.
        self.EMUREPO = new_url
        self.selected_emu_repo_url = new_url
        self.selected_emu_repo_branch = str(
            getattr(self, "selected_emu_repo_branch", "master") or "master"
        ).strip() or "master"

        # Eine OSCam-Emu-Revision gehört immer zu genau EINEM Repository.
        # Wird über "Repo URL" das Repository gewechselt, darf eine zuvor
        # ausgewählte SHA aus dem alten Repository nicht weiterverwendet werden.
        self.selected_emu_commit = None
        self.selected_emu_commit_repo_url = ""
        self.display_emu_commit = None
        globals()["SELECTED_EMU_COMMIT"] = ""
        globals()["SELECTED_EMU_COMMIT_REPO_URL"] = ""

        globals()["EMUREPO"] = new_url
        globals()["SELECTED_EMU_REPO_URL"] = new_url
        globals()["SELECTED_EMU_REPO_BRANCH"] = self.selected_emu_repo_branch
        if hasattr(self,"cfg"):
            self.cfg["EMUREPO"]=new_url
            self.cfg["emu_repo_url"]=new_url
            saver=globals().get("save_config")
            if callable(saver):
                saver(self.cfg,gui_instance=self)

        pbar=getattr(self,"progress_bar",None)
        if pbar:
            pbar.setValue(100)
            pbar.setFormat(("✅ OSCam-Emu Git gesetzt: %p%" if is_de else "✅ OSCam-Emu Git selected: %p%"))
            pbar.show()
            QTimer.singleShot(2500,getattr(self,"pbar_idle",lambda:pbar.setValue(0)))
        # Nach einem Repo-Wechsel die Revision-Anzeige sofort auf den
        # aktuellen Stand des neu gewählten OSCam-Emu-Repositories setzen.
        try:
            self.update_revision_button_labels()
        except Exception:
            pass

        if hasattr(self,"info_text"):
            self.info_text.append(f"<b>✅ OSCam-Emu Git: {new_url}</b>")
            self.info_text.append(
                "<b>ℹ️ OSCam-Emu Revision: Auswahl zurückgesetzt – "
                "beim nächsten Create Patch wird der aktuelle Branch-Stand "
                "dieses Repositories verwendet.</b>"
            )
            self.info_text.ensureCursorVisible()
        return True

    def collect_and_save(self):
        """Speichert leise und aktualisiert die Farben sofort."""
        try:
            theme_name = self.color_box.currentText()

            # Globale Farbe aktualisieren, damit repaint_ui_colors sie findet
            global current_diff_colors
            if theme_name in DIFF_COLORS:
                current_diff_colors = DIFF_COLORS[theme_name]

            new_cfg = {
                # "color" ist der kanonische Schlüssel in load_config().
                "color": theme_name,
                "commit_count": int(self.commit_spin.value()),
                "language": str(self.language_box.currentText()).lower()[:2],
                "work_dir": getattr(self, "WORK_DIR", self.base_dir),
                "s3_patch_path": getattr(
                    self, "OLD_PATCH_DIR", self.current_config.get("s3_patch_path", self.base_dir)
                ),
            }

            # Niemals die komplette Config mit einem Teil-Dictionary überschreiben.
            # save_config merged die Änderungen mit den vorhandenen Einstellungen.
            save_config(new_cfg, gui_instance=self, silent=True)
            self.current_config.update(new_cfg)
            # UI sofort neu färben
            self.repaint_ui_colors()

            # Log nur in der GUI (kein print!)
            self.info_text.append(f"💾 Konfiguration gespeichert: {theme_name}")

        except Exception as e:
            self.info_text.append(f"❌ Fehler beim Speichern: {e}")

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

    def init_ui(self):
        from PyQt6.QtWidgets import (
            QVBoxLayout,
            QHBoxLayout,
            QGridLayout,
            QLabel,
            QPushButton,
            QWidget,
            QTextEdit,
            QComboBox,
            QSpinBox,
            QProgressBar,
            QApplication,
            QFrame,
            QFileDialog,
        )
        from PyQt6.QtWidgets import QStyle, QSizePolicy
        from PyQt6.QtGui import QPixmap, QFont
        from PyQt6.QtCore import Qt, QSize, QTimer, QDateTime

        import subprocess
        import os
        import requests

        # ---------------------------------------------------------
        # 1. Grundwerte & Hauptlayout
        # ---------------------------------------------------------
        self.UI_BUTTON_H = 50
        self.UI_BADGE_H = 50
        self.UI_PROGRESS_H = 25
        self.UI_STATUS_H = 50
        self.UI_RADIUS = 10

        B_HEIGHT = self.UI_BUTTON_H
        B_WIDTH = 300
        CONTROL_HEIGHT = self.UI_BUTTON_H
        self.BUTTON_HEIGHT = self.UI_BUTTON_H
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 10, 12, 14)
        self.setStyleSheet("""
            QWidget { background-color: #10141d; color: #e8f1ff; }
            QGroupBox {
                background-color: #171d29;
                border: 1px solid #29384b;
                border-radius: 12px;
                margin-top: 13px;
                padding: 10px 8px 8px 8px;
                font-weight: 800;
                color: #35e6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #35e6ff;
                letter-spacing: 1px;
            }
            QToolTip {
                background: #111827; color: #f2f7ff;
                border: 1px solid #35e6ff; padding: 7px; border-radius: 6px;
            }
        """)
        self.create_buttons()
        
        # =========================================================
        # HEADER-BEREICH (STEAM / DISCORD CLEAN)
        # =========================================================

        header_widget = QFrame()
        self.header_widget = header_widget
        header_widget.setMinimumHeight(200)
        header_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_widget.setStyleSheet(
            """
            QFrame {
                background-color: #2F2F2F;
                border: 1px solid #444;
                border-radius: 10px;
            }
            QLabel {
                background-color: transparent;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                color: #EAFF00 !important;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #EAFF00;
                color: white !important;
            }
        """
        )

        header_layout = QHBoxLayout(header_widget)
        self.header_layout = header_layout
        header_layout.setContentsMargins(8, 6, 0, 6)
        header_layout.setSpacing(6)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # =========================================================
        # LEFT SECTION
        # =========================================================

        left_header_container = QWidget()
        left_header_layout = QHBoxLayout(left_header_container)
        self.left_header_layout = left_header_layout
        left_header_layout.setContentsMargins(4, 0, 0, 0)
        left_header_layout.setSpacing(8)
        left_header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # --- INFO BUTTON ---
        self.info_button = QPushButton()
        self.info_button.setMinimumSize(36, 36)
        self.info_button.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed
        )

        icon_info = self.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxInformation
        )
        self.info_button.setIcon(icon_info)
        self.info_button.setIconSize(QSize(28, 28))
        self.info_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Tooltip entsprechend der aktuellen Sprache
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")

        self.info_button.setToolTip(
            "Zeigt Informationen über das OSCam Toolkit an."
            if is_de
            else "Displays information about the OSCam Toolkit."
        )
        self.info_button.setToolTipDuration(10000)

        # Klick öffnet das Info-Fenster
        self.info_button.clicked.connect(self.show_info)

        left_header_layout.addWidget(self.info_button)


        # =========================================================
        # CLOCK + DATE (WICHTIG: VBOX = UNTEREINANDER)
        # =========================================================

        time_date_container = QWidget()
        time_date_layout = QVBoxLayout(time_date_container)
        time_date_layout.setContentsMargins(0, 0, 0, 0)
        time_date_layout.setSpacing(1)
        time_date_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        bold_font_time = QFont("Segoe UI", 8, QFont.Weight.Bold)
        bold_font_date = QFont("Segoe UI", 8, QFont.Weight.Bold)

        # --- CLOCK ---
        self.digital_clock = QLabel("--:--:--")
        self.digital_clock.setFont(bold_font_time)
        self.digital_clock.setStyleSheet("color: red;")
        time_date_layout.addWidget(self.digital_clock, alignment=Qt.AlignmentFlag.AlignLeft)

        # --- DATE ---
        self.date_label = QLabel("--.--.----")
        self.date_label.setFont(bold_font_date)
        self.date_label.setStyleSheet("color: orange; background: transparent;")
        time_date_layout.addWidget(self.date_label, alignment=Qt.AlignmentFlag.AlignLeft)


        
        # =========================================================
        # BUTTON CARD + S3 REPOSITORY-AUSWAHL
        # =========================================================

        btn_card = QWidget()
        btn_card_layout = QVBoxLayout(btn_card)
        btn_card_layout.setContentsMargins(0, 0, 0, 0)
        btn_card_layout.setSpacing(6)
        btn_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        s3_s4_h_layout = QHBoxLayout()
        s3_s4_h_layout.setSpacing(8)
        s3_s4_h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for _install_btn in (self.btn_s3, self.btn_s4, self.btn_ncam):
            _install_btn.setMinimumSize(105, 50)
            _install_btn.setMaximumWidth(260)
            _install_btn.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )

        s3_s4_h_layout.addWidget(self.btn_s3)
        s3_s4_h_layout.addWidget(self.btn_s4)
        btn_card_layout.addLayout(s3_s4_h_layout)

        btn_card_layout.addWidget(
            self.btn_ncam,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # ---------------------------------------------------------
        # S3 GIT-REPOSITORY AUSWÄHLEN
        # ---------------------------------------------------------
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        # Konfiguration laden, sofern noch nicht vorhanden.
        if not isinstance(getattr(self, "current_config", None), dict):
            self.current_config = {}

        self.cfg = self.current_config

        saved_repo_name = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)",
        )

        if saved_repo_name == "S3 Simplebuild":
            saved_repo_name = "S3 Simplebuild speeddy005"
        if saved_repo_name not in self.s3_repository_options:
            saved_repo_name = "S3 Simplebuild (Original)"

        self.selected_s3_repository = saved_repo_name

        self.s3_repo_label = QLabel("S3 Git-Quelle:")
        self.s3_repo_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        self.s3_repo_label.setStyleSheet(
            "color: #EAFF00; background: transparent; "
            "font-weight: bold; border: none;"
        )

        self.s3_repo_combo = QComboBox()
        self.s3_repo_combo.setObjectName("s3RepositoryCombo")
        self.s3_repo_combo.addItems(
            list(self.s3_repository_options.keys())
        )
        self.s3_repo_combo.setCurrentText(saved_repo_name)
        self.s3_repo_combo.setMinimumWidth(230)
        self.s3_repo_combo.setMinimumHeight(34)
        self.s3_repo_combo.setToolTip(
            "Repository auswählen, das bei der S3-Installation verwendet wird."
        )
        self.s3_repo_combo.setStyleSheet("""
            QComboBox {
                color: #EAFF00;
                background-color: #252525;
                border: 1px solid #666;
                border-radius: 6px;
                padding: 5px 8px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 1px solid #EAFF00;
            }
            QComboBox QAbstractItemView {
                color: #EAFF00;
                background-color: #252525;
                selection-background-color: #444;
                selection-color: white;
            }
        """)

        s3_repo_row = QHBoxLayout()
        s3_repo_row.setContentsMargins(0, 0, 0, 0)
        s3_repo_row.setSpacing(6)
        s3_repo_row.addWidget(self.s3_repo_label)
        s3_repo_row.addWidget(self.s3_repo_combo, 1)

        # Die Git-Quelle wird erst nach Auswahl des Installationspfads abgefragt.
        # Deshalb wird die ComboBox nicht unter den drei Hauptbuttons angezeigt.

        # Nur verbinden, nicht zusätzlich den S3-Button verdrahten.
        self.s3_repo_combo.currentTextChanged.connect(
            self.on_s3_repository_changed
        )

        # =========================================================
        # LEFT BUILD (ORDER WICHTIG!)
        # =========================================================

        left_header_layout.addWidget(time_date_container)
        left_header_layout.addWidget(btn_card)



        # =========================================================
        #         FINAL HEADER ASSEMBLY
        # =========================================================

        # LEFT-HEADER wird erst beim finalen Layout einmalig eingefügt.

        # =========================================================
        # SIGNALS (UNCHANGED)
        # =========================================================

        self.btn_s3.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_s3.customContextMenuRequested.connect(self.select_s3_path_manually)
        self.btn_s3.clicked.connect(self.start_s3_install)

        self.btn_s4.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_s4.customContextMenuRequested.connect(self.select_s4_path_manually)
        self.btn_s4.clicked.connect(self.start_s4_install)

        self.btn_ncam.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.btn_ncam.customContextMenuRequested.connect(self.select_ncam_path_manually)
        self.btn_ncam.clicked.connect(self.start_ncam_install)


        # =========================================================
        # FINAL HEADER ATTACH
        # =========================================================

        header_layout.addWidget(left_header_container, 0)
        #header_layout.addStretch(1)
        # --- MIDDLE: Logo (responsive) ---
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setMinimumSize(0, 0)
        self.logo_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        header_layout.addWidget(self.logo_label, 1)


        self.original_pixmap = None

        try:
            url = (
                "https://raw.githubusercontent.com/"
                "speedy005/oscam_patch_manager_new/master/"
                "speedy_banner.png"
            )

            resp = requests.get(url, timeout=5)
            resp.raise_for_status()

            pixmap = QPixmap()
            if pixmap.loadFromData(resp.content):
                self.original_pixmap = pixmap
                QTimer.singleShot(0, self._fit_header_logo)
            else:
                raise ValueError("Logo konnte nicht geladen werden")

        except Exception as exc:
            self.logo_label.setText("OSCAM TOOLKIT")
            self.logo_label.setStyleSheet(
                "color: white; font-size: 18px;"
            )
            self.original_pixmap = None
            print(f"Logo konnte nicht geladen werden: {exc}")



        # --- RIGHT: Log-Button + Version & Autor (OPTIMIERT) ---
        right_header_container = QWidget()
        right_header_layout = QHBoxLayout(right_header_container)
        self.right_header_layout = right_header_layout
        right_header_layout.setContentsMargins(0, 0, 0, 0)
        right_header_layout.setSpacing(8)
        right_header_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        # --- INSTALLATION / PATCH-BEREICH ZWISCHEN LABEL/LOG ---
        lang = getattr(self, "LANG", "de").lower()
        # Zwei Spalten: links die Patch-Ordner, rechts die Patch-Kopieraktionen.
        install_path_container = QWidget()
        install_path_layout = QHBoxLayout(install_path_container)
        install_path_layout.setContentsMargins(0, 0, 0, 0)
        install_path_layout.setSpacing(8)
        install_path_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )

        path_button_column = QWidget()
        path_button_layout = QVBoxLayout(path_button_column)
        path_button_layout.setContentsMargins(0, 0, 0, 0)
        path_button_layout.setSpacing(3)
        path_button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        patch_button_column = QWidget()
        patch_button_layout = QVBoxLayout(patch_button_column)
        patch_button_layout.setContentsMargins(0, 0, 0, 0)
        patch_button_layout.setSpacing(3)
        patch_button_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.header_btn_s3_ncam = QPushButton(self.TEXT.get("patch_folder_s3_ncam", "S3-NCam-Bonecrew-Pfad"))
        self.header_btn_s3_ncam.setMinimumSize(200, 50)
        self.header_btn_s3_ncam.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_s3_ncam.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_s3_ncam.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirOpenIcon))
        self.header_btn_s3_ncam.setIconSize(QSize(20, 20))
        self.header_btn_s3_ncam.setToolTip(
            self.TEXT.get("patch_folder_s3_ncam_tooltip", "S3-NCam-Bonecrew-Pfad wählen")
        )
        self.header_btn_s3_ncam.clicked.connect(self.select_ncam_patch_path_manually)
        path_button_layout.addWidget(self.header_btn_s3_ncam)

        self.header_btn_s4 = QPushButton(self.TEXT.get("patch_folder_s4", "S4-Pfad"))
        self.header_btn_s4.setMinimumSize(200, 50)
        self.header_btn_s4.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_s4.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_s4.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirOpenIcon))
        self.header_btn_s4.setIconSize(QSize(20, 20))
        self.header_btn_s4.setToolTip(
            self.TEXT.get("patch_folder_s4_tooltip", "S4-Pfad wählen")
        )
        self.header_btn_s4.clicked.connect(self.select_s4_patch_path_manually)
        path_button_layout.addWidget(self.header_btn_s4)

        # Die beiden Patch-Kopieraktionen ebenfalls untereinander.
        self.header_btn_patch_ncam = QPushButton(self.TEXT.get("patch_copy_s3_ncam", "Patch → S3-NCam"))
        self.header_btn_patch_ncam.setMinimumSize(200, 50)
        self.header_btn_patch_ncam.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_patch_ncam.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_patch_ncam.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        self.header_btn_patch_ncam.setIconSize(QSize(20, 20))
        self.header_btn_patch_ncam.setToolTip(
            "Kopiert oscam-emu.patch in den konfigurierten S3-NCam-Bonecrew-Patch-Ordner."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Copies oscam-emu.patch to the configured S3-NCam-Bonecrew patch folder."
        )
        self.header_btn_patch_ncam.clicked.connect(
            lambda checked=False: self.copy_patch_to_target("ncam")
        )
        patch_button_layout.addWidget(self.header_btn_patch_ncam)

        self.header_btn_patch_s4 = QPushButton(self.TEXT.get("patch_copy_s4", "Patch → S4"))
        self.header_btn_patch_s4.setMinimumSize(200, 50)
        self.header_btn_patch_s4.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.header_btn_patch_s4.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.header_btn_patch_s4.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_FileIcon))
        self.header_btn_patch_s4.setIconSize(QSize(20, 20))
        self.header_btn_patch_s4.setToolTip(
            "Kopiert oscam-emu.patch in den konfigurierten S4-Patch-Ordner."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Copies oscam-emu.patch to the configured S4 patch folder."
        )
        self.header_btn_patch_s4.clicked.connect(
            lambda checked=False: self.copy_patch_to_target("s4")
        )
        patch_button_layout.addWidget(self.header_btn_patch_s4)

        install_path_layout.addWidget(path_button_column)
        install_path_layout.addWidget(patch_button_column)

        
        # ---------------------------------------------------------
        # HEADER-AKTIONEN
        # Log speichern | Stats
        # Oscam Git URL leicht nach links versetzt darunter
        # ---------------------------------------------------------

        header_actions_container = QWidget()
        header_actions_layout = QGridLayout(header_actions_container)
        header_actions_layout.setContentsMargins(0, 0, 0, 0)
        header_actions_layout.setHorizontalSpacing(3)
        header_actions_layout.setVerticalSpacing(3)
        header_actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter |
            Qt.AlignmentFlag.AlignVCenter
        )

        # Einheitlicher Stil für ALLE Aktionsbuttons
        action_button_style = """
            QPushButton {
                color: #EAFF00;
                background-color: #3d3d3d;
                border: 1px solid #555;
                border-radius: 7px;
                padding: 2px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
                border: 1px solid #EAFF00;
                color: white;
            }
            QPushButton:pressed {
                background-color: #222;
                border: 1px solid white;
            }
        """

        # --- LOG SPEICHERN ---
        log_text = "Log speichern" if lang == "de" else "Save Log"

        self.log_button = QPushButton(log_text)
        self.log_button.setMinimumSize(120, 32)
        self.log_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.log_button.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.log_button.setIcon(
            self.style().standardIcon(
                QApplication.style().StandardPixmap.SP_DriveHDIcon
            )
        )
        self.log_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.log_button.setToolTip(
            "Speichert den aktuellen Log-/Protokollinhalt in einer Datei."
            if str(getattr(self, "LANG", "de")).lower().startswith("de")
            else "Saves the current log output to a file."
        )
        self.log_button.setStyleSheet(action_button_style)

        if hasattr(self, "export_log"):
            self.log_button.clicked.connect(self.export_log)

        # --- STATS ---
        self.telemetry_cb = QPushButton("Stats")
        self.telemetry_cb.setCheckable(True)
        self.telemetry_cb.setMinimumSize(58, 32)
        self.telemetry_cb.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.telemetry_cb.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.telemetry_cb.setChecked(
            bool(get_setting("allow_telemetry", True))
        )
        self.telemetry_cb.setCursor(Qt.CursorShape.PointingHandCursor)
        self.telemetry_cb.setToolTip(
            "Anonyme Nutzungsstatistik (Hit-Counter) erlauben/verbieten."
            if lang == "de" else
            "Allow/disallow anonymous usage statistics (Hit-Counter)."
        )
        self.telemetry_cb.setAccessibleName(
            "Stats aktivieren oder deaktivieren"
        )
        self.telemetry_cb.setStyleSheet(action_button_style)
        self.telemetry_cb.toggled.connect(self.on_telemetry_changed)

        # --- OSCAM-GIT-URL ---
        self.oscam_source_button = QPushButton("Oscam Git URL")
        self.oscam_source_button.setMinimumSize(300, 50)
        self.oscam_source_button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.oscam_source_button.setFont(
            QFont("Segoe UI", 8, QFont.Weight.Bold)
        )
        self.oscam_source_button.setIcon(self.style().standardIcon(QApplication.style().StandardPixmap.SP_DirLinkIcon))
        self.oscam_source_button.setIconSize(QSize(20, 20))
        self.oscam_source_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.oscam_source_button.setToolTip(
            "Quelle für Create Patch und OSCam-Emu-Git Patch auswählen"
            if lang == "de" else
            "Choose source for Create Patch and OSCam-Emu-Git Patch"
        )
        self.oscam_source_button.setStyleSheet(action_button_style)
        self.oscam_source_button.clicked.connect(self.choose_oscam_source)

        # --- OBERE REIHE ---
        header_actions_layout.addWidget(
            self.log_button, 0, 0, 1, 2,
            alignment=Qt.AlignmentFlag.AlignCenter
        ) 

        # --- UNTERE REIHE ---
        # Eigener Container, damit nur Oscam-git-url nach links
        # versetzt wird, ohne die obere Reihe zu verschieben.
        oscam_row_container = QWidget()
        oscam_row_layout = QHBoxLayout(oscam_row_container)
        oscam_row_layout.setContentsMargins(0, 0, 0, 0)
        oscam_row_layout.setSpacing(0)
        oscam_row_layout.addWidget(
            self.oscam_source_button,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        header_actions_layout.addWidget(
            oscam_row_container, 1, 0, 1, 2,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # Aktionsblock rechts neben den Patch-Kopierbuttons einsetzen.
        install_path_layout.addWidget(header_actions_container)


        # Kompakte, zum bestehenden Header passende Optik.
        for _btn in (
            self.header_btn_s3_ncam,
            self.header_btn_s4,
            self.header_btn_patch_ncam,
            self.header_btn_patch_s4,
        ):
            _btn.setMinimumWidth(0)
            _btn.setCursor(Qt.CursorShape.PointingHandCursor)
            _btn.setStyleSheet("""
                QPushButton {
                    color: #EAFF00;
                    background-color: #3d3d3d;
                    border: 1px solid #555;
                    border-radius: 7px;
                    padding: 2px 8px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                    border: 1px solid #EAFF00;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #222;
                    border: 1px solid white;
                }
            """)

        # Die Installations-/Patch-Aktionen sind Teil des rechten Header-Bereichs;
        # das Logo bleibt dadurch mittig zwischen linker und rechter Seite.

        # Fonts definieren, BEVOR sie benutzt werden (löst NameError)
        bold_font_header = QFont("Segoe UI", 25, QFont.Weight.Bold)
        bold_font_version = QFont("Segoe UI", 25, QFont.Weight.Bold)

        # Container für die Labels rechts oben
        version_text_container = QWidget()
        version_text_layout = QVBoxLayout(version_text_container)
        version_text_layout.setContentsMargins(8, 0, 8, 0)
        version_text_layout.setSpacing(2)
        version_text_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )

        # Farben und Version holen
        current_diff_colors = getattr(self, "current_diff_colors", {"fg": "#FF0000"})
        text_color = current_diff_colors.get("fg", "#EAFF00")
        app_v = getattr(self, "APP_VERSION", globals().get("APP_VERSION", "4.0.0"))

        # Das Haupt-Versionslabel (Das farbige)
        # WICHTIG: Wir weisen es self.version_label zu, damit es später aktualisierbar ist
        self.version_label = QLabel(f"v{app_v}")
        self.version_label.setFont(bold_font_version)
        self.version_label.setStyleSheet(
            f"color: {text_color}; background: transparent; margin-bottom: 5px;"
        )

        # Autor Label (Blau im Screenshot)
        self.by_label = QLabel("by speedy005")
        self.by_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.by_label.setStyleSheet("color: #0055ff; background: transparent;")

        # In den kleinen Container packen
        version_text_layout.addWidget(self.version_label)
        version_text_layout.addWidget(self.by_label)

        # Installations-/Patch-Buttons rechts neben dem mittigen Banner.
        # Version, Stats und "by speedy005" bleiben ganz rechts.
        right_header_layout.addWidget(install_path_container)
        right_header_layout.setSpacing(4)

        # Versionsanzeige etwas nach rechts verschieben
        right_header_layout.addSpacing(40)

        right_header_layout.addWidget(version_text_container)

        self.telemetry_cb.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed
        )
        right_header_layout.addWidget(
            self.telemetry_cb,
            0,
            Qt.AlignmentFlag.AlignTop
        )

        # Zum Haupt-Header hinzufügen
        header_layout.addWidget(right_header_container, 0)

        main_layout.addWidget(header_widget)
        QTimer.singleShot(0, self._fit_header_controls)
        # Theme-Farben und Tooltips werden zentral anhand der aktuellen Sprache
        # und des ausgewählten Farbschemas gesetzt.
        self.apply_global_button_style()

        # ---------------------------------------------------------
        # INFO + PROGRESS
        # ---------------------------------------------------------
        # Große Live-Konsole als visueller Mittelpunkt der Oberfläche
        console_panel = QGroupBox("LIVE SYSTEM CONSOLE  /  STATUS & LOGS")
        self.console_panel = console_panel
        console_layout = QVBoxLayout(console_panel)
        console_layout.setContentsMargins(10, 12, 10, 10)
        console_layout.setSpacing(8)
        self.info_text = QTextEdit()
        self.info_text.setObjectName("liveConsole")
        self.info_text.setReadOnly(True)
        # Begrenzung der sichtbaren Live-Konsole verhindert, dass sehr lange
        # Sitzungen unbegrenzt Speicher belegen. Build-Log-Dateien bleiben unberührt.
        try:
            self.info_text.document().setMaximumBlockCount(10000)
        except Exception as exc:
            print(f"[console] Begrenzung der Konsolenhistorie nicht verfügbar: {exc}")
        self.info_text.setMinimumHeight(220)
        self.info_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.info_text.setFont(QFont("Consolas", 11))
        self.info_text.setStyleSheet("""
            QTextEdit#liveConsole {
                background-color: #080c12; color: #b9f7ff;
                border: 1px solid #24465a; border-radius: 9px;
                padding: 10px; selection-background-color: #176b80;
            }
        """)
        # Kleine Werkzeugleiste für die Live-Konsole; ändert keine gespeicherten Logs.
        console_tools = QHBoxLayout()
        console_tools.setContentsMargins(0, 0, 0, 0)
        console_tools.setSpacing(6)

        is_de = str(getattr(self, "LANG", LANG)).lower() == "de"
        copy_log_button = QPushButton("LOG KOPIEREN" if is_de else "COPY LOG")
        copy_log_button.setToolTip(
            "Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren"
            if is_de else "Copy all visible console output to the clipboard"
        )
        def copy_visible_console():
            """Kopiert ausschließlich den aktuell sichtbaren Konsoleninhalt."""
            try:
                QApplication.clipboard().setText(self.info_text.toPlainText())
            except Exception as exc:
                self.append_info(self.info_text, f"Kopieren fehlgeschlagen: {exc}", "error")

        copy_log_button.clicked.connect(copy_visible_console)
        self.copy_log_button = copy_log_button

        analyze_build_logs_button = QPushButton("BUILD-LOG ANALYSIEREN" if is_de else "ANALYZE BUILD LOG")
        analyze_build_logs_button.setToolTip(
            "Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen"
            if is_de else "Check the newest build log for common errors and warnings"
        )
        analyze_build_logs_button.clicked.connect(self.analyze_latest_build_log)
        self.analyze_build_logs_button = analyze_build_logs_button

        diagnostics_button = QPushButton("SYSTEM-DIAGNOSE" if is_de else "SYSTEM DIAGNOSTICS")
        diagnostics_button.setToolTip(
            "System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build"
            if is_de else "Check system, tool directories and existing build logs; does not start a build"
        )
        diagnostics_button.clicked.connect(self.open_diagnostics_dialog)
        self.diagnostics_button = diagnostics_button

        log_history_button = QPushButton("BUILD-LOG-VERLAUF" if is_de else "BUILD LOG HISTORY")
        log_history_button.setToolTip(
            "Alle Build-Logs nach Status, Zeit und Fehlerhinweisen vergleichen"
            if is_de else "Compare all build logs by status, time and error indicators"
        )
        log_history_button.clicked.connect(self.open_build_log_history)
        self.log_history_button = log_history_button

        clear_console_button = QPushButton("KONSOLE LEEREN" if is_de else "CLEAR CONSOLE")
        clear_console_button.setToolTip(
            "Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert"
            if is_de else "Clear only the visible console output; log files remain unchanged"
        )
        clear_console_button.clicked.connect(self.info_text.clear)
        self.clear_console_button = clear_console_button

        for tool_button in (copy_log_button, analyze_build_logs_button, diagnostics_button, log_history_button, clear_console_button):
            tool_button.setMinimumHeight(30)
            tool_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            console_tools.addWidget(tool_button)

        console_tools.addStretch(1)
        console_layout.addLayout(console_tools)
        console_layout.addWidget(self.info_text, 1)
        main_layout.addWidget(console_panel, 10)

        # Auto-Scroll wird beim Hinzufügen neuer Meldungen gesteuert.
        # Kein periodischer Timer: so bleibt die Konsole ruhig, wenn der
        # Benutzer ältere Einträge liest.
        self.scroll_timer = None

        main_layout.addSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(self.UI_PROGRESS_H)
        self.progress_bar.setMaximumHeight(40)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setStyleSheet(
            """
        QProgressBar {
            border: 1px solid #444;
            border-radius: 8px;
            background-color: #1A1A1A;
            color: white;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
        }
        QProgressBar::chunk {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                              stop:0 #F37804, stop:1 #FFD700);
            border-radius: 8px;
        }
        """
        )
        main_layout.addWidget(self.progress_bar)
        # self.pbar_idle()
        # ---------------------------------------------------------
        # STATUS-BAR (MAXIMALER AUSBAU: GROSSE ANZEIGEN & ZIP)
        # ---------------------------------------------------------
        status_bar_container = QFrame()
        status_bar_container.setFixedHeight(self.UI_STATUS_H)
        status_bar_container.setStyleSheet(
            "QFrame { background-color: rgba(0,0,0,0.4); border: 1px solid #444; border-radius: 10px; }"
        )

        status_bar_layout = QHBoxLayout(status_bar_container)
        status_bar_layout.setContentsMargins(15, 0, 15, 0)
        status_bar_layout.setSpacing(12)

        # FIX 1: Feste Breite und statische Attribute verhindern das "Zucken" des Textes
        self.status_info_label = QLabel("SYSTEM STATUS:")
        self.status_info_label.setFixedWidth(220)  # Reserviert festen Platz
        self.status_info_label.setAttribute(Qt.WidgetAttribute.WA_StaticContents)
        self.status_info_label.setStyleSheet(
            "color: #FF0000; font-size: 22px; font-weight: bold; border: none; background: transparent;"
        )
        status_bar_layout.addWidget(self.status_info_label)

        # Listen-Trennung für Stabilität
        self.status_leds = []  # Bleiben immer statisch (Grün/Rot)
        self.user_leds = []  # Nur für Slider-Blinken

        tools_to_check = [
            "py",
            "qt6",
            "snd",
            "git",
            "patch",
            "zip",
            "gcc",
            "make",
            "ssl",
            "usb",
        ]
        label_colors = {
            "py": "#3776AB",
            "qt6": "#41CD52",
            "snd": "#FF0000",
            "git": "#2ecc71",
            "patch": "#3498db",
            "zip": "#E24A39",
            "gcc": "#f1c40f",
            "make": "#e67e22",
            "ssl": "#9b59b6",
            "usb": "#1abc9c",
        }

        for tool in tools_to_check:
            exists = False
            display_name = tool.upper()

            # --- SYSTEM CHECK ---
            if tool == "py":
                exists = True
                display_name = f"PY {sys.version_info.major}.{sys.version_info.minor}"
            elif tool == "qt6":
                exists = importlib.util.find_spec("PyQt6") is not None
            elif tool == "snd":
                exists = (
                    any(shutil.which(c) for c in ["paplay", "pw-play", "aplay"])
                    or platform.system() == "Windows"
                )
                display_name = "SOUND"
            elif tool in ["ssl", "usb"]:
                if platform.system() == "Linux" and shutil.which("dpkg"):
                    pkg = "libssl-dev" if tool == "ssl" else "libusb-1.0-0-dev"
                    exists = (
                        subprocess.run(
                            ["dpkg-query", "-W", "-f='${Status}'", pkg],
                            capture_output=True,
                            text=True,
                        ).returncode
                        == 0
                    )
                else:
                    exists = True
            else:
                exists = shutil.which(tool) is not None

            # Tool Container
            t_widget = QWidget()
            # FIX 2: Feste Breite für Container verhindert Layout-Verschiebungen in der Zeile
            t_widget.setMinimumWidth(80)
            t_lay = QHBoxLayout(t_widget)
            t_lay.setContentsMargins(0, 0, 0, 0)
            t_lay.setSpacing(6)

            # SYSTEM LED (Wird nur EINMAL gefärbt)
            led = QLabel()
            led.setFixedSize(16, 16)
            led.tool_exists = exists
            led.base_color = "#27ae60" if exists else "#c0392b"
            led.setStyleSheet(
                f"background-color: {led.base_color}; border-radius: 8px; border: 2px solid #555;"
            )
            led.setCursor(Qt.CursorShape.PointingHandCursor)
            led.mousePressEvent = lambda e, t=tool: self.show_tool_help(t)

            self.status_leds.append(led)

            # Text
            c = label_colors.get(tool, "#FFF")
            lbl = QLabel(display_name)
            lbl.setStyleSheet(
                f"color: {c}; font-size: 20px; font-weight: bold; font-family: 'Segoe UI';"
            )

            t_lay.addWidget(led)
            t_lay.addWidget(lbl)
            status_bar_layout.addWidget(t_widget)

        status_bar_layout.addStretch()

        # ---------------------------------------------------------
        # USER-LED entfernt (Punkt gelöscht)
        self.user_leds = []

        # ---------------------------------------------------------
        # SPEED REGLER
        # ---------------------------------------------------------
        speed_icon = QLabel("⚡")
        speed_icon.setStyleSheet(
            "font-size: 20px; border: none; background: transparent;"
        )
        status_bar_layout.addWidget(speed_icon)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setFixedWidth(110)
        self.slider_speed.setRange(50, 1000)
        self.slider_speed.setInvertedAppearance(True)

        current_speed = self.current_config.get("blink_speed", 500)
        self.slider_speed.setValue(current_speed)
        self.slider_speed.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider_speed.setStyleSheet(
            "QSlider::groove:horizontal { border: 1px solid #666; height: 6px; background: #222; border-radius: 3px; }"
            "QSlider::handle:horizontal { background: #F37804; border: 1px solid #444; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }"
        )

        if hasattr(self, "update_blink_speed"):
            self.slider_speed.valueChanged.connect(self.update_blink_speed)

        status_bar_layout.addWidget(self.slider_speed)

        self.lbl_speed_val = QLabel("")
        self.lbl_speed_val.setStyleSheet(
            "color: #aaa; font-size: 12px; font-weight: bold; border: none;"
        )
        self.lbl_speed_val.setFixedWidth(85)
        status_bar_layout.addWidget(self.lbl_speed_val)

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------
        self.btn_matrix = QPushButton("📟 MATRIX MODE")
        self.btn_matrix.setFixedSize(300, self.UI_BUTTON_H)
        self.btn_matrix.setStyleSheet(
            "QPushButton { background-color: #000; color: #00FF41; border: 1px solid #008F11; border-radius: 6px; font-size: 14px; font-weight: bold; } QPushButton:hover { background-color: #008F11; color: black; }"
        )
        if hasattr(self, "toggle_matrix"):
            self.btn_matrix.clicked.connect(lambda checked=False: self.toggle_matrix())
        status_bar_layout.addWidget(self.btn_matrix)

        self.btn_theme = QPushButton("🌓 THEME")
        self.btn_theme.setFixedSize(200, self.UI_BUTTON_H)
        self.btn_theme.setStyleSheet(
            "QPushButton { background-color: #444; color: red; border: 1px solid #666; border-radius: 6px; font-size: 18px; font-weight: bold; } QPushButton:hover { background-color: #555; border: 1px solid #F37804; }"
        )
        self.btn_theme.clicked.connect(self.toggle_theme)
        status_bar_layout.addWidget(self.btn_theme)

        main_layout.addWidget(status_bar_container)

        # --- ANIMATIONS-TIMER STARTEN ---
        self._blink_state = True
        self.master_timer = QTimer(self)
        self.master_timer.timeout.connect(self.animate_everything)
        self.master_timer.start(500)  # 500ms Takt für das Blinken
        # ---------------------------------------------------------
        # KONTROLL-BLOCK MIT HEADER
        # ---------------------------------------------------------

        controls_group = QFrame()
        # FIX: Wir setzen eine feste Mindesthöhe für den gesamten Block,
        # damit er beim Start nicht zusammenfällt.
        controls_group.setMinimumHeight(100)

        controls_group.setStyleSheet(
            f"""
        QFrame {{
            border: 1px solid #bbb;
            border-radius: 10px;
            background-color: #2F2F2F;
        }}
        /* FIX: Wir erzwingen hier im Stylesheet, dass alle Buttons 
           im Kasten sofort ihre Zielhöhe einnehmen */
        QPushButton {{
            min-height: {self.UI_BUTTON_H}px;
            max-height: {self.UI_BUTTON_H}px;
        }}
        """
        )
        controls_group_layout = QVBoxLayout(controls_group)

        # OPTIMIERUNG: Mehr Abstand nach oben (20) und unten (20) macht den Kasten höher
        controls_group_layout.setContentsMargins(0, 20, 15, 20)
        # Mehr Abstand zwischen Header und den Reglern
        controls_group_layout.setSpacing(0)

        translated_text = self.get_t("settings_header", "Einstellungen")
        self.controls_header = QLabel(translated_text)

        self.controls_header.setMinimumWidth(280)
        # OPTIMIERUNG: Header-Höhe von 28 auf 45 erhöht für mehr Präsenz
        self.controls_header.setMinimumHeight(50)
        self.controls_header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bg = current_diff_colors.get("bg", "#2F2F2F")  # Dunkelgrauer Hintergrund
        fg = current_diff_colors.get("fg", "#EAFF00")  # NEONGELBE SCHRIFT

        self.controls_header.setStyleSheet(
            f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                font-size: 20px;          /* Schrift im Header vergrößert */
                font-weight: bold;
                padding-left: 15px;
                padding-right: 15px;
                border-radius: 8px;
            }}
            """
        )

        controls_group_layout.addWidget(
            self.controls_header, alignment=Qt.AlignmentFlag.AlignLeft
        )

        controls_row = QWidget()
        controls_layout = QHBoxLayout(controls_row)
        # OPTIMIERUNG: Auch hier mehr Innenabstand für die Zeile
        controls_layout.setContentsMargins(0, 0, 5, 5)
        controls_layout.setSpacing(0)

        # Nutze hier deine neue B_HEIGHT (z.B. 60), falls definiert, sonst BUTTON_HEIGHT
        CONTROL_HEIGHT = getattr(self, "B_HEIGHT", 50)
        controls_layout.addStretch(0)
        control_style = f"""
        QComboBox, QSpinBox {{
            font-size: 18px;
            border-radius: {self.BUTTON_RADIUS}px;
            border: 2px solid #555;
            padding: 4px 8px;
            color: white;
            background-color: #444;
            height: {CONTROL_HEIGHT}px;
            margin-left: -2px;   /* Schiebt die Box näher an den Doppelpunkt des Labels */
        }}
        """

        def make_label(text):
            lbl = QLabel(text)
            lbl.setMinimumHeight(CONTROL_HEIGHT)

            # FIX: Von 85 auf 65 verringert, damit die Boxen näher am Wort kleben
            lbl.setFixedWidth(50)

            lbl.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            lbl.setStyleSheet(
                f"""
                color: {fg}; 
                font-weight: bold; 
                font-size: 18px;
                background: transparent;
                padding-left: 0px;
            """
            )
            return lbl

        # --- 1. Sprache-Dropdown (Kompakt) ---
        self.lang_label = make_label(self.get_t("language_label", "Sprache:"))
       

        self.language_box = QComboBox()
        self.language_box.addItems(["EN", "DE"])
        self.language_box.setFixedSize(80, B_HEIGHT)
        self.language_box.setStyleSheet(
            f"""
            QComboBox {{
                background-color: #444444; color: white; font-weight: bold; font-size: 20px;
                border: 2px solid #555555; border-radius: 6px; padding-left: 5px;
            }}
            QComboBox::drop-down {{ border: none; width: 0px; }}
            QComboBox::down-arrow {{
                image: none; border-left: 5px solid transparent; border-right: 5px solid transparent;
                border-top: 5px solid #FF0000;
            }}
        """
        )

        # Sprach-Logik (Einmalig)
        saved_lang = self.cfg.get("language", "de").lower()
        (
            self.language_box.setCurrentIndex(0)
            if saved_lang == "en"
            else self.language_box.setCurrentIndex(1)
        )
        self.language_box.currentIndexChanged.connect(self.change_language)
        self.language_box.setToolTip(
            "Sprache der Oberfläche auswählen"
            if str(self.cfg.get("language", "de")).lower() == "de"
            else "Choose the interface language"
        )
        self.language_box.setToolTipDuration(10000)

        # --- 2. Farbe/Style (Kompakt) ---
        self.color_label = make_label(self.get_t("color_label", "Farbe:"))
        self.color_label.setFixedWidth(120)
        self.color_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.color_box = QComboBox()
        self.color_box.addItems(list(DIFF_COLORS.keys()))
        # Older versions stored the theme as "color", newer UI code may use
        # "theme_color". Prefer the newer key but retain backward compatibility.
        saved_color = self.cfg.get("theme_color", self.cfg.get("color", "Classics"))
        index = self.color_box.findText(saved_color)
        self.color_box.setCurrentIndex(index if index >= 0 else 0)
        self.color_box.setFixedSize(120, CONTROL_HEIGHT)
        self.color_box.setStyleSheet(control_style)
        self.color_box.currentIndexChanged.connect(self.change_colors)

        # --- 3. Commits (Kompakt) ---
        self.commit_label = make_label(self.get_t("commit_count_label", "Commits:"))

        # Breite festlegen (sizeHint + Puffer)
        
        

        # HÖHE festlegen (z.B. 35 Pixel, passend zu deinen CONTROL_HEIGHT Werten)
        self.commit_label.setFixedSize(140, self.UI_BUTTON_H)

        self.commit_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        self.commit_spin = QSpinBox()
        self.commit_spin.setRange(1, 20)
        self.commit_spin.setFixedSize(75, CONTROL_HEIGHT)
        self.commit_spin.setValue(self.cfg.get("commit_count", 10))
        self.commit_spin.valueChanged.connect(self.commit_value_changed)
        self.commit_spin.setToolTip(
            "Anzahl der Commits für die Anzeige bzw. Auswertung festlegen"
            if str(getattr(self, "LANG", self.cfg.get("language", "de"))).lower() in ("de", "0")
            else "Set the number of commits to display or analyze"
        )
        self.commit_spin.setToolTipDuration(10000)

        self.commit_spin.setStyleSheet(
            """
            QSpinBox {
                background-color: #222222; color: #FFFFFF; font-size: 20px; font-weight: bold;
                border: 2px solid #555555; border-radius: 6px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #333333; width: 25px; border-left: 1px solid #555555;
            }
            QSpinBox::up-arrow { border-left: 6px solid transparent; border-right: 6px solid transparent; border-bottom: 6px solid #FF0000; }
            QSpinBox::down-arrow { border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid #FF0000; }
        """
        )

        # Signal wurde bereits einmalig oben verbunden.
        saved_commits = self.cfg.get("commit_count", 10)
        if int(self.commit_spin.value()) != int(saved_commits):
            self.commit_spin.setValue(saved_commits)

        self.btn_check_tools = QPushButton(
            self.get_t("check_tools_button", "🛠️ Tools prüfen")
        )
        self.btn_check_tools.setFixedSize(220, self.UI_BUTTON_H)

        # --- 0. Container Erstellung (Korrektur: QGroupBox statt QFrame) ---
        controls_group = QGroupBox("")
        controls_group_layout = QVBoxLayout(controls_group)

        # Stylesheet: Macht den Kasten extrem flach und rückt den Titel bündig
        controls_group.setStyleSheet(
            """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #555555;
                border-radius: 8px;
                margin-top: 10px; 
                background-color: transparent;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 3px;
                color: #00FF00;
            }
        """
        )
        # Erzwingt eine geringe Höhe für den gesamten Block
        # controls_group.setMaximumHeight(140)

        button_style = """
            QPushButton {
                background-color: #444444;
                color: white;
                font-weight: bold; 
                font-size: 24px;          /* Ein kleiner Schritt zurück auf 28px wirkt oft Wunder */
                font-family: sans-serif;
                
                border-radius: 6px;
                border: 3px solid #555555;

                /* ZENTRIERUNG ERZWINGEN */
                text-align: center;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover { 
                background-color: #333333; 
                color: #FFD700; 
                border: 3px solid #FFD700;
            }
        """
        # --- Deine neuen Maße (Jetzt auch im Code genutzt!) ---
        B_WIDTH = 440
        B_HEIGHT = self.UI_BUTTON_H
        I_SIZE = 25

        # --- 2. Ordner-Buttons (Mit korrekter Höhe und Icon-Größe) ---
        f_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        # --- 2. Ordner-Buttons (Oben) ---
        f_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        self.btn_open_work = QPushButton(" Arbeitsordner")
        self.btn_open_work.setIcon(f_icon)
        self.btn_open_work.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_work.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_work.setStyleSheet(button_style)
        self.btn_open_work.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "WORK_DIR", self.base_dir)
            )
        )

        self.btn_open_temp = QPushButton(" Temp-Repo")
        self.btn_open_temp.setIcon(f_icon)
        self.btn_open_temp.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_temp.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_temp.setStyleSheet(button_style)
        self.btn_open_temp.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "TEMP_REPO", ".")
            )
        )

        self.btn_open_emu = QPushButton(" Emu-Git")
        self.btn_open_emu.setIcon(f_icon)
        self.btn_open_emu.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_open_emu.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_open_emu.setStyleSheet(button_style)
        self.btn_open_emu.clicked.connect(
            lambda checked=False: self.open_custom_folder(
                getattr(self, "PATCH_EMU_GIT_DIR", ".")
            )
        )

        # --- 3. Funktions-Buttons (Unten) ---
        self.btn_check_tools = QPushButton("🛠️ Tools prüfen")
        self.btn_check_tools.setIconSize(QSize(I_SIZE, I_SIZE))  # Icon-Größe für Emojis
        self.btn_check_tools.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_check_tools.setStyleSheet(button_style)
        self.btn_check_tools.clicked.connect(self.run_full_system_check)

        self.btn_modifier = QPushButton("👤 Patch Autor")
        self.btn_modifier.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_modifier.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_modifier.setStyleSheet(button_style)
        self.btn_modifier.clicked.connect(self.change_modifier_name)

        self.btn_repo_url = QPushButton("🌐 Repo URL")
        self.btn_repo_url.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_repo_url.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_repo_url.setStyleSheet(button_style)
        self.btn_repo_url.clicked.connect(self.change_emu_repo)

        # --- Konfiguration (kannst du zentral anpassen) ---
        self.font_size_buttons = 12  # Hier die gewünschte Schriftgröße in Pixeln ändern
        current_lang = getattr(self, "lang", "de")  # Erkennt deine gewählte Sprache

        # 1. FARBSCHEMA ERMITTELN (Passend zu deinem toggle_theme)
        is_dark = "#2F2F2F" in self.styleSheet() or not self.styleSheet()

        if is_dark:
            # MATRIX / DARK COLORS (Orange/Gold)
            c1, c2, b_color = "#F37804", "#8B4513", "#444"
        else:
            # LIGHT / SYSTEM COLORS (Blau)
            c1, c2, b_color = "#3498db", "#2980b9", "#1c5980"

        # 2. TEXTE FÜR MEHRSPRACHIGKEIT
        lang = getattr(self, "LANG", "de").lower()
        text_patch_online = "🌐 Patch Online " if lang == "de" else "🌐 Load Patch "

        # 3. BUTTON ERSTELLEN
        self.btn_patch_online = QPushButton(text_patch_online)
        self.btn_patch_online.setFixedSize(B_WIDTH, B_HEIGHT)

        # 4. DYNAMISCHES STYLESHEET (Mit Variablen und Font-Fix 700)
        self.btn_patch_online.setStyleSheet(
            f"""
            QPushButton {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 {c1}, stop:1 {c2});
                color: white; 
                font-weight: 700; 
                font-size: {self.font_size_buttons}px;
                border: 1px solid {b_color};
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                  stop:0 {c2}, stop:1 {c1});
                border: 1px solid #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {b_color};
                padding-top: 2px;
                border-radius: 10px;
            }}
        """
        )

        # 5. VERKNÜPFUNG
        if hasattr(self, "handle_online_patch_button"):
            self.btn_patch_online.clicked.connect(self.handle_online_patch_button)

        # --- Bestehender Button: Commit Check ---
        self.btn_check_commit = QPushButton("🔄 Commit Check")
        self.btn_check_commit.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_check_commit.setFixedSize(B_WIDTH, B_HEIGHT)
        self.btn_check_commit.setStyleSheet(button_style)
        self.btn_check_commit.clicked.connect(self.check_for_new_commit)

        # --- Manuelles Projekt-Backup ---
        self.btn_backup_gui = QPushButton("💾 Backup erstellen")
        self.btn_backup_gui.setIconSize(QSize(I_SIZE, I_SIZE))
        self.btn_backup_gui.setFixedSize(300, B_HEIGHT)
        self.btn_backup_gui.setStyleSheet(button_style)
        self.btn_backup_gui.setToolTip(
            "Erstellt backup/backup_gi.zip mit dem aktuellen Projektstand"
        )
        self.btn_backup_gui.clicked.connect(self.create_gi_backup)

        # --- 4. GRID-LAYOUT (Header-Fix: Badge 220px, Lücke 5px, Badge 280px, Weißer Text) ---
        from PyQt6.QtWidgets import QFrame

        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(10, 0, 10, 10)
        grid_layout.setVerticalSpacing(5)
        grid_layout.setHorizontalSpacing(8)

        # Farben: Basis transparent (Neon weg), Hover nutzt System-Style
        base_bg = "transparent"
        hover_bg = current_diff_colors.get("btn_hover", "#2a4a6a")

        # Haupt-Container (Gesamtbreite: 220 + 5 + 280 = 505px)
        self.header_container = QWidget()
        self.header_container.setFixedSize(950, self.UI_BADGE_H)
        self.header_container.mousePressEvent = self.on_header_clicked

        h_layout = QHBoxLayout(self.header_container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(10)  # EXAKT 5 Pixel Lücke zwischen den Badges

        # --- A) LINKER BADGE (Einstellungen - Länge 220) ---
        self.left_badge = QFrame()
        self.left_badge.setFixedSize(180, self.UI_BADGE_H)
        self.left_badge.setStyleSheet(
            f"""
            QFrame {{
                background-color: {base_bg};
                border: 1px solid #444444;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: {hover_bg};
                border: 1px solid #777777;
            }}
        """
        )

        left_layout = QHBoxLayout(self.left_badge)
        left_layout.setContentsMargins(10, 0, 10, 0)

        # Icon links
        icon_label = QLabel()
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        icon_label.setPixmap(icon.pixmap(20, 20))
        left_layout.addWidget(icon_label)

        # --- TITEL (Dynamisch ans Theme angepasst) ---
        # Aktuelle Akzentfarbe aus dem Theme laden (z.B. Neongelb)
        t_fg = current_diff_colors.get("fg", "#EAFF00")

        title_text = " Einstellungen" if self.LANG == "de" else " Settings"
        self.header_label = QLabel(title_text)

        # 'white' durch die Theme-Variable {t_fg} ersetzt
        self.header_label.setStyleSheet(
            f"""
            QLabel {{
                color: {t_fg}; 
                font-weight: bold; 
                font-size: 15px; 
                background: transparent; 
                border: none;
            }}
        """
        )

        left_layout.addWidget(self.header_label)
        left_layout.addStretch()
        h_layout.addWidget(self.left_badge)

        # --- B) RECHTER BADGE (OSCam Status - Länge 280) ---
        self.right_badge = QFrame()
        self.right_badge.setFixedSize(600, self.UI_BADGE_H)
        self.right_badge.setStyleSheet(
            f"""
            QFrame {{
                background-color: transparent;
                border: 1px solid #444444;
                border-radius: 6px;
            }}
            QFrame:hover {{
                background-color: transparent;
                border: 1px solid #777777;
            }}
        """
        )

        right_layout = QHBoxLayout(self.right_badge)
        right_layout.setContentsMargins(
            10, 0, 10, 0
        )  # Margins setzen, um Platz für Text zu schaffen

        # Status-Label (Zwingend WEISSE Schrift)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 18px; background: transparent; border: none;"
        )

        # Füge das Label ohne Stretch hin
        right_layout.addWidget(self.status_label)

        # Keine weiteren Strecken mehr erforderlich
        h_layout.addWidget(self.right_badge)

        # --- Integration ins Grid (Zeile 0) ---
        grid_layout.addWidget(self.header_container, 0, 0, 1, 4)
        grid_layout.addWidget(self.btn_open_work, 1, 9)

        grid_layout.addWidget(self.btn_open_emu, 0, 6)
        grid_layout.addWidget(self.btn_repo_url, 0, 7)

        grid_layout.addWidget(self.btn_open_temp, 0, 8)
        grid_layout.addWidget(self.btn_backup_gui, 0, 9)

        # --- EINSTELLUNGEN: kompakt, linksbündig, eine Reihe ---
        settings_row = QHBoxLayout()
        settings_row.setContentsMargins(0, 0, 0, 0)
        settings_row.setSpacing(6)

        # Sprache
        self.lang_label.setFixedWidth(120)
        self.lang_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.language_box.setFixedWidth(90)

        settings_row.addWidget(self.lang_label)
        settings_row.addWidget(self.language_box)

        # Abstand zwischen den Gruppen
        settings_row.addSpacing(8)

        # Farbe
        self.color_label.setFixedWidth(80)
        self.color_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.color_box.setFixedWidth(200)

        settings_row.addWidget(self.color_label)
        settings_row.addWidget(self.color_box)

        settings_row.addSpacing(8)

        # Commits
        self.commit_label.setFixedWidth(140)
        self.commit_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.commit_spin.setFixedWidth(80)

        settings_row.addWidget(self.commit_label)
        settings_row.addWidget(self.commit_spin)

        # Backup-Button direkt hinter der Commit-Anzahl-Auswahl
        #settings_row.addWidget(self.btn_backup_gui)

        # Freier Platz bleibt rechts von den Einstellungen
        settings_row.addStretch(1)

        # Einstellungen in einer einzigen Reihe links anordnen
        grid_layout.addLayout(settings_row, 1, 0, 1, 6)

        # Die vier Git-/Revisions-Buttons direkt unter den Ordner-Buttons anordnen.
        # Die Widgets werden aus ihren bisherigen Layout-Positionen verschoben.
        grid_layout.addWidget(self.oscam_source_button, 1, 6)

        # Repo URL ist bereits oben neben Emu-Git platziert.

        # Keine Grid-Spalte künstlich verbreitern
        for i in range(grid_layout.columnCount()):
            grid_layout.setColumnStretch(i, 0)

        # Kleine Abstände zwischen den Grid-Elementen
        grid_layout.setHorizontalSpacing(6)
        grid_layout.setVerticalSpacing(6)


        # Layout zum Kasten hinzufügen
        controls_group_layout.addLayout(grid_layout)
        main_layout.addWidget(controls_group)

        # --- UNTERE SEKTION: klare Priorität für Patch-Aktionen ---
        self.grid_container = QGroupBox("PATCH & BUILD")
        self.grid_container.setObjectName("patchBuildPanel")
        self.grid_container.setStyleSheet("""
            QGroupBox#patchBuildPanel {
                margin-top: 4px;
            }

            QGroupBox#patchBuildPanel::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0px 5px;
                top: -10px;
            }
        """)
        self.layout_grid_buttons = QGridLayout(self.grid_container)
        # Kompakte, gleichmäßige Abstände; das Grid passt die Spaltenzahl
        # anhand der tatsächlich verfügbaren Breite dynamisch an.
        self.layout_grid_buttons.setHorizontalSpacing(6)
        self.layout_grid_buttons.setVerticalSpacing(6)
        self.layout_grid_buttons.setContentsMargins(8, 8, 8, 8)

        # Container zuerst einbetten, dann die vorhandenen Aktionsbuttons erzeugen.
        main_layout.addWidget(self.grid_container)
        self.setup_grid_buttons()

        # Die sechs bisher oben rechts platzierten Aktionsbuttons werden
        # in den PATCH & BUILD-Bereich integriert. Die Reihenfolge folgt
        # dem typischen Arbeitsablauf: Patch holen/erstellen, prüfen und
        # anwenden, sichern, anschließend Repository-/Systemwerkzeuge.
        
        patch_build_order = [
            getattr(self, "btn_patch_online", None),
            getattr(self, "buttons", {}).get("patch_create"),
            getattr(self, "buttons", {}).get("patch_renew"),
            getattr(self, "buttons", {}).get("patch_check"),
            getattr(self, "buttons", {}).get("patch_apply"),
            getattr(self, "buttons", {}).get("patch_zip"),
            getattr(self, "buttons", {}).get("backup_old"),
            getattr(self, "buttons", {}).get("clean_folder"),
            getattr(self, "buttons", {}).get("change_old_dir"),
            getattr(self, "btn_check_commit", None),
            getattr(self, "btn_modifier", None),
            getattr(self, "btn_check_tools", None),

            # Beenden
            getattr(self, "buttons", {}).get("exit"),

            # Direkt danach: Rechte fixen
            getattr(self, "btn_fix_perms", None),
        ]


        # Alte Grid-Einträge leeren und in der gewünschten Reihenfolge neu
        # einsetzen. Signale/Callbacks bleiben dabei unverändert verbunden.
        patch_layout = self.layout_grid_buttons
        while patch_layout.count():
            item = patch_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(self.grid_container)

        from PyQt6.QtWidgets import QSizePolicy
        seen_patch_buttons = set()
        ordered_patch_buttons = []
        for button in patch_build_order:
            if button is None or id(button) in seen_patch_buttons:
                continue
            seen_patch_buttons.add(id(button))
            ordered_patch_buttons.append(button)
            button.setParent(self.grid_container)
            # Die sechs verschobenen Buttons sollen sich genauso flexibel
            # an die Spaltenbreite anpassen wie die nativen Patch-Buttons.
            if button in (
                getattr(self, "btn_patch_online", None),
                #getattr(self, "btn_backup_gui", None),
                getattr(self, "btn_repo_url", None),
                getattr(self, "btn_check_commit", None),
                getattr(self, "btn_modifier", None),
                getattr(self, "btn_check_tools", None),
                getattr(self, "buttons", {}).get("exit"),
            ):
                button.setMinimumSize(250, 50)
                # Keine künstliche Maximalbreite: sonst entstehen im rechten
                # Bereich große Lücken, obwohl das Grid seine Spalten streckt.
                button.setMaximumHeight(50)
                button.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed,
                )

        # Erst kompakt einsetzen; ResponsiveGridReflow ordnet danach anhand
        # der realen Containerbreite in passende Spalten um.
        for index, button in enumerate(ordered_patch_buttons):
            patch_layout.addWidget(button, index, 0)

        # ResponsiveGridReflow liest dieselbe Layout-Reihenfolge aus und
        # passt die Spaltenzahl beim Fenster-Resize automatisch an.
        reflow = getattr(self, "_patch_grid_reflow", None)
        if reflow is not None:
            reflow.reflow()

        # Weitere Werkzeuge in einer separaten, responsiven Sektion.

        self.setup_option_buttons(main_layout)

        # Revisions-Buttons auf dieselbe Zeile wie „Oscam Git URL“ setzen.
        # Repo URL bleibt oben neben Emu-Git und wird nicht erneut verschoben.
        revision_button_min_width = 220
        revision_button_height = max(
            self.oscam_source_button.sizeHint().height(),
            self.oscam_source_button.height(),
            50,
        )
        for col, key in ((7, "streamboard_checkout"), (8, "oscam_emu_revision")):
            entry = self.option_buttons.get(key)
            if entry:
                button = entry[0] if isinstance(entry, (tuple, list)) else entry
                # Keine feste Breite erzwingen: Das Grid muss die Buttons an
                # die tatsächlich verfügbare Fensterbreite anpassen können.
                button.setMinimumWidth(revision_button_min_width)
                button.setMaximumWidth(16777215)
                button.setFixedHeight(revision_button_height)
                button.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed,
                )
                button.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                button.setStyleSheet(
                    button.styleSheet()
                    + "\nQPushButton { padding-left: 3px; padding-right: 3px; margin: 0px; }"
                )
                button.setToolTip(button.text())
                grid_layout.addWidget(
                    button, 1, col,
                    alignment=Qt.AlignmentFlag.AlignVCenter
                )


        
        
        # ---------------------------------------------------------
        # TIMER & DIGITAL CLOCK
        # ---------------------------------------------------------
        def update_digital_clock():
            now = QDateTime.currentDateTime()
            # Aktiviert die digitale Uhrzeit-Aktualisierung:
            self.digital_clock.setText(now.toString("HH:mm:ss"))
            # Aktualisiert das Datum:
            self.date_label.setText(now.toString("dd.MM.yyyy"))

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(update_digital_clock)
        self.clock_timer.start(1000)
        update_digital_clock()


        # ---------------------------------------------------------
        # FINAL SETTINGS
        # ---------------------------------------------------------
        self.change_colors()
        self.update_language()

        # Einheitliches Farbschema nach der vollständigen UI-Initialisierung
        # nochmals anwenden. Einige Widgets/Statusprüfungen werden verzögert
        # erstellt oder aktualisiert; diese Aufrufe stellen sicher, dass deren
        # individuelle Styles nicht dauerhaft das Theme überschreiben.
        # Stats bleibt eine QCheckBox und wird vom Button-Styling nicht verändert.
        for _style_delay in (0, 250, 1000):
            QTimer.singleShot(
                _style_delay,
                lambda: self.apply_global_button_style()
                if hasattr(self, "apply_global_button_style") else None,
            )

        # 2. Fenster-Eigenschaften bildschirmabhängig festlegen
        # Mindestgröße an die tatsächlich verfügbare Bildschirmfläche anpassen.
        # So verhindert die GUI auf kleineren Displays keine passende Fenstergröße.
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()  # ohne Taskleiste/Dock
            min_width = min(1200, max(640, available.width() - 50))
            min_height = min(850, max(480, available.height() - 80))
        else:
            min_width, min_height = 800, 600
        self.setMinimumSize(min_width, min_height)
        self.setWindowTitle(
            f"OSCam Toolkit v{APP_VERSION} | {getattr(self, 'patch_modifier', 'speedy005')}"
        )

        # 3. Maximiert starten, damit die GUI die verfügbare Bildschirmfläche nutzt.
        # Die Mindestgröße ist oben bereits an die Auflösung angepasst.
        self.showMaximized()
        QApplication.processEvents()  # WICHTIG: Berechnet die 60px Höhe vor dem ersten Klick
        self.updateGeometry()  # Stabilisiert das FlowLayout

        # 4. Signale sind bereits an den jeweiligen Handlern verbunden:
        #    Farbe -> change_colors(), Commits -> commit_value_changed().
        #    Keine zweite Verbindung hier, damit kein doppeltes Speichern/Feedback entsteht.

        # 5. System-Check mit kleiner Verzögerung starten
        # Wir definieren das Design zentral für ALLE Buttons der App
        neon_style = """
            QPushButton {
                background-color: #3d3d3d !important;
                color: #EAFF00 !important;
                border: 1px solid #555 !important;
                border-radius: 8px !important;
                padding: 5px !important;
                font-weight: bold !important;
                font-size: 12pt !important;
            }
            QPushButton:hover {
                background-color: #4d4d4d !important;
                border: 1px solid #EAFF00 !important;
                color: white !important;
            }
        """

        # --- THEME BEIM START LADEN (Matrix-Check) ---
        # 1. Sicherstellen, dass wir die aktuellsten Daten haben
        # Falls self.current_config noch leer ist, laden wir sie hier kurz manuell
        if not hasattr(self, "current_config") or not self.current_config:
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        self.current_config = json.load(f)
                    self.cfg = self.current_config
                except Exception as e:
                    print(f"Fehler beim Laden der Konfiguration: {e}")
                    self.current_config = {}
                    self.cfg = self.current_config
            else:
                self.current_config = {}
                self.cfg = self.current_config

        # S3-Git-Repositories
        self.s3_repository_options = {
            "S3 Simplebuild (Original)": "https://github.com/gorgone/s3_releases.git",
            "S3 Simplebuild speeddy005": "https://github.com/speedy005/speedy005-S3-Simplebuild.git",
        }

        # Gespeicherte Auswahl wiederherstellen
        self.selected_s3_repository = self.current_config.get(
            "s3_repository_name",
            "S3 Simplebuild (Original)"
        )

        if self.selected_s3_repository not in self.s3_repository_options:
            self.selected_s3_repository = "S3 Simplebuild (Original)"

        self.s3_repo_combo = None
        self.s3_install_worker = None

        cfg = getattr(self, "current_config", {})
        saved_theme = cfg.get("theme_mode", "standard")

        # 2. Matrix erzwingen
        if saved_theme == "matrix":
            # Wir setzen is_loading auf True, um Sounds/Logs beim Start zu blockieren
            was_loading = getattr(self, "is_loading", False)
            self.is_loading = True

            # WICHTIG: Erst das normale Stylesheet löschen, dann Matrix setzen
            self.setStyleSheet("")
            self.toggle_matrix(force_state="matrix")

            # Uhr-Update
            if hasattr(self, "analog_clock"):
                self.analog_clock.update()

            self.is_loading = was_loading
        else:
            # Falls nicht Matrix, Standard-Neon setzen
            self.setStyleSheet(self.styleSheet() + neon_style)

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

    def change_old_(self, info_widget=None, progress_callback=None):
        # --- Final Label verstecken ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        global OLD_, OLD_PATCH_FILE, ALT_PATCH_FILE

        info_widget = info_widget or self.info_text
        lang = getattr(self, "LANG", LANG)  # aktuelle GUI-Sprache

        new_dir = QFileDialog.getExistingDirectory(
            self, TEXTS[lang]["change_old_dir"], OLD_
        )

        if new_dir:
            OLD_ = new_dir
            OLD_PATCH_FILE = os.path.join(OLD_, "oscam-emu.patch")
            ALT_PATCH_FILE = os.path.join(OLD_, "oscam-emu.altpatch")

            self.OLD_PATCH_DIR = OLD_
            self.OLD_PATCH_FILE = OLD_PATCH_FILE
            self.ALT_PATCH_FILE = ALT_PATCH_FILE
            saved = save_config(
                {
                    "s3_patch_path": OLD_,
                    "old_patch_dir": OLD_,
                },
                gui_instance=self,
                silent=True,
            )
            if not saved:
                self.append_info(
                    info_widget,
                    "❌ Fehler beim Speichern des Patch-Pfads.",
                    "error",
                )
                return False

            self.append_info(
                info_widget,
                TEXTS[lang]["old_patch_path_changed"].format(OLD_=OLD_),
                "success",
            )
        else:
            self.append_info(
                info_widget, TEXTS[lang]["old_patch_path_cancelled"], "info"
            )

        if progress_callback:
            progress_callback(100)


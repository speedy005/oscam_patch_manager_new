"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerActionsMixin:
    """Patch Manager Actions"""

    def _run_grid_action(self, key, func):
        """Führt eine Grid-Aktion nach einem echten Button-Klick aus."""

        print(f"[GRID CLICK] START: {key}", flush=True)

        # ---------------------------------------------------------
        # Aktiven Button setzen
        # ---------------------------------------------------------
        try:
            self.set_active_button(key)
            print(f"[GRID CLICK] set_active_button OK: {key}", flush=True)
        except Exception as e:
            print(
                f"[GRID CLICK] set_active_button Fehler bei {key}: {e}",
                flush=True
            )

        # ---------------------------------------------------------
        # Callback prüfen
        # ---------------------------------------------------------
        if func is None:
            print(
                f"[GRID CLICK] FEHLER: Kein Callback für {key}",
                flush=True
            )
            return

        print(
            f"[GRID CLICK] Callback: {getattr(func, '__name__', repr(func))}",
            flush=True
        )

        # ---------------------------------------------------------
        # Aktion ausführen
        # ---------------------------------------------------------
        try:
            result = func()

            print(
                f"[GRID CLICK] ENDE: {key} -> {result!r}",
                flush=True
            )

            return result

        except Exception as e:
            print(
                f"[GRID CLICK] Aktion {key} fehlgeschlagen: {e}",
                flush=True
            )

            import traceback
            traceback.print_exc()

            return None

    def smooth_progress(pbar, start, end, duration=500):
        """
        Animiert die ProgressBar von start bis end in `duration` ms.
        """
        steps = max(abs(end - start), 1)
        interval = duration // steps
        value = start

        def update():
            nonlocal value
            if value >= end:
                timer.stop()
                return
            value += 1
            pbar.setValue(value)

        timer = QTimer()
        timer.timeout.connect(update)
        timer.start(interval)

    def animate_status_bar(self):
        """Wechselt den Zustand der User-LEDs für den Blink-Effekt mit Theme-Support.
        System-Status LEDs bleiben immer statisch.
        """
        # --- 0. NOTBREMSE: Verhindert Blinken beim Start ---
        if getattr(self, "is_loading", False):
            return

        if not hasattr(self, "user_leds") or not self.user_leds:
            return

        # Blink-Status umschalten
        self._blink_state = getattr(self, "_blink_state", False)
        self._blink_state = not self._blink_state

        # 1️⃣ Theme-Check
        is_matrix = self.current_config.get("theme_mode") == "matrix"

        # 2️⃣ Farben & Rahmen definieren
        if self._blink_state:
            # AN-Zustand
            color = "#00FF41" if is_matrix else "cyan"
            border = "1px solid #008F11" if is_matrix else "1px solid white"
        else:
            # AUS-Zustand
            color = "#002200" if is_matrix else "#222"
            border = "1px solid #004400" if is_matrix else "1px solid #444"

        # 3️⃣ Stylesheet auf User-LEDs anwenden
        style = f"background-color: {color}; border-radius: 5px; border: {border};"
        for led in self.user_leds:
            try:
                led.setStyleSheet(style)
            except:
                continue

    def _run_blink_sequence(self):
        """Führt genau 10 Farbwechsel (5 Blinks) aus und stoppt dann."""
        pbar = getattr(self, "progress_bar", None)
        if not pbar:
            return

        # Prüfen, ob wir fertig sind (10 Toggles = 5 Mal blinken)
        if self.blink_count >= 10:
            self.idle_blink_timer.stop()
            # Finaler "Steady" Style (Kein Grau!)
            self._apply_pbar_style(final=True)
            return

        # Farbwechsel
        self.blink_count += 1
        is_on = self.blink_count % 2 == 0
        self._apply_pbar_style(is_on)

    def _apply_pbar_style(self, is_on=True, final=False):
        """Hilfsfunktion für das Styling ohne Code-Duplikate."""
        pbar = getattr(self, "progress_bar", None)

        # Mode erkennen
        current_style = self.styleSheet()
        is_matrix = "#00ff00" in current_style.lower()

        if is_matrix:
            color = "#00FF00" if is_on else "#002200"
            bg = "#050505"
            border = "#00FF00"
        else:
            # Gold-Modus: Gold vs. Dunkel-Orange
            color = "#050504" if is_on else "#8B4513"
            bg = "#111111"
            border = "#444"

        # Falls wir fertig sind, setzen wir die Textfarbe fest auf Gold/Grün
        if final:
            color = "#0BF641" if not is_matrix else "#00FF00"

        pbar.setStyleSheet(
            f"""
            QProgressBar {{ 
                border: 2px solid {border}; border-radius: 8px; background-color: {bg}; 
                color: {color}; text-align: center; font-weight: 900; font-size: 20px; 
            }}
            QProgressBar::chunk {{ background: transparent; }}
        """
        )

    def on_telemetry_changed(self, checked):
        """Schaltet Stats um und speichert den Zustand dauerhaft."""
        try:
            checked = bool(checked)
            save_setting("allow_telemetry", checked)
            is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
            status = ("aktiviert" if checked else "deaktiviert") if is_de else ("enabled" if checked else "disabled")
            if hasattr(self, "info_text") and self.info_text is not None:
                message = f"Stats: {status}"
                if hasattr(self, "append_info"):
                    self.append_info(self.info_text, message, "success")
                else:
                    self.info_text.append(message)
            print(f"Stats {status}; allow_telemetry={checked}")
            # Die Status-Infobox wird bei jeder Änderung angezeigt.
            title = "Stats-Einstellung" if is_de else "Stats Settings"
            detail = (
                f"Anonyme Nutzungsstatistik ist jetzt {status}.\n\n"
                "Die Einstellung wird gespeichert und beim nächsten Start beibehalten."
                if is_de else
                f"Anonymous usage statistics are now {status}.\n\n"
                "This setting is saved and kept for the next launch."
            )
            QMessageBox.information(self, title, detail)
        except Exception as exc:
            print(f"Stats-Einstellung konnte nicht gespeichert werden: {exc}")
            try:
                QMessageBox.warning(self, "Stats", str(exc))
            except Exception:
                pass

    def init_button_signals(self):
        """Verknüpft Ordner- und Funktions-Buttons."""
        import os
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QMenu, QFileDialog
        from config_manager import save_config

        path_map = {
            "btn_open_temp": getattr(
                self, "TEMP_REPO", os.path.join(os.getcwd(), "oscam-svn")
            ),
            "btn_open_emu": getattr(
                self, "PATCH_EMU_GIT_DIR",
                os.path.join(os.getcwd(), "oscam-emu-patch")
            ),
        }

        # Arbeitsordner: immer den aktuell gespeicherten Wert verwenden
        work_button = getattr(self, "btn_open_work", None)
        if work_button:
            try:
                work_button.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass

            work_button.clicked.connect(
                lambda checked=False: self.open_custom_folder(
                    getattr(self, "WORK_DIR", os.getcwd())
                )
            )

            work_button.setContextMenuPolicy(
                Qt.ContextMenuPolicy.CustomContextMenu
            )

            # Vorherige Kontextmenü-Verbindung möglichst entfernen
            try:
                work_button.customContextMenuRequested.disconnect()
            except (TypeError, RuntimeError):
                pass

            def choose_work_dir(position):
                menu = QMenu(work_button)
                action_choose = menu.addAction(
                    "Anderen Arbeitsordner auswählen …"
                )
                selected = menu.exec(work_button.mapToGlobal(position))

                if selected != action_choose:
                    return

                current_dir = getattr(self, "WORK_DIR", os.getcwd())
                folder = QFileDialog.getExistingDirectory(
                    self,
                    "Arbeitsordner auswählen",
                    current_dir
                )

                if not folder:
                    return

                folder = os.path.normpath(folder)
                self.WORK_DIR = folder

                if not isinstance(getattr(self, "current_config", None), dict):
                    self.current_config = {}

                self.current_config["work_dir"] = folder

                save_config(
                    self.current_config,
                    gui_instance=self,
                    silent=True
                )

            work_button.customContextMenuRequested.connect(choose_work_dir)

        # Temp-Repo und EMU-Repo
        for btn_name, path in path_map.items():
            btn = getattr(self, btn_name, None)
            if not btn:
                continue

            try:
                btn.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass

            btn.clicked.connect(
                lambda checked=False, p=path: self.open_custom_folder(p)
            )

            if hasattr(self, "_play_sys_sound"):
                btn.clicked.connect(
                    lambda checked=False: self._play_sys_sound("standard")
                )

        # Funktions-Buttons
        func_names = {
            "btn_check_tools": "run_full_system_check",
            "restart_tool_button": "restart_app",
            "clean_emu_button": "clean_emu_data",
            "patch_emu_git_button": "run_patch_process",
            "btn_edit_patch": "edit_patch_header",
        }

        for btn_attr, method_name in func_names.items():
            btn = getattr(self, btn_attr, None)
            method = getattr(self, method_name, None)

            if btn and method:
                try:
                    btn.clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                btn.clicked.connect(method)
            elif btn:
                btn.setEnabled(False)
                btn.setToolTip(
                    f"Fehler: Methode '{method_name}' fehlt!"
                )

    def on_update_check_finished(self, update_available=False, new_rev=None):
        """
        Aktualisiert das UI:
        - Status Label (Update / aktuell)
        - Neongrün-Blinken der Revision (3 Mal)
        - ProgressBar bleibt unverändert
        - Am Ende: Label "Was bauen wir heute?" in Kasten
        """

        from datetime import datetime
        from PyQt6.QtCore import QTimer, Qt
        from PyQt6.QtWidgets import QLabel

        # Hide final label if exists
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        txt = getattr(self, "TEXT", {})
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.last_timestamp = timestamp  # Für Sprachwechsel speichern!

        # 1. Die alte Revision für die Anzeige zwischenspeichern
        old_rev = getattr(self, "current_rev", "11943")

        # --- Revisions-Sound nur beim roten Aufblinken ---
        sound_manager = getattr(self, "sound_manager", None)

        def blink_revision(color):
            set_status_ui(color)

            if color == C_BLINK and sound_manager and sound_manager.enabled:
                
                sound_manager.play_revision()

        # 2. Die neue Revision für die Zukunft speichern
        if update_available and new_rev:
            self.current_rev = new_rev

        self.last_remote_rev = new_rev

        # --- Zentrale Farben & Schriftarten ---
        C_TIME = "#FF0000"
        F_TIME = "Arial, Segoe UI, sans-serif"
        F_TIME_SIZE = "26px"
        F_TIME_WEIGHT = "bold"

        C_REV = "#00FF00"
        F_REV = "Arial, Segoe UI, sans-serif"
        F_REV_SIZE = "26px"
        F_REV_WEIGHT = "bold"

        C_BLINK = "#F70606"
        C_FINAL_COLOR = "cyan"
        BG_FINAL_LABEL = "black"
        F_FINAL_LABEL = "Arial, Segoe UI, sans-serif"
        F_FINAL_LABEL_SIZE = "26px"
        F_FINAL_LABEL_WEIGHT = "bold"
        FINAL_LABEL_BORDER_RADIUS = 6

        # Nachrichten
        MSG_UPTODATE_COLOR = "#00FF00"
        MSG_UPTODATE_FONT = "Arial, Segoe UI, sans-serif"
        MSG_UPTODATE_SIZE = "26px"
        MSG_UPTODATE_WEIGHT = "bold"

        MSG_UPDATE_COLOR = "#FFAA00"
        MSG_UPDATE_FONT = "Arial, Segoe UI, sans-serif"
        MSG_UPDATE_SIZE = "26px"
        MSG_UPDATE_WEIGHT = "bold"

        # --- System Sound Helper ---
        def play_system_sound(sound_type="info"):
            safe_play = globals().get("safe_play")
            if safe_play:
                sounds = {
                    "update": "dialog-information.oga",
                    "uptodate": "complete.oga",
                    "beep": "bell.oga",
                }
                safe_play(sounds.get(sound_type, "complete.oga"))

        # --- Status Label ---
        status_label = getattr(self, "status_label", None)
        msg = txt.get("oscam_uptodate", "OSCam ist aktuell.")

        def set_status_ui(rev_color=C_REV, opacity=1.0):
            """Aktualisiert Status Label mit Farben, Fonts und optional Blink"""
            if status_label:
                html = (
                    f"✅ <span style='font-size:{F_TIME_SIZE}; font-family:{F_TIME}; color:{C_TIME}; font-weight:{F_TIME_WEIGHT};'>[{timestamp}]</span> "
                    f"<span style='font-size:{MSG_UPTODATE_SIZE}; font-family:{MSG_UPTODATE_FONT}; font-weight:{MSG_UPTODATE_WEIGHT}; color:{MSG_UPTODATE_COLOR};'>{msg}</span> "
                    f"<span style='color:{rev_color}; opacity:{opacity}; font-size:{F_REV_SIZE}; font-family:{F_REV}; font-weight:{F_REV_WEIGHT};'>(r{old_rev})</span>"
                )
                status_label.setText(html)
                status_label.show()

        if update_available:
            title = txt.get("oscam_update_found", "UPDATE VERFÜGBAR")
            
            # Update-Meldung zusätzlich im großen Infoscreen anzeigen
            self.append_info(
                self.info_text,
                f"🚀 [{timestamp}] {title} "
                f"(r{old_rev} → r{new_rev})",
                "warning",
            )

            if status_label:
                html = (
                    f"🚀 <span style='font-size:{F_TIME_SIZE}; font-family:{F_TIME}; color:{C_TIME}; font-weight:{F_TIME_WEIGHT};'>[{timestamp}]</span> "
                    f"<span style='font-size:{MSG_UPDATE_SIZE}; font-family:{MSG_UPDATE_FONT}; font-weight:{MSG_UPDATE_WEIGHT}; color:{MSG_UPDATE_COLOR};'><b>{title}</b></span> "
                    f"<span style='color:{C_REV}; font-size:{F_REV_SIZE}; font-family:{F_REV}; font-weight:{F_REV_WEIGHT};'>(r{old_rev} ➔ r{new_rev})</span>"
                )
                status_label.setText(html)
            play_system_sound("update")

            # --- Blink-Sequenz 3x ---
            delays = [300, 600, 900, 1200, 1500, 1800]
            blink_colors = [
                "transparent",
                C_BLINK,
                "transparent",
                C_BLINK,
                "transparent",
                C_BLINK,
            ]
            for i, delay in enumerate(delays):
                QTimer.singleShot(
                    delay,
                    lambda c=blink_colors[i]: blink_revision(c)
                )

        
        else:
            # --- Up-to-date ---
            set_status_ui()

            # Status zusätzlich im großen Infoscreen anzeigen
            self.append_info(
                self.info_text,
                (
                    f'<span style="font-size:24px; font-weight:bold; color:#00FF00;">'
                    f'✅ [{timestamp}] {msg} </span>'
                    f'<span style="font-size:24px; font-weight:bold; color:#FF0000;">(r{old_rev})</span>'
                ),
                "html",
            )

            play_system_sound("uptodate" if new_rev else "error")

            # --- Blink-Sequenz für Revision ---
            delays = [300, 600, 900, 1200, 1500, 1800]
            blink_colors = [
                "transparent",
                C_BLINK,
                "transparent",
                C_BLINK,
                "transparent",
                C_BLINK,
            ]
            for i, delay in enumerate(delays):
                QTimer.singleShot(
                    delay,
                    lambda c=blink_colors[i]: blink_revision(c)
                )

    def trigger_alert_animation(self, widget):
        """Lässt ein Widget dezent rot pulsieren."""
        effect = QGraphicsColorizeEffect(widget)
        widget.setGraphicsEffect(effect)

        self.pulse_anim = QPropertyAnimation(effect, b"color")
        self.pulse_anim.setDuration(1200)
        self.pulse_anim.setStartValue(QColor(Qt.GlobalColor.transparent))
        self.pulse_anim.setEndValue(QColor(255, 50, 50))  # Softes Rot
        self.pulse_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.pulse_anim.setLoopCount(-1)  # Unendlich
        self.pulse_anim.start()

    def upload_progress_with_speed(self, current, total):
        """Aktualisiert Progressbar und zeigt Live-Speed im Log an."""
        import time

        # Initialisierung beim ersten Aufruf
        if not hasattr(self, "_upload_start_time") or current <= 0:
            self._upload_start_time = time.time()
            self._last_printed_second = 0

        # Progressbar füllen
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)

        # Geschwindigkeit berechnen (alle 0.5 Sekunden aktualisieren)
        elapsed = time.time() - self._upload_start_time
        if elapsed > 0.5:
            speed_kb = (current / 1024) / elapsed
            speed_text = (
                f"🚀 Upload: {speed_kb:.2f} KB/s ({current/1024:.1f} KB übertragen)"
            )

            # Schreibt die Info in das Log-Fenster (überschreibt die letzte Zeile nicht,
            # aber wir können eine Status-Zeile im GUI-Label nutzen oder im Log-Anhängen)
            if int(elapsed) > self._last_printed_second:
                self.append_info(self.info_text, speed_text, "info")
                self._last_printed_second = int(elapsed)

    def plugin_update_action(self, latest_version=None, progress_callback=None):
        """Aktualisiert das Projekt aus GitHub und schützt lokale Daten."""

        import json
        import os
        import sys
        import time
        import shutil
        import tempfile
        import zipfile
        import subprocess

        from pathlib import Path, PurePosixPath
        from io import BytesIO

        import requests

        from PyQt6.QtCore import QTime
        from PyQt6.QtWidgets import QMessageBox, QApplication

        project_dir = Path(__file__).resolve().parent.resolve()

        # --------------------------------------------------
        # 1. Grundeinstellungen und geschützte Ordner
        # --------------------------------------------------
        protected_dirs = {
            "backup",
            ".git",
            "oscam-emu-git",
            "streamboard-git",
            "__pycache__",
            ".venv",
            "venv",
        }

        protected_files = {
            "Noto_Color_Emoji.zip",
            "oscam_emu_toolkit2.png",
            "oscam-patch-generator.png",
            "speedy_oscam_managert.png",
            "final-oscam-emu-patch-maker.png",
            "final-englisch.png",
            "speedy_banner.png",
            "README.md",
            "version.txt",
            "config.json",
            "settings.json",
            "github_config.json",
            "install_counter.txt",
            "oscam_rev.txt",
        }

        config_file = project_dir / "config.json"
        custom_keys = (
            "s3_custom_path",
            "ncam_custom_path",
            "s4_custom_path",
        )

        # Einheitliche Pfadbehandlung, insbesondere unter Windows.
        def normalized_path(path):
            return os.path.normcase(
                os.path.abspath(os.fspath(path))
            )

        project_norm = normalized_path(project_dir)

        def is_inside(path, parent):
            """True, wenn path gleich parent ist oder darunter liegt."""
            try:
                return os.path.commonpath(
                    [normalized_path(path), normalized_path(parent)]
                ) == normalized_path(parent)
            except (ValueError, OSError):
                return False

        # --------------------------------------------------
        # 2. Konfigurierte Ordner sicher ermitteln
        # --------------------------------------------------
        protected_custom_paths = []

        try:
            with config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)

            if not isinstance(config, dict):
                raise ValueError(
                    "config.json enthält kein gültiges JSON-Objekt."
                )

            for key in custom_keys:
                value = config.get(key)

                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"Der Konfigurationswert '{key}' fehlt."
                    )

                custom_path = Path(value.strip()).expanduser()

                if not custom_path.is_absolute():
                    custom_path = project_dir / custom_path

                custom_path = custom_path.resolve()

                # Externe Pfade nicht stillschweigend akzeptieren.
                if not is_inside(custom_path, project_dir):
                    raise ValueError(
                        f"Der Ordner '{key}' liegt außerhalb des "
                        f"Projektverzeichnisses: {custom_path}"
                    )

                if normalized_path(custom_path) == project_norm:
                    raise ValueError(
                        f"Der Ordner '{key}' verweist auf das gesamte Projekt."
                    )

                if normalized_path(custom_path) not in {
                    normalized_path(p) for p in protected_custom_paths
                }:
                    protected_custom_paths.append(custom_path)

            if len(protected_custom_paths) != 3:
                raise ValueError(
                    "Die drei konfigurierten Ordner müssen eindeutig sein."
                )

        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            QMessageBox.critical(
                self,
                "Konfigurationsfehler",
                "Das Update wurde aus Sicherheitsgründen nicht gestartet.\n\n"
                "Die drei Ordner aus config.json konnten nicht sicher "
                "ermittelt werden.\n\n"
                f"Details: {exc}",
            )
            return False

        # --------------------------------------------------
        # 3. Zentrale Schutzprüfung für Backup und Update
        # --------------------------------------------------
        def is_protected(path):
            path = Path(path)

            try:
                relative = path.relative_to(project_dir)
            except ValueError:
                return True

            # Geschützte Standardordner überall im relativen Pfad.
            # Geschützte Standardordner und alle Ordner mit s3 oder s4
            # im Namen schützen – sowohl beim Backup als auch beim Update.
            protected_dir_names = {
                name.casefold() for name in protected_dirs
            }

            if any(
                part.casefold() in protected_dir_names
                or "s3" in part.casefold()
                or "s4" in part.casefold()
                for part in relative.parts[:-1]
            ):
                return True

            # Die drei konfigurierten Ordner samt Inhalt schützen.
            for custom_path in protected_custom_paths:
                if is_inside(path, custom_path):
                    return True

            # Bestimmte Dateien nicht sichern oder überschreiben.
            # config.json wird beim Update geschützt, aber im Backup gesichert.
            if path.name.casefold() in {
                name.casefold()
                for name in protected_files
                if name.casefold() != "config.json"
            }:
                return True

            # INI-Dateien grundsätzlich erhalten.
            if path.suffix.casefold() == ".ini":
                return True

            return False

        def update_progress(value, message):
            """Aktualisiert Fortschritt und optionale Statusanzeige."""
            if progress_callback:
                progress_callback(value, message)

            pbar = getattr(self, "progress_bar", None)
            if pbar is not None:
                pbar.setValue(value)
                pbar.setFormat(message)

            info = getattr(self, "info_text", None)
            if info is not None:
                timestamp = QTime.currentTime().toString("HH:mm:ss")
                self.append_info(
                    info,
                    f"🔄 [{timestamp}] Update {value}% – {message}",
                    "info",
                )

            QApplication.processEvents()

        # --------------------------------------------------
        # 4. Schreibrechte prüfen
        # --------------------------------------------------
        if not self._has_project_write_access(project_dir):
            lang = str(getattr(self, "LANG", "de")).lower()[:2]
            is_de = lang == "de"

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(
                "Administratorrechte erforderlich"
                if is_de else "Administrator privileges required"
            )
            msg_box.setText(
                (
                    "Für das Update fehlen Schreibrechte. "
                    "Soll das Programm mit Administratorrechten neu starten "
                    "und das Update automatisch fortsetzen?"
                )
                if is_de else
                (
                    "The update requires write access. Restart the application "
                    "with administrator privileges and continue automatically?"
                )
            )

            yes_button = msg_box.addButton(
                "Ja" if is_de else "Yes",
                QMessageBox.ButtonRole.YesRole,
            )
            no_button = msg_box.addButton(
                "Nein" if is_de else "No",
                QMessageBox.ButtonRole.NoRole,
            )

            msg_box.setDefaultButton(yes_button)
            msg_box.setEscapeButton(no_button)
            msg_box.exec()

            if msg_box.clickedButton() != yes_button:
                return False

            restart_result = self.restart_application_elevated(
                perform_update=True
            )

            if restart_result != "already_elevated":
                return False

        # --------------------------------------------------
        # 5. Dauerhaftes Backup sicher erstellen
        # --------------------------------------------------
        persistent_backup_dir = project_dir / "backup"
        persistent_backup_zip = persistent_backup_dir / "backup.zip"
        backup_temp_zip = persistent_backup_dir / "backup.tmp.zip"

        try:
            persistent_backup_dir.mkdir(parents=True, exist_ok=True)

            if backup_temp_zip.exists():
                backup_temp_zip.unlink()

            # os.walk mit topdown=True ist entscheidend:
            # Geschützte Verzeichnisse werden aus dirs entfernt,
            # bevor os.walk diese Verzeichnisse betreten kann.
            with zipfile.ZipFile(
                backup_temp_zip,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as backup_archive:

                for root, dirs, files in os.walk(
                    project_dir,
                    topdown=True,
                    followlinks=False,
                ):
                    root_path = Path(root)

                    filtered_dirs = []

                    for dirname in dirs:
                        candidate = root_path / dirname
                        # Alle Ordner ausschließen, deren Name s3 oder s4 enthält.
                        dirname_lower = dirname.casefold()

                        if "s3" in dirname_lower or "s4" in dirname_lower:
                            continue
                        # Standardordner ausschließen.
                        if dirname.casefold() in {
                            name.casefold() for name in protected_dirs
                        }:
                            continue

                        # Konfigurierte Ordner vor dem Betreten ausschließen.
                        if any(
                            normalized_path(candidate)
                            == normalized_path(custom_path)
                            for custom_path in protected_custom_paths
                        ):
                            continue

                        # Keine Verzeichnis-Symlinks verfolgen.
                        if candidate.is_symlink():
                            continue

                        filtered_dirs.append(dirname)

                    dirs[:] = filtered_dirs

                    for filename in files:
                        source_file = root_path / filename

                        # Keine Datei-Symlinks oder externen Ziele archivieren.
                        if source_file.is_symlink():
                            continue

                        if not is_inside(source_file, project_dir):
                            continue

                        # Zusätzliche Schutzprüfung, bevor die Datei gelesen wird.
                        if is_protected(source_file):
                            continue

                        relative_path = source_file.relative_to(project_dir)

                        backup_archive.write(
                            source_file,
                            arcname=relative_path.as_posix(),
                        )

            # Integrität des ZIP-Archivs prüfen.
            with zipfile.ZipFile(backup_temp_zip, "r") as backup_archive:
                bad_file = backup_archive.testzip()

                if bad_file is not None:
                    raise RuntimeError(
                        f"Backup-Prüfung fehlgeschlagen: {bad_file}"
                    )

            # Erst jetzt das bisherige Backup ersetzen.
            os.replace(backup_temp_zip, persistent_backup_zip)

        except Exception as backup_error:
            try:
                if backup_temp_zip.exists():
                    backup_temp_zip.unlink()
            except OSError:
                pass

            QMessageBox.critical(
                self,
                "Backup-Fehler",
                "Das Backup konnte nicht sicher erstellt werden:\n"
                f"{backup_error}\n\n"
                "Das Update wurde nicht gestartet. "
                "Ein eventuell vorhandenes backup.zip wurde nicht absichtlich "
                "durch ein unvollständiges Archiv ersetzt.",
            )
            return False

        # --------------------------------------------------
        # 6. Temporäres Rollback-Backup
        # --------------------------------------------------
        backup_dir = Path(tempfile.mkdtemp(prefix="oscam_backup_"))

        download_url = (
            "https://github.com/speedy005/oscam_patch_manager_new/"
            "archive/refs/heads/master.zip"
        )

        backup_files = []
        new_files = []
        rollback_errors = []

        try:
            # --------------------------------------------------
            # 7. GitHub-Archiv herunterladen
            # --------------------------------------------------
            update_progress(10, "GitHub wird heruntergeladen...")

            response = requests.get(
                download_url,
                timeout=(15, 120),
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()

            update_progress(20, "Download abgeschlossen. ZIP wird geprüft...")

            # --------------------------------------------------
            # 8. Archiv prüfen und Update-Dateien ermitteln
            # --------------------------------------------------
            with zipfile.ZipFile(BytesIO(response.content), "r") as archive:
                members = archive.namelist()

                file_members = [
                    member for member in members
                    if not member.endswith("/")
                ]

                if not file_members:
                    raise RuntimeError("Das GitHub-Archiv ist leer.")

                # GitHub-Archive müssen genau einen gemeinsamen Stammordner haben.
                first_parts = PurePosixPath(
                    file_members[0].replace("\\", "/")
                ).parts

                if not first_parts:
                    raise RuntimeError("Ungültige Archivstruktur.")

                root_name = first_parts[0]
                updates = []

                for member in file_members:
                    normalized_member = member.replace("\\", "/")
                    member_path = PurePosixPath(normalized_member)
                    parts = member_path.parts

                    if (
                        not parts
                        or parts[0] != root_name
                        or member_path.is_absolute()
                        or ".." in parts
                        or any(":" in part for part in parts)
                    ):
                        raise RuntimeError(
                            f"Unsicherer Dateipfad im Update: {member}"
                        )

                    relative_parts = parts[1:]

                    if not relative_parts:
                        continue

                    relative_name = PurePosixPath(*relative_parts)

                    if any(part in ("", ".", "..") for part in relative_parts):
                        raise RuntimeError(
                            f"Ungültiger Dateipfad im Update: {member}"
                        )

                    target = (
                        project_dir / Path(*relative_parts)
                    ).resolve()

                    if not is_inside(target, project_dir):
                        raise RuntimeError(
                            f"Datei liegt außerhalb des Projektordners: {target}"
                        )

                    # Geschützte Verzeichnisse und Dateien nie aktualisieren.
                    if is_protected(target):
                        continue

                    if target.exists() and not target.is_file():
                        raise RuntimeError(
                            f"Zielpfad ist keine Datei: {target}"
                        )

                    updates.append((member, target))

                if not updates:
                    raise RuntimeError(
                        "Keine aktualisierbaren Projektdateien gefunden."
                    )

                update_progress(
                    23,
                    f"{len(updates)} Update-Dateien gefunden.",
                )

                # --------------------------------------------------
                # 9. Vorhandene Dateien für Rollback sichern
                # --------------------------------------------------
                update_progress(25, "Rollback-Backup wird erstellt...")

                for _, target in updates:
                    if target.is_file():
                        backup_file = backup_dir / target.relative_to(project_dir)
                        backup_file.parent.mkdir(parents=True, exist_ok=True)

                        shutil.copy2(target, backup_file)
                        backup_files.append((target, backup_file))
                    else:
                        new_files.append(target)

                update_progress(35, "Rollback-Backup abgeschlossen.")

                # --------------------------------------------------
                # 10. Update installieren
                # --------------------------------------------------
                update_progress(40, "Projektdateien werden ersetzt...")

                for index, (member, target) in enumerate(updates):
                    relative_target = target.relative_to(project_dir)

                    # Vorhandene WAV-Dateien im sounds-Ordner erhalten.
                    if (
                        target.is_file()
                        and target.suffix.lower() == ".wav"
                        and "sounds" in relative_target.parts
                    ):
                        continue

                    target.parent.mkdir(parents=True, exist_ok=True)

                    temp_target = target.with_name(
                        target.name + ".update_tmp"
                    )

                    try:
                        with archive.open(member, "r") as source:
                            with open(temp_target, "wb") as destination:
                                shutil.copyfileobj(source, destination)

                        replace_error = None

                        for attempt in range(4):
                            try:
                                os.replace(temp_target, target)
                                replace_error = None
                                break

                            except PermissionError as exc:
                                replace_error = exc

                                print(
                                    f"[UPDATE DEBUG] Versuch {attempt + 1}/4: "
                                    f"{exc!r}; Ziel={target}"
                                )

                                if attempt < 3:
                                    time.sleep(0.5 * (attempt + 1))

                        if replace_error is not None:
                            raise replace_error

                    finally:
                        try:
                            if temp_target.exists():
                                temp_target.unlink()
                        except OSError:
                            pass

                    if not target.is_file():
                        raise RuntimeError(
                            f"Datei konnte nicht installiert werden: {target}"
                        )

                    progress = 40 + int(
                        50 * (index + 1) / len(updates)
                    )

                    update_progress(
                        progress,
                        f"Installiere Datei {index + 1}/{len(updates)}",
                    )

            # --------------------------------------------------
            # 11. Update erfolgreich
            # --------------------------------------------------
            lang = str(getattr(self, "LANG", "de")).lower()[:2]
            is_de = lang == "de"

            update_progress(
                100,
                "Update erfolgreich" if is_de else "Update successful",
            )

            timestamp = QTime.currentTime().toString("HH:mm:ss")

            info = getattr(self, "info_text", None)
            if info is not None:
                self.append_info(
                    info,
                    f"✅ [{timestamp}] "
                    + (
                        "Update erfolgreich abgeschlossen."
                        if is_de
                        else "Update completed successfully."
                    ),
                    "success",
                )

            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle(
                "Update erfolgreich" if is_de else "Update successful"
            )
            msg_box.setText(
                (
                    "Das Projekt wurde aktualisiert.\n\n"
                    "Lokale Konfigurationen und geschützte Ordner wurden erhalten.\n\n"
                    "Programm jetzt neu starten?"
                )
                if is_de else
                (
                    "The project has been updated.\n\n"
                    "Local configurations and protected folders were preserved.\n\n"
                    "Restart the application now?"
                )
            )

            yes_btn = msg_box.addButton(
                "Ja" if is_de else "Yes",
                QMessageBox.ButtonRole.YesRole,
            )
            msg_box.addButton(
                "Nein" if is_de else "No",
                QMessageBox.ButtonRole.NoRole,
            )

            msg_box.setDefaultButton(yes_btn)
            msg_box.exec()

            should_restart = msg_box.clickedButton() == yes_btn

            # Erfolgreiches Update: Rollback-Dateien nicht mehr erforderlich.
            shutil.rmtree(backup_dir, ignore_errors=True)

            if should_restart:
                if getattr(sys, "frozen", False):
                    command = [sys.executable, *sys.argv[1:]]
                    app_path = sys.executable
                else:
                    script_path = os.path.abspath(sys.argv[0])
                    command = [
                        sys.executable,
                        script_path,
                        *sys.argv[1:],
                    ]
                    app_path = script_path

                popen_kwargs = {
                    "cwd": os.path.dirname(app_path) or None,
                    "close_fds": True,
                }

                if os.name == "nt":
                    popen_kwargs["creationflags"] = getattr(
                        subprocess,
                        "CREATE_NEW_PROCESS_GROUP",
                        0,
                    )
                else:
                    popen_kwargs["start_new_session"] = True

                try:
                    process = subprocess.Popen(command, **popen_kwargs)

                    time.sleep(1)

                    if process.poll() is not None:
                        raise RuntimeError(
                            "Der neue Prozess wurde sofort beendet "
                            f"(Exit-Code {process.returncode})."
                        )

                except Exception as restart_error:
                    QMessageBox.critical(
                        self,
                        "Neustart fehlgeschlagen" if is_de else "Restart failed",
                        (
                            "Die aktualisierte Anwendung konnte nicht neu "
                            f"gestartet werden:\n{restart_error}"
                        )
                        if is_de else
                        (
                            "The updated application could not be restarted:\n"
                            f"{restart_error}"
                        ),
                    )
                    return True

                QApplication.quit()

            return True

        except Exception as error:
            # --------------------------------------------------
            # 12. Fehler: Rollback versuchen
            # --------------------------------------------------
            timestamp = QTime.currentTime().toString("HH:mm:ss")

            info = getattr(self, "info_text", None)
            if info is not None:
                self.append_info(
                    info,
                    f"❌ [{timestamp}] Update fehlgeschlagen: {error}",
                    "error",
                )
                self.append_info(
                    info,
                    f"↩️ [{timestamp}] Rollback wird ausgeführt...",
                    "warning",
                )

            # Neu angelegte Dateien entfernen.
            for target in reversed(new_files):
                try:
                    if target.exists() and target.is_file():
                        target.unlink()
                except Exception as rollback_error:
                    rollback_errors.append(
                        f"{target}: {rollback_error}"
                    )

            # Vorhandene Dateien wiederherstellen.
            for target, backup_file in reversed(backup_files):
                try:
                    if backup_file.exists():
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_file, target)
                except Exception as rollback_error:
                    rollback_errors.append(
                        f"{target}: {rollback_error}"
                    )

            details = f"Update fehlgeschlagen:\n{error}"

            if rollback_errors:
                details += (
                    "\n\nRollback nicht vollständig!\n"
                    f"Rollback-Backup:\n{backup_dir}\n\n"
                    + "\n".join(rollback_errors)
                )

                if info is not None:
                    self.append_info(
                        info,
                        f"⚠️ [{timestamp}] Rollback unvollständig. "
                        f"Backup prüfen: {backup_dir}",
                        "error",
                    )
            else:
                details += (
                    "\n\nDie geänderten Dateien wurden wiederhergestellt."
                )

                shutil.rmtree(backup_dir, ignore_errors=True)

                if info is not None:
                    self.append_info(
                        info,
                        f"✅ [{timestamp}] Rollback abgeschlossen.",
                        "success",
                    )

            QMessageBox.critical(
                self,
                "Update-Fehler",
                details,
            )

            return False

    def ask_for_update(self, latest_version):
        """Fragt nach Update mit Sound und bereitet die Regenbogen-Bar vor."""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        from PyQt6.QtCore import QTimer

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # SOUND abspielen, bevor die Box blockiert
        if "safe_play" in globals():
            safe_play("dialog-information.oga")

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Update" if is_de else "Update Available")
        message = (
            f"Update {latest_version} verfügbar. Jetzt installieren?"
            if is_de
            else f"Update {latest_version} available. Install now?"
        )
        msg_box.setText(message)

        yes_btn = msg_box.addButton(
            "Ja" if is_de else "Yes", QMessageBox.ButtonRole.YesRole
        )
        no_btn = msg_box.addButton(
            "Nein" if is_de else "No", QMessageBox.ButtonRole.NoRole
        )
        msg_box.setDefaultButton(yes_btn)

        if msg_box.exec() == 0 or msg_box.clickedButton() == yes_btn:
            # Regenbogen-Style sofort anwenden
            if pbar:
                rainbow = (
                    "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                    "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
                )
                pbar.setStyleSheet(
                    f"QProgressBar {{ text-align: center; font-weight: 900; color: black; background: #111; border: 2px solid #222; }} "
                    f"QProgressBar::chunk {{ background: {rainbow}; }}"
                )
                pbar.setFormat("🚀 Starte..." if is_de else "🚀 Starting...")
                pbar.setValue(5)
                pbar.show()
                QApplication.processEvents()

            QTimer.singleShot(200, lambda: self.plugin_update_action(latest_version))

    @staticmethod
    def start_update(self):
        print("Update starten …")

    def run_background_task(self, fn, *args, **kwargs):
        """Startet eine Funktion im Hintergrund und steuert die Progressbar"""
        self.progress_bar.setValue(0)
        self.progress_bar.show()

        self.worker = TaskWorker(fn, *args, **kwargs)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.info.connect(
            lambda txt, lvl: self.append_info(self.info_text, txt, lvl)
        )
        self.worker.start()

    def run_command(self, cmd, cwd=None):
        """Führt Befehle aus und gibt das Ergebnis als String zurück."""
        import subprocess

        try:
            if isinstance(cmd, str):
                import shlex
                command = shlex.split(cmd, posix=(os.name != "nt"))
            else:
                command = list(cmd)

            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
                check=False,
            )

            stdout = (result.stdout or "").strip()
            stderr = (result.stderr or "").strip()
            if result.returncode != 0:
                # Diagnose enthält Exit-Code und bevorzugt stderr; einige Tools
                # schreiben ihre Fehlermeldung allerdings nach stdout.
                detail = stderr or stdout
                if not detail:
                    detail = (
                        "Der Befehl hat keine weiteren Fehlerdetails ausgegeben."
                        if getattr(self, "current_language", "DE") == "DE"
                        else "The command did not provide additional error details."
                    )
                command_text = " ".join(str(part) for part in command)
                is_de = getattr(self, "current_language", "DE") == "DE"
                if is_de:
                    message = (
                        f"❌ Befehlsfehler (Exit-Code {result.returncode}): "
                        f"{command_text}\n{detail}"
                    )
                    if cwd:
                        message += f"\nArbeitsverzeichnis: {cwd}"
                else:
                    message = (
                        f"❌ Command failed (exit code {result.returncode}): "
                        f"{command_text}\n{detail}"
                    )
                    if cwd:
                        message += f"\nWorking directory: {cwd}"
                self.log(message, "error")
                return ""

            return stdout
        except FileNotFoundError as e:
            is_de = getattr(self, "current_language", "DE") == "DE"
            message = (
                f"❌ Programm/Befehl nicht gefunden: {e}"
                if is_de
                else f"❌ Program/command not found: {e}"
            )
            self.log(message, "error")
            return ""
        except Exception as e:
            is_de = getattr(self, "current_language", "DE") == "DE"
            message = (
                f"❌ Systemfehler beim Ausführen des Befehls: {e}"
                if is_de
                else f"❌ System error while running command: {e}"
            )
            self.log(message, "error")
            return ""

    def change_old_patch_dir(self, info_widget=None, progress_callback=None):
        """
        Ändert den Speicherort des alten Patch-Ordners mit Neon-Regenbogen-Progress.
        Text bleibt am Ende 3 Sekunden stehen, bevor der Balken zurückgesetzt wird.
        """

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        
        from PyQt6.QtWidgets import QFileDialog, QApplication
        from PyQt6.QtCore import QTimer
        import json, os

        widget = info_widget or getattr(self, "info_text", None)
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # --- Neon-Styles Definition ---
        STYLE_NEON = """
            QProgressBar {{
                border: 2px solid #444444;
                border-radius: 8px;
                background-color: #0A0A0A;
                color: {text_color};
                text-align: center;
                font-weight: 900;
                font-size: 20px;
                min-height: 35px;
            }}
            QProgressBar::chunk {{
                background-color: {chunk_color};
                border-radius: 6px;
            }}
        """
    
        RAINBOW_GRADIENT = (
            "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #FF00FF, stop:0.5 #00FFFF, stop:1 #39FF14)"
        )

        # -------------------------------
        # Helper-Funktionen
        # -------------------------------
        def log(text, level="info"):
            if widget and hasattr(self, "append_info"):
                self.append_info(widget, text, level)

        def set_progress(val, text=None):
            if not pbar: return
            pbar.setStyleSheet(STYLE_NEON.format(text_color="black", chunk_color=RAINBOW_GRADIENT))
            pbar.show()
            pbar.setValue(val)
            if text: pbar.setFormat(text)
            QApplication.processEvents()
            if progress_callback:
                try: progress_callback(val)
                except: pass

        def finalize_pbar(text, visible_seconds=3):
            if not pbar: return
            pbar.setStyleSheet(STYLE_NEON.format(text_color="black", chunk_color=RAINBOW_GRADIENT))
            pbar.setValue(100)
            pbar.setFormat(text)
        
            # Nach 3 Sekunden Chunk transparent, Value auf 0
            QTimer.singleShot(visible_seconds * 1000, lambda: pbar.setStyleSheet(
                STYLE_NEON.format(text_color="black", chunk_color="transparent")
            ))
            QTimer.singleShot(visible_seconds * 1000, lambda: pbar.setValue(0))
            if progress_callback:
                QTimer.singleShot(visible_seconds * 1000, lambda: progress_callback(0))

        # -------------------------------
        # START
        # -------------------------------
        if pbar:
            set_progress(10, "📂 " + ("Ordner auswählen..." if is_de else "Select folder..."))

        # Nutzt Standard-Pfad falls OLD_PATCH_DIR nicht gesetzt
        start_dir = getattr(self, "OLD_PATCH_DIR", os.getcwd())
        new_dir = QFileDialog.getExistingDirectory(self, "Select S3 Patch Folder", start_dir)

        if new_dir:
            if pbar:
                set_progress(50, "🔄 " + ("Pfade aktualisieren..." if is_de else "Updating paths..."))
        
            # Pfade aktualisieren
            self.OLD_PATCH_DIR = new_dir
            self.OLD_PATCH_FILE = os.path.join(new_dir, "oscam-emu.patch")
            self.ALT_PATCH_FILE = os.path.join(new_dir, "oscam-emu.altpatch")
            self.PATCH_MANAGER_OLD = os.path.join(new_dir, "oscam_patch_manager_old.py")
            self.CONFIG_OLD = os.path.join(new_dir, "config_old.json")
            self.GITHUB_CONFIG_OLD = os.path.join(new_dir, "github_upload_config_old.json")

            # Config sicher aktualisieren: aktuelle Datei laden und nur
            # den geänderten Wert ergänzen.
            if hasattr(self, "cfg"):
                try:
                    config_path = CONFIG_FILE
                    current_cfg = {}

                    if os.path.isfile(config_path):
                        with open(config_path, "r", encoding="utf-8") as f:
                            loaded = json.load(f)
                        if isinstance(loaded, dict):
                            current_cfg = loaded

                    current_cfg["s3_patch_path"] = new_dir

                    with open(config_path, "w", encoding="utf-8") as f:
                        json.dump(current_cfg, f, indent=4, ensure_ascii=False)
                        f.write("\n")

                    self.cfg = current_cfg
                    self.current_config = current_cfg

                    success_msg = f"✅ Ordner geändert: {new_dir}" if is_de else f"✅ Folder changed: {new_dir}"
                    log(success_msg, "success")
                    if pbar:
                        finalize_pbar("✅ " + ("Gespeichert!" if is_de else "Saved!"))
                    if "safe_play" in globals():
                        safe_play("complete.oga")

                except Exception as e:
                    log(f"❌ Fehler: {e}", "error")
                    if pbar:
                        finalize_pbar("❌ " + str(e))
                    if "safe_play" in globals():
                        safe_play("dialog-error.oga")
        else:
            log("ℹ️ Abgebrochen" if is_de else "ℹ️ Cancelled", "info")
            if pbar:
                finalize_pbar("ℹ️ " + ("Abgebrochen" if is_de else "Cancelled"))

    def update_plugin_button_state(self):
        """Aktualisiert den Text und die Farbe des Update-Buttons."""
        btn_data = self.option_buttons.get("plugin_update")
        if not btn_data:
            return
        btn = btn_data[0]

        lang = str(getattr(self, "LANG", "de")).lower()
        t = TEXTS.get(lang, TEXTS.get("de", {}))

        cv = APP_VERSION.lstrip("v")
        lv = getattr(self, "latest_version", cv)

        if Version(lv) > Version(cv):
            txt = t.get("state_plugin_update_available", "Update: {current} → {latest}")
            btn.setText(txt.format(current=cv, latest=lv))
            btn.setStyleSheet(
                "background-color: #d35400; color: white; font-weight: bold;"
            )
        else:
            txt = t.get("state_plugin_uptodate", "v{version} aktuell")
            btn.setText(txt.format(version=cv))
            btn.setStyleSheet(
                "background-color: #1E90FF; color: white; font-weight: bold;"
            )

    def fetch_latest_version(self):
        """Vergleicht lokale APP_VERSION mit version.txt auf GitHub"""
        import requests
        from packaging.version import Version

        widget = getattr(self, "info_text", None)

        def log(text_key, level="info", **kwargs):
            colors = {
                "success": "green",
                "warning": "orange",
                "error": "red",
                "info": "gray",
            }
            color = colors.get(level, "gray")
            text_template = TEXTS[LANG].get(text_key, text_key)
            text = text_template.format(**kwargs)

            if isinstance(widget, QTextEdit):
                widget.append(f'<span style="color:{color}">{text}</span>')
                widget.moveCursor(QTextCursor.MoveOperation.End)
                QApplication.processEvents()
            else:
                print(f"[{level.upper()}] {text}")

        try:
            url = "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/version.txt"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            latest = resp.text.strip()
            self.latest_version = latest

            if Version(latest) > Version(APP_VERSION):
                log("github_version_available", "info", version=latest)
                self.ask_for_update(latest)  # 👈 wichtig
            else:
                log("update_current_version", "success", version=APP_VERSION)

        except Exception as e:
            log("github_version_fetch_failed", "warning", error=str(e))

    def fetch_latest_github_version(self):
        """
        Holt die neueste Version von GitHub (version.txt) und aktualisiert self.latest_version.
        """
        try:
            import requests

            url = "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/version.txt"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            version = resp.text.strip().lstrip("v")  # "v1.4.7" → "1.4.7"
            self.latest_version = version

            self.append_info(
                self.info_text, f"Verfügbare GitHub-Version: v{version}", "info"
            )

            # Button-Zustand aktualisieren
            self.update_plugin_button_state()
            return version

        except Exception as e:
            self.append_info(
                self.info_text,
                f"❌ Fehler beim Abrufen der GitHub-Version: {e}",
                "error",
            )
            self.latest_version = None
            self.update_plugin_button_state()
            return None

    def plugin_update_button_clicked(
        self, checked=False, info_widget=None, progress_callback=None
    ):
        """
        Geprüfter Update-Callback mit Regenbogen-Progress und schwarzem Text (DE/EN).
        Zentrierte Log-Ausgabe und korrekte URL-Verarbeitung.
        Erzwingt Ja/Nein Buttons passend zur gewählten Sprache.
        """

        # --- Final Label sofort ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        from PyQt6.QtWidgets import QTextEdit, QApplication, QMessageBox
        from PyQt6.QtGui import QTextCursor
        import requests, time, re

        # --- 1. SPRACHE & PROGRESSBAR SETUP ---
        lang_key = getattr(self, "LANG", "de").lower()
        is_de = lang_key == "de"
        widget = info_widget or getattr(self, "info_text", None)
        pbar = getattr(self, "progress_bar", None)

        if pbar:
            rainbow = (
                "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
            )
            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center; font-weight: bold; border: 2px solid #222;
                    border-radius: 6px; background-color: #111; color: black; font-size: 11pt;
                }}
                QProgressBar::chunk {{ background-color: {rainbow}; border-radius: 4px; }}
                """
            )
            msg_check = "Prüfe auf Updates..." if is_de else "Checking for updates..."
            pbar.setFormat(f"{msg_check} %p%")
            pbar.setValue(0)
            pbar.show()
            QApplication.processEvents()

        # Version-Klasse (Fallback)
        try:
            from packaging.version import Version
        except ImportError:

            class Version:
                def __init__(self, v):
                    self.v = [int(x) for x in re.findall(r"\d+", str(v))]

                def __gt__(self, other):
                    return self.v > other.v

                def __lt__(self, other):
                    return self.v < other.v

                def __eq__(self, other):
                    return self.v == other.v

        def log(text_key, level="info", **kwargs):
            colors = {
                "success": "#00FF00",
                "warning": "orange",
                "error": "red",
                "info": "#00ADFF",
            }
            color = colors.get(level, "gray")
            lang_dict = (
                globals()
                .get("TEXTS", {})
                .get(lang_key, globals().get("TEXTS", {}).get("en", {}))
            )
            text_template = lang_dict.get(text_key, text_key)

            try:
                safe_kwargs = {
                    "current": globals().get("APP_VERSION", "3.3.7"),
                    "latest": getattr(self, "latest_version", "???"),
                }
                safe_kwargs.update(kwargs)
                text = text_template.format(**safe_kwargs)
            except:
                text = text_template

            if isinstance(widget, QTextEdit):
                widget.append(
                    f'<div style="text-align:center;"><span style="color:{color}"><b>{text}</b></span></div>'
                )
                widget.moveCursor(QTextCursor.MoveOperation.End)
                QApplication.processEvents()

        log("update_check_start", "info")
        if pbar:
            pbar.setValue(20)

        # --- 2. URL & CHECK ---
        version_url_base = "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/refs/heads/master/version.txt"

        try:
            v_url = f"{version_url_base}?nocache={int(time.time())}"
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(v_url, headers=headers, timeout=10)
            resp.raise_for_status()

            latest_str = resp.text.strip().lower().replace("v", "").strip()
            current_str = (
                globals()
                .get("APP_VERSION", "3.3.7")
                .strip()
                .lower()
                .replace("v", "")
                .strip()
            )

            self.latest_version = latest_str
            v_latest = Version(latest_str)
            v_current = Version(current_str)

            if pbar:
                pbar.setValue(60)

            # --- 3. VERGLEICH & MESSAGEBOX ---
            if v_latest > v_current:
                log("update_found", "warning", latest=latest_str, current=current_str)

                if pbar:
                    pbar.setValue(80)
                    msg_up = "Update verfügbar!" if is_de else "Update available!"
                    pbar.setFormat(f"✨ {msg_up} (v{latest_str})")

                lang_dict = globals().get("TEXTS", {}).get(lang_key, {})
                msg_title = lang_dict.get("update_box_title", "Update")
                msg_body = lang_dict.get("update_box_msg", "Update?").format(
                    latest=latest_str, current=current_str
                )

                msg_box = QMessageBox(self)
                msg_box.setWindowTitle(msg_title)
                msg_box.setText(msg_body)

                # Buttons manuell setzen um "Yes/No" (Systemsprache) zu umgehen
                yes_text, no_text = ("Ja", "Nein") if is_de else ("Yes", "No")
                yes_button = msg_box.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
                no_button = msg_box.addButton(no_text, QMessageBox.ButtonRole.NoRole)

                msg_box.setDefaultButton(yes_button)
                msg_box.setEscapeButton(no_button)

                msg_box.exec()

                if msg_box.clickedButton() == yes_button:
                    if hasattr(self, "plugin_update_action"):
                        self.plugin_update_action(latest_version=latest_str)
                else:
                    log("update_declined", "info")
                    if pbar:
                        pbar.setValue(100)
            else:
                # Aktuell
                if pbar:
                    pbar.setFormat(
                        f"✅ v{current_str} aktuell 100%"
                        if is_de
                        else f"✅ v{current_str} up-to-date 100%"
                    )
                    pbar.setValue(100)
                log("update_no_update", "success")

        except Exception as e:
            error_label = "Fehler" if is_de else "Error"
            log("update_fail", "error", error=str(e))
            if pbar:
                pbar.setStyleSheet("QProgressBar { color: red; font-weight: bold; }")
                pbar.setFormat(f"❌ {error_label}: {str(e)[:50]}")
                pbar.setValue(100)

        # Timer zum Aufräumen
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(
            4000,
            lambda: (
                self.pbar_idle()
                if hasattr(self, "pbar_idle")
                else (pbar.hide() if pbar else None)
            ),
        )

        # UI Color Fix für Hover-Effekte
        if hasattr(self, "repaint_ui_colors"):
            self.repaint_ui_colors()

    def check_for_update_on_start(self):
        """
        Vervollständigt den Log voll übersetzbar.
        Finalisiert den System-Check mit der korrekten Konfiguration aus der JSON.
        """
        if getattr(self, "_update_dialog_active", False):
            return
        self._update_dialog_active = True

        import requests
        import time

        # Nutzen der im Skript definierten Version-Klasse als Fallback
        try:
            from packaging.version import Version
        except ImportError:
            Version = globals().get("Version")

        txt = getattr(self, "TEXT", {})

        # --- ZENTRALE FORMATIERUNG ---
        SZ_BIG = "35px"  # Orange Titel
        SZ_NORM = "35px"  # Standard-Inhalte
        F_FAMILY = "'Arial', sans-serif"

        C_ORANGE = "#F37804"
        C_GREEN = "#00FF00"
        C_BLUE = "#00ADFF"
        C_LINE = "#808080"

        v_url = "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/version.txt"

        try:
            # Cache-Busting durch Timestamp
            resp = requests.get(f"{v_url}?t={int(time.time())}", timeout=5)
            resp.raise_for_status()

            latest_v = resp.text.strip().lstrip("v")
            current_v = APP_VERSION.strip().lstrip("v")

            output = []

            # --- LOGIK: VERSION VERGLEICHEN ---
            is_new = False
            try:
                is_new = Version(latest_v) > Version(current_v)
            except Exception:
                is_new = latest_v != current_v

            if is_new:
                # --- FALL: UPDATE VERFÜGBAR ---
                label = txt.get("new_version_available", "Update verfügbar")
                output.append(
                    f'<span style="font-family:{F_FAMILY}; font-size:{SZ_BIG}; color:{C_ORANGE}"><b>➔ {label}: v{latest_v}</b></span>'
                )

                if hasattr(self, "btn_update"):
                    btn_tpl = txt.get("upd_btn_new", "Update verfügbar: v{v}")
                    btn_txt = btn_tpl.format(v=latest_v, latest=latest_v)
                    self.btn_update.setText(btn_txt)
                    # WICHTIG: Farbe setzen, aber Größe stabil halten (Fixed-Policy vorausgesetzt)
                    self.btn_update.setStyleSheet(
                        f"color: {C_ORANGE}; font-weight: bold; border: 1px solid {C_ORANGE}; border-radius: 5px;"
                    )
            
                
            # --- FALL: KEIN UPDATE ---
            else:
                output.append(
                    f'<div style="font-family:{F_FAMILY}; font-size:{SZ_NORM}; '
                    f'color:{C_GREEN}; text-align:left;"><b>'
                    f'{txt.get("no_update_found", "Kein Update vorhanden....")}'
                    f'</b></div>'
                )

                upd_ok_msg = txt.get("upd_ok", "Plugin ist aktuell")
                output.append(
                    f'<div style="font-family:{F_FAMILY}; font-size:{SZ_NORM}; '
                    f'color:{C_BLUE}; text-align:left;"><b>'
                    f'✅ {upd_ok_msg} (Version: {current_v})'
                    f'</b></div>'
                )

                if hasattr(self, "btn_update"):
                    btn_curr_tpl = txt.get("upd_btn_current", "v{v} (Aktuell)")
                    btn_curr_txt = btn_curr_tpl.format(v=current_v, current=current_v)
                    self.btn_update.setText(btn_curr_txt)
                    self.btn_update.setStyleSheet(
                        "color: #00FF00; font-weight: bold; "
                        "border: 1px solid #00FF00; border-radius: 5px;"
                    )

            # --- KONFIGURATIONS-BLOCK ---
            output.append(
                f'<div style="color:{C_LINE}; text-align:left;">{"-" * 45}</div>'
            )
            output.append(
                f'<div style="font-family:{F_FAMILY}; font-size:{SZ_BIG}; '
                f'color:{C_ORANGE}; text-align:left;"><b>'
                f'{txt.get("active_conf", "🛠️ Aktive Konfiguration:")}'
                f'</b></div>'
            )

            # Sicherer Zugriff auf Config
            cfg_obj = getattr(self, "cfg", {})
            author = cfg_obj.get(
                "patch_modifier", getattr(self, "patch_modifier", "speedy005")
            )
            repo_url = cfg_obj.get(
                "EMUREPO",
                getattr(self, "EMUREPO", "https://github.com/speedy005/Oscam-emu.git"),
            )

            output.append(
                f'<div style="font-family:{F_FAMILY}; font-size:{SZ_NORM}; '
                f'color:{C_GREEN}; text-align:left;"><b>'
                f'👤 {txt.get("patch_author", "Patch Autor")}: {author}'
                f'</b></div>'
            )
            output.append(
                f'<div style="font-family:{F_FAMILY}; font-size:{SZ_NORM}; '
                f'color:{C_BLUE}; text-align:left;"><b>'
                f'🌐 {txt.get("repository", "Repository")}: {repo_url}'
                f'</b></div>'
            )
            output.append(
                f'<div style="color:{C_LINE}; text-align:left;">{"-" * 45}</div>'
            )

            # Log ausgeben
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                self.append_info(self.info_text, "\n".join(output), "html")

            # Abschluss-Sound
            if "safe_play" in globals():
                safe_play("complete.oga")

            if is_new:
                self.show_update_dialog(latest_v, current_v)

        except Exception as e:
            if "safe_play" in globals():
                safe_play("dialog-error.oga")

            err_lbl = txt.get("update_error", "Update-Check fehlgeschlagen")
            if hasattr(self, "append_info"):
                self.append_info(
                    self.info_text,
                    f'<span style="font-family:{F_FAMILY}; '
                    f'font-size:{SZ_NORM}; color:red;"><b>'
                    f'➔ {err_lbl}: {e}</b></span>',
                    "html",
                )
        finally:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(
                1000, lambda: setattr(self, "_update_dialog_active", False)
            )

    def on_clean_emu_clicked(self):
        """Bereinigt das Emu-/Patch-Arbeitsverzeichnis über die zentrale Funktion."""
        self.update_language()
        cleaner = getattr(self, "oscam_emu_git_clear", None)
        if not callable(cleaner):
            message = "Die Bereinigungsfunktion ist nicht verfügbar."
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                self.append_info(self.info_text, message, "error")
            else:
                print(f"[CLEAN] {message}")
            return False
        return cleaner(
            info_widget=getattr(self, "info_text", None),
            progress_callback=(
                self.progress_bar.setValue
                if getattr(self, "progress_bar", None) is not None
                else None
            ),
        )

    def on_button_clicked(self, key, func):
        self.set_active_button(key)
        self.run_action(func)

    def close_with_confirm(self):
        """
        Zeigt eine sprachabhängige Bestätigungsabfrage beim Beenden.
        Speichert die aktuelle Konfiguration und beendet anschließend die Anwendung.
        """

        from PyQt6.QtWidgets import QApplication, QMessageBox

        # ------------------------------------------------------------
        # Sprache ermitteln
        # ------------------------------------------------------------
        lang = str(
            getattr(self, "LANG", "de")
        ).lower().strip()

        # Nur die Sprache vor dem Länder-/Regionscode verwenden:
        # z.B. "de_DE" -> "de"
        lang = lang.split("_")[0].split("-")[0]

        # ------------------------------------------------------------
        # Übersetzung sicher laden
        # ------------------------------------------------------------
        texts = globals().get("TEXTS", {})

        if not isinstance(texts, dict):
            texts = {}

        t = texts.get(lang)

        if not isinstance(t, dict):
            t = texts.get("en", {})

        if not isinstance(t, dict):
            t = {}

        # ------------------------------------------------------------
        # Texte mit Fallbacks
        # ------------------------------------------------------------
        title = t.get(
            "exit",
            "Programm beenden" if lang == "de" else "Exit"
        )

        question = t.get(
            "exit_question",
            (
                "Möchtest du den OSCam Patch Manager wirklich beenden?"
                if lang == "de"
                else "Do you really want to exit?"
            )
        )

        yes_text = t.get(
            "yes",
            "Ja" if lang == "de" else "Yes"
        )

        no_text = t.get(
            "no",
            "Nein" if lang == "de" else "No"
        )

        # ------------------------------------------------------------
        # Bestätigungsdialog
        # ------------------------------------------------------------
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(str(title))
        msg.setText(str(question))

        yes_button = msg.addButton(
            str(yes_text),
            QMessageBox.ButtonRole.YesRole
        )

        no_button = msg.addButton(
            str(no_text),
            QMessageBox.ButtonRole.NoRole
        )

        msg.setDefaultButton(no_button)

        msg.exec()

        # ------------------------------------------------------------
        # Nur bei "Ja" wirklich beenden
        # ------------------------------------------------------------
        if msg.clickedButton() != yes_button:
            return

        # ------------------------------------------------------------
        # Aktuelle GUI-Werte speichern
        # ------------------------------------------------------------
        exit_updates = {
            "s3_custom_path": getattr(
                self,
                "S3_PATH",
                r"C:\s3"
            ),

            "ncam_custom_path": getattr(
                self,
                "NCAM_PATH",
                r"C:\opt\ncam"
            ),

            "s4_custom_path": getattr(
                self,
                "S4_PATH",
                r"C:\opt\simplebuild4"
            ),

            "last_session_exit": "success",
        }

        # ------------------------------------------------------------
        # Bereits vorhandene Konfiguration übernehmen
        # ------------------------------------------------------------
        old_cfg = getattr(
            self,
            "cfg",
            getattr(
                self,
                "current_config",
                {}
            )
        )

        if isinstance(old_cfg, dict):
            for key in (
                "color",
                "language",
                "commit_count",
                "theme_mode",
                "blink_speed",
                "led_enabled",
                "EMUREPO",
                "patch_modifier",
                "s3_patch_path",
            ):
                if key in old_cfg:
                    exit_updates[key] = old_cfg[key]

        # ------------------------------------------------------------
        # Konfiguration speichern
        # ------------------------------------------------------------
        try:
            save_config_func = globals().get("save_config")

            if callable(save_config_func):
                self.is_closing = True

                save_config_func(
                    exit_updates,
                    gui_instance=self,
                    silent=True
                )

        except Exception as e:
            print(
                f"[WARN] Config save failed: {e}"
            )

        
        # ------------------------------------------------------------
        # Beenden-Sound
        # ------------------------------------------------------------
        try:
            sound_manager = getattr(self, "sound_manager", None)

            if sound_manager and sound_manager.enabled:
                sound_manager.exit_sound.play()

                # Sound kurz abspielen lassen, bevor die Anwendung schließt
                QTimer.singleShot(800, QApplication.quit)
            else:
                QApplication.quit()

        except Exception as e:
            print(f"[WARN] Exit sound failed: {e}")
            QApplication.quit()


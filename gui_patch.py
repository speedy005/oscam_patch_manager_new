"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerPatchMixin:
    """Patch Manager Patch"""

    def setup_online_patch_ui(self, parent_layout):
        """Erstellt die UI für den Online-Download inklusive Sound-Feedback."""
        from PyQt6.QtWidgets import (
            QGroupBox,
            QVBoxLayout,
            QComboBox,
            QPushButton,
            QLabel,
        )
        import locale

        # Spracherkennung
        try:
            loc = locale.getlocale()[0] or locale.getdefaultlocale()[0] or "en"
            lang = loc[:2].lower()
        except:
            lang = "en"
        self.lang = lang  # Speichern für handle_online_patch_button

        # Lokalisierung
        if lang == "de":
            self.T_PATCH_TITLE = "🌐 Online Patch-Downloader"
            self.T_PATCH_SEL = "Quelle wählen:"
            self.T_PATCH_BTN = "Patch laden & prüfen"
        else:
            self.T_PATCH_TITLE = "🌐 Online Patch-Downloader"
            self.T_PATCH_SEL = "Select Source:"
            self.T_PATCH_BTN = "Download & Verify Patch"

        # UI Komponenten
        self.group_online = QGroupBox(self.T_PATCH_TITLE)
        layout_online = QVBoxLayout()

        self.combo_source = QComboBox()
        self.combo_source.addItems(ONLINE_PATCHES.keys())
        self.combo_source.setMinimumHeight(50)

        self.btn_online = QPushButton(self.T_PATCH_BTN)
        self.btn_online.setMinimumHeight(50)
        self.btn_online.setStyleSheet(
            "font-weight: bold; background-color: #2c3e50; color: white;"
        )

        # FIX: Hier wurde der Funktionsname korrigiert von download_and_apply... zu handle_online_patch_button
        self.btn_online.clicked.connect(self.handle_online_patch_button)

        layout_online.addWidget(QLabel(self.T_PATCH_SEL))
        layout_online.addWidget(self.combo_source)
        layout_online.addWidget(self.btn_online)
        self.group_online.setLayout(layout_online)
        parent_layout.addWidget(self.group_online)

        # Sound-Feedback
        safe_play_func = globals().get("safe_play")
        if safe_play_func:
            safe_play_func("dialog-information.oga")

    def handle_online_patch_button(self):
        """Online-Patch herunterladen mit Statusmeldungen und echtem Download-Fortschritt."""

        from PyQt6.QtWidgets import QInputDialog, QMessageBox, QApplication
        from PyQt6.QtCore import QTimer
        import requests
        import re
        import os

        # ---------------------------------------------------------
        # Hilfsfunktionen
        # ---------------------------------------------------------

        def _(key, default):
            return getattr(self, "get_t", lambda x, y: y)(key, default)

        def set_status(text, value=None, color=None):
            """Progressbar aktualisieren und GUI sofort neu zeichnen."""
            if not pbar:
                return

            if value is not None:
                pbar.setValue(max(0, min(100, int(value))))

            pbar.setFormat(text)

            if color:
                pbar.setStyleSheet(
                    f"""
                    QProgressBar {{
                        text-align: center;
                        font-weight: 900;
                        border: 2px solid {color};
                        border-radius: 6px;
                        background-color: #111;
                        color: {color};
                        font-size: 13pt;
                    }}
                    QProgressBar::chunk {{
                        background-color: {color};
                        border-radius: 4px;
                    }}
                    """
                )

            pbar.show()
            pbar.repaint()
            QApplication.processEvents()

        def restore_style():
            if pbar:
                pbar.setValue(0)
                pbar.setFormat("%p%")
                pbar.setStyleSheet(
                    """
                    QProgressBar {
                        border: 1px solid #444;
                        border-radius: 8px;
                        background-color: #1A1A1A;
                        color: black;
                        text-align: center;
                        font-weight: bold;
                    }

                    QProgressBar::chunk {
                        background-color: qlineargradient(
                            x1:0, y1:0, x2:1, y2:0,
                            stop:0 #F37804,
                            stop:1 #FFD700
                        );
                        border-radius: 8px;
                    }
                    """
                )

        def play_sound(filename):
            safe_play_func = globals().get("safe_play")
            if safe_play_func:
                try:
                    safe_play_func(filename)
                except Exception:
                    pass

        # ---------------------------------------------------------
        # Sprache
        # ---------------------------------------------------------

        lang = str(
            getattr(
                self,
                "lang",
                getattr(self, "LANG", "en")
            )
        ).lower()[:2]

        is_de = lang == "de"

        # ---------------------------------------------------------
        # Progressbar
        # ---------------------------------------------------------

        pbar = getattr(self, "progress_bar", None)

        rainbow = (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:0, "
            "stop:0.0 #FF0000, "
            "stop:0.2 #FF7F00, "
            "stop:0.4 #FFFF00, "
            "stop:0.6 #00FF00, "
            "stop:0.8 #0000FF, "
            "stop:1.0 #8B00FF"
            ");"
        )

        if pbar:
            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center;
                    font-weight: 900;
                    border: 2px solid #222;
                    border-radius: 6px;
                    background-color: #111;
                    color: black;
                    font-size: 13pt;
                }}

                QProgressBar::chunk {{
                    background-color: {rainbow};
                    border-radius: 4px;
                }}
                """
            )

            pbar.setValue(0)
            pbar.setFormat(
                "🔍 " +
                _("patch_dl_wait", "Prüfe verfügbare Patches...")
            )
            pbar.show()
            pbar.repaint()
            QApplication.processEvents()

        # ---------------------------------------------------------
        # Texte
        # ---------------------------------------------------------

        T_CHECKING = (
            "🔍 " +
            _("patch_dl_wait", "Prüfe verfügbare Patches...")
        )

        T_FOUND = (
            "📦 " +
            _("patch_dl_found", "Patches gefunden")
        )

        T_START = (
            "🌐 " +
            _("patch_dl_start", "Download wird gestartet...")
        )

        T_DOWNLOADING = (
            "⬇️ " +
            _("patch_dl_downloading", "Download")
        )

        T_SAVING = (
            "💾 " +
            _("patch_dl_saving", "Speichere Patch...")
        )

        T_DONE = (
            "✅ " +
            _("patch_dl_done", "Patch erfolgreich heruntergeladen!")
        )

        T_CANCELLED = (
            "❌ " +
            _("patch_dl_cancelled", "Download abgebrochen.")
        )

        T_ERROR = (
            "❌ " +
            _("patch_dl_error", "Fehler beim Download")
        )

        # ---------------------------------------------------------
        # Sound + Status
        # ---------------------------------------------------------

        play_sound("dialog-information.oga")
        set_status(T_CHECKING, 10)

        # ---------------------------------------------------------
        # Patch-Liste holen
        # ---------------------------------------------------------

        patch_list = globals().get(
            "ONLINE_PATCHES",
            getattr(self, "ONLINE_PATCHES", {})
        )

        if not patch_list:
            play_sound("dialog-error.oga")

            set_status(
                "❌ " +
                _("patch_dl_no_patches", "Keine Patches verfügbar."),
                0,
                "#FF3333"
            )

            QMessageBox.warning(
                self,
                _("patch_dl_title", "Patch Download"),
                _("patch_dl_no_patches", "Es wurden keine Online-Patches gefunden.")
            )

            QTimer.singleShot(3000, restore_style)
            return

        # ---------------------------------------------------------
        # Versionen prüfen
        # ---------------------------------------------------------

        display_items = {}

        total_patches = len(patch_list)

        for index, (name, url) in enumerate(patch_list.items(), start=1):

            progress = 10 + int((index / total_patches) * 25)

            set_status(
                f"🔍 Prüfe {name}... {progress}%",
                progress
            )

            try:
                res = requests.get(
                    url,
                    headers={"Range": "bytes=0-511"},
                    timeout=5
                )

                res.raise_for_status()

                match = re.search(
                    r"patch version:\s*([\d\.-]+)",
                    res.text,
                    re.IGNORECASE
                )

                version = match.group(1) if match else "unknown"

                display_items[
                    f"{name} [{version}]"
                ] = (
                    url,
                    version,
                    name
                )

            except requests.RequestException:
                display_items[
                    f"{name} [Offline]"
                ] = (
                    url,
                    "unknown",
                    name
                )

            except Exception:
                display_items[
                    f"{name} [Fehler]"
                ] = (
                    url,
                    "unknown",
                    name
                )

        # ---------------------------------------------------------
        # Keine Ergebnisse
        # ---------------------------------------------------------

        if not display_items:
            play_sound("dialog-error.oga")

            set_status(
                "❌ Keine Patches gefunden",
                0,
                "#FF3333"
            )

            QMessageBox.warning(
                self,
                _("patch_dl_title", "Patch Download"),
                _("patch_dl_none", "Es konnten keine Patches gefunden werden.")
            )

            QTimer.singleShot(3000, restore_style)
            return

        set_status(
            f"📦 {T_FOUND}: {len(display_items)}",
            40
        )

        # ---------------------------------------------------------
        # Patch auswählen
        # ---------------------------------------------------------

        dialog = QInputDialog(self)

        dialog.setWindowTitle(
            _("patch_dl_title", "Patch Download")
        )

        dialog.setLabelText(
            _("patch_dl_select", "Wähle einen Patch:")
        )

        dialog.setComboBoxItems(
            list(display_items.keys())
        )

        dialog.setOkButtonText("OK")

        dialog.setCancelButtonText(
            "Abbrechen" if is_de else "Cancel"
        )

        QApplication.processEvents()

        # ---------------------------------------------------------
        # Abbruch
        # ---------------------------------------------------------

        if not dialog.exec():

            play_sound("dialog-warning.oga")

            set_status(
                T_CANCELLED,
                100,
                "#FF3333"
            )

            QTimer.singleShot(
                500,
                lambda: (
                    set_status(T_CANCELLED, 0, "#FF3333")
                )
            )

            QTimer.singleShot(
                3000,
                restore_style
            )

            return

        # ---------------------------------------------------------
        # Auswahl auslesen
        # ---------------------------------------------------------

        item = dialog.textValue()

        if item not in display_items:
            play_sound("dialog-error.oga")

            set_status(
                "❌ Ungültige Patch-Auswahl",
                0,
                "#FF3333"
            )

            QTimer.singleShot(3000, restore_style)
            return

        url, version, original_name = display_items[item]

        # ---------------------------------------------------------
        # Download vorbereiten
        # ---------------------------------------------------------

        set_status(
            f"{T_START} {original_name}",
            45
        )

        QApplication.processEvents()

        # Dateiname sicher erzeugen
        clean_name = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            original_name
        ).strip("_")

        if not clean_name:
            clean_name = "patch"

        if version == "unknown":
            file_name = f"{clean_name}.patch"
        else:
            file_name = f"{clean_name}_v{version}.patch"

        # ---------------------------------------------------------
        # Download
        # ---------------------------------------------------------

        try:

            with requests.get(
                url,
                timeout=30,
                stream=True
            ) as response:

                response.raise_for_status()

                total_size = int(
                    response.headers.get(
                        "content-length",
                        0
                    )
                )

                downloaded = 0

                # Datei binär schreiben.
                # Dadurch funktioniert es auch mit ungewöhnlichen
                # Patch-Dateien.
                with open(file_name, "wb") as file:

                    for chunk in response.iter_content(
                        chunk_size=64 * 1024
                    ):

                        if not chunk:
                            continue

                        file.write(chunk)

                        downloaded += len(chunk)

                        # -----------------------------------------
                        # Echter Prozentfortschritt
                        # -----------------------------------------

                        if total_size > 0:

                            percent = int(
                                downloaded * 100 / total_size
                            )

                            downloaded_mb = (
                                downloaded / 1024 / 1024
                            )

                            total_mb = (
                                total_size / 1024 / 1024
                            )

                            status = (
                                f"{T_DOWNLOADING}: "
                                f"{percent}%  "
                                f"({downloaded_mb:.1f} / "
                                f"{total_mb:.1f} MB)"
                            )

                            set_status(
                                status,
                                percent
                            )

                        else:

                            downloaded_mb = (
                                downloaded / 1024 / 1024
                            )

                            set_status(
                                f"{T_DOWNLOADING}: "
                                f"{downloaded_mb:.1f} MB",
                                50
                            )

            # -----------------------------------------------------
            # Speichern erfolgreich
            # -----------------------------------------------------

            set_status(
                T_SAVING,
                100
            )

            QApplication.processEvents()

            # Prüfen, ob Datei wirklich existiert
            if not os.path.isfile(file_name):
                raise IOError(
                    "Die Patch-Datei konnte nicht erstellt werden."
                )

            file_size = os.path.getsize(file_name)

            if file_size == 0:
                raise IOError(
                    "Der Server hat eine leere Patch-Datei geliefert."
                )

            # -----------------------------------------------------
            # Erfolg
            # -----------------------------------------------------

            play_sound("complete.oga")

            set_status(
                f"✅ {T_DONE}  "
                f"{os.path.basename(file_name)}",
                100,
                "#00FF66"
            )

            QMessageBox.information(
                self,
                _("patch_dl_success_title", "Patch Download"),
                (
                    _("patch_dl_success", "Patch erfolgreich gespeichert.")
                    + "\n\n"
                    + f"📄 {os.path.abspath(file_name)}"
                    + "\n"
                    + f"📦 {file_size / 1024 / 1024:.2f} MB"
                )
            )

            # Nach Meldung wieder normale Progressbar
            QTimer.singleShot(
                3000,
                restore_style
            )

        # ---------------------------------------------------------
        # HTTP / Netzwerkfehler
        # ---------------------------------------------------------

        except requests.exceptions.Timeout:

            play_sound("dialog-error.oga")

            error_text = (
                _("patch_dl_timeout", "Zeitüberschreitung beim Download.")
            )

            set_status(
                f"❌ {error_text}",
                0,
                "#FF3333"
            )

            QMessageBox.critical(
                self,
                _("patch_dl_error_title", "Download-Fehler"),
                error_text
            )

            QTimer.singleShot(
                3000,
                restore_style
            )

        except requests.exceptions.HTTPError as e:

            play_sound("dialog-error.oga")

            error_text = (
                f"{T_ERROR}: HTTP {e.response.status_code}"
                if e.response is not None
                else str(e)
            )

            set_status(
                f"❌ {error_text}",
                0,
                "#FF3333"
            )

            QMessageBox.critical(
                self,
                _("patch_dl_error_title", "Download-Fehler"),
                error_text
            )

            QTimer.singleShot(
                3000,
                restore_style
            )

        except requests.exceptions.RequestException as e:

            play_sound("dialog-error.oga")

            error_text = (
                _("patch_dl_network_error", "Netzwerkfehler:")
                + f"\n{e}"
            )

            set_status(
                "❌ Netzwerkfehler",
                0,
                "#FF3333"
            )

            QMessageBox.critical(
                self,
                _("patch_dl_error_title", "Download-Fehler"),
                error_text
            )

            QTimer.singleShot(
                3000,
                restore_style
            )

        # ---------------------------------------------------------
        # Sonstige Fehler
        # ---------------------------------------------------------

        except Exception as e:

            play_sound("dialog-error.oga")

            error_text = (
                _("patch_dl_unknown_error", "Unerwarteter Fehler:")
                + f"\n{e}"
            )

            set_status(
                "❌ Fehler beim Patch-Download",
                0,
                "#FF3333"
            )

            QMessageBox.critical(
                self,
                _("patch_dl_error_title", "Download-Fehler"),
                error_text
            )

            QTimer.singleShot(
                3000,
                restore_style
            )

    def run_patch_process(self, patch_data, is_dry_run=True):
        """Führt einen Patch-Test oder die echte Anwendung mit Diagnose aus."""

        # --- Final Label sofort ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import subprocess
        import shutil

        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        action = "Patch-Test" if is_dry_run else "Patch-Anwendung"
        action_en = "Patch dry-run" if is_dry_run else "Patch application"
        cmd = ["patch", "-p1"]
        if is_dry_run:
            cmd.append("--dry-run")

        target_dir = os.path.abspath(
            os.path.expanduser(str(getattr(self, "local_oscam_path", os.getcwd())))
        )

        def report(level, de_text, en_text=None):
            self.log(de_text if is_de or en_text is None else en_text, level)

        if not shutil.which("patch"):
            report(
                "error",
                "❌ Das Programm 'patch' wurde nicht gefunden. Unter Debian/Ubuntu/WSL: sudo apt update && sudo apt install patch",
                "❌ The 'patch' program was not found. On Debian/Ubuntu/WSL: sudo apt update && sudo apt install patch",
            )
            return False

        if not os.path.isdir(target_dir):
            report(
                "error",
                f"❌ OSCam-Zielordner existiert nicht: {target_dir}",
                f"❌ OSCam target directory does not exist: {target_dir}",
            )
            return False

        if not isinstance(patch_data, str) or not patch_data.strip():
            report(
                "error",
                "❌ Patch-Datei ist leer oder konnte nicht gelesen werden.",
                "❌ Patch data is empty or could not be read.",
            )
            return False

        report(
            "info",
            f"🔎 {action} gestartet · Ziel: {target_dir}",
            f"🔎 {action_en} started · target: {target_dir}",
        )

        try:
            process = subprocess.Popen(
                cmd,
                cwd=target_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            stdout, stderr = process.communicate(input=patch_data, timeout=120)
            output = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip())

            if process.returncode == 0:
                report(
                    "success",
                    f"✅ {action} erfolgreich abgeschlossen.",
                    f"✅ {action_en} completed successfully.",
                )
                if output:
                    self.log(output, "info")
                return True

            details = output or ("Keine Details vom patch-Befehl erhalten." if is_de else "The patch command returned no details.")
            details_lower = details.lower()
            if any(term in details_lower for term in ("reversed (or previously applied)", "previously applied", "reversed patch")):
                hint = ("Hinweis: Der Patch könnte bereits angewendet sein oder in umgekehrter Richtung vorliegen." if is_de else "Hint: The patch may already be applied or may be reversed.")
            elif any(term in details_lower for term in ("can't find file", "cannot find file", "no file to patch")):
                hint = ("Hinweis: Prüfe den Zielordner und den Patch-Level (-p1)." if is_de else "Hint: Check the target directory and patch level (-p1).")
            elif any(term in details_lower for term in ("hunk failed", "failed hunk", "malformed patch")):
                hint = ("Hinweis: Der Quellcode passt möglicherweise nicht zur Patch-Version; prüfe Revision und Konflikte." if is_de else "Hint: The source may not match this patch version; check the revision and conflicts.")
            else:
                hint = ("Hinweis: Prüfe Zielpfad, Quellcode-Revision und Patch-Datei." if is_de else "Hint: Check the target path, source revision, and patch file.")

            report(
                "error",
                f"❌ {action} fehlgeschlagen (Exit-Code {process.returncode}).\n{hint}\nZielordner: {target_dir}",
                f"❌ {action_en} failed (exit code {process.returncode}).\n{hint}\nTarget directory: {target_dir}",
            )
            if output:
                self.log(output, "error")
            return False

        except subprocess.TimeoutExpired:
            try:
                process.kill()
                stdout, stderr = process.communicate()
            except Exception:
                stdout, stderr = "", ""
            report(
                "error",
                f"❌ {action} nach 120 Sekunden abgebrochen. Zielordner: {target_dir}",
                f"❌ {action_en} timed out after 120 seconds. Target directory: {target_dir}",
            )
            output = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip())
            if output:
                self.log(output, "error")
            return False
        except FileNotFoundError as exc:
            report(
                "error",
                f"❌ Benötigter Befehl oder Zielpfad nicht gefunden: {exc}",
                f"❌ Required command or target path not found: {exc}",
            )
            return False
        except Exception as exc:
            report(
                "error",
                f"🚨 Fehler beim Ausführen des Patch-Befehls: {type(exc).__name__}: {exc}",
                f"🚨 Error while running patch command: {type(exc).__name__}: {exc}",
            )
            return False

    def select_patch_path(self):
        """Öffnet Verzeichnis-Dialog mit Regenbogen-Progress, Sound und Auto-Reset zu Idle."""

        # --- Final-Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        import os
        from PyQt6.QtWidgets import QFileDialog, QApplication
        from PyQt6.QtCore import QTimer

        # 1. SETUP & SPRACHE
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # Lokalisierte Texte
        T_TITLE = "Patch-Ordner auswählen" if is_de else "Select Patch Folder"
        T_LOAD = "Ordner wird gewählt..." if is_de else "Selecting folder..."
        T_DONE = "Pfad gespeichert!" if is_de else "Path saved!"

        # --- SOUND START ---
        if "safe_play" in globals():
            safe_play("service-login.oga")

        # 2. REGENBOGEN-PROGRESS AKTIVIEREN
        if pbar:
            rainbow = (
                "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
            )
            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center; font-weight: 900; border: 2px solid #222;
                    border-radius: 8px; background-color: #111; color: black; font-size: 14pt;
                }}
                QProgressBar::chunk {{ background: {rainbow}; border-radius: 6px; }}
            """
            )
            pbar.setFormat(f"📁 {T_LOAD}")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        # 3. DIALOG ÖFFNEN
        start_path = getattr(self, "OLD_PATCH_DIR", os.getcwd())
        directory = QFileDialog.getExistingDirectory(self, T_TITLE, start_path)

        if directory:
            directory = os.path.normpath(directory)

            # --- INTERNE WERTE UPDATEN ---
            # Wir nutzen save_config, um die Datei sicher zu schreiben
            new_cfg_data = {"s3_patch_path": directory, "old_patch_dir": directory}

            # Falls save_config existiert, nutzen wir sie (triggert auch Sound/Log)
            if "save_config" in globals():
                save_config(new_cfg_data, gui_instance=self)
            else:
                # Fallback falls save_config nicht global erreichbar
                self.cfg.update(new_cfg_data)
                self.OLD_PATCH_DIR = directory

            # Pfade für die App-Logik setzen
            self.OLD_PATCH_FILE = os.path.join(directory, "oscam-emu.patch")
            self.ALT_PATCH_FILE = os.path.join(directory, "oscam-emu.altpatch")

            if pbar:
                pbar.setValue(100)
                pbar.setFormat(f"✅ {T_DONE}")

            if "safe_play" in globals():
                safe_play("complete.oga")

            if hasattr(self, "log_message"):
                msg = (
                    f"📁 Neuer Patch-Pfad: {directory}"
                    if is_de
                    else f"📁 New Patch Path: {directory}"
                )
                self.log_message(
                    f"<span style='color:#FFD700; font-weight:bold;'>{msg}</span>"
                )
        else:
            # Abgebrochen -> Kurzes Feedback
            if pbar:
                pbar.setValue(0)
                pbar.setFormat("❌" if is_de else "❌")

        # 4. AUTO-RESET ZU DEINEM NEUEN IDLE (mit den 5 Blinks)
        # Wir warten 2 Sekunden, damit der User das "Pfad gespeichert" lesen kann
        if hasattr(self, "pbar_idle"):
            QTimer.singleShot(2500, self.pbar_idle)

    def get_backup_excluded_dirs(self, project_dir):
        """Ermittelt geschützte Projektordner aus config.json."""
        import json
        from pathlib import Path

        project_dir = Path(project_dir).resolve()

        excluded_dirs = {
            "backup",
            "oscam-emu-git",
            "streamboard-git",
            "__pycache__",
        }

        config_file = project_dir / "config.json"

        try:
            with config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)

            for key in (
                "s3_custom_path",
                "ncam_custom_path",
                "s4_custom_path",
            ):
                value = config.get(key)

                if not isinstance(value, str) or not value.strip():
                    continue

                custom_path = Path(value).resolve()

                # Nur Ordner ausschließen, die innerhalb des
                # Projektordners liegen, nicht externe Verzeichnisse.
                try:
                    relative = custom_path.relative_to(project_dir)
                except ValueError:
                    continue

                if relative.parts:
                    excluded_dirs.add(relative.parts[0])

        except (OSError, ValueError, TypeError) as exc:
            print(f"[BACKUP] config.json konnte nicht gelesen werden: {exc}")

        return excluded_dirs

    def create_gi_backup(self):
        """Erstellt ein geprüftes Backup mit Linux-Dateirechten.

        Schließt geschützte Ordner und Symlinks aus.
        Das bestehende Backup bleibt bis zum erfolgreichen Abschluss erhalten.
        """

        import os
        import json
        import stat
        import shutil
        import tempfile
        import zipfile

        from pathlib import Path
        from PyQt6.QtWidgets import QMessageBox

        project_dir = Path(__file__).resolve().parent.resolve()
        backup_dir = project_dir / "backup"
        backup_zip = backup_dir / "backup_git.zip"
        config_file = project_dir / "config.json"

        excluded_dirs = {
            "backup",
            ".git",
            "oscam-emu-git",
            "streamboard-git",
            "__pycache__",
            ".venv",
            "venv",
        }

        excluded_names = {name.casefold() for name in excluded_dirs}
        def is_excluded_dir(dirname):
            name = dirname.casefold()

            return (
                name in excluded_names
                or "s3" in name
                or "s4" in name
            )
        def norm(path):
            return os.path.normcase(os.path.abspath(str(path)))

        def is_inside(path, parent):
            try:
                return os.path.commonpath(
                    [norm(path), norm(parent)]
                ) == norm(parent)
            except (ValueError, OSError):
                return False

        def add_to_archive(archive, source, arcname):
            """Schreibt Dateien mit Unix-Modus und ohne Symlink-Verfolgung."""
            source = Path(source)

            if source.is_symlink():
                return False

            file_stat = source.stat(follow_symlinks=False)

            if not (stat.S_ISREG(file_stat.st_mode)
                    or stat.S_ISDIR(file_stat.st_mode)):
                return False

            if stat.S_ISDIR(file_stat.st_mode):
                arcname = arcname.rstrip("/") + "/"

            info = zipfile.ZipInfo.from_file(
                source,
                arcname=arcname,
            )
            info.create_system = 3  # Unix
            info.external_attr = (file_stat.st_mode & 0xFFFF) << 16

            if stat.S_ISDIR(file_stat.st_mode):
                info.external_attr |= 0x10
                archive.writestr(info, b"")
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                with source.open("rb") as src:
                    with archive.open(info, "w") as dst:
                        shutil.copyfileobj(src, dst)

            return True

        temp_zip = None

        try:
            # --------------------------------------------------
            # 1. Konfiguration prüfen
            # --------------------------------------------------
            with config_file.open("r", encoding="utf-8") as file:
                config = json.load(file)

            if not isinstance(config, dict):
                raise ValueError(
                    "config.json enthält kein JSON-Objekt."
                )

            custom_paths = []

            for key in (
                "s3_custom_path",
                "ncam_custom_path",
                "s4_custom_path",
            ):
                value = config.get(key)

                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"Der Konfigurationswert '{key}' fehlt "
                        "oder ist ungültig."
                    )

                custom_path = Path(
                    value.strip()
                ).expanduser()

                if not custom_path.is_absolute():
                    custom_path = project_dir / custom_path

                custom_path = custom_path.resolve()

                if not is_inside(custom_path, project_dir):
                    raise ValueError(
                        "Der konfigurierte Pfad liegt außerhalb "
                        f"des Projekts: {custom_path}"
                    )

                if norm(custom_path) == norm(project_dir):
                    raise ValueError(
                        f"'{key}' verweist auf das gesamte "
                        "Projektverzeichnis."
                    )

                if norm(custom_path) not in {
                    norm(path) for path in custom_paths
                }:
                    custom_paths.append(custom_path)

            if len(custom_paths) != 3:
                raise ValueError(
                    "Die drei konfigurierten Ordner müssen "
                    "eindeutig sein."
                )

            # --------------------------------------------------
            # 2. Eindeutiges temporäres Archiv erstellen
            # --------------------------------------------------
            backup_dir.mkdir(parents=True, exist_ok=True)

            fd, temp_name = tempfile.mkstemp(
                prefix="backup_git.",
                suffix=".tmp.zip",
                dir=backup_dir,
            )
            os.close(fd)
            temp_zip = Path(temp_name)

            file_count = 0
            dir_count = 0

            # --------------------------------------------------
            # 3. Projektdateien archivieren
            # --------------------------------------------------
            with zipfile.ZipFile(
                temp_zip,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as archive:

                for root, dirs, files in os.walk(
                    project_dir,
                    topdown=True,
                    followlinks=False,
                ):
                    root_path = Path(root)
                    filtered_dirs = []

                    for dirname in dirs:
                        candidate = root_path / dirname

                        # s3-/s4-Ordner und geschützte Standardordner ausschließen.
                        if is_excluded_dir(dirname):
                            continue

                        if any(
                            norm(candidate) == norm(custom_path)
                            or is_inside(candidate, custom_path)
                            for custom_path in custom_paths
                        ):
                            continue

                        if candidate.is_symlink():
                            continue

                        filtered_dirs.append(dirname)

                    # Verzeichnisliste vor dem Abstieg einschränken.
                    dirs[:] = filtered_dirs

                    # Verzeichnismetadaten einschließlich Modus sichern.
                    for dirname in filtered_dirs:
                        candidate = root_path / dirname

                        relative_path = candidate.relative_to(
                            project_dir
                        ).as_posix()

                        if add_to_archive(
                            archive, candidate, relative_path
                        ):
                            dir_count += 1

                    for filename in files:
                        source_file = root_path / filename

                        # Symlinks und spezielle Dateitypen überspringen.
                        if source_file.is_symlink():
                            continue

                        if not is_inside(source_file, project_dir):
                            continue

                        if any(
                            is_inside(source_file, custom_path)
                            for custom_path in custom_paths
                        ):
                            continue

                        relative_path = source_file.relative_to(
                            project_dir
                        )
                        relative_parts = relative_path.parts

                        if any(
                            part.casefold() in excluded_names
                            for part in relative_parts
                        ):
                            continue

                        # Backup-Dateien niemals selbst archivieren.
                        if (
                            norm(source_file) == norm(backup_zip)
                            or source_file == temp_zip
                        ):
                            continue

                        if add_to_archive(
                            archive,
                            source_file,
                            relative_path.as_posix(),
                        ):
                            file_count += 1

            # --------------------------------------------------
            # 4. Archiv und Dateirechte überprüfen
            # --------------------------------------------------
            with zipfile.ZipFile(temp_zip, "r") as archive:
                bad_file = archive.testzip()

                if bad_file is not None:
                    raise RuntimeError(
                        f"ZIP-Prüfung fehlgeschlagen: {bad_file}"
                    )

                for info in archive.infolist():
                    # Alle Einträge müssen Unix-Modi enthalten.
                    if info.create_system != 3:
                        raise RuntimeError(
                            "Unix-Dateimetadaten fehlen: "
                            f"{info.filename}"
                        )

                    mode = (info.external_attr >> 16) & 0xFFFF

                    if not mode:
                        raise RuntimeError(
                            "Dateirechte fehlen: "
                            f"{info.filename}"
                        )

            # --------------------------------------------------
            # 5. Erst jetzt das bisherige Backup ersetzen
            # --------------------------------------------------
            os.replace(temp_zip, backup_zip)
            temp_zip = None

            QMessageBox.information(
                self,
                "Backup erfolgreich",
                f"Das Backup wurde erstellt und geprüft:\n"
                f"{backup_zip}\n\n"
                f"Dateien: {file_count}\n"
                f"Verzeichnisse: {dir_count}\n"
                "Linux-Dateirechte: gespeichert\n"
                "Symlinks: übersprungen",
            )

            if hasattr(self, "log_message"):
                self.log_message(
                    f"Backup erstellt: {backup_zip} "
                    f"({file_count} Dateien, {dir_count} Verzeichnisse)"
                )

            return True

        except Exception as exc:
            # Nur das neue temporäre Archiv entfernen.
            # Das bisherige Backup wird nicht absichtlich verändert.
            if temp_zip is not None:
                try:
                    temp_zip.unlink(missing_ok=True)
                except OSError:
                    pass

            QMessageBox.critical(
                self,
                "Backup fehlgeschlagen",
                "Das Backup konnte nicht sicher erstellt werden:\n"
                f"{exc}\n\n"
                "Das bisherige Backup wurde nicht absichtlich "
                "ersetzt.",
            )

            if hasattr(self, "log_message"):
                self.log_message(f"Backup-Fehler: {exc}")

            return False

    def _has_project_write_access(self, project_dir):
        """Prüft, ob der aktuelle Prozess im Projektordner schreiben darf."""
        import os
        import tempfile
        from pathlib import Path

        project_dir = Path(project_dir)

        try:
            with tempfile.NamedTemporaryFile(
                prefix=".write_test_",
                dir=str(project_dir),
                delete=True,
            ):
                pass
            return True
        except (OSError, PermissionError):
            return False

    def zip_patch(self, info_widget=None, progress_callback=None):
        """Erstellt ein ZIP des Patches mit Neon-Regenbogen-Progress und Auto-Reset."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        from PyQt6.QtWidgets import QTextEdit, QApplication
        from PyQt6.QtCore import QTimer
        import zipfile
        import os

        # 1. Widget & ProgressBar Setup
        widget = (
            info_widget
            if isinstance(info_widget, QTextEdit)
            else getattr(self, "info_text", None)
        )
        lang = getattr(self, "LANG", "de").lower()[:2]
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

        if pbar:
            pbar.setStyleSheet(STYLE_NEON.format(text_color="black", chunk_color=RAINBOW_GRADIENT))
            msg_zip = "Erstelle ZIP..." if is_de else "Creating ZIP..."
            pbar.setFormat(f"📦 {msg_zip} %p%")
            pbar.setValue(10)
            pbar.show()
            QApplication.processEvents()

        # Hilfsfunktionen
        def get_msg(key, default, **kwargs):
            # Annahme: TEXTS ist global definiert
            template = TEXTS.get(lang, {}).get(key, default)
            try: return template.format(**kwargs)
            except: return template

        def play_zip_sound(success=True):
            if "safe_play" in globals():
                safe_play("complete.oga" if success else "dialog-error.oga")

        # --- Eigentliche ZIP-Logik ---
        try:
            patch_file = globals().get("PATCH_FILE", "oscam-emu.patch")
            zip_file_path = globals().get("ZIP_FILE", "oscam-emu.patch.zip")

            if pbar: pbar.setValue(30)

            if not os.path.exists(patch_file):
                msg = get_msg("patch_file_missing", "Datei nicht gefunden: {path}", path=patch_file)
                if hasattr(self, "append_info"): self.append_info(widget, msg, "error")
                play_zip_sound(False)
                if pbar:
                    pbar.setStyleSheet(STYLE_NEON.format(text_color="#FF0000", chunk_color="#800"))
                    pbar.setValue(100)
                return

            if pbar: pbar.setValue(60)

            # Zippen
            with zipfile.ZipFile(zip_file_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(patch_file, os.path.basename(patch_file))

            if pbar: pbar.setValue(90)

            # Erfolgsmeldung
            msg = get_msg("zip_success", "✅ Patch erfolgreich gepackt: {zip_file}", zip_file=zip_file_path)
            if hasattr(self, "append_info"): self.append_info(widget, msg, "success")
            play_zip_sound(True)

            if pbar:
                done_msg = "ZIP erstellt!" if is_de else "ZIP created!"
                pbar.setFormat(f"✅ {done_msg}")

        except Exception as e:
            if pbar:
                pbar.setStyleSheet(STYLE_NEON.format(text_color="#FF0000", chunk_color="#800"))
            msg = get_msg("zip_failed", "❌ Fehler beim Zippen: {error}", error=str(e))
            if hasattr(self, "append_info"): self.append_info(widget, msg, "error")
            play_zip_sound(False)

        # --- ABSCHLUSS & AUTO-RESET ---
        if pbar:
            pbar.setValue(100)
        
            def restore_pbar():
                pbar.setValue(0)
                pbar.setFormat("%p%")
                pbar.setStyleSheet("""
                    QProgressBar { 
                        border: 1px solid #444; border-radius: 8px; background-color: #1A1A1A; 
                        color: black; text-align: center; font-weight: bold; 
                    }
                    QProgressBar::chunk { 
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F37804, stop:1 #FFD700); 
                        border-radius: 8px; 
                    }
                """)

            QTimer.singleShot(3000, restore_pbar)

        if progress_callback:
            try: progress_callback(100)
            except: pass

        QApplication.processEvents()

    def edit_patch_header(self, info_widget=None, progress_callback=None):
        """Öffnet den Header-Editor mit Neon-Regenbogen-Progress, Sound und Sprach-Support."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import os
        from PyQt6.QtWidgets import (
            QDialog,
            QVBoxLayout,
            QTextEdit,
            QDialogButtonBox,
            QApplication,
        )
        from PyQt6.QtCore import QTimer

        # 1. Sprache & Progress Setup
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # Lokalisierte Texte
        T_LOADING = "Editor wird geladen..." if is_de else "Loading editor..."
        T_SAVED = "Patch gespeichert!" if is_de else "Patch saved!"
        T_CANCEL = "Abgebrochen" if is_de else "Cancelled"
        T_TITLE = "Patch-Header Editor"

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

        # --- SOUND BEIM ÖFFNEN ---
        if "safe_play" in globals():
            safe_play("service-login.oga")

        if pbar:
            pbar.setStyleSheet(STYLE_NEON.format(text_color="black", chunk_color=RAINBOW_GRADIENT))
            pbar.setFormat(f"📝 {T_LOADING}")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        # Pfad zur Datei sicherstellen
        base = getattr(self, "base_dir", os.getcwd())
        p_file = os.path.join(base, "oscam-emu.patch")

        if not os.path.exists(p_file):
            if pbar:
                pbar.setStyleSheet(STYLE_NEON.format(text_color="#FF0000", chunk_color="#800"))
                pbar.setFormat("❌ Datei fehlt!" if is_de else "❌ File missing!")
                pbar.setValue(100)
            if "safe_play" in globals():
                safe_play("dialog-error.oga")
            return

        # 2. Dialog erstellen
        dlg = QDialog(self)
        dlg.setWindowTitle(T_TITLE)
        dlg.resize(900, 700)
        ly = QVBoxLayout(dlg)

        edit = QTextEdit()
        # Matrix-Style: Schwarz mit grüner Schrift
        edit.setStyleSheet(
            "background-color: #000; color: #39FF14; font-family: monospace; font-size: 11pt; border: 1px solid #333;"
        )

        try:
            with open(p_file, "r", encoding="utf-8", errors="ignore") as f:
                edit.setPlainText(f.read())
            if pbar:
                pbar.setValue(60)
        except Exception:
            if pbar: pbar.setValue(0)
            return

        ly.addWidget(edit)

        # --- BUTTONS ---
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        btn_save = bb.button(QDialogButtonBox.StandardButton.Save)
        if btn_save: btn_save.setText("Speichern" if is_de else "Save")
        btn_cancel = bb.button(QDialogButtonBox.StandardButton.Cancel)
        if btn_cancel: btn_cancel.setText("Abbrechen" if is_de else "Cancel")

        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        ly.addWidget(bb)

        if pbar: pbar.setValue(90)

        # 3. Dialog ausführen
        result = dlg.exec()

        if result == QDialog.DialogCode.Accepted:
            try:
                if "safe_play" in globals(): safe_play("complete.oga")

                content = edit.toPlainText()
                with open(p_file, "w", encoding="utf-8") as f:
                    f.write(content)

                if pbar:
                    pbar.setValue(100)
                    pbar.setFormat(f"✅ {T_SAVED}")
            except Exception:
                if "safe_play" in globals(): safe_play("dialog-error.oga")
                if pbar:
                    pbar.setStyleSheet(STYLE_NEON.format(text_color="#FF0000", chunk_color="#800"))
        else:
            if "safe_play" in globals(): safe_play("dialog-error.oga")
            if pbar:
                pbar.setValue(0)
                pbar.setFormat(f"↩️ {T_CANCEL}")

        # 4. AUTO-RESET (nach 3 Sekunden zurück zum Standard Orange/Gold)
        def restore_pbar():
            if pbar:
                pbar.setValue(0)
                pbar.setFormat("%p%")
                pbar.setStyleSheet(
                    """
                    QProgressBar { 
                        border: 1px solid #444; border-radius: 8px; background-color: #1A1A1A; 
                        color: black; text-align: center; font-weight: bold; 
                    }
                    QProgressBar::chunk { 
                        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #F37804, stop:1 #FFD700); 
                        border-radius: 8px; 
                    }
                """
                )

        QTimer.singleShot(3000, restore_pbar)
        if progress_callback: progress_callback(100)

    def check_patch(self, info_widget=None, progress_callback=None):
        """
        Prüft den erzeugten OSCam-Emu-Patch gegen den aktuellen
        Streamboard-OSCam-Quellcode.

        Der erzeugte Patch besitzt einen eigenen 3-zeiligen Header.
        Dieser Header wird für git apply temporär entfernt.

        Es werden KEINE Änderungen am Repository vorgenommen.
        Es wird ausschließlich ausgeführt:

            git apply --check --binary

        Dadurch wird nur geprüft, ob der Patch sauber anwendbar ist.
        """

        import os
        import tempfile

        from PyQt6.QtWidgets import QApplication

        print(
            "[PATCH CHECK] check_patch() START",
            flush=True
        )

        # ---------------------------------------------------------
        # Info-Widget bestimmen
        # ---------------------------------------------------------

        if info_widget is None:
            info_widget = getattr(
                self,
                "info_text",
                None
            )

        lang = getattr(
            self,
            "LANG",
            "de"
        ).lower()

        is_de = lang == "de"

        # ---------------------------------------------------------
        # Final-Label ausblenden
        # ---------------------------------------------------------

        if hasattr(self, "hide_final_label"):
            try:
                self.hide_final_label()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Logging
        # ---------------------------------------------------------

        def write_log(text, level="info"):

            print(
                f"[PATCH CHECK] {text}",
                flush=True
            )

            try:
                self.append_info(
                    info_widget,
                    str(text),
                    level
                )

            except Exception as exc:

                print(
                    "[PATCH CHECK] append_info Fehler:",
                    exc,
                    flush=True
                )

                try:
                    if info_widget is not None:
                        info_widget.append(
                            str(text)
                        )
                except Exception:
                    pass

        # ---------------------------------------------------------
        # ProgressBar
        # ---------------------------------------------------------

        pbar = getattr(
            self,
            "progress_bar",
            None
        )

        def update_p(
            value,
            error=False,
            text=None
        ):

            try:

                if pbar:

                    pbar.setValue(
                        int(value)
                    )

                    if error:

                        pbar.setFormat(
                            "❌ Patch Fehler"
                        )

                    elif text:

                        pbar.setFormat(
                            str(text)
                        )

                    else:

                        pbar.setFormat(
                            "%p%"
                        )

                    pbar.show()

            except Exception:
                pass

            if progress_callback:

                try:

                    progress_callback(
                        int(value)
                    )

                except Exception:
                    pass

            try:
                QApplication.processEvents()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Sound
        # ---------------------------------------------------------

        def play_check_sound(success=True):

            try:

                if "safe_play" in globals():

                    globals()["safe_play"](
                        "complete.oga"
                        if success
                        else
                        "dialog-error.oga"
                    )

            except Exception:
                pass

        # ---------------------------------------------------------
        # Einheitliche Fehlerbehandlung
        # ---------------------------------------------------------

        def check_failed(message):

            write_log(
                "❌ " + str(message),
                "error"
            )

            update_p(
                100,
                error=True,
                text=(
                    "❌ Patch Fehler"
                    if is_de
                    else
                    "❌ Patch Error"
                )
            )

            play_check_sound(
                False
            )

            return False

        # ---------------------------------------------------------
        # START
        # ---------------------------------------------------------

        write_log(
            "🔍 PATCH PRÜFEN wurde gestartet...",
            "info"
        )

        update_p(
            5,
            text=(
                "Patch-Prüfung startet..."
                if is_de
                else
                "Starting patch check..."
            )
        )

        # =========================================================
        # PATCH_FILE
        # =========================================================

        
        patch_file = (
            getattr(self, "PATCH_FILE", None)
            or globals().get("PATCH_FILE")
        )

        if not patch_file:
            try:
                from paths import PATCH_FILE as CONFIG_PATCH_FILE
                patch_file = CONFIG_PATCH_FILE
            except (ImportError, AttributeError):
                patch_file = None

        if not patch_file:
            return check_failed(
                "PATCH_FILE ist nicht konfiguriert. "
                "Der Pfad konnte auch nicht aus paths.py gelesen werden."
            )


        if not patch_file:

            return check_failed(
                "PATCH_FILE ist nicht konfiguriert."
            )

        patch_file = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(
                    str(patch_file)
                )
            )
        )

        write_log(
            f"📄 Patch-Datei:\n{patch_file}",
            "info"
        )

        # ---------------------------------------------------------
        # Patch vorhanden?
        # ---------------------------------------------------------

        if not os.path.isfile(
            patch_file
        ):

            return check_failed(
                "Patch-Datei wurde nicht gefunden:\n"
                f"{patch_file}"
            )

        # ---------------------------------------------------------
        # Patch-Größe
        # ---------------------------------------------------------

        try:

            patch_size = os.path.getsize(
                patch_file
            )

        except Exception as exc:

            return check_failed(
                "Patch-Datei kann nicht gelesen werden:\n"
                f"{exc}"
            )

        if patch_size <= 0:

            return check_failed(
                "Patch-Datei ist leer."
            )

        write_log(
            "✓ Patch-Datei gefunden.",
            "success"
        )

        write_log(
            "✓ Patch-Größe: "
            f"{patch_size:,} Bytes".replace(",", "."),
            "success"
        )

        update_p(
            20,
            text=(
                "Patch gefunden..."
                if is_de
                else
                "Patch found..."
            )
        )

       
        # =========================================================
        # STREAMREPO
        # =========================================================

        streamboard_repo = (
            globals().get("STREAMREPO")
            or getattr(self, "STREAMREPO", None)
        )

        if not streamboard_repo:
            try:
                from paths import STREAMREPO as CONFIG_STREAMREPO
                streamboard_repo = CONFIG_STREAMREPO
            except (ImportError, AttributeError):
                streamboard_repo = None

        if not streamboard_repo:
            try:
                from paths import TEMP_REPO as CONFIG_TEMP_REPO
                streamboard_repo = CONFIG_TEMP_REPO
            except (ImportError, AttributeError):
                streamboard_repo = None

        if not streamboard_repo:
            return check_failed(
                "STREAMREPO ist nicht konfiguriert. "
                "Der Pfad konnte nicht aus paths.py gelesen werden."
            )

        streamboard_repo = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(
                    str(streamboard_repo)
                )
            )
        )

        write_log(
            "📁 Prüfe gegen aktuelles "
            "Streamboard-Repository:",
            "info"
        )

        write_log(
            f"   {streamboard_repo}",
            "info"
        )

        if not os.path.isdir(
            os.path.join(streamboard_repo, ".git")
        ):
            return check_failed(
                "STREAMREPO ist kein gültiges Git-Repository:\n"
                f"{streamboard_repo}"
            )


        # ---------------------------------------------------------
        # Repository vorhanden?
        # ---------------------------------------------------------

        if not os.path.isdir(
            streamboard_repo
        ):

            return check_failed(
                "Streamboard-Repository existiert nicht:\n"
                f"{streamboard_repo}"
            )

        update_p(
            30,
            text=(
                "Streamboard-Repository prüfen..."
                if is_de
                else
                "Checking Streamboard repository..."
            )
        )

        # =========================================================
        # GIT REPOSITORY PRÜFEN
        # =========================================================

        try:

            write_log(
                "🔎 Prüfe Streamboard-Git-Repository...",
                "info"
            )

            result = git_command(
                [
                    "rev-parse",
                    "--is-inside-work-tree"
                ],
                cwd=streamboard_repo,
                allowed_returncodes=(0,),
                timeout=60
            )

            if (
                (result.stdout or "")
                .strip()
                .lower()
                != "true"
            ):

                raise RuntimeError(
                    "Das Streamboard-Verzeichnis ist "
                    "kein Git-Repository."
                )

            write_log(
                "✓ Streamboard-Git-Repository erkannt.",
                "success"
            )

        except Exception as exc:

            return check_failed(
                "Streamboard-Git-Repository konnte "
                "nicht geprüft werden:\n"
                f"{exc}"
            )

        # =========================================================
        # AKTUELLEN STREAMBOARD-HEAD ERMITTELN
        # =========================================================

        try:

            result = git_command(
                [
                    "rev-parse",
                    "HEAD"
                ],
                cwd=streamboard_repo,
                allowed_returncodes=(0,),
                timeout=60
            )

            streamboard_commit = (
                result.stdout or ""
            ).strip()

            if not streamboard_commit:

                raise RuntimeError(
                    "Streamboard-HEAD konnte "
                    "nicht ermittelt werden."
                )

            write_log(
                "✓ Aktueller Streamboard-HEAD:",
                "success"
            )

            write_log(
                f"   {streamboard_commit}",
                "info"
            )

        except Exception as exc:

            return check_failed(
                "Streamboard-HEAD konnte "
                "nicht ermittelt werden:\n"
                f"{exc}"
            )

        update_p(
            40,
            text=(
                "Streamboard-Stand ermittelt..."
                if is_de
                else
                "Streamboard revision detected..."
            )
        )

        # =========================================================
        # PATCH EINLESEN
        # =========================================================

        temporary_patch = None

        try:

            write_log(
                "📖 Lese Patch-Datei...",
                "info"
            )

            with open(
                patch_file,
                "r",
                encoding="utf-8",
                errors="replace"
            ) as handle:

                content = handle.read()

        except Exception as exc:

            return check_failed(
                "Patch-Datei konnte nicht gelesen werden:\n"
                f"{exc}"
            )

        update_p(
            50,
            text=(
                "Patch vorbereiten..."
                if is_de
                else
                "Preparing patch..."
            )
        )

        # =========================================================
        # HEADER ENTFERNEN
        # =========================================================

        marker = "diff --git "

        position = content.find(
            marker
        )

        if position < 0:

            return check_failed(
                "Im Patch wurde kein "
                "'diff --git'-Block gefunden."
            )

        header = content[
            :position
        ].strip()

        git_patch = content[
            position:
        ]

        if not git_patch.strip():

            return check_failed(
                "Der eigentliche Git-Patch ist leer."
            )

        if header:

            write_log(
                "✓ Patch-Header erkannt und entfernt.",
                "success"
            )

            write_log(
                "   Git-Diff beginnt bei Zeichen "
                f"{position}.",
                "info"
            )

        else:

            write_log(
                "ℹ️ Kein zusätzlicher Patch-Header "
                "gefunden.",
                "info"
            )

        # =========================================================
        # TEMPORÄRE PATCH-DATEI
        # =========================================================

        try:

            temp_handle = tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".patch",
                prefix="oscam_patch_check_",
                delete=False
            )

            temporary_patch = temp_handle.name

            try:

                temp_handle.write(
                    git_patch
                )

            finally:

                temp_handle.close()

            temporary_size = os.path.getsize(
                temporary_patch
            )

            if temporary_size <= 0:

                raise RuntimeError(
                    "Temporäre Git-Patch-Datei ist leer."
                )

            write_log(
                "✓ Temporärer Git-Patch wurde erzeugt.",
                "success"
            )

            write_log(
                f"   {temporary_patch}",
                "info"
            )

            write_log(
                "   Größe: "
                f"{temporary_size:,} Bytes"
                .replace(",", "."),
                "info"
            )

        except Exception as exc:

            return check_failed(
                "Temporärer Git-Patch konnte "
                "nicht erzeugt werden:\n"
                f"{exc}"
            )

        update_p(
            65,
            text=(
                "Git-Patch vorbereitet..."
                if is_de
                else
                "Git patch prepared..."
            )
        )

        # =========================================================
        # GIT APPLY --CHECK
        # =========================================================

        try:

            write_log(
                "",
                "info"
            )

            write_log(
                "🔍 Prüfe Patch mit:",
                "info"
            )

            write_log(
                "   git apply --check --binary",
                "info"
            )

            write_log(
                "   Repository:",
                "info"
            )

            write_log(
                f"   {streamboard_repo}",
                "info"
            )

            write_log(
                "   Keine Änderungen werden angewendet.",
                "info"
            )

            result = git_command(
                [
                    "apply",
                    "--check",
                    "--binary",
                    temporary_patch
                ],
                cwd=streamboard_repo,
                allowed_returncodes=(0, 1),
                timeout=600
            )

            stdout = (
                result.stdout or ""
            ).strip()

            stderr = (
                result.stderr or ""
            ).strip()

            update_p(
                85,
                text=(
                    "Patch wird geprüft..."
                    if is_de
                    else
                    "Checking patch..."
                )
            )

            # =====================================================
            # ERFOLG
            # =====================================================

            if result.returncode == 0:

                write_log(
                    "",
                    "info"
                )

                write_log(
                    "════════════════════════════════════════════",
                    "info"
                )

                write_log(
                    "✅ PATCH-PRÜFUNG ERFOLGREICH",
                    "success"
                )

                write_log(
                    "✓ Der Patch kann auf den aktuellen "
                    "Streamboard-Stand angewendet werden.",
                    "success"
                )

                write_log(
                    f"✓ Streamboard-HEAD: "
                    f"{streamboard_commit}",
                    "info"
                )

                write_log(
                    "✓ git apply --check war erfolgreich.",
                    "success"
                )

                if stdout:

                    write_log(
                        stdout,
                        "info"
                    )

                write_log(
                    "════════════════════════════════════════════",
                    "info"
                )

                update_p(
                    100,
                    text="✅ Patch OK"
                )

                if pbar:

                    try:

                        pbar.setFormat(
                            "✅ Patch OK"
                        )

                    except Exception:
                        pass

                play_check_sound(
                    True
                )

                print(
                    "[PATCH CHECK] ERFOLGREICH",
                    flush=True
                )

                return True

            # =====================================================
            # FEHLER
            # =====================================================

            error_text = (
                stderr
                or stdout
                or
                f"git apply beendet mit "
                f"Returncode {result.returncode}"
            )

            write_log(
                "",
                "info"
            )

            write_log(
                "════════════════════════════════════════════",
                "info"
            )

            write_log(
                "❌ PATCH-PRÜFUNG FEHLGESCHLAGEN",
                "error"
            )

            write_log(
                "Der Patch kann nicht sauber auf den "
                "aktuellen Streamboard-Stand angewendet werden.",
                "error"
            )

            write_log(
                f"Streamboard-HEAD: "
                f"{streamboard_commit}",
                "info"
            )

            write_log(
                "",
                "info"
            )

            write_log(
                "Git-Fehler:",
                "error"
            )

            write_log(
                error_text,
                "error"
            )

            write_log(
                "════════════════════════════════════════════",
                "info"
            )

            update_p(
                100,
                error=True,
                text="❌ Patch Fehler"
            )

            if pbar:

                try:

                    pbar.setFormat(
                        "❌ Patch Fehler"
                    )

                except Exception:
                    pass

            play_check_sound(
                False
            )

            print(
                "[PATCH CHECK] FEHLGESCHLAGEN",
                flush=True
            )

            return False

        except Exception as exc:

            write_log(
                "❌ Fehler beim Ausführen von "
                "git apply --check:",
                "error"
            )

            write_log(
                str(exc),
                "error"
            )

            update_p(
                100,
                error=True,
                text="❌ Patch Fehler"
            )

            if pbar:

                try:

                    pbar.setFormat(
                        "❌ Patch Fehler"
                    )

                except Exception:
                    pass

            play_check_sound(
                False
            )

            print(
                "[PATCH CHECK] EXCEPTION:",
                exc,
                flush=True
            )

            return False

        finally:

            # -----------------------------------------------------
            # Temporäre Datei löschen
            # -----------------------------------------------------

            if temporary_patch:

                try:

                    if os.path.isfile(
                        temporary_patch
                    ):

                        os.remove(
                            temporary_patch
                        )

                        print(
                            "[PATCH CHECK] "
                            "Temporäre Patch-Datei gelöscht.",
                            flush=True
                        )

                except Exception as exc:

                    print(
                        "[PATCH CHECK] "
                        "Temporäre Patch-Datei konnte "
                        f"nicht gelöscht werden: {exc}",
                        flush=True
                    )

            print(
                "[PATCH CHECK] check_patch() ENDE",
                flush=True
            )

    def create_option_button(
        self, key, text, color="#FFFFFF", fg="black", callback=None
    ):
        """
        Erstellt einen stylischen Option-Button für die GUI.
        - key: eindeutiger Button-Key
        - text: Anzeige-Text
        - color: Hintergrundfarbe (Hex)
        - fg: Textfarbe (Hex)
        - callback: Funktion beim Klick, bekommt info_widget + progress_callback übergeben
        """
        btn = QPushButton(text)
        btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(self.BUTTON_HEIGHT)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color};
                color: {fg};
                border-radius: {self.BUTTON_RADIUS}px;
            }}
            QPushButton:hover {{
                background-color: {self.adjust_color(color, 1.2)};
            }}
            QPushButton:pressed {{
                background-color: {self.adjust_color(color, 0.85)};
            }}
        """
        )

        # Click Event mit info_widget & progress_callback
        if callback:
            btn.clicked.connect(
                lambda checked=False: callback(
                    info_widget=self.info_text, progress_callback=None
                )
            )

        return btn

    def on_header_clicked(self, event):
        """Wird aufgerufen, wenn man auf den blinkenden Balken klickt."""
        if (
            hasattr(self, "pulse_anim")
            and self.pulse_anim.state() == QPropertyAnimation.State.Running
        ):

            # Sofortiges Feedback im Log (Nutzt deine append_info)
            self.append_info("Update-Prozess gestartet...", "info")

            self.pulse_anim.stop()
            if self.header_container.graphicsEffect():
                self.header_container.setGraphicsEffect(None)

            self.header_label.setText(" Aktualisierung läuft...")

            # Start des Pulls
            self.run_git_pull()

    def apply_patch(self, info_widget=None, progress_callback=None):
        """
        Wendet den OSCam-Emu-Patch auf das konfigurierte
        Streamboard-OSCam-Quellverzeichnis an.

        Das Zielverzeichnis wird ausschließlich über STREAMREPO
        bestimmt.

        Erwartetes Verzeichnis:
            <PLUGIN_DIR>\\streamboard-git
        """

        if hasattr(self, "hide_final_label"):
            try:
                self.hide_final_label()
            except Exception:
                pass

        import os
        from PyQt6.QtWidgets import QApplication

        # ---------------------------------------------------------
        # Info-Widget
        # ---------------------------------------------------------

        info_widget = (
            info_widget
            if info_widget is not None
            else getattr(
                self,
                "info_text",
                None
            )
        )

        # ---------------------------------------------------------
        # Sprache
        # ---------------------------------------------------------

        lang = getattr(
            self,
            "LANG",
            "de"
        ).lower()

        # ---------------------------------------------------------
        # ProgressBar
        # ---------------------------------------------------------

        pbar = getattr(
            self,
            "progress_bar",
            None
        )

        rainbow = (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:0, "
            "stop:0.0 #FF0000, "
            "stop:0.2 #FF7F00, "
            "stop:0.4 #FFFF00, "
            "stop:0.6 #00FF00, "
            "stop:0.8 #0000FF, "
            "stop:1.0 #8B00FF"
            ");"
        )

        style_rainbow = f"""
            QProgressBar {{
                text-align: center;
                font-weight: 900;
                border: 2px solid #222;
                border-radius: 6px;
                background-color: #111;
                color: black;
                font-size: 14pt;
            }}

            QProgressBar::chunk {{
                background: {rainbow};
                border-radius: 4px;
            }}
        """

        style_error = """
            QProgressBar {
                text-align: center;
                font-weight: 900;
                border: 2px solid #500;
                border-radius: 6px;
                background-color: #111;
                color: #FF0000;
                font-size: 14pt;
            }

            QProgressBar::chunk {
                background: #800;
                border-radius: 4px;
            }
        """

        def update_p(value, is_err=False):
            """Aktualisiert ProgressBar und optionalen Callback."""

            if pbar:
                try:
                    pbar.setFormat("%p%")
                    pbar.setStyleSheet(
                        style_error
                        if is_err
                        else style_rainbow
                    )
                    pbar.setValue(value)
                    pbar.show()
                except Exception:
                    pass

            if progress_callback:
                try:
                    progress_callback(value)
                except Exception:
                    pass

            try:
                QApplication.processEvents()
            except Exception:
                pass

        def play_apply_sound(success=True):
            """Spielt Abschluss- bzw. Fehlerton."""

            try:
                safe_play = globals().get(
                    "safe_play"
                )

                if safe_play:
                    safe_play(
                        "complete.oga"
                        if success
                        else "dialog-error.oga"
                    )
            except Exception:
                pass

        # =========================================================
        # KONFIGURATION
        # =========================================================

        patch_file = globals().get(
            "PATCH_FILE",
            getattr(
                self,
                "PATCH_FILE",
                ""
            )
        )

        # ---------------------------------------------------------
        # WICHTIG:
        # Das OSCam-Quellverzeichnis kommt ausschließlich
        # aus STREAMREPO.
        # ---------------------------------------------------------

        source_dir = globals().get(
            "STREAMREPO",
            ""
        )

        if not source_dir:
            source_dir = getattr(
                self,
                "STREAMREPO",
                ""
            )

        # ---------------------------------------------------------
        # PATCH_FILE prüfen
        # ---------------------------------------------------------

        if not patch_file:
            self.append_info(
                info_widget,
                "❌ PATCH_FILE ist nicht konfiguriert!",
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            return False

        # ---------------------------------------------------------
        # STREAMREPO prüfen
        # ---------------------------------------------------------

        if not source_dir:
            self.append_info(
                info_widget,
                (
                    "❌ STREAMREPO ist nicht konfiguriert!\n\n"
                    "Das OSCam-Quellverzeichnis muss über "
                    "STREAMREPO definiert werden."
                ),
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            return False

        # ---------------------------------------------------------
        # Pfade normalisieren
        # ---------------------------------------------------------

        patch_file = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(
                    str(patch_file)
                )
            )
        )

        source_dir = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(
                    str(source_dir)
                )
            )
        )

        # ---------------------------------------------------------
        # Start
        # ---------------------------------------------------------

        update_p(10)

        self.append_info(
            info_widget,
            f"📁 OSCam-Quellverzeichnis:\n{source_dir}",
            "info"
        )

        # ---------------------------------------------------------
        # Patch-Datei prüfen
        # ---------------------------------------------------------

        if not os.path.isfile(
            patch_file
        ):
            msg = self.get_t(
                "patch_file_missing",
                "❌ Patch-Datei fehlt!"
            ).format(
                path=patch_file
            )

            self.append_info(
                info_widget,
                msg,
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            if pbar:
                try:
                    pbar.setFormat(
                        "❌ Datei fehlt"
                    )
                except Exception:
                    pass

            return False

        # ---------------------------------------------------------
        # OSCam-Verzeichnis prüfen
        # ---------------------------------------------------------

        if not os.path.isdir(
            source_dir
        ):
            self.append_info(
                info_widget,
                (
                    "❌ OSCam-Quellverzeichnis nicht gefunden:\n"
                    f"{source_dir}"
                ),
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            return False

        # =========================================================
        # OSCAM QUELLCODE PRÜFEN
        # =========================================================

        required_files = (
            "Makefile",
            "oscam.c",
            "globals.h"
        )

        missing_files = [
            filename
            for filename in required_files
            if not os.path.isfile(
                os.path.join(
                    source_dir,
                    filename
                )
            )
        ]

        if missing_files:
            self.append_info(
                info_widget,
                (
                    "❌ Das Zielverzeichnis enthält keinen "
                    "vollständigen OSCam-Quellcode.\n\n"
                    f"Verzeichnis:\n{source_dir}\n\n"
                    "Fehlende Dateien:\n"
                    + "\n".join(
                        f"• {filename}"
                        for filename in missing_files
                    )
                ),
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            return False

        # ---------------------------------------------------------
        # Logger
        # ---------------------------------------------------------

        def logger(
            text,
            level="info"
        ):
            try:
                self.append_info(
                    info_widget,
                    text,
                    level
                )
            except Exception:
                pass

        # =========================================================
        # STARTMELDUNG
        # =========================================================

        start_msg = self.get_t(
            "executing_git_apply",
            "🚀 Wende Patch an..."
        ).format(
            patch=os.path.basename(
                patch_file
            )
        )

        self.append_info(
            info_widget,
            start_msg,
            "warning"
        )

        self.append_info(
            info_widget,
            f"📁 Ziel: {source_dir}",
            "info"
        )

        self.append_info(
            info_widget,
            f"📄 Patch: {patch_file}",
            "info"
        )

        update_p(40)

        # =========================================================
        # PATCH ANWENDEN
        # =========================================================

        try:

            self.append_info(
                info_widget,
                "🔧 Führe git apply aus...",
                "info"
            )

            code = run_bash(
                f'git apply {patch_file}',
                cwd=source_dir,
                logger=logger,
                lang=lang
            )

            # -----------------------------------------------------
            # ERFOLG
            # -----------------------------------------------------

            if code == 0:

                self.append_info(
                    info_widget,
                    self.get_t(
                        "patch_emu_git_done",
                        "✅ Patch erfolgreich angewendet"
                    ),
                    "success"
                )

                self.append_info(
                    info_widget,
                    f"📁 Gepatchtes Repository:\n{source_dir}",
                    "success"
                )

                update_p(100)

                play_apply_sound(
                    True
                )

                if pbar:
                    try:
                        pbar.setFormat(
                            "✅ Patch angewendet"
                        )
                    except Exception:
                        pass

                return True

            # -----------------------------------------------------
            # GIT APPLY FEHLER
            # -----------------------------------------------------

            self.append_info(
                info_widget,
                self.get_t(
                    "patch_emu_git_apply_failed",
                    "❌ Patch konnte nicht angewendet werden"
                ),
                "error"
            )

            self.append_info(
                info_widget,
                (
                    f"📁 Zielverzeichnis:\n"
                    f"{source_dir}"
                ),
                "error"
            )

            self.append_info(
                info_widget,
                (
                    f"📄 Patch-Datei:\n"
                    f"{patch_file}"
                ),
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            if pbar:
                try:
                    pbar.setFormat(
                        "❌ Fehler beim Patchen"
                    )
                except Exception:
                    pass

            return False

        # =========================================================
        # SCHWERER FEHLER
        # =========================================================

        except Exception as exc:

            self.append_info(
                info_widget,
                (
                    "❌ Schwerer Fehler beim Patchen:\n"
                    f"{exc}"
                ),
                "error"
            )

            update_p(
                100,
                True
            )

            play_apply_sound(
                False
            )

            if pbar:
                try:
                    pbar.setFormat(
                        "❌ Fehler beim Patchen"
                    )
                except Exception:
                    pass

            return False

        # =========================================================
        # ABSCHLUSS
        # =========================================================

        finally:

            try:
                QApplication.processEvents()
            except Exception:
                pass

    def select_ncam_patch_path_manually(self):
        """Wählt ausschließlich den Patch-Ordner für S3-NCam-Bonecrew."""
        from PyQt6.QtWidgets import QMessageBox

        is_de = str(getattr(self, "LANG", "de")).lower()[:2] == "de"
        current = getattr(self, "NCAM_PATCH_PATH", "") or getattr(self, "OLD_PATCH_DIR", os.getcwd())
        title = "S3-NCam-Bonecrew Patch-Ordner auswählen" if is_de else "Select S3-NCam-Bonecrew patch folder"
        directory = QFileDialog.getExistingDirectory(self, title, current)
        if not directory:
            return
        directory = os.path.normpath(directory)
        if not isinstance(getattr(self, "cfg", None), dict):
            self.cfg = {}
        saved = save_config({"ncam_patch_path": directory}, gui_instance=self, silent=True)
        if saved is False:
            QMessageBox.warning(
                self, "Fehler" if is_de else "Error",
                ("Der S3-NCam-Patch-Pfad konnte nicht gespeichert werden:\n" if is_de else "Could not save the S3-NCam patch path:\n") + directory,
            )
            return
        self.NCAM_PATCH_PATH = directory
        self.cfg["ncam_patch_path"] = directory
        QMessageBox.information(
            self, "Pfad gespeichert" if is_de else "Path saved",
            ("S3-NCam-Patch-Pfad wurde gespeichert:\n" if is_de else "S3-NCam patch path was saved:\n") + directory,
        )

    def select_s4_patch_path_manually(self):
        """Wählt ausschließlich den Patch-Ordner für S4."""
        from PyQt6.QtWidgets import QMessageBox

        is_de = str(getattr(self, "LANG", "de")).lower()[:2] == "de"
        current = getattr(self, "S4_PATCH_PATH", "") or getattr(self, "OLD_PATCH_DIR", os.getcwd())
        title = "S4 Patch-Ordner auswählen" if is_de else "Select S4 patch folder"
        directory = QFileDialog.getExistingDirectory(self, title, current)
        if not directory:
            return
        directory = os.path.normpath(directory)
        if not isinstance(getattr(self, "cfg", None), dict):
            self.cfg = {}
        saved = save_config({"s4_patch_path": directory}, gui_instance=self, silent=True)
        if saved is False:
            QMessageBox.warning(
                self, "Fehler" if is_de else "Error",
                ("Der S4-Patch-Pfad konnte nicht gespeichert werden:\n" if is_de else "Could not save the S4 patch path:\n") + directory,
            )
            return
        self.S4_PATCH_PATH = directory
        self.cfg["s4_patch_path"] = directory
        QMessageBox.information(
            self, "Pfad gespeichert" if is_de else "Path saved",
            ("S4-Patch-Pfad wurde gespeichert:\n" if is_de else "S4 patch path was saved:\n") + directory,
        )

    def copy_patch_to_target(self, target):
        """Kopiert oscam-emu.patch in den gewählten S3-NCam- oder S4-Ordner."""
        import os
        import shutil
        from PyQt6.QtWidgets import QMessageBox
        from paths import PATCH_FILE as CONFIG_PATCH_FILE

        is_de = str(getattr(self, "LANG", "de")).lower()[:2] == "de"

        # Patch-Quelldatei ermitteln
        source = (
            getattr(self, "PATCH_FILE", None)
            or globals().get("PATCH_FILE")
            or CONFIG_PATCH_FILE
        )
        source = os.path.abspath(
            os.path.expanduser(
                os.path.expandvars(str(source))
            )
        )

        # Gespeicherte Konfiguration lesen
        cfg = getattr(self, "cfg", {})
        if not isinstance(cfg, dict):
            cfg = {}

        # Zielordner ermitteln
        if target == "ncam":
            destination_dir = (
                getattr(self, "NCAM_PATCH_PATH", None)
                or globals().get("NCAM_PATCH_PATH")
                or cfg.get("ncam_patch_path", "")
            )
            label = "S3-NCam-Bonecrew"

        elif target == "s4":
            destination_dir = (
                getattr(self, "S4_PATCH_PATH", None)
                or globals().get("S4_PATCH_PATH")
                or cfg.get("s4_patch_path", "")
            )
            label = "S4"

        else:
            return

        destination_dir = (
            os.path.abspath(
                os.path.expanduser(
                    os.path.expandvars(str(destination_dir))
                )
            )
            if destination_dir else ""
        )

        # Quelldatei prüfen
        if not os.path.isfile(source):
            QMessageBox.warning(
                self,
                "Patch fehlt" if is_de else "Patch missing",
                f"Die Quelldatei wurde nicht gefunden:\n{source}"
                if is_de else
                f"The patch file was not found:\n{source}",
            )
            return

        # Zielordner prüfen
        if not destination_dir:
            QMessageBox.warning(
                self,
                "Pfad fehlt" if is_de else "Path missing",
                f"Bitte zuerst den Zielordner für {label} auswählen."
                if is_de else
                f"Please select the destination folder for {label} first.",
            )
            return

        if not os.path.isdir(destination_dir):
            QMessageBox.warning(
                self,
                "Ordner fehlt" if is_de else "Folder missing",
                f"Der Zielordner existiert nicht:\n{destination_dir}"
                if is_de else
                f"The destination folder does not exist:\n{destination_dir}",
            )
            return

        try:
            destination = os.path.join(
                destination_dir, "oscam-emu.patch"
            )

            # Backup der vorhandenen Datei anlegen
            if os.path.isfile(destination):
                shutil.copy2(destination, destination + ".bak")

            shutil.copy2(source, destination)

            message = (
                f"Patch erfolgreich nach {label} kopiert:\n{destination}"
            )
            self.append_info(
                getattr(self, "info_text", None),
                f"✅ {message}",
                "success",
            )

            QMessageBox.information(
                self,
                "Patch kopiert" if is_de else "Patch copied",
                message if is_de else
                f"Patch successfully copied to {label}:\n{destination}",
            )

        except Exception as exc:
            self.append_info(
                getattr(self, "info_text", None),
                f"❌ Patch-Kopie fehlgeschlagen: {exc}",
                "error",
            )
            QMessageBox.critical(
                self,
                "Fehler" if is_de else "Error",
                f"Patch konnte nicht kopiert werden:\n{exc}"
                if is_de else
                f"Could not copy patch:\n{exc}",
            )


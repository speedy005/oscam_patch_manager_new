"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()
from PyQt6.QtCore import pyqtSlot


class PatchManagerInstallationMixin:
    """Patch Manager Installation"""

    def on_s3_repository_changed(self, repo_name):
        try:
            if repo_name not in self.s3_repository_options:
                return

            self.selected_s3_repository = repo_name

            if not isinstance(getattr(self, "current_config", None), dict):
                self.current_config = load_config()

            self.current_config["s3_repository_name"] = repo_name

            success = save_config(
                {"s3_repository_name": repo_name},
                gui_instance=self,
                silent=True
            )

            if not success:
                print("Fehler: S3-Repository konnte nicht gespeichert werden.")

        except Exception as exc:
            import traceback
            print(f"Fehler bei der S3-Git-Auswahl: {exc}")
            traceback.print_exc()

    def start_s3_installation(self):
        repo_name = self.s3_repo_combo.currentText()
        repo_url = self.s3_repo_combo.currentData()

        if not repo_url:
            QMessageBox.warning(
                self,
                "S3-Installation",
                "Bitte wählen Sie ein Git-Repository aus.",
            )
            return

        if (
            self.s3_install_worker is not None
            and self.s3_install_worker.isRunning()
        ):
            QMessageBox.information(
                self,
                "S3-Installation",
                "Eine S3-Installation läuft bereits.",
            )
            return

        self.selected_s3_repository = repo_name
        self.current_config["s3_repository_name"] = repo_name

        try:
            save_config(self.current_config)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Konfiguration",
                f"Auswahl konnte nicht gespeichert werden:\n{e}",
            )

        # Build-Log für genau diesen S3-Start vorbereiten. Der S3-Button
        # startet S3InstallWorker (kein externes Terminal über open_terminal);
        # deshalb müssen die vom Worker gesendeten Log-Signale hier in eine
        # Datei geschrieben werden.
        try:
            log_dir = getattr(self, "build_log_dir", None)
            if not log_dir:
                log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
                os.makedirs(log_dir, exist_ok=True)
                self.build_log_dir = log_dir
            else:
                os.makedirs(log_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.s3_build_log_file = os.path.join(log_dir, f"S3_build_{stamp}.log")
            with open(self.s3_build_log_file, "w", encoding="utf-8") as log_file:
                log_file.write(f"S3 Build-Log gestartet: {datetime.now().isoformat(timespec='seconds')}\n")
                log_file.write(f"Repository: {repo_name}\nURL: {repo_url}\nZielpfad: {self.S3_PATH}\n\n")
            print(f"[BUILD-LOG] S3-Logdatei: {self.s3_build_log_file}")
        except Exception as log_error:
            self.s3_build_log_file = None
            print(f"[BUILD-LOG] S3-Logdatei konnte nicht erstellt werden: {log_error}")

        self.s3_install_worker = S3InstallWorker(
            base_target_dir=self.S3_PATH,
            repo_url=repo_url,
            project_name=repo_name,
        )

        self.s3_install_worker.finished_signal.connect(
            self.on_s3_install_finished
        )

        self.s3_install_worker.log_signal.connect(
            self.append_s3_install_log
        )

        self.s3_install_worker.start()

    def on_s3_install_finished(self, success, message):
        if success:
            QMessageBox.information(
                self,
                "S3-Installation erfolgreich",
                message,
            )
        else:
            QMessageBox.critical(
                self,
                "S3-Installationsfehler",
                message,
            )

        self.update_ui_texts()

    def append_s3_install_log(self, message):
        """Zeigt Worker-Meldungen an und schreibt sie in das aktive S3-Log."""
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [S3] {message}"
        print(line)
        log_path = getattr(self, "s3_build_log_file", None)
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8", errors="replace") as log_file:
                    log_file.write(line + "\n")
                    log_file.flush()
            except OSError as log_error:
                print(f"[BUILD-LOG] Schreiben fehlgeschlagen ({log_path}): {log_error}")

    @pyqtSlot(str)
    def _system_check_append_html(self, fragment):
        """Append one worker result to the large info screen on the GUI thread."""
        if not fragment:
            return

        widget = getattr(self, "info_text", None)
        if widget is None:
            return

        buffer = getattr(self, "_system_check_html", None)
        if buffer is None:
            buffer = []
            self._system_check_html = buffer
        buffer.append(fragment)

        # Append only the new fragment. Replacing the complete document with
        # setHtml() for every worker signal can cause later status rows to be
        # lost when fragments contain independent HTML blocks/styles.
        # This slot is invoked in the GUI thread through the queued Qt signal.
        try:
            cursor = widget.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertHtml(fragment)
            widget.setTextCursor(cursor)
            widget.ensureCursorVisible()
        except Exception as exc:
            # Safe fallback keeps diagnostics visible if rich-text insertion
            # fails for an unusual fragment.
            print(f"[system-check] HTML-Ausgabe fehlgeschlagen: {exc}")
            widget.append(fragment)

    @pyqtSlot(int, str)
    def _system_check_update_progress(self, value, text):
        """Update the progress bar safely from the GUI thread."""
        pbar = getattr(self, "progress_bar", None)
        if pbar is None:
            return
        value = max(0, min(100, int(value)))
        pbar.setValue(value)
        pbar.setFormat(f"{text}   %p%")

    @pyqtSlot(str)
    def _system_check_append_error(self, message):
        """Display worker errors in the same info screen as the check output."""
        safe_message = (str(message).replace("&", "&amp;")
                        .replace("<", "&lt;").replace(">", "&gt;"))
        self._system_check_append_html(
            "<br><div style='text-align:center;color:#FF0000;"
            "font-family:Arial Black;font-size:18pt;'>"
            f"❌ System Check Error:<br>{safe_message}</div>"
        )
        self._system_check_had_error = True

    def run_full_system_check(self, clear_log=True):
        """
        Startet den Systemcheck ohne die GUI zu blockieren.

        Alle langsamen/blockierenden Operationen laufen im Worker-Thread.
        Die GUI wird ausschließlich über Qt-Signale aktualisiert.
        """

        from PyQt6.QtCore import QThread

        # ------------------------------------------------------------
        # Doppelstart verhindern
        # ------------------------------------------------------------

        if getattr(self, "_checking_active", False):
            return

        self._checking_active = True
        self.is_loading = True

        # ------------------------------------------------------------
        # UI vorbereiten
        # ------------------------------------------------------------

        if hasattr(self, "hide_final_label"):
            try:
                self.hide_final_label()
            except Exception:
                pass
        elif hasattr(self, "final_label"):
            try:
                if self.final_label:
                    self.final_label.hide()
            except Exception:
                pass

        if clear_log and hasattr(self, "log_window"):
            try:
                self.log_window.clear()
            except Exception:
                pass

        widget = getattr(self, "info_text", None)
        pbar = getattr(self, "progress_bar", None)

        if widget is None:
            self.is_loading = False
            self._checking_active = False
            return

        # ------------------------------------------------------------
        # Progressbar
        # ------------------------------------------------------------

        if pbar:

            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setTextVisible(True)

            pbar.setStyleSheet(
                """
                QProgressBar {
                    border: 2px solid #444444;
                    border-radius: 8px;
                    background-color: #0A0A0A;
                    color: black;
                    text-align: center;
                    font-weight: 900;
                    font-size: 20px;
                    min-height: 35px;
                }

                QProgressBar::chunk {
                    background-color: qlineargradient(
                        spread:pad,
                        x1:0,
                        y1:0,
                        x2:1,
                        y2:0,
                        stop:0 #FF00FF,
                        stop:0.5 #00FFFF,
                        stop:1 #39FF14
                    );
                    border-radius: 6px;
                }
                """
            )

            pbar.setFormat(
                "🚀 Initialisiere System...   %p%"
            )
            pbar.show()

        # ------------------------------------------------------------
        # Info-Widget leeren
        # ------------------------------------------------------------

        if clear_log:
            widget.setHtml("")

        # ------------------------------------------------------------
        # HTML-Puffer und Startstatus
        # ------------------------------------------------------------

        self._system_check_html = []
        self._system_check_had_error = False
        self._system_check_append_html(
            "<div style='text-align:center;color:#00ADFF;"
            "font-family:Arial,sans-serif;font-size:16pt;font-weight:bold;'>"
            "Systemstartprüfung wird ausgeführt …</div>"
        )

        # ------------------------------------------------------------
        # Worker / Thread erstellen
        # ------------------------------------------------------------

        self._system_check_thread = QThread(self)

        # ------------------------------------------------------------
        # Eingestellte Repo-URL aus deiner Anwendung holen
        #
        # Passe die Attributnamen hier nur an, falls deine URL anders
        # gespeichert wird.
        # ------------------------------------------------------------

        repo_url = ""

        possible_repo_attributes = (
            "repo_url",
            "repository_url",
            "github_repo_url",
            "REPO_URL",
            "GITHUB_REPO_URL",
            "repo",
        )

        for attr_name in possible_repo_attributes:

            try:
                value = getattr(
                    self,
                    attr_name,
                    "",
                )

                if isinstance(value, str) and value.strip():
                    repo_url = value.strip()
                    break

            except Exception:
                pass

        # ------------------------------------------------------------
        # Worker
        # ------------------------------------------------------------

        self._system_check_worker = SystemCheckWorker(
            lang=getattr(
                self,
                "LANG",
                "de",
            ),
            repo_url=repo_url,
        )

        self._system_check_worker.moveToThread(
            self._system_check_thread
        )

        # ------------------------------------------------------------
        # Signale
        # ------------------------------------------------------------

        # Connect to QObject slots (rather than local closures) so Qt queues
        # every widget update from the worker thread onto the GUI thread.
        self._system_check_worker.html.connect(self._system_check_append_html)
        self._system_check_worker.progress.connect(self._system_check_update_progress)
        self._system_check_worker.error.connect(self._system_check_append_error)

        self._system_check_worker.finished.connect(
            self._system_check_finished
        )

        # ------------------------------------------------------------
        # Worker nach Beendigung aufräumen
        # ------------------------------------------------------------

        self._system_check_worker.finished.connect(
            self._system_check_thread.quit
        )

        self._system_check_worker.finished.connect(
            self._system_check_worker.deleteLater
        )

        self._system_check_thread.finished.connect(
            self._system_check_thread.deleteLater
        )

        # ------------------------------------------------------------
        # Thread starten
        # ------------------------------------------------------------

        self._system_check_thread.started.connect(
            self._system_check_worker.run
        )
        if hasattr(self, "sound_manager"):
            self.sound_manager.play_start()

        self._system_check_thread.start()

    def _system_check_finished(self):
        """
        Wird nach erfolgreichem oder fehlerhaftem Worker-Ende
        im GUI-Thread ausgeführt.
        """
        if (
            not getattr(self, "_system_check_had_error", False)
            and hasattr(self, "sound_manager")
        ):
            self.sound_manager.play_success()
        pbar = getattr(
            self,
            "progress_bar",
            None,
        )

        if pbar:
            pbar.setValue(100)

            is_de = (
                getattr(
                    self,
                    "LANG",
                    "de",
                ).lower()
                == "de"
            )

            pbar.setFormat(
                (
                    "✅ System Check abgeschlossen ✔   %p%"
                    if is_de
                    else
                    "✅ System check completed ✔   %p%"
                )
            )

        # ------------------------------------------------------------
        # Status zurücksetzen
        # ------------------------------------------------------------

        self.is_loading = False
        self._checking_active = False

        # ------------------------------------------------------------
        # Vorhandene Update-Prüfung beibehalten
        #
        # Wichtig:
        # Sie läuft jetzt NACH dem Systemcheck.
        # ------------------------------------------------------------

        try:
            self.check_for_update_on_start()
        except Exception as e:
            widget = getattr(
                self,
                "info_text",
                None,
            )

            if widget:
                widget.append(
                    "<br>"
                    "<span style='"
                    "color:#F57A08;"
                    "font-weight:bold;"
                    "'>"
                    f"⚠️ Update check: {e}"
                    "</span>"
                )

        # ------------------------------------------------------------
        # Referenzen behalten wir bis zum Thread-Ende.
        # Danach können sie freigegeben werden.
        # ------------------------------------------------------------

        try:
            thread = getattr(
                self,
                "_system_check_thread",
                None,
            )

            if thread and not thread.isRunning():
                self._system_check_thread = None
                self._system_check_worker = None

        except Exception:
            pass

    def fix_all_tool_permissions(self, **kwargs):
        """Setzt rekursiv Schreibrechte mit ProgressBar, Sound und Sprachprüfung."""
        import os
        from PyQt6.QtWidgets import QApplication

        # --- START SOUND & SPRACHE ---
        if "safe_play" in globals():
            safe_play("dialog-information.oga")

        # Aktuelle Sprache live ermitteln
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        
        base_path = os.path.dirname(os.path.realpath(__file__))
        pbar = getattr(self, "progress_bar", None)

        start_msg = f"<b>🔧 Starte Rechte-Reparatur in:</b> {base_path}" if is_de else f"<b>🔧 Starting permission fix in:</b> {base_path}"
        if hasattr(self, "info_text"):
            self.info_text.append(start_msg)
        QApplication.processEvents()

        # 1. Dateien zählen (mit Ausschluss von .git für Speed & Stabilität)
        all_items = []
        exclude_dirs = {".git", "__pycache__", ".github"}
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Verzeichnisse im Set ausschließen
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for name in dirs + files:
                    all_items.append(os.path.join(root, name))
                
                QApplication.processEvents() # Verhindert "Keine Rückmeldung"
        except Exception as e:
            if hasattr(self, "info_text"):
                self.info_text.append(f"<span style='color:red'>Error: {e}</span>")

        total = len(all_items)
        if total == 0:
            if pbar: pbar.hide()
            return

        # 2. Rechte setzen
        count = 0
        for path in all_items:
            try:
                # 0o777 für Ordner, 0o666 für Dateien
                os.chmod(path, 0o777 if os.path.isdir(path) else 0o666)
                count += 1
                
                # Progress Update
                if pbar and count % 2 == 0:
                    val = int((count / total) * 100)
                    pbar.setValue(val)
                    msg = "Fixe Rechte..." if is_de else "Fixing perms..."
                    pbar.setFormat(f"🔐 {msg} {val}%")
                    QApplication.processEvents() 
            except:
                continue

        # 3. ABSCHLUSS
        if pbar:
            pbar.setValue(100)
            pbar.setFormat("✅ Rechte fixiert!" if is_de else "✅ Rights fixed!")
        
        if "safe_play" in globals():
            safe_play("complete.oga")

        final_msg = f"✅ Fertig! {count} Objekte angepasst." if is_de else f"✅ Done! {count} objects adjusted."
        if hasattr(self, "info_text"):
            self.info_text.append(f"<span style='color:#39FF14'><b>{final_msg}</b></span>")
            self.info_text.ensureCursorVisible()

    def check_ncam_updates(self):
        """
        Startet den Update-Check für NCam Bonecrew.
        Arbeitet plattformübergreifend (Linux/Windows) mit NCAM_PATH.
        """
        import os

        # Remote Git-URL (Beispiel)
        ncam_git_url = "https://github.com/speedy005/NCam-speedy_dany"

        # Lokaler Pfad
        local_path = getattr(self, "NCAM_PATH", "/opt/s3_ncam_bonecrew_test")
        if not os.path.exists(local_path):
            print(f"[NCAM] Lokaler Pfad existiert nicht: {local_path}")
            return

        # Worker starten (OSCUpdateWorker plattformunabhängig implementiert)
        self.ncam_update_worker = OSCamUpdateWorker(ncam_git_url, local_path)
        self.ncam_update_worker.status_signal.connect(self.on_ncam_update_status)
        self.ncam_update_worker.start()

    def on_ncam_update_status(self, update_available, remote_hash):
        """Reagiert auf das Ergebnis des NCam-Update-Checks."""
        from PyQt6.QtWidgets import QPushButton

        btn = getattr(self, "btn_ncam", None)
        if not btn:
            return

        if update_available:
            print(f"[NCAM] Update verfügbar! Neuer Hash: {remote_hash[:7]}")
            btn.setText("🚀 NCam Update!")
            btn.setStyleSheet(
                "background-color: orange; color: black; font-weight: bold; border-radius: 8px;"
            )
        else:
            print("[NCAM] Aktuell.")
            btn.setText("NCam OK")
            btn.setStyleSheet(
                "background-color: #00FF00; color: black; font-weight: bold; border-radius: 8px;"
            )

        # Auch nach einer asynchronen NCam-Statusänderung gilt das ausgewählte
        # Farbschema für alle Buttons; der Status-Text bleibt dabei erhalten.
        try:
            if hasattr(self, "apply_global_button_style"):
                self.apply_global_button_style()
        except Exception as exc:
            print(f"[NCAM] Globales Button-Theme konnte nicht angewendet werden: {exc}")

        # Animation beenden, ohne einen zusätzlichen Ton auszulösen
        def finish_blink():
            if sound_manager:
                sound_manager.revision_timer.stop()

        QTimer.singleShot(2200, finish_blink)


        # Sound erst nach Abschluss der Animation stoppen
        def finish_blink():
            if sound_manager:
                sound_manager.stop_revision_blink_sound()

        QTimer.singleShot(2200, finish_blink)

    def hide_final_label(self):
        """Blendet das finale Status-Label aus."""
        if hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
            from PyQt6.QtWidgets import QApplication

            QApplication.processEvents()

    def auto_detect_ncam_path(self):
        """Sucht den NCam Bonecrew Pfad automatisch auf Linux & Windows."""
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        is_win = platform.system() == "Windows"
        project = "s3_ncam_bonecrew_test"
    
        # Basis-Pfade definieren
        if is_win:
            base_candidates = ["C:\\opt", "D:\\opt", os.path.expanduser("~")]
        else:
            base_candidates = ["/opt", os.path.expanduser("~")]

        search_paths = [os.path.join(b, project) for b in base_candidates]
        search_paths.append(os.getcwd()) # Aktuelles Verzeichnis einbeziehen

        # Suche nach der 's3' Datei (mit .exe unter Windows)
        binary = "s3.exe" if is_win else "s3"
    
        for p in search_paths:
            full_binary_path = os.path.normpath(os.path.join(p, binary))
            if os.path.exists(full_binary_path):
                self.NCAM_PATH = os.path.normpath(p)
                print(f"[AUTO-DETECT] NCam gefunden: {self.NCAM_PATH}")
                return True
            
        print("[AUTO-DETECT] NCam konnte nicht gefunden werden.")
        return False

    def auto_detect_s3_path(self):
        """Sucht S3 Installation automatisch auf Linux & Windows."""
        is_win = platform.system() == "Windows"
        binary = "s3.exe" if is_win else "s3"

        # Standard-Installationsorte
        if is_win:
            candidates = ["C:\\s3", "C:\\opt\\s3", os.path.join(os.path.expanduser("~"), "s3")]
        else:
            candidates = ["/opt/s3", "/usr/local/bin", "/usr/bin", os.path.expanduser("~/s3")]

        for c in candidates:
            # 1. Pfad ist ein Ordner, der die Binary enthält
            if os.path.isdir(c) and os.path.exists(os.path.join(c, binary)):
                self.S3_PATH = os.path.normpath(c)
                return True
            # 2. Pfad ist direkt die Binary selbst
            if os.path.isfile(c) and (c.endswith(binary)):
                self.S3_PATH = os.path.normpath(os.path.dirname(c))
                return True

        return False

    def auto_detect_s4_path(self):
        """Sucht SimpleBuild 4 Installation automatisch auf Linux & Windows."""
        is_win = platform.system() == "Windows"
        binary = "s4.exe" if is_win else "s4"

        # Standard-Installationsorte für SimpleBuild 4
        if is_win:
            candidates = [
                "C:\\simplebuild4", 
                "C:\\opt\\simplebuild4", 
                os.path.join(os.path.expanduser("~"), "simplebuild4")
            ]
        else:
            candidates = [
                "/opt/simplebuild4", 
                "/usr/local/bin", 
                "/usr/bin", 
                os.path.expanduser("~/simplebuild4")
            ]

        for c in candidates:
            # 1. Pfad ist ein Ordner, der die Binary enthält
            if os.path.isdir(c) and os.path.exists(os.path.join(c, binary)):
                self.S4_PATH = os.path.normpath(c)
                return True
            # 2. Pfad ist direkt die Binary selbst
            if os.path.isfile(c) and (c.endswith(binary)):
                self.S4_PATH = os.path.normpath(os.path.dirname(c))
                return True

        return False

    def find_existing_path(possible_paths):
        """Prüft eine Liste von Pfaden und gibt den ersten existierenden zurück."""
        import os

        for path in possible_paths:
            try:
                # Prüft, ob der Pfad existiert
                if os.path.exists(path):
                    # Wenn es ein Verzeichnis ist, prüfen ob es Dateien enthält
                    if os.path.isdir(path):
                        if os.listdir(path):
                            return path
                    # Wenn es eine Datei ist, direkt zurückgeben
                    else:
                        return path
            except Exception:
                continue
        return None

    def select_ncam_path_manually(self):
        """Dialog zur manuellen Auswahl des NCam Bonecrew Pfads."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os, platform

        lang = getattr(self, "LANG", "de").lower()[:2]
        t = {
            "de": {
                "hint": "NCam Bonecrew Ordner wählen", 
                "ok": "NCam Pfad gesetzt", 
                "err": "Datei 's3' nicht im Ordner gefunden!"
            },
            "en": {
                "hint": "Select NCam Bonecrew folder", 
                "ok": "NCam path set", 
                "err": "File 's3' not found in the selected folder!"
            },
        }.get(lang, {"hint": "Select NCam Bonecrew folder", "ok": "NCam path set", "err": "File 's3' not found!"})

        is_win = platform.system() == "Windows"
        default_start = "C:\\opt\\ncam" if is_win else "/opt/s3_ncam_bonecrew"
        start_path = getattr(self, "NCAM_PATH", default_start)
        
        chosen_dir = QFileDialog.getExistingDirectory(self, t["hint"], start_path)
        if not chosen_dir:
            return

        chosen_dir = os.path.normpath(chosen_dir)
        sub_folder = "s3_ncam_bonecrew"

        # KORREKTUR: Flexibler Check für Windows (s3 und s3.exe abdecken)
        possible_exes = ["s3", "s3.exe"] if is_win else ["s3"]
        exists = False

        for exe in possible_exes:
            path_direct = os.path.join(chosen_dir, exe)
            path_sub = os.path.join(chosen_dir, sub_folder, exe)

            if os.path.exists(path_direct) or os.path.exists(path_sub):
                # Wenn der User den Basis-Ordner gewählt hat, hängen wir den Unterordner an
                if os.path.exists(path_sub) and not chosen_dir.lower().endswith(sub_folder.lower()):
                    chosen_dir = os.path.join(chosen_dir, sub_folder)
                exists = True
                break

        if exists:
            self.NCAM_PATH = os.path.normpath(chosen_dir)
            save_config({"ncam_custom_path": self.NCAM_PATH}, gui_instance=self)
            
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()
                
            QMessageBox.information(self, "OK", f"{t['ok']}:\n{self.NCAM_PATH}")
        else:
            QMessageBox.warning(self, "Error", t["err"])

    def start_ncam_install(self):
        """Startet die NCam Installation."""
        from PyQt6.QtWidgets import QFileDialog
        import os, platform
        
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        is_de = getattr(self, "LANG", "de") == "de"
        default_start = "C:\\" if platform.system() == "Windows" else "/opt"
        start_path = getattr(self, "NCAM_PATH", default_start)

        chosen_dir = QFileDialog.getExistingDirectory(
            self, 
            "Installationsordner wählen" if is_de else "Select Installation Folder",
            start_path
        )

        if not chosen_dir:
            return 

        self.NCAM_PATH = os.path.normpath(chosen_dir)
    
        try:
            os.makedirs(self.NCAM_PATH, exist_ok=True)
            self.btn_ncam.setEnabled(False)
            self.btn_ncam.setText("⏳ ..." if is_de else "⏳ Busy...")

            # Nutzt den dedizierten NCam-Worker
            self.ncam_worker = NcamBonecrewInstallWorker(self.NCAM_PATH)
            self.ncam_worker.finished_signal.connect(self.on_ncam_finished)
            self.ncam_worker.start()
        except Exception as e:
            self.on_ncam_finished(False, f"Fehler beim Erstellen des Ordners: {str(e)}")

    def on_ncam_finished(self, success, message):
        """Nach Abschluss des Workers für NCam."""
        import os
        from PyQt6.QtWidgets import QMessageBox

        is_de = getattr(self, "LANG", "de") == "de"
        self.btn_ncam.setEnabled(True)

        if success:
            # 1. Pfad-Logik: Der Worker nutzt jetzt "s3_ncam_bonecrew"
            sub_folder = "s3_ncam_bonecrew"
            
            # Wir prüfen, ob der aktuelle NCAM_PATH den Unterordner bereits enthält
            current_base = getattr(self, "NCAM_PATH", "")
            if not current_base.lower().endswith(sub_folder.lower()):
                new_path = os.path.normpath(os.path.join(current_base, sub_folder))
            else:
                new_path = os.path.normpath(current_base)

            # 2. Instanz-Variable und Config permanent aktualisieren
            self.NCAM_PATH = new_path
            # Speichert den Pfad in der json, damit er beim nächsten Start direkt da ist
            save_config({"ncam_custom_path": self.NCAM_PATH}, gui_instance=self)

            # 3. Visuelles Feedback bei Erfolg
            self.btn_ncam.setStyleSheet(
                """
                QPushButton {
                    background-color: green;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    text-align: center;
                }
                """
            )
            self.btn_ncam.setText("✅ Fertig" if is_de else "✅ Done")

            # UI-Texte aktualisieren, falls die Funktion existiert
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()

            QMessageBox.information(
                self,
                "NCam Installation" if is_de else "NCam Setup",
                f"{message}\n\nPfad: {self.NCAM_PATH}"
                if is_de
                else f"{message}\n\nPath: {self.NCAM_PATH}"
            )
        else:
            # Fehler-Zustand: Roter Button
            self.btn_ncam.setStyleSheet(
                """
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                    border-radius: 5px;
                    text-align: center;
                }
                """
            )
            self.btn_ncam.setText("❌ Fehler" if is_de else "❌ Error")

            QMessageBox.critical(
                self,
                "NCam Installation" if is_de else "NCam Setup",
                message
            )

            # Standard-Buttontext wiederherstellen
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()

    def select_s4_path_manually(self, pos=None):
        """
        Dialog zur manuellen Auswahl des SimpleBuild 4 Pfads.
        Validiert flexibel auf 'simplebuild' und setzt den Pfad direkt auf den Zielordner.
        """
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os, platform

        lang = getattr(self, "LANG", "de").lower()[:2]
        t = {
            "de": {
                "hint": "SimpleBuild 4 Ordner wählen", 
                "ok": "S4 Pfad gesetzt",
                "err_title": "Fehler",
                "err_msg": "Die ausführbare S4-Datei wurde in diesem Ordner nicht gefunden!"
            },
            "en": {
                "hint": "Select S4 folder", 
                "ok": "S4 path set",
                "err_title": "Error",
                "err_msg": "The executable S4 file was not found in this folder!"
            },
        }.get(lang, {
            "hint": "Select SimpleBuild 4 folder", 
            "ok": "S4 path set",
            "err_title": "Error",
            "err_msg": "The executable S4 file was not found in this folder!"
        })

        is_win = platform.system() == "Windows"

        # Startpfad ermitteln (Fallback auf sinnvollen OS-Standard)
        default_start = "C:\\opt" if is_win else "/opt"
        start_path = getattr(self, "S4_PATH", default_start)
        if not os.path.exists(start_path):
            start_path = os.path.expanduser("~")

        chosen_dir = QFileDialog.getExistingDirectory(self, t["hint"], start_path)

        if not chosen_dir:
            return  # Abbruch durch den Nutzer

        chosen_dir = os.path.normpath(chosen_dir)
        sub_folder = "simplebuild4"
        possible_exes = ["simplebuild", "simplebuild.exe", "s4", "s4.exe"]
        
        final_path = None

        # Schleife prüft beide Ebenen separat
        for exe in possible_exes:
            path_direct = os.path.join(chosen_dir, exe)
            path_sub = os.path.join(chosen_dir, sub_folder, exe)
            
            # Fall A: User steht direkt im Ordner 'simplebuild4'
            if os.path.exists(path_direct):
                final_path = chosen_dir
                break
            # Fall B: User hat den übergeordneten Ordner gewählt
            elif os.path.exists(path_sub):
                final_path = os.path.join(chosen_dir, sub_folder)
                break

        if final_path:
            # Wir erzwingen, dass der Pfad sauber im Speicher landet
            self.S4_PATH = os.path.normpath(final_path)
            
            # Zentrales Speichern in der Config
            if "save_config" in globals():
                save_config({"s4_custom_path": self.S4_PATH}, gui_instance=self, silent=True)
                
            # UI direkt aktualisieren, damit der Button sofort grün wird ("S4 OK")
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()
                
            QMessageBox.information(self, "OK", f"{t['ok']}:\n{self.S4_PATH}")
        else:
            QMessageBox.warning(self, t["err_title"], t["err_msg"])

    def start_s4_install(self):
        """Startet die SimpleBuild 4 Installation über Worker, Pfad wählbar und OS-optimiert."""
        import os, platform
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        is_de = getattr(self, "LANG", "de") == "de"
        is_win = platform.system() == "Windows"

        # 1. Intelligenten Startpfad für den Dialog wählen
        # Falls S4_PATH noch nicht gesetzt ist, nehmen wir einen sinnvollen Standard
        default_base = "C:\\opt" if is_win else "/opt"
        start_path = getattr(self, "S4_PATH", os.path.expanduser("~"))
    
        # Falls der aktuelle Pfad nicht existiert, nimm die Basis
        if not os.path.exists(start_path):
            start_path = default_base if os.path.exists(default_base) else os.path.expanduser("~")

        chosen_dir = QFileDialog.getExistingDirectory(
            self,
            "Wähle S4 Installationsordner" if is_de else "Select S4 Installation Folder",
            start_path,
        )

        if not chosen_dir:
            return  # Abbruch durch Nutzer

        # --- WINDOWS & VM FIX: Pfad normalisieren ---
        # Macht aus / und \ den jeweils richtigen Trenner für das OS
        self.S4_PATH = os.path.normpath(chosen_dir)

        try:
            # Ordner erstellen (Dank deines Admin-Elevators klappt das auch auf C:\)
            os.makedirs(self.S4_PATH, exist_ok=True)
        
            # Test-Schreibzugriff (nur um sicherzugehen)
            test_file = os.path.join(self.S4_PATH, ".permissions_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Keine Schreibrechte in diesem Ordner!\n{str(e)}" if is_de 
                else f"No write permissions in this folder!\n{str(e)}"
            )
            return

        # 🚨 FIX: Den neu gewählten Pfad sofort dauerhaft in der config.json sichern 🚨
        if "save_config" in globals():
            save_config({"s4_custom_path": self.S4_PATH}, gui_instance=self, silent=True)

        # 2. UI Feedback mit korrekter deutscher Übersetzung
        self.btn_s4.setEnabled(False)
        busy_text = "⏳ Installation läuft..." if is_de else "⏳ Installing..."
        self.btn_s4.setText(busy_text)
    
        if hasattr(self, "log"): # Falls deine GUI eine Log-Funktion hat
           self.log("s4_patch_create_clone_start", "info") 

        # 3. Worker starten
        self.s4_worker = S4InstallWorker(self.S4_PATH)
        self.s4_worker.finished_signal.connect(self.on_s4_finished)
        self.s4_worker.start()

    def on_s4_finished(self, success, message):
        """Nach Abschluss des Workers für SimpleBuild 4."""
        import os
        from PyQt6.QtWidgets import QMessageBox

        is_de = getattr(self, "LANG", "de") == "de"
        self.btn_s4.setEnabled(True)

        if success:
            # 1. Pfad-Logik: Der Worker hat den spezifischen Unterordner erstellt
            sub_folder = "simplebuild4"
            
            # Wir prüfen, ob der aktuelle S4_PATH den Unterordner bereits enthält
            current_base = getattr(self, "S4_PATH", "")
            if not current_base.lower().endswith(sub_folder.lower()):
                new_path = os.path.normpath(os.path.join(current_base, sub_folder))
            else:
                new_path = os.path.normpath(current_base)

            # 2. Instanz-Variable und Config permanent aktualisieren
            self.S4_PATH = new_path
            # Speichert den Pfad in der json, damit er beim nächsten Start direkt da ist
            if "save_config" in globals():
                save_config({"s4_custom_path": self.S4_PATH}, gui_instance=self, silent=True)
            
            # 3. Visuelles Feedback über die zentrale UI-Logik steuern
            # Das sorgt für den korrekten "S4 OK" Text und das perfekte grüne Design
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()

            QMessageBox.information(
                self, 
                "S4 Installation" if is_de else "S4 Setup", 
                f"{message}\n\nPfad: {self.S4_PATH}" if is_de else f"{message}\n\nPath: {self.S4_PATH}"
            )
        else:
            # Fehler-Zustand: Wir updaten das UI, damit der Button orange bleibt (bereit für neuen Versuch)
            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()
                
            QMessageBox.critical(
                self, 
                "SimpleBuild 4 Installation" if is_de else "SimpleBuild 4 Setup", 
                message
            )

    def select_s3_path_manually(self):
        """Dialog zur manuellen Auswahl des S3-Pfads."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import os
        import platform
        import traceback

        lang = getattr(self, "LANG", "de").lower()[:2]

        if lang == "en":
            hint = "Select S3 folder"
            ok_text = "S3 path set"
            err_title = "Error"
            err_msg = "The S3 executable (s3 or s3.exe) was not found in this folder."
        else:
            hint = "S3-Ordner wählen"
            ok_text = "S3-Pfad gesetzt"
            err_title = "Fehler"
            err_msg = "Die ausführbare S3-Datei wurde in diesem Ordner nicht gefunden!"

        is_win = platform.system() == "Windows"
        default_start = "C:\\s3" if is_win else "/opt/s3"
        start_path = getattr(self, "S3_PATH", default_start)

        if not os.path.exists(start_path):
            start_path = os.path.expanduser("~")

        chosen_dir = QFileDialog.getExistingDirectory(
            self, hint, start_path
        )

        if not chosen_dir:
            return

        chosen_dir = os.path.normpath(chosen_dir)

        # Ausführbare Datei direkt oder im Unterordner s3 suchen
        found_path = None

        for exe in ("s3.exe", "s3"):
            direct = os.path.join(chosen_dir, exe)
            sub = os.path.join(chosen_dir, "s3", exe)

            if os.path.isfile(direct):
                found_path = chosen_dir
                break

            if os.path.isfile(sub):
                found_path = os.path.join(chosen_dir, "s3")
                break

        if found_path is None:
            QMessageBox.warning(self, err_title, err_msg)
            return

        old_path = getattr(self, "S3_PATH", default_start)
        self.S3_PATH = os.path.normpath(found_path)

        try:
            # Nur den Pfad speichern; keine unnötigen UI-Effekte auslösen.
            success = save_config(
                {"s3_custom_path": self.S3_PATH},
                gui_instance=None,
                silent=True
            )

            if not success:
                self.S3_PATH = old_path
                QMessageBox.critical(
                    self,
                    err_title,
                    "Der S3-Pfad konnte nicht gespeichert werden."
                )
                return

            # Die gespeicherte Konfiguration mit der GUI synchronisieren.
            if not isinstance(getattr(self, "current_config", None), dict):
                self.current_config = {}

            self.current_config["s3_custom_path"] = self.S3_PATH

            if hasattr(self, "update_ui_texts"):
                self.update_ui_texts()

            QMessageBox.information(
                self, "OK", f"{ok_text}:\n{self.S3_PATH}"
            )

        except Exception as exc:
            traceback.print_exc()

            QMessageBox.critical(
                self,
                err_title,
                f"Fehler beim Setzen des S3-Pfads:\n{exc}"
            )

    def start_s3_install(self):
        """Startet die S3 Installation über Worker, Pfad wählbar und OS-optimiert."""
        import os, platform
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        is_de = getattr(self, "LANG", "de") == "de"
        is_win = platform.system() == "Windows"

        # 1. Intelligenten Startpfad für den Dialog wählen
        # Falls S3_PATH noch nicht gesetzt ist, nehmen wir einen sinnvollen Standard
        default_base = "C:\\opt" if is_win else "/opt"
        start_path = getattr(self, "S3_PATH", os.path.expanduser("~"))
    
        # Falls der aktuelle Pfad nicht existiert, nimm die Basis
        if not os.path.exists(start_path):
            start_path = default_base if os.path.exists(default_base) else os.path.expanduser("~")

        chosen_dir = QFileDialog.getExistingDirectory(
            self,
            "Wähle S3 Installationsordner" if is_de else "Select S3 Installation Folder",
            start_path,
        )

        if not chosen_dir:
            return  # Abbruch durch Nutzer

        # Nicht den Repository-Unterordner "support" als Installationsbasis
        # verwenden. Wenn .../s3/support gewählt wurde, auf .../s3 gehen;
        # andernfalls den Ordner oberhalb von support als Basis nehmen.
        chosen_path = os.path.normpath(chosen_dir)
        if os.path.basename(chosen_path).lower() == "support":
            parent_path = os.path.dirname(chosen_path)
            if os.path.basename(parent_path).lower() == "s3":
                chosen_path = parent_path
            else:
                chosen_path = os.path.dirname(chosen_path)

        # S3_PATH bezeichnet den gemeinsamen Basisordner; der Worker legt
        # das Repository direkt in <Basisordner>/s3 ab.
        self.S3_PATH = os.path.normpath(chosen_path)

        try:
            # Ordner erstellen (Dank deines Admin-Elevators klappt das auch auf C:\)
            os.makedirs(self.S3_PATH, exist_ok=True)
        
            # Test-Schreibzugriff (nur um sicherzugehen)
            test_file = os.path.join(self.S3_PATH, ".permissions_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)

        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error", 
                f"Keine Schreibrechte in diesem Ordner!\n{str(e)}" if is_de 
                else f"No write permissions in this folder!\n{str(e)}"
            )
            return

        # 2. UI Feedback
        self.btn_s3.setEnabled(False)
        # Nutze ein Icon oder Text-Update
        busy_text = "⏳ Installation läuft..." if is_de else "⏳ Installing..."
        self.btn_s3.setText(busy_text)
    
        if hasattr(self, "log"): # Falls deine GUI eine Log-Funktion hat
            self.log("patch_create_clone_start", "info") 

        # 3. Worker starten
        # WICHTIG: Der S3InstallWorker muss intern os.path.join nutzen!
        # Repository auswählen
        repositories = list(S3InstallWorker.REPOSITORIES.keys())

        selected_repo, ok = QInputDialog.getItem(
            self,
            "S3 Installation",
            "Welches S3-Repository möchtest du installieren?",
            repositories,
            0,
            False,
        )

        if not ok or not selected_repo:
            self.btn_s3.setEnabled(True)
            self.btn_s3.setText("S3")
            return

        # Ausgewählte Repository-URL ermitteln
        repo_url = S3InstallWorker.REPOSITORIES[selected_repo]

        # Build-Logging am tatsächlich verwendeten S3-Button aktivieren.
        # Der Button ist mit start_s3_install() verbunden (nicht mit
        # start_s3_installation()). Deshalb muss das Log hier angelegt werden.
        from datetime import datetime
        try:
            log_dir = getattr(self, "build_log_dir", None)
            if not log_dir:
                log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
                self.build_log_dir = log_dir
            os.makedirs(log_dir, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.s3_build_log_file = os.path.join(log_dir, f"S3_build_{stamp}.log")
            with open(self.s3_build_log_file, "w", encoding="utf-8") as log_file:
                log_file.write(f"S3 Build-Log gestartet: {datetime.now().isoformat(timespec='seconds')}\n")
                log_file.write(f"Repository: {selected_repo}\nURL: {repo_url}\nZielpfad: {self.S3_PATH}\n")
                log_file.write("Status: S3-Worker wurde angefordert.\n\n")
            print(f"[BUILD-LOG] S3-Logdatei: {self.s3_build_log_file}")
        except Exception as log_error:
            self.s3_build_log_file = None
            print(f"[BUILD-LOG] S3-Logdatei konnte nicht erstellt werden: {log_error}")

        # Worker mit dem ausgewählten Repository starten
        self.s3_worker = S3InstallWorker(
            base_target_dir=self.S3_PATH,
            repo_url=repo_url,
            project_name=selected_repo,
            sub_folder="s3",
            parent=self,
        )

        self.s3_worker.finished_signal.connect(self.on_s3_finished)
        # Falls der Worker Logmeldungen bereitstellt, dauerhaft in dieselbe
        # Datei schreiben. Nicht jeder Worker besitzt dieses Signal.
        if hasattr(self.s3_worker, "log_signal"):
            self.s3_worker.log_signal.connect(self.append_s3_install_log)
        self.s3_worker.start()

    def on_s3_finished(self, success, message):
        """Nach Abschluss des Workers für S3."""
        from PyQt6.QtWidgets import QMessageBox

        is_de = getattr(self, "LANG", "de") == "de"
        log_path = getattr(self, "s3_build_log_file", None)
        if log_path:
            try:
                with open(log_path, "a", encoding="utf-8") as log_file:
                    log_file.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] Ergebnis: {'ERFOLG' if success else 'FEHLER'}\n")
                    log_file.write(str(message) + "\n")
            except OSError as log_error:
                print(f"[BUILD-LOG] Abschluss konnte nicht geschrieben werden: {log_error}")
        self.btn_s3.setEnabled(True)

        # Visuelles Feedback über die zentrale UI-Logik steuern.
        # Das sucht nach der s3 Binary und setzt das perfekte grüne oder orange Design auf.
        if hasattr(self, "update_ui_texts"):
            self.update_ui_texts()

        if success:
            QMessageBox.information(
                self, 
                "S3 Installation" if is_de else "S3 Setup", 
                message
            )
        else:
            QMessageBox.critical(
                self, 
                "S3 Installation" if is_de else "S3 Setup", 
                message
            )


        from PyQt6.QtCore import QTimer

    def check_git_installed():
        """Prüft, ob Git im System-Pfad verfügbar ist."""
        git_path = shutil.which("git")
        if git_path:
            print(f"[SYSTEM] Git gefunden: {git_path}")
            return True
        else:
            print("[!] FEHLER: Git ist nicht installiert oder nicht im PATH.")
            return False

    def open_custom_folder(self, path):
        """Öffnet Ordner mit Regenbogen-Progress und Sound beim Start & Ende."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        import os, platform, subprocess
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # --- 1. SOUND BEIM ÖFFNEN (Start) ---
        if "safe_play" in globals():
            safe_play("service-login.oga")

        # Setup & Sprach-Check
        pbar = getattr(self, "progress_bar", None)
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"

        T_OPEN = "Öffne Ordner..." if is_de else "Opening folder..."
        T_DONE = "Ordner offen!" if is_de else "Folder opened!"

        if pbar:
            # REGENBOGEN-PROGRESS Setup
            rainbow = (
                "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
            )
            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center; font-weight: 700; border: 2px solid #222;
                    border-radius: 6px; background-color: #111; color: black; font-size: 15pt;
                }}
                QProgressBar::chunk {{ background-color: {rainbow}; border-radius: 4px; }}
            """
            )
            pbar.setFormat(f"📂 {T_OPEN} %p%")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        # 2. Ordner-Logik: Windows und WSL unterstützen
        try:
            import shutil

            raw_path = os.path.expanduser(str(path or "").strip())

            if not raw_path:
                raise ValueError("Der Ordnerpfad ist leer.")

            is_windows_path = (
                len(raw_path) >= 3
                and raw_path[1] == ":"
                and raw_path[2] in ("\\", "/")
            ) or raw_path.startswith("\\\\")

            is_wsl = (
                platform.system() == "Linux"
                and (
                    "microsoft" in platform.release().lower()
                    or "WSL_DISTRO_NAME" in os.environ
                )
            )

            
            
            if is_wsl:
                explorer = shutil.which("explorer.exe") or "/mnt/c/Windows/explorer.exe"

                if not os.path.isfile(explorer):
                    raise FileNotFoundError(
                        "explorer.exe wurde in WSL nicht gefunden."
                    )

                if is_windows_path:
                    result = subprocess.run(
                        ["wslpath", "-u", raw_path],
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    linux_path = result.stdout.strip()
                else:
                    linux_path = os.path.abspath(raw_path)

                if not os.path.isdir(linux_path):
                    raise FileNotFoundError(
                        f"Der Ordner existiert nicht: {linux_path}"
                    )

                result = subprocess.run(
                    ["wslpath", "-w", linux_path],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                windows_path = result.stdout.strip()

                subprocess.Popen(
                    [explorer, windows_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

            else:
                folder = os.path.abspath(raw_path)

                if not os.path.isdir(folder):
                    raise FileNotFoundError(
                        f"Der Ordner existiert nicht: {folder}"
                    )

                if platform.system() == "Windows":
                    os.startfile(folder)
                elif platform.system() == "Linux":
                    subprocess.Popen(["xdg-open", folder])
                else:
                    subprocess.Popen(["open", folder])


            if pbar:
                pbar.setValue(100)

        except Exception as exc:
            QMessageBox.warning(
                self,
                "Ordner öffnen" if is_de else "Open folder",
                f"Ordner konnte nicht geöffnet werden:\n{exc}",
            )

            # --- 2. SOUND NACH DEM ÖFFNEN (Abschluss) ---
            if "safe_play" in globals():
                # Signalisiert, dass der Befehl durch ist
                safe_play("complete.oga")

            if pbar:
                pbar.setValue(100)
                pbar.setFormat(f"✅ {T_DONE} 100%")

        except Exception:
            if "safe_play" in globals():
                safe_play("dialog-error.oga")
            if pbar:
                pbar.setValue(0)

        # 3. AUTO-RESET (3 Sekunden) -> Zurück zu Orange/Gold
        if pbar:

            def restore_pbar():
                pbar.setValue(0)
                pbar.setFormat("%p%")
                pbar.setStyleSheet(
                    """
                    QProgressBar { border: 1px solid #444; border-radius: 8px; background-color: #1A1A1A; 
                    color: black; text-align: center; font-weight: bold; }
                    QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #F37804, stop:1 #FFD700); border-radius: 8px; }
                """
                )

            QTimer.singleShot(3000, restore_pbar)

    def start_s3_menu(self):
        """Startet das gewählte S3-Menü unter Windows/WSL2 oder Linux."""

        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import os
        import shutil
        import platform

        s3_exec = None
        is_de = getattr(self, "LANG", "de") == "de"
        is_win = platform.system() == "Windows"

        # ---------------------------------------------------------
        # WINDOWS: Variante auswählen und über WSL2 starten
        # ---------------------------------------------------------
        
        if is_win:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            from windows_msys2_setup import prepare_tool, launch_tool_menu

            # Aktuelle Sprache sicher aus TEXTS laden
            lang = str(getattr(self, "LANG", "de")).lower()[:2]
            T = TEXTS.get(lang, TEXTS.get("de", {}))

            choice = QMessageBox(self)
            choice.setWindowTitle(
                T.get("s3_choice_title", "S3 Simplebuild auswählen")
            )
            choice.setText(
                T.get(
                    "s3_choice_text",
                    "Welches S3-Menü möchtest du starten?",
                )
            )
            choice.setInformativeText(
                T.get(
                    "s3_choice_info",
                    "Gorgone verwendet den Ordner 's3'.\n"
                    "Speedy005 verwendet den Ordner 's3_speedy005'.",
                )
            )

            gorgone_btn = choice.addButton(
                T.get("s3_choice_gorgone", "S3 Gorgone"),
                QMessageBox.ButtonRole.AcceptRole,
            )
            speedy_btn = choice.addButton(
                T.get("s3_choice_speedy005", "S3 Speedy005"),
                QMessageBox.ButtonRole.ActionRole,
            )
            choice.addButton(
                T.get("button_cancel", "Abbrechen"),
                QMessageBox.ButtonRole.RejectRole,
            )

            choice.exec()
            selected = choice.clickedButton()

            if selected not in (gorgone_btn, speedy_btn):
                return


            try:
                def _setup_log(line):
                    if hasattr(self, "info_text") and self.info_text:
                        safe_line = (
                            str(line)
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                        )
                        self.info_text.append(safe_line)
                    QApplication.processEvents()

                # Fester Projektpfad: nicht aus S3_PATH ableiten,
                # weil dieser Pfad aus der alten Konfiguration stammen kann.
                project_dir = os.path.dirname(os.path.abspath(__file__))

                if selected is gorgone_btn:
                    tool_name = "s3"
                    folder_name = "s3"
                else:
                    tool_name = "s3_speedy005"
                    folder_name = "s3_speedy005"

                variant_path = os.path.join(project_dir, folder_name)

                _setup_log(f"S3-Variante: {tool_name}")
                _setup_log(f"Zielordner: {variant_path}")

                # Vorhandenes Ziel niemals automatisch umbenennen,
                # löschen oder auf ein anderes Repository umstellen.
                s3_path = str(
                    prepare_tool(
                        tool_name,
                        variant_path,
                        log=_setup_log,
                    )
                )

                self.S3_PATH = s3_path

                if not isinstance(
                    getattr(self, "current_config", None), dict
                ):
                    self.current_config = {}

                self.current_config["s3_custom_path"] = s3_path

                if "save_config" in globals():
                    save_config(
                        {"s3_custom_path": s3_path},
                        gui_instance=self,
                        silent=True,
                    )

                launch_tool_menu(
                    tool_name,
                    s3_path,
                    log=_setup_log,
                )
                return

            except Exception as exc:
                QMessageBox.critical(
                    self,
                    "S3 / WSL2",
                    "WSL2-Einrichtung oder S3-Start fehlgeschlagen:\n"
                    f"{exc}",
                )
                return

        # ---------------------------------------------------------
        # LINUX: Bisherigen nativen Startablauf beibehalten
        # ---------------------------------------------------------
        default_start = "/opt/s3"
        s3_path = getattr(self, "S3_PATH", default_start)
        sub_folder = "s3"

        possible_names = ["s3"]
        possible_paths = []

        for name in possible_names:
            possible_paths.append(os.path.join(s3_path, name))
            possible_paths.append(
                os.path.join(s3_path, sub_folder, name)
            )

        possible_paths.extend([
            "/opt/s3_neu/s3",
            "/opt/s3/s3",
            os.path.expanduser("~/s3/s3"),
            shutil.which("s3"),
        ])

        for path in possible_paths:
            if path and os.path.exists(path) and not os.path.isdir(path):
                if os.access(path, os.X_OK):
                    s3_exec = os.path.normpath(path)

                    if (
                        sub_folder in path.lower()
                        and not s3_path.lower().endswith(sub_folder.lower())
                    ):
                        self.S3_PATH = os.path.normpath(
                            os.path.join(s3_path, sub_folder)
                        )
                    else:
                        self.S3_PATH = os.path.normpath(s3_path)

                    success = save_config(
                        {"s3_custom_path": self.S3_PATH},
                        gui_instance=None,
                        silent=True,
                    )

                    if not success:
                        from PyQt6.QtWidgets import QMessageBox
                        QMessageBox.warning(
                            self,
                            "Fehler",
                            "Der S3-Pfad konnte nicht gespeichert werden.",
                        )
                        return

                    if not isinstance(
                        getattr(self, "current_config", None), dict
                    ):
                        self.current_config = {}

                    self.current_config["s3_custom_path"] = self.S3_PATH
                    break

        if s3_exec:
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                msg = f"🚀 S3 Menü: {s3_exec}"
                self.append_info(self.info_text, msg, "info")

            self.open_terminal(
                s3_path=s3_exec,
                use_sudo=True,
            )
        else:
            err_msg = (
                "❌ Fehler: S3-Startdatei nicht gefunden!"
                if is_de
                else "❌ Error: S3 executable not found!"
            )

            if hasattr(self, "info_text") and self.info_text:
                self.info_text.append(
                    f'<br><span style="color:red;"><b>{err_msg}</b></span>'
                )

            self.open_terminal()

    def start_s4_menu(self):
        """Startet SimpleBuild 4 unter Windows in WSL2 und unter Linux nativ."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        
        import os, shutil, platform, subprocess

        s4_exec = None
        is_de = getattr(self, "LANG", "de") == "de"
        is_win = platform.system() == "Windows"

        # 1. Basis-Pfad holen für S4
        default_start = "C:\\opt\\simplebuild4" if is_win else "/opt/simplebuild4"
        s4_path = getattr(self, "S4_PATH", default_start)
        if is_win:
            try:
                from windows_msys2_setup import prepare_tool
                from PyQt6.QtWidgets import QApplication, QMessageBox
                def _setup_log(line):
                    if hasattr(self, "info_text") and self.info_text:
                        self.info_text.append(str(line).replace("&", "&amp;").replace("<", "&lt;"))
                    QApplication.processEvents()
                s4_path = str(prepare_tool("s4", s4_path, log=_setup_log))
                self.S4_PATH = s4_path
                if "save_config" in globals():
                    save_config({"s4_custom_path": self.S4_PATH}, gui_instance=self, silent=True)
                from windows_msys2_setup import launch_tool_menu
                launch_tool_menu("s4", s4_path, log=_setup_log)
                return
            except Exception as exc:
                QMessageBox.critical(self, "S4 / WSL2", f"WSL2-Einrichtung oder S4-Start fehlgeschlagen:\n{exc}")
                return
        sub_folder = "simplebuild4"

        # Mögliche Dateinamen für das S4 Skript
        possible_names = ["simplebuild", "simplebuild.exe", "s4", "s4.exe"]
        possible_paths = []

        # Suchliste aufbauen
        for name in possible_names:
            possible_paths.append(os.path.join(s4_path, name))
            possible_paths.append(os.path.join(s4_path, sub_folder, name))

        # System-Fallbacks
        if is_win:
            possible_paths.extend([
                "C:\\opt\\simplebuild4\\simplebuild",
                "C:\\opt\\simplebuild4\\simplebuild.exe",
                "C:\\s4\\simplebuild",
                "C:\\s4\\simplebuild.exe",
                os.path.join(os.path.expanduser("~"), "Downloads", "simplebuild4", "s4")
            ])
        else:
            possible_paths.extend([
                "/opt/simplebuild4/simplebuild",
                "/opt/s4/simplebuild",
                os.path.expanduser("~/simplebuild4/simplebuild"),
                shutil.which("simplebuild"),
                shutil.which("s4"),
            ])

        # 2. Den ersten Treffer validieren
        for path in possible_paths:
            if path and os.path.exists(path) and not os.path.isdir(path):
                if is_win or os.access(path, os.X_OK):
                    s4_exec = os.path.normpath(path)
                
                    if sub_folder in path.lower() and not s4_path.lower().endswith(sub_folder.lower()):
                       self.S4_PATH = os.path.normpath(os.path.join(s4_path, sub_folder))
                       if "save_config" in globals():
                            save_config({"s4_custom_path": self.S4_PATH}, gui_instance=self, silent=True)
                    break

        # 3. Ausführung
        if s4_exec:
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                msg = f"🚀 S4 Menü: {s4_exec}"
                self.append_info(self.info_text, msg, "info")

            # --- BC FIX FÜR DIE GLOBALEN USER-PROFILEDATEIEN ---
            # --- FORCIERTER BASH-AUFRUF UNTER WINDOWS ---
            if is_win:
                # Suchen nach Git Bash oder MSYS2 Bash
                bash_executable = None
                for potential_bash in [
                    os.environ.get("MSYS2_BASH", r"C:\msys64\usr\bin\bash.exe"),
                    os.path.join(os.environ.get("MSYS2_ROOT", r"C:\msys64"), "usr", "bin", "bash.exe"),
                    r"C:\tools\msys64\usr\bin\bash.exe",
                ]:
                    if potential_bash and os.path.exists(potential_bash):
                        bash_executable = potential_bash
                        break
                
                if bash_executable:
                    # Unix-konforme Pfade erzeugen
                    s4_unix = s4_exec.replace("\\", "/")
                    exec_dir = os.path.dirname(s4_exec).replace("\\", "/")
                    
                    # Startet ein neues, echtes Konsolenfenster direkt in der Bash mit dem Menü-Parameter
                    # Dadurch interpretiert Windows die Datei niemals wieder als Python-Datei!
                    from windows_msys2_setup import bash_environment
                    s4_cmd = (f'export MSYSTEM=UCRT64; export PATH=/ucrt64/bin:/usr/bin:/bin; '
                              f'cd "{exec_dir}" || exit 2; ./{os.path.basename(s4_unix)} menu; exec bash -i')
                    subprocess.Popen(
                        [bash_executable, "--login", "-i", "-c", s4_cmd],
                        env=bash_environment(), creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                    return

            # Normaler Linux-Start oder Fallback, falls oben keine Bash gefunden wurde
            self.open_terminal(s3_path=s4_exec, use_sudo=not is_win)
            
        else:
            err_msg = (
                "❌ Fehler: SimpleBuild 4 Startdatei nicht gefunden!"
                if is_de
                else "❌ Error: SimpleBuild 4 executable not found!"
            )
            if hasattr(self, "info_text") and self.info_text:
                self.info_text.append(f'<br><span style="color:red;"><b>{err_msg}</b></span>')

            self.open_terminal()

    def start_ncam_menu(self):
        """Startet NCam Bonecrew unter Windows in WSL2 und unter Linux nativ."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import os, shutil, platform, subprocess, urllib.request, tarfile

        is_de = getattr(self, "LANG", "de") == "de"
        is_win = platform.system() == "Windows"

        # 1. Pfade ermitteln für NCam / S3
        default_start = "C:\\opt\\ncam" if is_win else "/opt/s3_ncam_bonecrew"
        ncam_path = getattr(self, "NCAM_PATH", default_start)
        if is_win:
            try:
                from windows_msys2_setup import prepare_tool
                from PyQt6.QtWidgets import QApplication, QMessageBox
                def _setup_log(line):
                    if hasattr(self, "info_text") and self.info_text:
                        self.info_text.append(str(line).replace("&", "&amp;").replace("<", "&lt;"))
                    QApplication.processEvents()
                ncam_path = str(prepare_tool("ncam", ncam_path, log=_setup_log))
                self.NCAM_PATH = ncam_path
                if "save_config" in globals():
                    save_config({"ncam_custom_path": self.NCAM_PATH}, gui_instance=self, silent=True)
                from windows_msys2_setup import launch_tool_menu
                launch_tool_menu("ncam", ncam_path, log=_setup_log)
                return
            except Exception as exc:
                QMessageBox.critical(self, "NCam Bonecrew / WSL2", f"WSL2-Einrichtung oder NCam-Start fehlgeschlagen:\n{exc}")
                return
        sub_folder = "s3_ncam_bonecrew"

        possible_names = ["s3", "s3.exe"] if is_win else ["s3"]
        ncam_exec = None

        for name in possible_names:
            path_direct = os.path.join(ncam_path, name)
            path_sub = os.path.join(ncam_path, sub_folder, name)

            if os.path.exists(path_direct) and not os.path.isdir(path_direct):
                ncam_exec = os.path.normpath(path_direct)
                break
            elif os.path.exists(path_sub) and not os.path.isdir(path_sub):
                ncam_exec = os.path.normpath(path_sub)
                if sub_folder in path_sub.lower() and not ncam_path.lower().endswith(sub_folder.lower()):
                    self.NCAM_PATH = os.path.normpath(os.path.join(ncam_path, sub_folder))
                    if "save_config" in globals():
                        save_config({"ncam_custom_path": self.NCAM_PATH}, gui_instance=self, silent=True)
                break

        # 2. Ausführung
        if ncam_exec:
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                msg = f"🚀 NCam Menü: {ncam_exec}"
                self.append_info(self.info_text, msg, "info")

            # --- BC FIX ÜBER DIE GLOBALEN USER-PROFILEDATEIEN ---
            # Startet Terminal exakt wie das funktionierende S3-Menü
            self.open_terminal(s3_path=ncam_exec, use_sudo=not is_win)
        else:
            err_msg = f"❌ NCam nicht gefunden in: {ncam_path}"
            if hasattr(self, "info_text") and self.info_text:
                self.info_text.append(f'<br><span style="color:orange;"><b>{err_msg}</b></span>')

    def find_s3_executable(self):
        """Sucht automatisch nach der s3-Startdatei an bekannten Orten."""
        import os, shutil, platform

        is_win = platform.system() == "Windows"
        
        # 1. Prüfen, ob s3 global im System-PATH bekannt ist
        system_path = shutil.which("s3")
        if system_path:
            return system_path

        # 2. Dynamische Liste der wahrscheinlichsten Verzeichnisse generieren
        search_dirs = []

        # Füge die aktuell in der Instanz konfigurierten Pfade als höchste Priorität hinzu
        for path_attr in ["S3_PATH", "NCAM_PATH", "S4_PATH"]:
            current_val = getattr(self, path_attr, None)
            if current_val:
                search_dirs.append(current_val)

        # Standard-Fallback-Verzeichnisse für Linux und Windows
        if is_win:
            search_dirs.extend([
                "C:\\s3",
                "C:\\opt\\ncam",
                "C:\\opt\\s4",
                "C:\\opt\\s3",
            ])
        else:
            search_dirs.extend([
                "/opt/s3",
                "/opt/s3_ncam_bonecrew",
                "/opt/s4",
                os.path.expanduser("~/s3"),
                os.path.expanduser("~/simplebuild"),
                "/var/lib/s3",
            ])

        # Unterordner-Strukturen, die von den Workern angelegt werden
        sub_folders = ["", "s3", "s3_ncam_bonecrew", "s4"]
        
        # Mögliche Dateinamen (S4 nutzt simplebuild/s4, die anderen s3)
        possible_exes = ["s3", "s3.exe", "s4", "s4.exe", "simplebuild", "simplebuild.exe"]

        # 3. Such-Schleife über alle Pfad-Kombinationen
        for base_dir in search_dirs:
            if not base_dir or not os.path.exists(base_dir):
                continue
                
            for sub in sub_folders:
                for exe in possible_exes:
                    full_path = os.path.normpath(os.path.join(base_dir, sub, exe))
                    
                    if os.path.exists(full_path) and not os.path.isdir(full_path):
                        # Rechteprüfung: os.X_OK nur auf Linux/macOS erzwingen
                        if is_win or os.access(full_path, os.X_OK):
                            return full_path

        return None  # Nichts gefunden

    def manual_tool_check(self):
        """System-Check mit Regenbogen-Progress, Sound und DE/EN Support."""

        # --- Final-Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        import time, shutil, os, platform
        from datetime import datetime
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # 1. Doppelklick-Sperre & Setup
        now_ts = time.time()
        if hasattr(self, "_last_check_run") and (now_ts - self._last_check_run) < 0.5:
            return
        self._last_check_run = now_ts

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Lokalisierte Texte
        T_START = "System-Check..." if is_de else "System Check..."
        T_DONE = "Check bereit!" if is_de else "Check ready!"
        T_ERR = "Fehler!" if is_de else "Error!"

        # --- SOUND BEIM ÖFFNEN (Start) ---
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
                    text-align: center; font-weight: 700; border: 2px solid #222;
                    border-radius: 6px; background-color: #111; color: black; font-size: 15pt;
                }}
                QProgressBar::chunk {{ background-color: {rainbow}; border-radius: 4px; }}
            """
            )
            pbar.setFormat(f"🛠️ {T_START} %p%")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        try:
            self.info_text.clear()
            msg_init = (
                f"Starte System-Check... [{timestamp}]"
                if is_de
                else f"Starting system check... [{timestamp}]"
            )
            self.append_info(msg_init, "info")

            if pbar:
                pbar.setValue(50)

            # 3. Tools prüfen
            required_tools = ["git", "python3"]
            if platform.system() != "Windows":
                required_tools.extend(["patch", "zip"])

            missing = [t for t in required_tools if shutil.which(t) is None]

            if not missing:
                self.append_info(
                    (
                        "✅ Alle benötigten System-Tools sind bereit."
                        if is_de
                        else "✅ All required tools are ready."
                    ),
                    "success",
                )

                # --- SOUND BEI ERFOLG ---
                if "safe_play" in globals():
                    safe_play("complete.oga")

                if pbar:
                    pbar.setValue(100)
                    pbar.setFormat(f"✅ {T_DONE} 100%")

                # Folgeschritte ausführen
                if hasattr(self, "check_for_plugin_update"):
                    self.check_for_plugin_update()
                if hasattr(self, "show_start_config"):
                    self.show_start_config()
            else:
                # --- SOUND BEI WARNUNG ---
                if "safe_play" in globals():
                    safe_play("dialog-error.oga")
                missing_str = ", ".join(missing)
                self.append_info(
                    (
                        f"⚠️ Fehlende Tools: {missing_str}"
                        if is_de
                        else f"⚠️ Missing tools: {missing_str}"
                    ),
                    "warning",
                )
                if pbar:
                    pbar.setValue(0)

        except Exception as e:
            if "safe_play" in globals():
                safe_play("dialog-error.oga")
            self.append_info(f"❌ Check-Fehler: {str(e)}", "error")
            if pbar:
                pbar.setStyleSheet("QProgressBar { color: red; font-weight: 700; }")

        # 4. AUTO-RESET (3 Sekunden) -> Zurück zu Orange/Gold Style
        if pbar:

            def restore_style():
                pbar.setValue(0)
                pbar.setFormat("%p%")
                pbar.setStyleSheet(
                    """
                    QProgressBar { border: 1px solid #444; border-radius: 8px; background-color: #1A1A1A; 
                    color: black; text-align: center; font-weight: bold; }
                    QProgressBar::chunk { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #F37804, stop:1 #FFD700); border-radius: 8px; }
                """
                )

            QTimer.singleShot(3000, restore_style)

    def show_start_config(self):
        """Entfernt alle Textanzeigen und setzt nur noch den ProgressBar-Abschluss."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # --- 1. PROGRESSBAR ABSCHLUSS-TEXT ---
        pbar = getattr(self, "progress_bar", None)
        if pbar:
            lang = getattr(self, "LANG", "de").lower()
            is_de = lang == "de"
            ready_txt = "✅ System bereit" if is_de else "✅ System ready"

            pbar.setValue(100)
            pbar.setFormat(f"{ready_txt}")

            # CSS für gute Lesbarkeit auf dem Regenbogen-Balken
            pbar.setStyleSheet(
                pbar.styleSheet() + " QProgressBar { color: black; font-weight: bold; }"
            )

        QApplication.processEvents()

        # --- 2. SOUND & TIMER ---
        if "safe_play" in globals():
            safe_play("complete.oga")

        # Nach 3 Sek. wird der Balken durch pbar_idle geleert/versteckt
        if hasattr(self, "pbar_idle"):
            QTimer.singleShot(500, self.pbar_idle)

    def open_terminal(self, **kwargs):
        """Öffnet Terminal (S3, S4 oder NCam) mit Sudo-Support, Regenbogen-Progress und Sound."""
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import subprocess, platform, shutil, os
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # 1. PARAMETER RAUSHOLEN & SOFORT RADIKAL BEREINIGEN
        s3_path_raw = kwargs.get("s3_path")
        use_sudo = kwargs.get("use_sudo", False)
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # FIX: Alle eventuell mitgelieferten Anführungszeichen sofort entfernen,
        # bevor irgendeine Pfadfunktion (dirname/basename) darauf zugreift!
        s3_path = None
        if s3_path_raw:
            s3_path = str(s3_path_raw).replace('"', '').strip()

        # Erweiterte Erkennung für S3, S4 und NCam
        s3_path_lower = s3_path.lower() if s3_path else ""
        if "ncam" in s3_path_lower:
            proj_name = "NCam"
        elif "s4" in s3_path_lower or "simplebuild" in s3_path_lower:
            proj_name = "S4"
        else:
            proj_name = "S3"

        T_LOAD = (
            (
                f"{proj_name} Menü wird gestartet..."
                if s3_path
                else "Terminal wird geöffnet..."
            )
            if is_de
            else (f"Starting {proj_name} menu..." if s3_path else "Opening terminal...")
        )
        # Das Öffnen des Menüs ist kein abgeschlossener Build. Die Anzeige
        # darf daher nicht fälschlich einen erfolgreichen Build suggerieren.
        T_DONE = "Terminal geöffnet – Build läuft extern" if is_de else "Terminal opened – build runs externally"

        # Vorabprüfung: bekannte Startdateien und Arbeitsverzeichnis validieren,
        # bevor ein externes Terminal geöffnet wird. Unter Windows wird der Pfad
        # später durch MSYS2/WSL verarbeitet; dort keine Linux-Rechteprüfung.
        if s3_path and platform.system() == "Linux":
            start_dir = os.path.dirname(s3_path) or os.getcwd()
            if not os.path.isdir(start_dir):
                raise_msg = (
                    f"Arbeitsverzeichnis nicht gefunden: {start_dir}"
                    if is_de else f"Working directory not found: {start_dir}"
                )
                if hasattr(self, "append_info") and getattr(self, "info_text", None):
                    self.append_info(self.info_text, f"❌ {raise_msg}", "error")
                if pbar:
                    pbar.setValue(0)
                    pbar.setFormat("❌ " + ("Pfadfehler" if is_de else "Path error"))
                return
            if not os.path.isfile(s3_path):
                raise_msg = (
                    f"Startdatei nicht gefunden: {s3_path}"
                    if is_de else f"Startup file not found: {s3_path}"
                )
                if hasattr(self, "append_info") and getattr(self, "info_text", None):
                    self.append_info(self.info_text, f"❌ {raise_msg}", "error")
                if pbar:
                    pbar.setValue(0)
                    pbar.setFormat("❌ " + ("Datei fehlt" if is_de else "File missing"))
                return
            if not os.access(s3_path, os.X_OK):
                raise_msg = (
                    f"Startdatei ist nicht ausführbar: {s3_path} (Tipp: chmod +x {shlex.quote(s3_path)})"
                    if is_de else f"Startup file is not executable: {s3_path} (tip: chmod +x {shlex.quote(s3_path)})"
                )
                if hasattr(self, "append_info") and getattr(self, "info_text", None):
                    self.append_info(self.info_text, f"❌ {raise_msg}", "error")
                if pbar:
                    pbar.setValue(0)
                    pbar.setFormat("❌ " + ("Keine Ausführungsrechte" if is_de else "Not executable"))
                return

        if "safe_play" in globals():
            safe_play("service-login.oga")

        # 2. PROGRESSBAR STYLE (REGENBOGEN)
        if pbar:
            rainbow = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
            pbar.setStyleSheet(
                f"QProgressBar {{ text-align: center; font-weight: 700; border: 2px solid #222; border-radius: 6px; background-color: #111; color: black; font-size: 15pt; }} QProgressBar::chunk {{ background-color: {rainbow}; border-radius: 4px; }}"
            )
            pbar.setFormat(f"💻 {T_LOAD} %p%")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        
        build_log_path = None
        try:
            # 3. BEFEHL ZUSAMMENBAUEN
            system = platform.system()
            terminal_opened = False
            exec_cmd = ""
            is_s4_script = proj_name == "S4"

            if s3_path:
                s3_dir = os.path.dirname(s3_path)
                exe_name = os.path.basename(s3_path)

                s3_cmd = f"./{exe_name} menu"
                if is_s4_script:
                    s3_cmd = f"./{exe_name}"
                if use_sudo and system == "Linux":
                    s3_cmd = f"sudo {s3_cmd}"

                if system == "Windows":
                    from windows_msys2_setup import bash_environment

                    msys2_root = os.environ.get("MSYS2_ROOT", r"C:\msys64")
                    bash_candidates = [
                        os.environ.get("MSYS2_BASH"),
                        os.path.join(msys2_root, "usr", "bin", "bash.exe"),
                        r"C:\msys64\usr\bin\bash.exe",
                        r"C:\tools\msys64\usr\bin\bash.exe",
                    ]
                    msys2_bash = next(
                        (
                            os.path.normpath(candidate)
                            for candidate in bash_candidates
                            if candidate and os.path.isfile(candidate)
                        ),
                        None,
                    )

                    if not msys2_bash:
                        raise FileNotFoundError(
                            "MSYS2 Bash nicht gefunden. Bitte MSYS2_ROOT "
                            "oder MSYS2_BASH prüfen."
                        )

                    s3_dir_bash = os.path.normpath(s3_dir).replace("\\", "/")
                    s3_dir_bash_q = "'" + s3_dir_bash.replace("'", "'\\''") + "'"
                    exe_name_q = "'" + exe_name.replace("'", "'\\''") + "'"

                    # Auch beim Start unter Windows/MSYS2 Logs im Startordner
                    # des Patch Managers anlegen. Zuvor wurde nur der Linux-
                    # Terminalzweig protokolliert, weshalb hier kein Ordner entstand.
                    log_dir = getattr(self, "build_log_dir", None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
                    os.makedirs(log_dir, exist_ok=True)
                    log_stamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
                    build_log_path = os.path.abspath(os.path.join(
                        log_dir, f"{proj_name.lower()}_{log_stamp}.log"
                    ))
                    # Datei sofort anlegen, damit auch dann ein sichtbares Log
                    # existiert, wenn MSYS2 kein `script`-Programm mitbringt.
                    with open(build_log_path, "w", encoding="utf-8", errors="replace") as log_file:
                        log_file.write(
                            f"{proj_name} Build-Log\n"
                            f"Start: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}\n"
                            f"Arbeitsverzeichnis: {s3_dir}\n"
                            "=" * 72 + "\n"
                        )
                    log_path_bash = build_log_path.replace("\\", "/")
                    log_path_bash_q = "'" + log_path_bash.replace("'", "'\\''") + "'"
                    quoted_s3_cmd = "'" + s3_cmd.replace("'", "'\\''") + "'"
                    run_cmd = f"cd {s3_dir_bash_q} && {s3_cmd}"
                    quoted_run_cmd = "'" + run_cmd.replace("'", "'\\''") + "'"
                    bash_cmd = (
                        "export MSYSTEM=UCRT64; "
                        "export PATH=/ucrt64/bin:/usr/bin:/bin; "
                        f"cd {s3_dir_bash_q} || exit 2; "
                        "if command -v script >/dev/null 2>&1; then "
                        f"script -q -e -c {quoted_run_cmd} {log_path_bash_q}; result=$?; "
                        "else "
                        f"echo 'Hinweis: util-linux script nicht gefunden; kein Log-Mitschnitt.'; "
                        f"echo 'FEHLER: MSYS2-Programm script fehlt; Build-Ausgabe wird nicht mitgeschnitten.' >> {log_path_bash_q}; "
                        f"{s3_cmd}; result=$?; "
                        "fi; "
                        'echo; echo "Simplebuild beendet (Exit-Code: $result)"; '
                        f'echo "Protokoll: {log_path_bash}"; '
                        "exec bash -i"
                    )

                    subprocess.Popen(
                        [msys2_bash, "--login", "-i", "-c", bash_cmd],
                        env=bash_environment(),
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                    terminal_opened = True

                elif system == "Linux":
                    # Shell-Befehl als Argumente aufbauen, nicht als
                    # zusätzlich verschachtelten, gequoteten Befehl.
                    exec_cmd = (
                        f"cd {shlex.quote(s3_dir)} && "
                        f"{s3_cmd}"
                    )

            elif system == "Windows":
                subprocess.Popen(
                    ["cmd"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                )
                terminal_opened = True

            if system == "Linux" and not terminal_opened:
                terminals = [
                    ("x-terminal-emulator", "debian"),
                    ("gnome-terminal", "gnome"),
                    ("konsole", "kde"),
                    ("xfce4-terminal", "xfce"),
                    ("mate-terminal", "mate"),
                    ("lxterminal", "lx"),
                    ("xterm", "xterm"),
                    ("kgx", "gnome"),
                    ("ptyxis", "gnome"),
                    ("tilix", "tilix"),
                    ("kitty", "kitty"),
                    ("alacritty", "alacritty"),
                    ("wezterm", "wezterm"),
                    ("foot", "foot"),
                ]

                terminal_errors = []

                for term, kind in terminals:
                    terminal_path = shutil.which(term)
                    if not terminal_path:
                        continue

                    # Persistentes Terminalprotokoll: `script` erhält ein echtes
                    # Pseudo-TTY, damit die interaktiven SimpleBuild-Menüs weiterhin
                    # Eingaben annehmen können. Falls `script` fehlt, bleibt das
                    # bisherige Startverhalten unverändert.
                    # Protokolle immer im Verzeichnis ablegen, aus dem der
                    # Patch Manager gestartet wurde (nicht im Home-Cache).
                    log_dir = getattr(self, "build_log_dir", None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
                    os.makedirs(log_dir, exist_ok=True)
                    log_stamp = QDateTime.currentDateTime().toString("yyyyMMdd_HHmmss")
                    build_log_path = os.path.abspath(os.path.join(
                        log_dir, f"{proj_name.lower()}_{log_stamp}.log"
                    ))
                    with open(build_log_path, "w", encoding="utf-8", errors="replace") as log_file:
                        log_file.write(
                            f"{proj_name} Build-Log\n"
                            f"Start: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}\n"
                            f"Arbeitsverzeichnis: {s3_dir}\n"
                            "=" * 72 + "\n"
                        )
                    quoted_log_path = shlex.quote(build_log_path)
                    quoted_exec_cmd = shlex.quote(exec_cmd)
                    shell_command = (
                        f"cd {shlex.quote(s3_dir)} && "
                        "if command -v script >/dev/null 2>&1; then "
                        f"script -q -e -c {quoted_exec_cmd} {quoted_log_path}; result=$?; "
                        "else "
                        f"{exec_cmd}; result=$?; "
                        "echo 'Hinweis: util-linux script nicht gefunden; kein Log-Mitschnitt.'; "
                        f"echo 'FEHLER: util-linux script fehlt; Build-Ausgabe wird nicht mitgeschnitten.' >> {quoted_log_path}; "
                        "fi; "
                        f"echo; echo \"Simplebuild beendet (Exit-Code: $result)\"; "
                        f"echo \"Protokoll: {build_log_path}\"; "
                        "exec bash"
                    )

                    if kind == "debian":
                        args = [
                            terminal_path, "-e", "bash", "-lc",
                            shell_command,
                        ]
                    elif kind in ("gnome", "mate", "kde"):
                        args = [
                            terminal_path, "--", "bash", "-lc",
                            shell_command,
                        ]
                    elif kind == "xfce":
                        args = [
                            terminal_path, "--command",
                            f"bash -lc {shlex.quote(shell_command)}",
                        ]
                    elif kind == "lx":
                        args = [
                            terminal_path, "-e",
                            f"bash -lc {shlex.quote(shell_command)}",
                        ]
                    elif kind == "xterm":
                        args = [
                            terminal_path, "-e", "bash", "-lc",
                            shell_command,
                        ]
                    elif kind == "tilix":
                        args = [
                            terminal_path, "-e",
                            f"bash -lc {shlex.quote(shell_command)}",
                        ]
                    elif kind == "kitty":
                        args = [terminal_path, "bash", "-lc", shell_command]
                    elif kind == "alacritty":
                        args = [
                            terminal_path, "-e", "bash", "-lc",
                            shell_command,
                        ]
                    elif kind == "wezterm":
                        args = [
                            terminal_path, "start", "--",
                            "bash", "-lc", shell_command,
                        ]
                    elif kind == "foot":
                        args = [terminal_path, "bash", "-lc", shell_command]
                    else:
                        args = [
                            terminal_path, "-e", "bash", "-lc",
                            shell_command,
                        ]

                    try:
                        subprocess.Popen(args, start_new_session=True)
                        terminal_opened = True
                        break
                    except OSError as exc:
                        terminal_errors.append(f"{term}: {exc}")

                if not terminal_opened:
                    details = "\n".join(terminal_errors)
                    raise RuntimeError(
                        "Kein Terminal-Emulator gefunden oder gestartet."
                        + (f"\n{details}" if details else "")
                    )

            if "safe_play" in globals():
                safe_play("complete.oga")
            if pbar:
                # 100 % bedeutet hier nur: Terminalstart abgeschlossen.
                # Der eigentliche Build läuft im externen Terminal.
                pbar.setValue(100)
                pbar.setFormat(f"🖥️ {T_DONE}")
            if hasattr(self, "append_info") and hasattr(self, "info_text"):
                self.append_info(
                    self.info_text,
                    (
                        f"🖥️ [{QTime.currentTime().toString('HH:mm:ss')}] "
                        f"{proj_name}: Terminal geöffnet. Arbeitsverzeichnis: "
                        f"{os.path.dirname(s3_path) if s3_path else os.getcwd()}. "
                        f"Build-Ausgabe und Exit-Code erscheinen im externen Terminal. "
                        + (f"Protokoll: {build_log_path}. " if build_log_path else "")
                        + "Dieser Status bestätigt nur den Terminalstart."
                    )
                    if is_de else
                    (
                        f"🖥️ [{QTime.currentTime().toString('HH:mm:ss')}] "
                        f"{proj_name}: terminal opened. Working directory: "
                        f"{os.path.dirname(s3_path) if s3_path else os.getcwd()}. "
                        f"Build output and exit code appear in the external terminal. "
                        + (f"Log: {build_log_path}. " if build_log_path else "")
                        + "This status confirms only that the terminal started."
                    ),
                    "info",
                )

        except Exception as e:
            if "safe_play" in globals():
                safe_play("dialog-error.oga")
            if pbar:
                pbar.setFormat("❌ Error!")
            if hasattr(self, "append_info"):
                self.append_info(
                    self.info_text,
                    f"❌ Fehler: {str(e)}",
                    "error",
                )


            # 5. RESET NACH 3 SEKUNDEN
            if pbar:
                QTimer.singleShot(
                    3000,
                    (
                        self.pbar_idle
                        if hasattr(self, "pbar_idle")
                        else lambda: pbar.setValue(0)
                    ),
                )

    def restart_application_with_info(
        self, checked=False, progress_callback=None, info_widget=None
    ):
        """
        Sichert alle Daten und startet das Tool plattformübergreifend neu.
        Final-Label wird vorher ausgeblendet.
        """

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        from PyQt6.QtWidgets import QMessageBox, QApplication
        from PyQt6.QtCore import QTimer  # FIX: QTimer Import hinzugefügt
        import sys
        import os
        import subprocess

        # 1. Sprache & Texte sicherstellen
        lang_key = getattr(self, "LANG", "de").lower()
        lang_pack = (
            globals()
            .get("TEXTS", {})
            .get(lang_key, globals().get("TEXTS", {}).get("en", {}))
        )

        # 2. Dialog aufbauen
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(lang_pack.get("restart_tool", "Neustart"))
        msg.setText(
            lang_pack.get(
                "restart_tool_question", "Möchten Sie das Tool jetzt neu starten?"
            )
        )

        yes_btn = msg.addButton(
            lang_pack.get("yes", "Ja"), QMessageBox.ButtonRole.YesRole
        )
        no_btn = msg.addButton(
            lang_pack.get("no", "Nein"), QMessageBox.ButtonRole.NoRole
        )

        msg.exec()

        if msg.clickedButton() == yes_btn:
            # Sound abspielen
            # Neustart-Sound
            sound_manager = getattr(self, "sound_manager", None)
            if sound_manager and sound_manager.enabled:
                sound_manager.exit_sound.play()
                QApplication.processEvents()

            # --- KRITISCHES SPEICHERN VOR NEUSTART ---
            try:
                # Falls self.cfg existiert, stellen wir sicher, dass die aktuellen UI-Werte drin sind
                if hasattr(self, "cfg"):
                    # Manuelle Synchronisation der wichtigsten Felder (Sicherheitsnetz)
                    if hasattr(self, "patch_modifier"):
                        self.cfg["patch_modifier"] = self.patch_modifier
                    if hasattr(self, "EMUREPO"):
                        self.cfg["EMUREPO"] = self.EMUREPO
                    if hasattr(self, "LANG"):
                        self.cfg["language"] = self.LANG.upper()

                    # Speichern (Silent=True, da wir eh beenden)
                    if "save_config" in globals():
                        globals()["save_config"](
                            self.cfg, gui_instance=self, silent=True
                        )

                # WICHTIG: Gib dem OS kurz Zeit, die Datei physisch zu schreiben
                QApplication.processEvents()

            except Exception as e:
                print(f"⚠️ Save error before restart: {e}")

            # --- PLATTFORMÜBERGREIFENDER NEUSTART ---
            try:
                python_exe = sys.executable
                # FIX: Variable einheitlich auf 'script' benannt
                script = os.path.realpath(sys.argv[0])
                cmd_args = sys.argv[1:]

                # Starte neuen Prozess
                if os.name == "nt":
                    # FIX: 'script_path' zu 'script' korrigiert
                    subprocess.Popen(
                        [python_exe, script] + cmd_args,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                        close_fds=True,
                        shell=False,
                    )
                else:
                    # FIX: 'script_path' zu 'script' korrigiert
                    subprocess.Popen(
                        [python_exe, script] + cmd_args,
                        cwd=os.path.dirname(script),
                        start_new_session=True,
                        close_fds=True
                    )

                # Beende aktuelle Instanz sauber
                QApplication.processEvents()
                QTimer.singleShot(800, QApplication.quit)
                
            except Exception as e:
                print(f"❌ Kritischer Fehler beim Neustart: {e}")
                QApplication.quit()
                sys.exit(0)
        else:
            # Bei "Nein" Fortschrittsbalken (falls vorhanden) auf 100 setzen
            if progress_callback:
                try:
                    progress_callback(100)
                except:
                    pass

    def restart_application_elevated(self, *args, **kwargs):
        """Startet das Tool mit erhöhten Rechten neu."""
        import os
        import sys
        import shutil
        import platform
        import subprocess

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import QTimer

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"

        perform_update = bool(kwargs.get("perform_update", False))

        extra_args = (
            ["--perform-update"]
            if perform_update and "--perform-update" not in sys.argv
            else []
        )

        # Prüfen, ob der aktuelle Prozess bereits erhöhte Rechte besitzt.
        already_elevated = False

        if os.name == "nt":
            try:
                import ctypes
                already_elevated = bool(
                    ctypes.windll.shell32.IsUserAnAdmin()
                )
            except Exception:
                already_elevated = False

        elif hasattr(os, "geteuid"):
            already_elevated = os.geteuid() == 0

        
        if already_elevated:
            if perform_update:
                # Der laufende Prozess hat bereits erhöhte Rechte.
                return "already_elevated"

            QMessageBox.information(

                self,
                "Hinweis" if is_de else "Information",
                (
                    "Das Tool läuft bereits mit Administratorrechten."
                    if is_de
                    else "The application is already running with administrator privileges."
                ),
            )
            return True

        # Bei einem manuellen Admin-Neustart erst bestätigen lassen.
        if not perform_update:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle(
                "Administratorrechte" if is_de else "Administrator privileges"
            )
            msg_box.setText(
                "Das Tool mit erhöhten Rechten neu starten?"
                if is_de
                else "Restart the application with elevated privileges?"
            )

            yes_button = msg_box.addButton(
                "Ja" if is_de else "Yes",
                QMessageBox.ButtonRole.YesRole,
            )
            no_button = msg_box.addButton(
                "Nein" if is_de else "No",
                QMessageBox.ButtonRole.NoRole,
            )

            msg_box.setDefaultButton(no_button)
            msg_box.setEscapeButton(no_button)
            msg_box.exec()

            if msg_box.clickedButton() != yes_button:
                return False

        script = os.path.realpath(sys.argv[0])
        cwd = os.path.dirname(script) or os.getcwd()

        try:
            if os.name == "nt":
                import ctypes

                # Windows: Neustart über UAC.
                if getattr(sys, "frozen", False):
                    executable = sys.executable
                    params = subprocess.list2cmdline(
                        sys.argv[1:] + extra_args
                    )
                else:
                    executable = sys.executable
                    params = subprocess.list2cmdline(
                        [script] + sys.argv[1:] + extra_args
                    )

                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    executable,
                    params,
                    cwd,
                    1,
                )

                if result <= 32:
                    raise RuntimeError(
                        "ShellExecuteW Fehlercode: "
                        f"{result}\n"
                        f"Python: {sys.executable}\n"
                        f"Skript: {script}\n"
                        f"Argumente: {params}\n"
                        f"Arbeitsverzeichnis: {cwd}"
                    )

            elif platform.system() == "Linux":
                # Linux: Rechteerhöhung über PolicyKit.
                pkexec = shutil.which("pkexec")

                if not pkexec:
                    QMessageBox.warning(
                        self,
                        "Nicht verfügbar" if is_de else "Unavailable",
                        (
                            "pkexec ist nicht installiert. Bitte installiere "
                            "PolicyKit oder starte das Tool über deine "
                            "Systemverwaltung mit Root-Rechten."
                            if is_de
                            else
                            "pkexec is unavailable. Install PolicyKit or "
                            "start the application with root privileges."
                        ),
                    )
                    return False

                # Für die grafische Sitzung benötigte Variablen übernehmen.
                env_args = []

                for key in (
                    "DISPLAY",
                    "XAUTHORITY",
                    "WAYLAND_DISPLAY",
                    "XDG_RUNTIME_DIR",
                    "QT_QPA_PLATFORM",
                    "DBUS_SESSION_BUS_ADDRESS",
                ):
                    value = os.environ.get(key)
                    if value:
                        env_args.append(f"{key}={value}")

                if getattr(sys, "frozen", False):
                    command = (
                        [sys.executable] + sys.argv[1:] + extra_args
                    )
                else:
                    command = (
                        [sys.executable, script]
                        + sys.argv[1:]
                        + extra_args
                    )

                subprocess.Popen(
                    [pkexec, "env"] + env_args + command,
                    cwd=cwd,
                )

            else:
                QMessageBox.warning(
                    self,
                    "Nicht unterstützt" if is_de else "Unsupported",
                    (
                        "Diese Plattform wird nicht unterstützt."
                        if is_de
                        else "This platform is not supported."
                    ),
                )
                return False

            # Die bisherige GUI erst nach erfolgreichem Anstoßen beenden.
            QTimer.singleShot(500, QApplication.quit)
            return True

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Neustart fehlgeschlagen" if is_de else "Restart failed",
                str(exc),
            )
            return False

    def restart_application(self, *args, **kwargs):
        """Startet die Anwendung neu und zeigt kurz den Neon-Status an."""

        # --- Final Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        import subprocess
        import sys
        import os
        from PyQt6.QtWidgets import QApplication

        # --- Progress-Bar Feedback (Neon-Design) ---
        pbar = getattr(self, "progress_bar", None)
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        reboot_txt = "🔄 Neustart..." if lang == "de" else "🔄 Restarting..."

        if pbar:
            # Dein spezifisches Stylesheet (Dunkel, 20px, Neon-Gradient)
            rainbow = (
                "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, "
                "stop:0 #FF00FF, stop:0.5 #00FFFF, stop:1 #39FF14)"
            )
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #444444;
                    border-radius: 8px;
                    background-color: #0A0A0A;
                    color: black;
                    text-align: center;
                    font-weight: 900;
                    font-size: 20px;
                    min-height: 35px;
                }}
                QProgressBar::chunk {{
                    background-color: {rainbow};
                    border-radius: 6px;
                }}
            """)
            pbar.setValue(100)
            pbar.setFormat(reboot_txt)
            pbar.show()
            QApplication.processEvents()

        # Speichern vor dem Exit
        try:
            if hasattr(self, "cfg"):
                self.cfg["language"] = getattr(self, "LANG", "DE").upper()
                if "save_config" in globals():
                    # Zugriff auf die globale save_config Funktion
                    globals()["save_config"](self.cfg)
        except:
            pass

        # Sound abspielen
        # Neustart-Sound
        sound_manager = getattr(self, "sound_manager", None)
        if sound_manager and sound_manager.enabled:
            sound_manager.exit_sound.play()
            QApplication.processEvents()

        # PFAD-FIX für Windows (Leerzeichen in 'Program Files' etc.)
        python = sys.executable
        script = os.path.realpath(sys.argv[0]) # Nutzt sys.argv[0] für den korrekten Skript-Einstiegspunkt
        
        # --- FIX FÜR WINDOWS NEUSTART (Entkopplung des Prozesses) ---
        creation_flags = 0
        if platform.system() == "Windows":
            # Verhindert, dass der neue Prozess an der sterbenden alten CMD-Instanz hängen bleibt
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        try:
            subprocess.Popen(
                [python, script] + sys.argv[1:],
                cwd=os.path.dirname(script),
                creationflags=creation_flags
            )
        except Exception:
            # Fallback falls die Argumentenliste beschädigt ist
            subprocess.Popen([python, script], cwd=os.path.dirname(script), creationflags=creation_flags)

        # --- DER ENTSCHEIDENDE FIX: Altes GUI-Fenster hart schließen ---
        # Schließt die PyQt6-Schleife
        from PyQt6.QtCore import QEventLoop, QTimer

        if sound_manager and sound_manager.enabled:
            loop = QEventLoop()
            QTimer.singleShot(800, loop.quit)
            loop.exec()

        QApplication.quit()
        sys.exit(0)


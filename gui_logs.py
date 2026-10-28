"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerLogsMixin:
    """Patch Manager Logs"""

    def export_log(self):
        """Speichert Log als Textdatei mit originalem Sound-Code, Regenbogen und Gold-Reset."""
        import shutil, subprocess, os
        from datetime import datetime
        from PyQt6.QtWidgets import QFileDialog, QApplication
        from PyQt6.QtCore import QTimer

        # --- 1. ORIGINAL SOUND BEIM STARTEN (Klick) ---
        for player in ["paplay", "pw-play", "aplay"]:
            if shutil.which(player):
                start_sound = (
                    "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"
                )
                if os.path.exists(start_sound):
                    subprocess.Popen(
                        [player, start_sound],
                        stderr=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                    )
                break

        text = self.info_text.toPlainText()
        if not text.strip():
            return

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

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
            pbar.setFormat("📝 " + ("Speichere Log..." if is_de else "Saving Log..."))
            pbar.setValue(30)
            pbar.show()
            QApplication.processEvents()

        # 3. DATEI-DIALOG
        t_title = "Log speichern" if is_de else "Save Log"
        t_filter = "Textdateien (*.txt)" if is_de else "Text Files (*.txt)"
        filename = (
            f"oscam_patch_manager_log_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        )

        file_path, _ = QFileDialog.getSaveFileName(self, t_title, filename, t_filter)

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(text)

                # Erfolgsmeldung im Log-Fenster
                if hasattr(self, "append_info"):
                    self.append_info(
                        self.info_text, f"✅ Log gespeichert: {file_path}", "success"
                    )

                # --- 4. ORIGINAL SOUND BEIM ERFOLG ---
                for player in ["paplay", "pw-play", "aplay"]:
                    if shutil.which(player):
                        success_sound = (
                            "/usr/share/sounds/freedesktop/stereo/complete.oga"
                        )
                        if os.path.exists(success_sound):
                            subprocess.Popen(
                                [player, success_sound],
                                stderr=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL,
                            )
                        break

                if pbar:
                    pbar.setValue(100)
                    pbar.setFormat("✅ " + ("Gespeichert!" if is_de else "Saved!"))

            except Exception as e:
                if hasattr(self, "append_info"):
                    self.append_info(self.info_text, f"❌ Fehler: {e}", "error")
        else:
            # Abgebrochen
            if pbar:
                pbar.setValue(0)

        # 5. AUTO-RESET ZU DEINEM GOLD-BLINKEN (pbar_idle)
        if hasattr(self, "pbar_idle"):
            QTimer.singleShot(2500, self.pbar_idle)

    def copy_to_clipboard(self):
        """Kopiert den Log in die Zwischenablage."""
        QApplication.clipboard().setText(self.info_text.toPlainText())
        # Einheitlicher Feedback-Ton auf Windows und Linux.
        safe_play("dialog-information.oga")

    def log_message(self, message):
        """Zentrale Funktion: Zeit in ROT, Inhalt in CYAN - sauber untereinander."""
        from datetime import datetime

        now = datetime.now().strftime("%H:%M:%S")

        # 1. Sicherstellen, dass wir eine neue Zeile haben
        self.info_text.append("")

        # 2. HTML-Zeile bauen (Zeit ROT, Nachricht CYAN/Inhalt)
        full_html = f"<span style='color:red;'>[{now}]</span> {message}"

        # 3. Cursor ans Ende und HTML einfügen
        self.info_text.moveCursor(QTextCursor.MoveOperation.End)
        self.info_text.insertHtml(full_html)

        # 4. Scrollen
        self.info_text.moveCursor(QTextCursor.MoveOperation.End)

    def scroll_to_bottom_smooth(self):
        """Scrollt das Info-Fenster sanft nach unten."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

        if not hasattr(self, "info_text") or not self.info_text:
            return

        scrollbar = self.info_text.verticalScrollBar()

        # Animation für die Eigenschaft 'value' der Scrollbar
        self.scroll_anim = QPropertyAnimation(scrollbar, b"value")
        self.scroll_anim.setDuration(300)  # Dauer in ms
        self.scroll_anim.setStartValue(scrollbar.value())
        self.scroll_anim.setEndValue(scrollbar.maximum())

        # Eine sanfte Kurve (beschleunigt und bremst ab)
        self.scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_anim.start()

    def analyze_latest_build_log(self):
        """Crash-safe entry point for the BUILD-LOG analysis button."""
        try:
            return self._analyze_latest_build_log_impl()
        except Exception as exc:
            # Exceptions escaping a PyQt button slot can terminate the whole GUI.
            # Keep this diagnostic action isolated and report the failure in the console.
            import traceback
            is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
            message = (
                f"BUILD-LOG-Analyse abgebrochen; die GUI bleibt geöffnet. Details: {exc}"
                if is_de else
                f"BUILD LOG analysis stopped; the GUI will remain open. Details: {exc}"
            )
            try:
                info = getattr(self, "info_text", None)
                if info is not None and hasattr(self, "append_info"):
                    self.append_info(info, message, "error")
                else:
                    print(message)
                print(traceback.format_exc())
            except Exception:
                print(message)
                traceback.print_exc()
            return None

    def _analyze_latest_build_log_impl(self):
        """Analyze recent build logs with project, completion and error indicators."""
        import os
        import re
        from datetime import datetime
        from PyQt6.QtCore import QDateTime
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox

        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")

        def show_analysis_window(window_title, body, severity="info"):
            """Display analysis results in a dedicated, read-only window."""
            result_dialog = QDialog(self)
            result_dialog.setWindowTitle(window_title)
            result_dialog.resize(900, 650)
            result_layout = QVBoxLayout(result_dialog)
            heading = QLabel(window_title, result_dialog)
            heading.setWordWrap(True)
            result_layout.addWidget(heading)
            result_text = QTextEdit(result_dialog)
            result_text.setReadOnly(True)
            result_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            result_text.setPlainText(str(body))
            result_layout.addWidget(result_text, 1)
            button_row = QHBoxLayout()
            copy_button = QPushButton("Text kopieren" if is_de else "Copy text", result_dialog)
            copy_button.clicked.connect(lambda: QApplication.clipboard().setText(result_text.toPlainText()))
            close_button = QPushButton("Schließen" if is_de else "Close", result_dialog)
            close_button.clicked.connect(result_dialog.accept)
            button_row.addWidget(copy_button)
            button_row.addStretch(1)
            button_row.addWidget(close_button)
            result_layout.addLayout(button_row)
            result_dialog.setModal(True)
            result_dialog.exec()

        log_dir = getattr(self, "build_log_dir", None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
        try:
            candidates = [
                os.path.join(log_dir, name)
                for name in os.listdir(log_dir)
                if name.lower().endswith(".log") and os.path.isfile(os.path.join(log_dir, name))
            ]
        except OSError as exc:
            message = (f"Build-Log-Ordner kann nicht gelesen werden: {exc}" if is_de else f"Cannot read build-log directory: {exc}")
            show_analysis_window("BUILD-LOG-ANALYSE" if is_de else "BUILD LOG ANALYSIS", message, "error")
            return

        if not candidates:
            message = (f"Keine Build-Logs gefunden. Erwarteter Ordner: {log_dir}" if is_de
                       else f"No build logs found. Expected folder: {log_dir}")
            show_analysis_window("BUILD-LOG-ANALYSE" if is_de else "BUILD LOG ANALYSIS", message, "warning")
            return

        candidates.sort(key=os.path.getmtime, reverse=True)
        latest_path = candidates[0]
        try:
            with open(latest_path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
            lines = content.splitlines()
        except OSError as exc:
            message = (f"Log konnte nicht gelesen werden: {exc}" if is_de else f"Could not read log: {exc}")
            show_analysis_window("BUILD-LOG-ANALYSE" if is_de else "BUILD LOG ANALYSIS", message, "error")
            return

        error_pattern = re.compile(
            r"\b(error:|fatal error:|undefined reference|no such file or directory|"
            r"command not found|cannot find|failed|failure|error\s*\[|make\[[0-9]+\]: \*\*\*)",
            re.IGNORECASE,
        )
        warning_pattern = re.compile(r"\bwarning:|\bdeprecated\b", re.IGNORECASE)
        errors = [(i + 1, line.strip()) for i, line in enumerate(lines) if error_pattern.search(line)]
        warnings = [(i + 1, line.strip()) for i, line in enumerate(lines) if warning_pattern.search(line)]

        exit_matches = re.findall(r"(?:Exit-Code|exit code):\s*(-?\d+)", content, re.IGNORECASE)
        exit_code = exit_matches[-1] if exit_matches else None
        finished_match = re.search(r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", content, re.IGNORECASE)
        started_marker = "SIMPLEBUILD_STARTED" in content
        finished_marker = finished_match is not None
        if finished_marker:
            status_code = finished_match.group(1)
            status = (("ERFOLGREICH" if status_code == "0" else "FEHLGESCHLAGEN") if is_de
                      else ("SUCCESSFUL" if status_code == "0" else "FAILED"))
        elif started_marker:
            status = "GESTARTET – Abschlussmarker fehlt" if is_de else "STARTED – completion marker missing"
        elif exit_code is not None:
            status = (("ERFOLGREICH (Exit-Code 0)" if exit_code == "0" else f"FEHLGESCHLAGEN (Exit-Code {exit_code})") if is_de
                      else ("SUCCESSFUL (exit code 0)" if exit_code == "0" else f"FAILED (exit code {exit_code})"))
        elif errors:
            status = "FEHLERHINWEISE GEFUNDEN – Ergebnis nicht bestätigt" if is_de else "ERROR INDICATORS FOUND – outcome not confirmed"
        else:
            status = "UNBEKANNT – kein eindeutiger Abschlussmarker" if is_de else "UNKNOWN – no definitive completion marker"

        # Extract a likely project label from the log header or filename; never infer success from the name.
        project_match = re.search(r"^\s*(.+?)\s+Build-Log\s*$", content, re.IGNORECASE | re.MULTILINE)
        project = project_match.group(1).strip() if project_match else os.path.basename(latest_path).rsplit("_", 1)[0]
        start_match = re.search(r"^\s*Start:\s*(.+)$", content, re.IGNORECASE | re.MULTILINE)
        finish_match = re.search(r"^.*(?:Simplebuild beendet|Ergebnis):.*$", content, re.IGNORECASE | re.MULTILINE)

        summary = [
            "=" * 54,
            (f"BUILD-LOG-Analyse: {os.path.basename(latest_path)}" if is_de else f"BUILD LOG ANALYSIS: {os.path.basename(latest_path)}"),
            (f"Projekt: {project}" if is_de else f"Project: {project}"),
            (f"Status: {status}" if is_de else f"Status: {status}"),
            (f"Analysiert am: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}" if is_de else f"Analyzed at: {QDateTime.currentDateTime().toString('yyyy-MM-dd HH:mm:ss')}"),
            (f"Log geändert: {datetime.fromtimestamp(os.path.getmtime(latest_path)).astimezone().isoformat(timespec='seconds')}" if is_de else f"Log modified: {datetime.fromtimestamp(os.path.getmtime(latest_path)).astimezone().isoformat(timespec='seconds')}"),
        ]
        if start_match:
            summary.append((f"Startzeit: {start_match.group(1).strip()}" if is_de else f"Start time: {start_match.group(1).strip()}"))
        if finish_match:
            summary.append((f"Abschlusszeile: {finish_match.group(0).strip()}" if is_de else f"Completion line: {finish_match.group(0).strip()}"))
        summary.append((f"Fehler-Treffer: {len(errors)} | Warnungen: {len(warnings)}" if is_de else f"Error matches: {len(errors)} | Warnings: {len(warnings)}"))
        if exit_code is not None:
            summary.append(f"Exit-Code: {exit_code}")
        if errors:
            summary.append("--- Fehler ---" if is_de else "--- Errors ---")
            summary.extend(f"Zeile {number}: {line}" for number, line in errors[:25])
        if warnings:
            summary.append("--- Warnungen (max. 15) ---" if is_de else "--- Warnings (max. 15) ---")
            summary.extend(f"Zeile {number}: {line}" for number, line in warnings[:15])
        if not errors and not warnings:
            summary.append("Keine typischen Fehler-/Warnungsmuster gefunden; das ist kein sicherer Erfolgsnachweis." if is_de
                           else "No common error/warning patterns found; this does not guarantee success.")
        summary.append((f"Vollständiges Log: {latest_path}" if is_de else f"Full log: {latest_path}"))

        # Compact overview of the next four newest logs helps compare projects without opening files manually.
        if len(candidates) > 1:
            summary.append("--- Weitere aktuelle Logs ---" if is_de else "--- Other recent logs ---")
            for path in candidates[1:5]:
                try:
                    with open(path, "r", encoding="utf-8", errors="replace") as handle:
                        sample = handle.read()
                    marker = re.search(r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", sample, re.IGNORECASE)
                    exit_found = re.findall(r"(?:Exit-Code|exit code):\s*(-?\d+)", sample, re.IGNORECASE)
                    if marker:
                        state = (("Erfolg" if marker.group(1) == "0" else "Fehler") if is_de else ("Success" if marker.group(1) == "0" else "Failed"))
                    elif "SIMPLEBUILD_STARTED" in sample:
                        state = "Abschluss fehlt" if is_de else "Completion missing"
                    elif exit_found:
                        state = (("Erfolg" if exit_found[-1] == "0" else "Fehler") if is_de else ("Success" if exit_found[-1] == "0" else "Failed"))
                    else:
                        state = "Unbekannt" if is_de else "Unknown"
                    summary.append(f"{os.path.basename(path)} — {state}")
                except OSError:
                    summary.append(f"{os.path.basename(path)} — " + ("nicht lesbar" if is_de else "unreadable"))
        report_text = "\n".join(summary)
        show_analysis_window(
            (f"BUILD-LOG-ANALYSE – {os.path.basename(latest_path)}" if is_de else f"BUILD LOG ANALYSIS – {os.path.basename(latest_path)}"),
            report_text,
            "error" if errors or (exit_code is not None and exit_code != "0") else ("warning" if "UNKNOWN" in status.upper() or "UNBEKANNT" in status.upper() or warnings else "info"),
        )

    def append_info(self, *args, **kwargs):
        from PyQt6.QtGui import QTextCursor
        from PyQt6.QtWidgets import QApplication, QTextEdit
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation

        # 1. Argumente sicher entpacken
        try:
            if len(args) == 3:
                widget, text, level = args[0], args[1], args[2]
            elif len(args) == 2:
                widget = getattr(self, "info_text", None)
                text, level = args[0], args[1]
            else:
                return
        except:
            return

        if not isinstance(widget, QTextEdit) or widget is None:
            return

        # Vor dem Einfügen merken, ob der Benutzer bereits am Ende liest.
        # Nur dann später automatisch nach unten scrollen.
        scrollbar = widget.verticalScrollBar()
        was_at_bottom = (
            scrollbar is None
            or scrollbar.value() >= scrollbar.maximum() - 2
        )

        # 2. Farben & Variablen
        colors = {
            "success": "#00FF00",
            "warning": "orange",
            "error": "red",
            "info": "yellow",
            "white": "white",
            "raw": "transparent",
        }
        lvl_str = str(level).lower()
        current_color = colors.get(lvl_str, "white")
        do_newline = kwargs.get("newline", True)

        # Persist only noteworthy events; ordinary build output stays in the live
        # console so the event history remains compact. Logging failures must
        # never interfere with the GUI or the original operation.
        if lvl_str in ("error", "warning", "success"):
            try:
                import json
                import os
                from datetime import datetime
                from pathlib import Path

                log_root = Path(os.path.dirname(os.path.abspath(__file__))) / "event_history"
                log_root.mkdir(parents=True, exist_ok=True)
                event_file = log_root / "events.jsonl"
                max_bytes = 2 * 1024 * 1024
                if event_file.exists() and event_file.stat().st_size >= max_bytes:
                    backup = log_root / "events.previous.jsonl"
                    try:
                        if backup.exists():
                            backup.unlink()
                        event_file.replace(backup)
                    except OSError:
                        # Continue without rotation if the file is locked.
                        pass
                event = {
                    "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "level": lvl_str,
                    "message": str(text)[:4000],
                }
                with event_file.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False) + "\n")
            except Exception:
                pass

        
        # 3. HTML vorbereiten
        from html import escape as _html_escape

        html_output = ""
        if do_newline and widget.toPlainText().strip() != "":
            html_output += "<br>"

        if lvl_str == "html":
            # Nur für bewusst erzeugte, formatierte HTML-Ausgaben.
            html_output += str(text)
        else:
            # Normale Meldungen bleiben sicherer Klartext.
            safe_text = (
                _html_escape(str(text))
                .replace("\r", "")
                .replace("\n", "<br>")
            )

            if lvl_str == "raw":
                html_output += f'<div style="display:inline;">{safe_text}</div>'
            else:
                html_output += (
                    f'<div style="color:{current_color}; display:inline;">'
                    f'{safe_text}</div>'
                )


        # 4. Am Ende einfügen
        # NIEMALS setHtml()/clear()/setPlainText() verwenden:
        # append_info ist bewusst nicht-destruktiv, damit der komplette
        # große Infoscreen mit allen bisherigen Meldungen sichtbar bleibt.
        cursor = widget.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        widget.setTextCursor(cursor)
        cursor.insertHtml(html_output)

        # 5. Scroll-Verhalten: nur automatisch folgen, wenn der Benutzer
        # vor der neuen Meldung bereits am unteren Ende der Konsole war.
        if was_at_bottom and scrollbar is not None:
            scrollbar.setValue(scrollbar.maximum())
            widget.ensureCursorVisible()

    def log(self, msg, level="info"):
        """
        Gibt Nachrichten im Infoscreen aus.
        Nutzt die vorhandene append_info Logik, um den THEME-Fehler zu vermeiden.
        """
        from PyQt6.QtGui import QTextCursor
        from PyQt6.QtWidgets import QApplication

        # Wir nutzen deine funktionierende append_info statt dem kaputten THEME-Dictionary
        if hasattr(self, "append_info") and hasattr(self, "info_text"):
            self.append_info(self.info_text, msg, level)
        else:
            # Notfall-Fallback falls append_info nicht erreichbar ist
            self.info_text.append(msg)

        # Sicherstellen, dass das Fenster zum Ende scrollt
        self.info_text.moveCursor(QTextCursor.MoveOperation.End)

        # GUI aktualisieren, damit der Text sofort erscheint (wichtig bei Prozessen)
        QApplication.processEvents()

    def open_build_log_history(self):
        """Crash-safe entry point: history errors must never escape a Qt slot."""
        try:
            return self._open_build_log_history_impl()
        except Exception as exc:
            import traceback
            is_de = str(getattr(self, "LANG", LANG)).lower().startswith("de")
            title = "Fehler im Build-Log-Verlauf" if is_de else "Build log history error"
            message = (("Der Build-Log-Verlauf konnte nicht geöffnet werden. Die Haupt-GUI bleibt geöffnet.\n\n" if is_de
                        else "Build log history could not be opened. The main GUI will remain open.\n\n")
                       + f"{type(exc).__name__}: {exc}")
            try:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, title, message)
            except Exception:
                print(message)
            traceback.print_exc()
            return None

    def _open_build_log_history_impl(self):
        """Show a read-only, bilingual overview of existing build logs."""
        import os
        import re
        import csv
        from datetime import datetime
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                     QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
                                     QHeaderView, QLineEdit, QComboBox, QTextEdit)
        from PyQt6.QtCore import QTimer

        is_de = str(getattr(self, "LANG", LANG)).lower().startswith("de")
        title = "BUILD-LOG-VERLAUF" if is_de else "BUILD LOG HISTORY"
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(1080, 650)
        # Avoid forcing a very wide window on smaller displays; action buttons
        # are already arranged in separate rows below.
        dialog.setMinimumSize(720, 500)
        layout = QVBoxLayout(dialog)
        summary_label = QLabel()
        layout.addWidget(summary_label)
        filter_row = QHBoxLayout()
        search_label = QLabel("Suche:" if is_de else "Search:")
        search_input = QLineEdit()
        search_input.setPlaceholderText("Dateiname oder Status…" if is_de else "Filename or status…")
        status_filter = QComboBox()
        status_filter.addItems((["Alle Status", "Erfolgreich", "Fehlgeschlagen", "Unbekannt", "Gestartet", "Lesefehler"] if is_de
                                else ["All statuses", "Successful", "Failed", "Unknown", "Started", "Read error"]))
        issue_filter = QComboBox()
        issue_filter.addItems((['Alle Logs', 'Mit Fehlern', 'Mit Fehlern oder Warnungen'] if is_de
                               else ['All logs', 'With errors', 'With errors or warnings']))
        issue_filter.setToolTip('Nach Fehlern und Warnungen filtern' if is_de else 'Filter by errors and warnings')
        filter_row.addWidget(search_label)
        filter_row.addWidget(search_input, 1)
        filter_row.addWidget(status_filter)
        filter_row.addWidget(issue_filter)
        layout.addLayout(filter_row)
        headers = (["Projekt/Datei", "Status", "Geändert", "Größe", "Fehler", "Warnungen"] if is_de
                   else ["Project/File", "Status", "Modified", "Size", "Errors", "Warnings"])
        table = QTableWidget(0, len(headers), dialog)
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in range(1, len(headers)):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(table, 1)

        def scan_logs():
            log_dir = getattr(self, "build_log_dir", None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
            rows = []
            try:
                # Collect file metadata once (rather than calling stat repeatedly during sorting).
                # Limit the overview to the newest 500 logs to keep refreshes predictable.
                candidates = []
                for name in os.listdir(log_dir):
                    if not name.lower().endswith(".log"):
                        continue
                    path = os.path.join(log_dir, name)
                    try:
                        stat = os.stat(path)
                        if os.path.isfile(path):
                            candidates.append((stat.st_mtime, name, stat.st_size))
                    except OSError:
                        # Keep inaccessible entries visible if their metadata can no longer be read.
                        candidates.append((0, name, None))
                candidates.sort(key=lambda entry: entry[0], reverse=True)
                max_log_files = 500
                names = [(name, size) for _, name, size in candidates[:max_log_files]]
                omitted_count = max(0, len(candidates) - len(names))
            except OSError as exc:
                return [], f"{('Log-Ordner nicht lesbar' if is_de else 'Log directory unreadable')}: {exc}"
            error_re = re.compile(r"\b(error:|fatal error:|undefined reference|command not found|failed|failure|make\[[0-9]+\]: \*\*\*)", re.I)
            warning_re = re.compile(r"\bwarning:|\bdeprecated\b", re.I)
            # A per-file cap alone could still read several gigabytes when hundreds
            # of logs exist. Bound the complete refresh as well as each individual log.
            total_scan_budget = 32 * 1024 * 1024
            scanned_bytes = 0
            for name, known_size in names:
                path = os.path.join(log_dir, name)
                try:
                    max_scan_bytes = 8 * 1024 * 1024
                    remaining_budget = max(0, total_scan_budget - scanned_bytes)
                    if remaining_budget == 0:
                        rows.append({"file": name, "path": path,
                                     "status": "Unbekannt (Scan-Limit)" if is_de else "Unknown (scan limit)",
                                     "modified": datetime.fromtimestamp(os.path.getmtime(path)).astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                                     "size": known_size if isinstance(known_size, int) else "",
                                     "errors": "", "warnings": "", "scan_truncated": True,
                                     "scan_limited": True})
                        continue
                    # Counts/status are based on the sampled prefix for oversized files.
                    read_limit = min(max_scan_bytes, remaining_budget)
                    with open(path, "rb") as fh:
                        raw_content = fh.read(read_limit)
                    scanned_bytes += len(raw_content)
                    scan_truncated = (isinstance(known_size, int) and known_size > len(raw_content)) or len(raw_content) == read_limit
                    content = raw_content.decode("utf-8", errors="replace")
                    finished = re.findall(r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", content, re.I)
                    exit_codes = re.findall(r"(?:Exit-Code|exit code):\s*(-?\d+)", content, re.I)
                    if finished:
                        code = finished[-1]
                        status = (("Erfolgreich" if code == "0" else f"Fehlgeschlagen ({code})") if is_de else ("Successful" if code == "0" else f"Failed ({code})"))
                    elif "SIMPLEBUILD_STARTED" in content:
                        status = "Gestartet – Abschluss fehlt" if is_de else "Started – completion missing"
                    elif exit_codes:
                        code = exit_codes[-1]
                        status = (("Erfolgreich" if code == "0" else f"Fehlgeschlagen ({code})") if is_de else ("Successful" if code == "0" else f"Failed ({code})"))
                    else:
                        status = "Unbekannt" if is_de else "Unknown"
                    errors = len(error_re.findall(content))
                    warnings = len(warning_re.findall(content))
                    modified = datetime.fromtimestamp(os.path.getmtime(path)).astimezone().strftime("%Y-%m-%d %H:%M:%S")
                    file_size = known_size if isinstance(known_size, int) else os.path.getsize(path)
                    rows.append({"file": name, "path": path, "status": status, "modified": modified,
                                 "size": file_size, "errors": errors, "warnings": warnings,
                                 "scan_truncated": scan_truncated, "scan_limited": False})
                except OSError:
                    rows.append({"file": name, "path": path, "status": "Lesefehler" if is_de else "Read error",
                                 "modified": "", "size": "", "errors": "", "warnings": ""})
            if omitted_count:
                limit_note = (f"Anzeige auf die {max_log_files} neuesten Logs begrenzt; {omitted_count} ältere Logs ausgelassen."
                              if is_de else
                              f"Showing the {max_log_files} newest logs; omitted {omitted_count} older logs.")
            else:
                limit_note = None
            return rows, limit_note

        current_rows = []
        all_rows = []
        current_problem = None

        def safe_callback(callback, *args):
            """Keep exceptions in Qt signal callbacks from taking down the GUI."""
            try:
                return callback(*args)
            except Exception as exc:
                try:
                    if 'live_timer' in locals():
                        live_timer.stop()
                except Exception:
                    pass
                try:
                    QMessageBox.warning(
                        dialog,
                        "Fehler im Build-Log-Verlauf" if is_de else "Build log history error",
                        ("Der Build-Log-Verlauf konnte diesen Schritt nicht ausführen. Die GUI bleibt geöffnet.\n\n" if is_de
                         else "Build log history could not complete this action. The GUI will remain open.\n\n")
                        + f"{type(exc).__name__}: {exc}",
                    )
                except Exception:
                    pass
                return None

        def render_rows():
            nonlocal current_rows
            # Preserve selected log filenames when filters or a refresh rebuild the table.
            previously_selected = set()
            try:
                for selected_index in table.selectionModel().selectedRows():
                    old_row = selected_index.row()
                    if 0 <= old_row < len(current_rows):
                        previously_selected.add(str(current_rows[old_row].get("file", "")))
            except Exception:
                previously_selected = set()
            query = search_input.text().strip().casefold()
            selected_status = status_filter.currentText().casefold()
            all_statuses = {"alle status", "all statuses"}
            visible = []
            for item in all_rows:
                haystack = (str(item["file"]) + " " + str(item["status"]) + " " + str(item["path"])).casefold()
                status_text = str(item["status"]).casefold()
                if query and query not in haystack:
                    continue
                selected_issue = issue_filter.currentText().casefold()
                issue_errors = selected_issue in ("mit fehlern", "with errors")
                issue_errors_warnings = selected_issue in ("mit fehlern oder warnungen", "with errors or warnings")
                try:
                    error_count = int(item.get("errors", 0) or 0)
                    warning_count = int(item.get("warnings", 0) or 0)
                except (TypeError, ValueError):
                    error_count, warning_count = 0, 0
                if issue_errors and error_count <= 0:
                    continue
                if issue_errors_warnings and error_count <= 0 and warning_count <= 0:
                    continue
                if selected_status not in all_statuses:
                    if selected_status in ("fehlgeschlagen", "failed"):
                        if not ("fehlgeschlagen" in status_text or "failed" in status_text): continue
                    elif selected_status in ("erfolgreich", "successful"):
                        if not ("erfolgreich" in status_text or "successful" in status_text): continue
                    elif selected_status in ("unbekannt", "unknown"):
                        if not ("unbekannt" in status_text or "unknown" in status_text): continue
                    elif selected_status in ("gestartet", "started"):
                        if not ("gestartet" in status_text or "started" in status_text): continue
                    elif selected_status in ("lesefehler", "read error"):
                        if not ("lesefehler" in status_text or "read error" in status_text): continue
                visible.append(item)
            current_rows = visible
            # Batch table painting to reduce flicker and UI overhead when many logs are shown.
            table.setUpdatesEnabled(False)
            try:
                table.setRowCount(len(current_rows))
                for r, item in enumerate(current_rows):
                    values = [item["file"], item["status"], item["modified"],
                              (f'{item["size"]:,} B' if isinstance(item["size"], int) else str(item["size"])),
                              str(item["errors"]), str(item["warnings"])]
                    for c, value in enumerate(values):
                        cell = QTableWidgetItem(value)
                        if c == 0:
                            tip = item["path"]
                            if item.get("scan_limited"):
                                tip += ("\nInhaltsanalyse wegen des Gesamtlimits von 32 MiB übersprungen; Status und Trefferzahlen sind unbekannt."
                                        if is_de else
                                        "\nContent scan skipped due to the 32 MiB total limit; status and counts are unknown.")
                            elif item.get("scan_truncated"):
                                tip += ("\nInhaltsanalyse begrenzt; Fehler-/Warnungszahlen können unvollständig sein."
                                        if is_de else
                                        "\nContent scan was limited; error/warning counts may be incomplete.")
                            cell.setToolTip(tip)
                        table.setItem(r, c, cell)
                    if str(item.get("file", "")) in previously_selected:
                        table.selectRow(r)
            finally:
                table.setUpdatesEnabled(True)
            failed = sum("fehl" in str(x["status"]).lower() or "fail" in str(x["status"]).lower() for x in current_rows)
            unknown = sum("unbekannt" in str(x["status"]).lower() or "unknown" in str(x["status"]).lower() for x in current_rows)
            summary = (f"{len(current_rows)} von {len(all_rows)} Logs angezeigt · {failed} fehlgeschlagen · {unknown} unbekannt" if is_de
                       else f"Showing {len(current_rows)} of {len(all_rows)} logs · {failed} failed · {unknown} unknown")
            if current_problem:
                summary += " — " + current_problem
            summary_label.setText(summary)

        def refresh():
            nonlocal all_rows, current_problem
            all_rows, current_problem = scan_logs()
            render_rows()

        def preview_log(row, column=0):
            if row < 0 or row >= len(current_rows):
                return
            item = current_rows[row]
            preview = QDialog(dialog)
            preview.setWindowTitle(("Log ansehen: " if is_de else "View log: ") + item["file"])
            preview.resize(900, 600)
            preview_layout = QVBoxLayout(preview)
            path_label = QLabel(item["path"])
            path_label.setWordWrap(True)
            preview_layout.addWidget(path_label)
            text_view = QTextEdit(preview)
            text_view.setReadOnly(True)
            try:
                preview_limit = 8 * 1024 * 1024
                with open(item["path"], "rb") as log_file:
                    raw_preview = log_file.read(preview_limit + 1)
                preview_truncated = len(raw_preview) > preview_limit
                preview_text = raw_preview[:preview_limit].decode("utf-8", errors="replace")
                if preview_truncated:
                    preview_text += ("\n\n[Ansicht gekürzt: nur die ersten 8 MiB werden angezeigt.]"
                                     if is_de else
                                     "\n\n[Preview truncated: showing only the first 8 MiB.] ")
                text_view.setPlainText(preview_text)
            except OSError as exc:
                text_view.setPlainText(("Log konnte nicht gelesen werden: " if is_de else "Could not read log: ") + str(exc))
            preview_layout.addWidget(text_view, 1)
            close_preview = QPushButton("Schließen" if is_de else "Close")
            close_preview.clicked.connect(preview.accept)
            preview_layout.addWidget(close_preview)
            preview.exec()

        def compare_selected_logs():
            """Compare exactly two selected logs in a separate, read-only diff window."""
            selected_indexes = sorted({index.row() for index in table.selectionModel().selectedRows()})
            if len(selected_indexes) != 2:
                QMessageBox.information(
                    dialog, "Hinweis" if is_de else "Notice",
                    "Bitte genau zwei Logs auswählen (Strg-Klick für Mehrfachauswahl)." if is_de else
                    "Please select exactly two logs (Ctrl-click to select multiple rows)."
                )
                return
            first, second = (current_rows[i] for i in selected_indexes)
            diff_dialog = QDialog(dialog)
            diff_dialog.setWindowTitle(("Build-Logs vergleichen: " if is_de else "Compare build logs: ") + first["file"] + " ↔ " + second["file"])
            diff_dialog.resize(1000, 680)
            diff_layout = QVBoxLayout(diff_dialog)
            details = QLabel(
                (f"ALT: {first['file']}  |  Status: {first['status']}\nNEU: {second['file']}  |  Status: {second['status']}" if is_de else
                 f"FIRST: {first['file']}  |  Status: {first['status']}\nSECOND: {second['file']}  |  Status: {second['status']}")
            )
            details.setWordWrap(True)
            diff_layout.addWidget(details)
            diff_view = QTextEdit(diff_dialog)
            diff_view.setReadOnly(True)
            diff_layout.addWidget(diff_view, 1)
            try:
                import difflib
                max_bytes = 2 * 1024 * 1024
                def read_limited(path):
                    with open(path, "rb") as source:
                        data = source.read(max_bytes + 1)
                    truncated = len(data) > max_bytes
                    data = data[:max_bytes]
                    return data.decode("utf-8", errors="replace").splitlines(), truncated
                first_lines, first_truncated = read_limited(first["path"])
                second_lines, second_truncated = read_limited(second["path"])
                diff_lines = list(difflib.unified_diff(
                    first_lines, second_lines,
                    fromfile=first["file"], tofile=second["file"], lineterm=""
                ))
                if first_truncated or second_truncated:
                    diff_lines.append("")
                    diff_lines.append("[" + ("Datei gekürzt: maximal 2 MiB je Log." if is_de else "File truncated: maximum 2 MiB per log.") + "]")
                if diff_lines:
                    diff_view.setPlainText("\n".join(diff_lines))
                else:
                    diff_view.setPlainText("Die Inhalte sind identisch." if is_de else "The contents are identical.")
            except OSError as exc:
                diff_view.setPlainText(("Vergleich fehlgeschlagen: " if is_de else "Comparison failed: ") + str(exc))
            close_diff = QPushButton("Schließen" if is_de else "Close")
            close_diff.clicked.connect(diff_dialog.accept)
            diff_layout.addWidget(close_diff)
            diff_dialog.exec()

        def export_csv():
            if not current_rows:
                QMessageBox.information(dialog, "Hinweis" if is_de else "Notice",
                                        "Keine Logs zum Exportieren vorhanden." if is_de else "No logs available to export.")
                return
            path, _ = QFileDialog.getSaveFileName(dialog, "Log-Verlauf als CSV speichern" if is_de else "Save log history as CSV",
                                                  "build_log_history.csv", "CSV (*.csv)")
            if not path:
                return
            try:
                with open(path, "x", newline="", encoding="utf-8-sig") as fh:
                    writer = csv.writer(fh, delimiter=";")
                    writer.writerow(headers + (["Pfad"] if is_de else ["Path"]))
                    for item in current_rows:
                        writer.writerow([item["file"], item["status"], item["modified"], item["size"], item["errors"], item["warnings"], item["path"]])
                QMessageBox.information(dialog, "Export erfolgreich" if is_de else "Export successful", path)
            except FileExistsError:
                QMessageBox.warning(dialog, "Datei existiert" if is_de else "File exists",
                                    "Datei existiert bereits; bitte anderen Namen wählen." if is_de else "File already exists; choose another name.")
            except OSError as exc:
                QMessageBox.critical(dialog, "Exportfehler" if is_de else "Export error", str(exc))

        def export_json():
            """Export the currently filtered build-log rows as UTF-8 JSON, without overwriting files."""
            import json
            if not current_rows:
                QMessageBox.information(
                    dialog, "Hinweis" if is_de else "Notice",
                    "Keine Logs zum Exportieren vorhanden." if is_de else "No logs available to export."
                )
                return
            default_name = "build_log_history.json"
            target, _ = QFileDialog.getSaveFileName(
                dialog,
                "Log-Verlauf als JSON speichern" if is_de else "Save log history as JSON",
                default_name,
                ("JSON-Datei (*.json)" if is_de else "JSON file (*.json)")
            )
            if not target:
                return
            payload = {
                "format_version": 1,
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "language": "de" if is_de else "en",
                "filters": {
                    "search": search_input.text().strip(),
                    "status": status_filter.currentText(),
                    "issues": issue_filter.currentText(),
                },
                "count": len(current_rows),
                "logs": [
                    {
                        "file": item.get("file", ""),
                        "path": item.get("path", ""),
                        "status": item.get("status", ""),
                        "modified": item.get("modified", ""),
                        "size_bytes": item.get("size", ""),
                        "errors": item.get("errors", ""),
                        "warnings": item.get("warnings", ""),
                    }
                    for item in current_rows
                ],
            }
            try:
                # Exclusive creation prevents accidental overwrite of an existing export.
                with open(target, "x", encoding="utf-8", newline="") as output:
                    json.dump(payload, output, ensure_ascii=False, indent=2)
                    output.write("\n")
                QMessageBox.information(
                    dialog,
                    "Export erfolgreich" if is_de else "Export successful",
                    ("JSON-Export gespeichert unter:\n" if is_de else "JSON export saved to:\n") + target,
                )
            except FileExistsError:
                QMessageBox.warning(
                    dialog, "Datei existiert" if is_de else "File exists",
                    "Die Datei existiert bereits. Bitte einen anderen Namen wählen." if is_de else
                    "The file already exists. Please choose another name."
                )
            except OSError as exc:
                QMessageBox.critical(
                    dialog, "Exportfehler" if is_de else "Export error",
                    ("JSON-Export fehlgeschlagen:\n" if is_de else "JSON export failed:\n") + str(exc)
                )

        def find_duplicate_logs():
            """Find byte-identical logs by SHA-256 without changing any files."""
            import hashlib
            # Group by size first to avoid hashing files that cannot be identical.
            size_groups = {}
            unreadable = []
            for item in all_rows:
                size = item.get("size")
                if not isinstance(size, int):
                    continue
                size_groups.setdefault(size, []).append(item)
            candidates = [group for group in size_groups.values() if len(group) > 1]
            digest_groups = {}
            for group in candidates:
                for item in group:
                    try:
                        digest = hashlib.sha256()
                        with open(item["path"], "rb") as source:
                            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                                digest.update(chunk)
                        digest_groups.setdefault((item["size"], digest.hexdigest()), []).append(item)
                    except OSError as exc:
                        unreadable.append(f"{item['file']}: {exc}")
            duplicates = [group for group in digest_groups.values() if len(group) > 1]
            result_dialog = QDialog(dialog)
            result_dialog.setWindowTitle("Identische Build-Logs" if is_de else "Identical build logs")
            result_dialog.resize(800, 500)
            result_layout = QVBoxLayout(result_dialog)
            result_text = QTextEdit(result_dialog)
            result_text.setReadOnly(True)
            lines = []
            if duplicates:
                for number, group in enumerate(duplicates, 1):
                    lines.append((f"Gruppe {number} – identischer Inhalt ({group[0]['size']} Bytes):" if is_de else
                                  f"Group {number} – identical content ({group[0]['size']} bytes):"))
                    lines.extend("  • " + entry["path"] for entry in group)
                    lines.append("")
            else:
                lines.append("Keine byte-identischen Logs gefunden." if is_de else "No byte-identical logs found.")
            if unreadable:
                lines.extend(["", "Nicht lesbar:" if is_de else "Unreadable:", *unreadable])
            result_text.setPlainText("\n".join(lines))
            result_layout.addWidget(result_text, 1)
            close_result = QPushButton("Schließen" if is_de else "Close")
            close_result.clicked.connect(result_dialog.accept)
            result_layout.addWidget(close_result)
            result_dialog.exec()

        def show_build_summary():
            """Show a compact read-only health summary for the currently scanned logs."""
            summary_dialog = QDialog(dialog)
            summary_dialog.setWindowTitle("Build-Übersicht" if is_de else "Build summary")
            summary_dialog.resize(760, 520)
            summary_layout = QVBoxLayout(summary_dialog)
            summary_text = QTextEdit(summary_dialog)
            summary_text.setReadOnly(True)
            summary_layout.addWidget(summary_text, 1)

            rows = list(all_rows)
            total = len(rows)
            successful = sum("erfolgreich" in str(x.get("status", "")).casefold() or "successful" in str(x.get("status", "")).casefold() for x in rows)
            failed = sum("fehlgeschlagen" in str(x.get("status", "")).casefold() or "failed" in str(x.get("status", "")).casefold() for x in rows)
            started = sum("gestartet" in str(x.get("status", "")).casefold() or "started" in str(x.get("status", "")).casefold() for x in rows)
            unknown = sum("unbekannt" in str(x.get("status", "")).casefold() or "unknown" in str(x.get("status", "")).casefold() for x in rows)
            unreadable = sum("lesefehler" in str(x.get("status", "")).casefold() or "read error" in str(x.get("status", "")).casefold() for x in rows)
            try:
                errors = sum(int(x.get("errors", 0) or 0) for x in rows)
                warnings = sum(int(x.get("warnings", 0) or 0) for x in rows)
            except (TypeError, ValueError):
                errors = warnings = 0
            resolved = successful + failed
            success_rate = (successful / resolved * 100.0) if resolved else None
            lines = [
                "BUILD-ÜBERSICHT" if is_de else "BUILD SUMMARY",
                "=" * 54,
                (f"Logs gesamt: {total}" if is_de else f"Total logs: {total}"),
                (f"Erfolgreich: {successful}" if is_de else f"Successful: {successful}"),
                (f"Fehlgeschlagen: {failed}" if is_de else f"Failed: {failed}"),
                (f"Gestartet / ohne Abschlussmarker: {started}" if is_de else f"Started / missing completion marker: {started}"),
                (f"Unbekannter Status: {unknown}" if is_de else f"Unknown status: {unknown}"),
                (f"Lesefehler: {unreadable}" if is_de else f"Read errors: {unreadable}"),
                (f"Erkannte Fehler-Treffer insgesamt: {errors}" if is_de else f"Detected error matches: {errors}"),
                (f"Erkannte Warnungs-Treffer insgesamt: {warnings}" if is_de else f"Detected warning matches: {warnings}"),
                (f"Erfolgsquote bei abgeschlossenen Builds: {success_rate:.1f}%" if is_de else f"Success rate for completed builds: {success_rate:.1f}%") if success_rate is not None else ("Erfolgsquote: nicht berechenbar (keine abgeschlossenen Builds)" if is_de else "Success rate: unavailable (no completed builds)"),
                "",
                ("Neueste Logs:" if is_de else "Most recent logs:"),
            ]
            for item in rows[:10]:
                lines.append(f"• {item.get('modified', '')} | {item.get('status', '')} | {item.get('file', '')}")
            if not rows:
                lines.append("Keine Logs gefunden." if is_de else "No logs found.")
            lines.extend(["", ("Hinweis: Fehler- und Warnungszahlen beruhen auf Textmustern; sie sind keine vollständige Compilerdiagnose." if is_de else "Note: error and warning counts are based on text patterns; they are not a complete compiler diagnosis.")])
            summary_text.setPlainText("\n".join(lines))
            close_summary = QPushButton("Schließen" if is_de else "Close")
            close_summary.clicked.connect(summary_dialog.accept)
            summary_layout.addWidget(close_summary)
            summary_dialog.exec()

        def check_log_integrity():
            """Perform read-only sanity checks on available log files."""
            result_dialog = QDialog(dialog)
            result_dialog.setWindowTitle("Log-Prüfung" if is_de else "Log integrity check")
            result_dialog.resize(900, 560)
            result_layout = QVBoxLayout(result_dialog)
            result_text = QTextEdit(result_dialog)
            result_text.setReadOnly(True)
            result_layout.addWidget(result_text, 1)
            findings = []
            checked = 0
            max_files = 500
            max_bytes = 8 * 1024 * 1024
            for item in all_rows[:max_files]:
                path = item.get("path", "")
                name = item.get("file", os.path.basename(path))
                issues = []
                try:
                    size = os.path.getsize(path)
                    if size == 0:
                        issues.append("Leere Datei" if is_de else "Empty file")
                    if size > max_bytes:
                        issues.append((f"Große Datei ({size} Bytes; Inhalt nur teilweise geprüft)" if is_de else
                                       f"Large file ({size} bytes; content only partially checked)"))
                    with open(path, "rb") as fh:
                        data = fh.read(max_bytes + 1)
                    truncated = len(data) > max_bytes
                    data = data[:max_bytes]
                    if data:
                        if not data.endswith((b"\n", b"\r")) and not truncated:
                            issues.append("Letzte Zeile ohne Zeilenumbruch" if is_de else "Last line has no line ending")
                        decoded = data.decode("utf-8", errors="replace")
                        if "\ufffd" in decoded:
                            issues.append("Ungültige UTF-8-Sequenzen möglich (kann auch andere Kodierung sein)" if is_de else
                                           "Possible invalid UTF-8 sequences (file may use another encoding)")
                        if "SIMPLEBUILD_STARTED" in decoded and not re.search(r"SIMPLEBUILD_FINISHED:exit=-?\d+", decoded, re.I):
                            issues.append("Startmarker ohne Abschlussmarker im geprüften Inhalt" if is_de else
                                           "Start marker without completion marker in checked content")
                        if truncated:
                            issues.append("Prüfung auf 8 MiB begrenzt" if is_de else "Check limited to 8 MiB")
                    checked += 1
                except OSError as exc:
                    issues.append(("Nicht lesbar: " if is_de else "Unreadable: ") + str(exc))
                if issues:
                    findings.append(name + "\n  " + "\n  ".join(issues) + "\n  " + path)
            if len(all_rows) > max_files:
                findings.append((f"Hinweis: nur die ersten {max_files} Logs geprüft." if is_de else
                                 f"Note: only the first {max_files} logs were checked."))
            header = (f"Geprüfte Logs: {checked}\nAuffällige Dateien: {len(findings)}\n\n" if is_de else
                      f"Logs checked: {checked}\nFiles with findings: {len(findings)}\n\n")
            if findings:
                result_text.setPlainText(header + "\n\n".join(findings))
            else:
                result_text.setPlainText(header + ("Keine Auffälligkeiten nach den einfachen Plausibilitätsprüfungen gefunden. Das bestätigt nicht die fachliche Richtigkeit des Logs." if is_de else
                                                    "No issues found by these basic sanity checks. This does not certify the log's correctness."))
            close_result = QPushButton("Schließen" if is_de else "Close")
            close_result.clicked.connect(result_dialog.accept)
            result_layout.addWidget(close_result)
            result_dialog.exec()

        # Arrange actions in compact, grouped rows instead of one very wide toolbar.
        action_area = QVBoxLayout()
        action_row1 = QHBoxLayout()
        action_row2 = QHBoxLayout()
        action_row3 = QHBoxLayout()
        refresh_button = QPushButton("Aktualisieren" if is_de else "Refresh")
        refresh_button.setToolTip("Log-Liste neu einlesen (F5)." if is_de else "Reload the log list (F5).")
        refresh_button.clicked.connect(lambda: safe_callback(refresh))
        search_input.textChanged.connect(lambda _text: safe_callback(render_rows))
        status_filter.currentTextChanged.connect(lambda _text: safe_callback(render_rows))
        issue_filter.currentTextChanged.connect(lambda _text: safe_callback(render_rows))
        table.cellDoubleClicked.connect(lambda row, column: safe_callback(preview_log, row, column))
        open_selected_button = QPushButton("Ausgewähltes Log öffnen" if is_de else "Open selected log")
        open_selected_button.setToolTip("Vorschau des ausgewählten Logs öffnen (Enter)." if is_de else "Open a preview of the selected log (Enter).")
        def open_selected_log():
            row = table.currentRow()
            if row >= 0:
                preview_log(row, 0)
            else:
                QMessageBox.information(dialog, "Hinweis" if is_de else "Notice",
                                        "Bitte zuerst ein Log auswählen." if is_de else "Please select a log first.")
        open_selected_button.clicked.connect(lambda: safe_callback(open_selected_log))

        def show_log_findings():
            """Show numbered error/warning lines from the selected log without modifying it."""
            row = table.currentRow()
            if row < 0 or row >= len(current_rows):
                QMessageBox.information(
                    dialog, "Hinweis" if is_de else "Notice",
                    "Bitte zuerst ein Log auswählen." if is_de else "Please select a log first."
                )
                return
            item = current_rows[row]
            findings_dialog = QDialog(dialog)
            findings_dialog.setWindowTitle(("Fehler- und Warnungsdetails: " if is_de else "Error and warning details: ") + item["file"])
            findings_dialog.resize(900, 560)
            findings_layout = QVBoxLayout(findings_dialog)
            findings_path = QLabel(item["path"])
            findings_path.setWordWrap(True)
            findings_layout.addWidget(findings_path)
            findings_text = QTextEdit(findings_dialog)
            findings_text.setReadOnly(True)
            findings_layout.addWidget(findings_text, 1)
            try:
                finding_re = re.compile(
                    r"error:|fatal error:|undefined reference|command not found|\bfailed\b|\bfailure\b|make\[[0-9]+\]: \*\*\*|\bwarning:|\bdeprecated\b",
                    re.I,
                )
                matches = []
                with open(item["path"], "r", encoding="utf-8", errors="replace") as log_file:
                    for line_number, line in enumerate(log_file, 1):
                        if finding_re.search(line):
                            matches.append(f"{line_number}: {line.rstrip()}" )
                            if len(matches) >= 500:
                                matches.append("… weitere Treffer ausgelassen …" if is_de else "… additional matches omitted …")
                                break
                if matches:
                    findings_text.setPlainText("\n".join(matches))
                else:
                    findings_text.setPlainText("Keine passenden Fehler- oder Warnungszeilen gefunden." if is_de else "No matching error or warning lines found.")
            except OSError as exc:
                findings_text.setPlainText(("Log konnte nicht gelesen werden: " if is_de else "Could not read log: ") + str(exc))
            close_findings = QPushButton("Schließen" if is_de else "Close")
            close_findings.clicked.connect(findings_dialog.accept)
            findings_layout.addWidget(close_findings)
            findings_dialog.exec()

        def save_log_analysis_report():
            """Export a self-contained, read-only analysis report for the selected log."""
            row = table.currentRow()
            if row < 0 or row >= len(current_rows):
                QMessageBox.information(
                    dialog, "Hinweis" if is_de else "Notice",
                    "Bitte zuerst ein Log auswählen." if is_de else "Please select a log first."
                )
                return
            item = current_rows[row]
            default_name = os.path.splitext(os.path.basename(item["file"]))[0] + "_analysis.txt"
            target, _ = QFileDialog.getSaveFileName(
                dialog,
                "Analysebericht speichern" if is_de else "Save analysis report",
                default_name,
                ("Textdatei (*.txt)" if is_de else "Text file (*.txt)")
            )
            if not target:
                return
            finding_re = re.compile(
                r"error:|fatal error:|undefined reference|command not found|\bfailed\b|\bfailure\b|make\[[0-9]+\]: \*\*\*|\bwarning:|\bdeprecated\b",
                re.I,
            )
            matches = []
            try:
                with open(item["path"], "r", encoding="utf-8", errors="replace") as log_file:
                    for line_number, line in enumerate(log_file, 1):
                        if finding_re.search(line):
                            matches.append(f"{line_number}: {line.rstrip()}")
                            if len(matches) >= 500:
                                matches.append("… weitere Treffer ausgelassen …" if is_de else "… additional matches omitted …")
                                break
                report_lines = [
                    "BUILD-LOG-ANALYSEBERICHT" if is_de else "BUILD LOG ANALYSIS REPORT",
                    "=" * 72,
                    ("Datei: " if is_de else "File: ") + str(item["file"]),
                    ("Pfad: " if is_de else "Path: ") + str(item["path"]),
                    ("Status: " if is_de else "Status: ") + str(item["status"]),
                    ("Geändert: " if is_de else "Modified: ") + str(item["modified"]),
                    ("Größe: " if is_de else "Size: ") + str(item["size"]),
                    ("Fehler-Treffer: " if is_de else "Error matches: ") + str(item["errors"]),
                    ("Warnungs-Treffer: " if is_de else "Warning matches: ") + str(item["warnings"]),
                    ("Erstellt: " if is_de else "Created: ") + datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "",
                    ("Fehler- und Warnungszeilen (max. 500):" if is_de else "Error and warning lines (max. 500):"),
                    "-" * 72,
                    *(matches or (["Keine passenden Zeilen gefunden."] if is_de else ["No matching lines found."])),
                ]
                # Exclusive creation prevents accidentally overwriting an existing report.
                with open(target, "x", encoding="utf-8-sig", newline="") as report_file:
                    report_file.write("\n".join(report_lines) + "\n")
                QMessageBox.information(
                    dialog, "Bericht gespeichert" if is_de else "Report saved",
                    ("Analysebericht gespeichert unter:\n" if is_de else "Analysis report saved to:\n") + target
                )
            except FileExistsError:
                QMessageBox.warning(
                    dialog, "Datei existiert" if is_de else "File exists",
                    "Die Datei existiert bereits. Bitte einen anderen Namen wählen." if is_de else
                    "The file already exists. Please choose another name."
                )
            except OSError as exc:
                QMessageBox.critical(
                    dialog, "Exportfehler" if is_de else "Export error",
                    ("Der Analysebericht konnte nicht gespeichert werden:\n" if is_de else "Could not save analysis report:\n") + str(exc)
                )

        def export_filtered_error_digest():
            """Export a compact read-only digest for the currently filtered logs."""
            rows = list(current_rows[:100])
            if not rows:
                QMessageBox.information(
                    dialog, "Keine Logs" if is_de else "No logs",
                    "Die aktuelle Auswahl enthält keine Logs." if is_de else "The current selection contains no logs."
                )
                return
            target, _ = QFileDialog.getSaveFileName(
                dialog,
                "Fehlerübersicht speichern" if is_de else "Save error digest",
                "build_error_digest.txt",
                ("Textdatei (*.txt)" if is_de else "Text file (*.txt)")
            )
            if not target:
                return
            finding_re = re.compile(
                r"error:|fatal error:|undefined reference|command not found|\bfailed\b|\bfailure\b|make\[[0-9]+\]: \*\*\*|\bwarning:|\bdeprecated\b",
                re.I,
            )
            report = [
                "BUILD-LOG-FEHLERÜBERSICHT" if is_de else "BUILD LOG ERROR DIGEST",
                "=" * 72,
                ("Logs in aktueller Filterauswahl: " if is_de else "Logs in current filtered selection: ") + str(len(rows)),
                ("Erstellt: " if is_de else "Generated: ") + datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                ("Hinweis: Musterbasierte Erkennung; Treffer sind keine vollständige Compilerdiagnose." if is_de else "Note: pattern-based detection; matches are not a complete compiler diagnosis."),
                "",
            ]
            for index, item in enumerate(rows, 1):
                report.extend([
                    f"[{index}] {item.get('file', '')}",
                    ("Pfad: " if is_de else "Path: ") + str(item.get("path", "")),
                    ("Status: " if is_de else "Status: ") + str(item.get("status", "")),
                    ("Fehler: " if is_de else "Errors: ") + str(item.get("errors", "")) + " | " + ("Warnungen: " if is_de else "Warnings: ") + str(item.get("warnings", "")),
                ])
                matched = []
                try:
                    with open(item["path"], "r", encoding="utf-8", errors="replace") as log_file:
                        for line_number, line in enumerate(log_file, 1):
                            if finding_re.search(line):
                                matched.append(f"  {line_number}: {line.rstrip()}")
                                if len(matched) >= 50:
                                    matched.append("  … weitere Treffer ausgelassen …" if is_de else "  … additional matches omitted …")
                                    break
                except (OSError, KeyError) as exc:
                    matched.append(("  Log nicht lesbar: " if is_de else "  Log unreadable: ") + str(exc))
                report.extend(matched or (["  Keine passenden Fehler-/Warnungszeilen gefunden."] if is_de else ["  No matching error/warning lines found."]))
                report.append("")
            try:
                # Exclusive creation avoids overwriting an existing report.
                with open(target, "x", encoding="utf-8-sig", newline="") as output:
                    output.write("\n".join(report) + "\n")
                QMessageBox.information(
                    dialog, "Export abgeschlossen" if is_de else "Export complete",
                    ("Fehlerübersicht gespeichert:\n" if is_de else "Error digest saved:\n") + target
                )
            except FileExistsError:
                QMessageBox.warning(
                    dialog, "Datei existiert" if is_de else "File exists",
                    "Die Datei existiert bereits. Bitte einen anderen Namen wählen." if is_de else "The file already exists. Please choose another name."
                )
            except OSError as exc:
                QMessageBox.critical(
                    dialog, "Exportfehler" if is_de else "Export error",
                    ("Fehlerübersicht konnte nicht gespeichert werden:\n" if is_de else "Could not save error digest:\n") + str(exc)
                )

        summary_button = QPushButton("Build-Übersicht" if is_de else "Build summary")
        summary_button.setToolTip("Zusammenfassung aller gefundenen Logs anzeigen." if is_de else "Show a summary of all discovered logs.")
        summary_button.clicked.connect(lambda: safe_callback(show_build_summary))
        integrity_button = QPushButton("Logs prüfen" if is_de else "Check logs")
        integrity_button.setToolTip("Prüft einfache Auffälligkeiten, ohne Dateien zu verändern." if is_de else "Checks basic log anomalies without modifying files.")
        integrity_button.clicked.connect(lambda: safe_callback(check_log_integrity))
        duplicates_button = QPushButton("Duplikate prüfen" if is_de else "Find duplicates")
        duplicates_button.setToolTip("Byte-identische Logs anhand SHA-256 finden; Dateien bleiben unverändert." if is_de else "Find byte-identical logs using SHA-256; files remain unchanged.")
        duplicates_button.clicked.connect(lambda: safe_callback(find_duplicate_logs))
        compare_button = QPushButton("Logs vergleichen" if is_de else "Compare logs")
        compare_button.setToolTip("Genau zwei Logs auswählen und Unterschiede anzeigen." if is_de else "Select exactly two logs to view their differences.")
        compare_button.clicked.connect(lambda: safe_callback(compare_selected_logs))
        findings_button = QPushButton("Fehler/Warnungen" if is_de else "Errors/Warnings")
        findings_button.setToolTip("Erkannte Fehler- und Warnungszeilen des ausgewählten Logs anzeigen." if is_de else "Show detected error and warning lines from the selected log.")
        findings_button.clicked.connect(lambda: safe_callback(show_log_findings))
        report_button = QPushButton("Analysebericht speichern…" if is_de else "Save analysis report…")
        report_button.setToolTip("Einen Textbericht zum ausgewählten Log speichern." if is_de else "Save a text report for the selected log.")
        report_button.clicked.connect(lambda: safe_callback(save_log_analysis_report))
        digest_button = QPushButton("Fehlerübersicht exportieren…" if is_de else "Export error digest…")
        digest_button.setToolTip("Fehler-/Warnungstreffer der aktuell gefilterten Logs gesammelt exportieren." if is_de else "Export error/warning matches for the currently filtered logs in one report.")
        digest_button.clicked.connect(lambda: safe_callback(export_filtered_error_digest))
        live_button = QPushButton("Live-Aktualisierung: AUS" if is_de else "Live refresh: OFF")
        live_button.setToolTip("Automatische Aktualisierung alle 10 Sekunden ein-/ausschalten." if is_de else "Toggle automatic refresh every 10 seconds.")
        live_timer = QTimer(dialog)
        live_timer.setInterval(10000)
        live_timer.timeout.connect(lambda: safe_callback(refresh))
        live_enabled = {"value": False}
        def toggle_live_refresh():
            live_enabled["value"] = not live_enabled["value"]
            if live_enabled["value"]:
                live_timer.start()
            else:
                live_timer.stop()
            live_button.setText(("Live-Aktualisierung: AN" if live_enabled["value"] else "Live-Aktualisierung: AUS") if is_de
                                else ("Live refresh: ON" if live_enabled["value"] else "Live refresh: OFF"))
        live_button.clicked.connect(lambda: safe_callback(toggle_live_refresh))
        export_button = QPushButton("CSV exportieren…" if is_de else "Export CSV…")
        export_button.setToolTip("Aktuell gefilterte Logs als CSV speichern." if is_de else "Save the currently filtered logs as CSV.")
        export_button.clicked.connect(lambda: safe_callback(export_csv))
        json_export_button = QPushButton("JSON exportieren…" if is_de else "Export JSON…")
        json_export_button.setToolTip(
            "Aktuell gefilterte Logs als JSON exportieren, ohne vorhandene Dateien zu überschreiben."
            if is_de else
            "Export currently filtered logs as JSON without overwriting existing files."
        )
        json_export_button.clicked.connect(lambda: safe_callback(export_json))
        close_button = QPushButton("Schließen" if is_de else "Close")
        close_button.setToolTip("Build-Log-Verlauf schließen." if is_de else "Close build log history.")
        close_button.clicked.connect(dialog.accept)
        dialog.finished.connect(live_timer.stop)
        # Keyboard shortcuts speed up navigation without adding more toolbar buttons.
        try:
            from PyQt6.QtGui import QKeySequence, QShortcut
            refresh_shortcut = QShortcut(QKeySequence("F5"), dialog)
            refresh_shortcut.activated.connect(lambda: safe_callback(refresh))
            find_shortcut = QShortcut(QKeySequence("Ctrl+F"), dialog)
            find_shortcut.activated.connect(search_input.setFocus)
            open_shortcut = QShortcut(QKeySequence("Return"), table)
            open_shortcut.activated.connect(lambda: safe_callback(open_selected_log))
            copy_path_shortcut = QShortcut(QKeySequence("Ctrl+C"), table)
            def copy_selected_log_paths():
                selected = sorted({index.row() for index in table.selectionModel().selectedRows()})
                if not selected:
                    row = table.currentRow()
                    selected = [row] if 0 <= row < len(current_rows) else []
                paths = [str(current_rows[index].get("path", "")) for index in selected
                         if 0 <= index < len(current_rows)]
                if paths:
                    QApplication.clipboard().setText("\n".join(paths))
            copy_path_shortcut.activated.connect(lambda: safe_callback(copy_selected_log_paths))
            table.setToolTip(("F5: Aktualisieren · Strg+F: Suche · Enter: Log öffnen · Strg+C: Pfad kopieren"
                              if is_de else "F5: Refresh · Ctrl+F: Search · Enter: Open log · Ctrl+C: Copy path"))
        except Exception:
            pass
        for button in (refresh_button, open_selected_button, compare_button, summary_button):
            button.setMinimumWidth(105)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            action_row1.addWidget(button, 1)
        for button in (integrity_button, duplicates_button, findings_button, report_button):
            button.setMinimumWidth(105)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            action_row2.addWidget(button, 1)
        for button in (digest_button, live_button, export_button, json_export_button, close_button):
            button.setMinimumWidth(105)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            action_row3.addWidget(button, 1)
        action_area.addLayout(action_row1)
        action_area.addLayout(action_row2)
        action_area.addLayout(action_row3)
        layout.addLayout(action_area)
        safe_callback(refresh)
        try:
            dialog.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Fehler" if is_de else "Error",
                                 ("Build-Log-Verlauf wurde sicher beendet; die Haupt-GUI bleibt geöffnet.\n" if is_de
                                  else "Build log history was stopped safely; the main GUI remains open.\n") + f"{type(exc).__name__}: {exc}")
        finally:
            live_timer.stop()

    def open_event_history_viewer(self):
        """Zeigt gespeicherte Warnungen, Fehler und Erfolgsmeldungen an."""
        import json
        from pathlib import Path
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                     QLineEdit, QComboBox, QPlainTextEdit,
                                     QPushButton, QFileDialog, QMessageBox)
        is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
        dialog = QDialog(self)
        dialog.setWindowTitle("Ereignis- und Fehlerhistorie" if is_de else "Event and error history")
        dialog.resize(850, 560)
        dialog.setMinimumSize(600, 380)
        layout = QVBoxLayout(dialog)
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Filter:" if is_de else "Level:"))
        level = QComboBox()
        level.addItem("Alle" if is_de else "All", "all")
        level.addItem("Fehler" if is_de else "Errors", "error")
        level.addItem("Warnungen" if is_de else "Warnings", "warning")
        level.addItem("Erfolge" if is_de else "Successes", "success")
        filters.addWidget(level)
        search = QLineEdit()
        search.setPlaceholderText("Text suchen…" if is_de else "Search text…")
        filters.addWidget(search, 1)
        layout.addLayout(filters)
        output = QPlainTextEdit()
        output.setReadOnly(True)
        output.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(output, 1)
        status = QLabel()
        layout.addWidget(status)
        event_dir = Path(__file__).resolve().parent / "event_history"
        files = [event_dir / "events.previous.jsonl", event_dir / "events.jsonl"]
        records = []
        for file_path in files:
            try:
                with file_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        try:
                            item = json.loads(line)
                            if isinstance(item, dict):
                                records.append(item)
                        except (json.JSONDecodeError, TypeError):
                            continue
            except OSError:
                continue
        records.sort(key=lambda item: str(item.get("timestamp", "")), reverse=True)
        visible_text = []
        def refresh_events(*_):
            selected = level.currentData()
            needle = search.text().strip().casefold()
            visible_text.clear()
            for item in records:
                item_level = str(item.get("level", "info")).lower()
                message = str(item.get("message", ""))
                timestamp = str(item.get("timestamp", ""))
                if selected != "all" and item_level != selected:
                    continue
                if needle and needle not in (timestamp + " " + message).casefold():
                    continue
                visible_text.append(f"[{timestamp}] [{item_level.upper()}] {message}")
            output.setPlainText("\n".join(visible_text))
            status.setText((f"{len(visible_text)} Einträge angezeigt · {len(records)} insgesamt" if is_de else
                            f"Showing {len(visible_text)} entries · {len(records)} total"))
        level.currentIndexChanged.connect(refresh_events)
        search.textChanged.connect(refresh_events)
        buttons = QHBoxLayout()
        export_button = QPushButton("Gefiltert exportieren…" if is_de else "Export filtered…")
        close_button = QPushButton("Schließen" if is_de else "Close")
        def export_events():
            path, _ = QFileDialog.getSaveFileName(dialog,
                "Ereignisse exportieren" if is_de else "Export events",
                "ereignisse.txt" if is_de else "events.txt", "Text (*.txt)")
            if not path:
                return
            try:
                with open(path, "x", encoding="utf-8") as handle:
                    handle.write("\n".join(visible_text))
            except FileExistsError:
                QMessageBox.warning(dialog, "Datei existiert" if is_de else "File exists",
                                    "Die Datei existiert bereits." if is_de else "That file already exists.")
            except OSError as exc:
                QMessageBox.warning(dialog, "Exportfehler" if is_de else "Export error", str(exc))
        export_button.clicked.connect(export_events)
        close_button.clicked.connect(dialog.accept)
        buttons.addWidget(export_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        refresh_events()
        dialog.exec()

    def open_diagnostics_dialog(self):
        """Read-only system/tool/build-log diagnostics; never starts or cancels builds."""
        import json
        import os
        import platform
        import shutil
        from datetime import datetime
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox

        is_de = str(getattr(self, "LANG", LANG)).lower().startswith("de")
        dialog = QDialog(self)
        dialog.setWindowTitle("Systemdiagnose & Build-Logs" if is_de else "System diagnostics & build logs")
        dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        intro = QLabel(
            "Nur lesende Prüfung. Es wird kein Build gestartet/abgebrochen und es werden keine Logs gelöscht."
            if is_de else
            "Read-only checks. No build is started/cancelled and no logs are deleted."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        summary = QLabel("Diagnose wird vorbereitet …" if is_de else "Preparing diagnostics …")
        summary.setWordWrap(True)
        summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        summary.setStyleSheet("QLabel { padding: 8px; border: 1px solid palette(mid); border-radius: 4px; }")
        layout.addWidget(summary)
        output = QTextEdit()
        output.setReadOnly(True)
        output.setFont(QFont("Consolas", 10))
        layout.addWidget(output, 1)

        def collect_report():
            report = {"created_at": datetime.now().astimezone().isoformat(), "system": {}, "tools": {}, "build_logs": [], "process_monitor": {}}
            tool_paths = {
                "git": shutil.which("git"),
                "bash": shutil.which("bash"),
                "wsl": shutil.which("wsl") or shutil.which("wsl.exe"),
                "make": shutil.which("make") or shutil.which("mingw32-make"),
                "gcc": shutil.which("gcc"),
                "g++": shutil.which("g++"),
                "clang": shutil.which("clang"),
                "python": shutil.which("python") or shutil.which("python3"),
            }
            report["system"] = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "python": sys.version,
                "executable": sys.executable,
                "cwd": os.getcwd(),
                "tools_on_path": tool_paths,
                "available_tool_count": sum(bool(value) for value in tool_paths.values()),
                "missing_common_tools": [name for name, value in tool_paths.items() if value is None],
            }
            # Read-only process snapshot. A compiler process alone is only an indicator,
            # not proof that it belongs to this application or one of its builds.
            process_candidates = []
            process_errors = []
            process_keywords = ("make", "gcc", "g++", "cc1", "clang", "cmake", "ninja", "ld", "simplebuild", "build.sh", "arm-linux")
            try:
                import psutil  # Optional dependency; never install it automatically.
                for proc in psutil.process_iter(["pid", "name", "exe"]):
                    try:
                        name = str(proc.info.get("name") or "")
                        exe = str(proc.info.get("exe") or "")
                        haystack = (name + " " + exe).lower()
                        if any(keyword in haystack for keyword in process_keywords):
                            process_candidates.append({"pid": proc.info.get("pid"), "name": name, "executable": exe})
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except ImportError:
                # Standard-library fallback, keeping only matching process rows.
                try:
                    if platform.system().lower() == "windows":
                        result = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=5, check=False)
                        import csv
                        import io
                        for row in csv.reader(io.StringIO(result.stdout or "")):
                            if len(row) >= 2 and any(k in row[0].lower() for k in process_keywords):
                                process_candidates.append({"pid": row[1], "name": row[0], "executable": ""})
                        if result.returncode and not result.stdout:
                            process_errors.append((result.stderr or "tasklist failed")[:300])
                    else:
                        result = subprocess.run(["ps", "-eo", "pid=,comm="], capture_output=True, text=True, timeout=5, check=False)
                        for line in (result.stdout or "").splitlines():
                            parts = line.strip().split(None, 1)
                            if len(parts) == 2 and any(k in parts[1].lower() for k in process_keywords):
                                process_candidates.append({"pid": parts[0], "name": parts[1], "executable": ""})
                        if result.returncode and not result.stdout:
                            process_errors.append((result.stderr or "ps failed")[:300])
                except (OSError, subprocess.SubprocessError) as exc:
                    process_errors.append(str(exc)[:300])
            # Track workers owned by this GUI separately from system-wide process matches.
            tracked_workers = []
            worker_attributes = (
                ("s3_install_worker", "S3 installation" if not is_de else "S3-Installation"),
                ("s3_worker", "S3 build" if not is_de else "S3-Build"),
                ("ncam_worker", "NCam installation" if not is_de else "NCam-Installation"),
                ("ncam_update_worker", "NCam update" if not is_de else "NCam-Update"),
            )
            for attr_name, display_name in worker_attributes:
                worker = getattr(self, attr_name, None)
                if worker is None:
                    continue
                try:
                    running = bool(worker.isRunning()) if callable(getattr(worker, "isRunning", None)) else False
                    finished = bool(worker.isFinished()) if callable(getattr(worker, "isFinished", None)) else not running
                    tracked_workers.append({
                        "name": display_name,
                        "state": "RUNNING" if running else "FINISHED" if finished else "NOT RUNNING / UNKNOWN",
                    })
                except RuntimeError as exc:
                    tracked_workers.append({"name": display_name, "state": "STATUS UNKNOWN", "detail": str(exc)[:200]})

            if any(item.get("state") == "RUNNING" for item in tracked_workers):
                overall_status = "GUI BUILD WORKER RUNNING" if not is_de else "GUI-BUILD-WORKER LÄUFT"
            elif process_errors and not process_candidates:
                overall_status = "STATUS UNKNOWN" if not is_de else "STATUS UNBEKANNT"
            elif process_candidates:
                overall_status = "SYSTEM PROCESS CANDIDATES FOUND; NOT ATTRIBUTED TO GUI" if not is_de else "SYSTEM-PROZESS-KANDIDATEN GEFUNDEN; GUI-ZUORDNUNG UNBEKANNT"
            else:
                overall_status = "NO TRACKED GUI BUILD RUNNING" if not is_de else "KEIN VERFOLGTER GUI-BUILD AKTIV"

            report["process_monitor"] = {
                "status": overall_status,
                "tracked_gui_workers": tracked_workers,
                "confidence": "GUI worker state is application-specific; system process matches are indicators only, not proof." if not is_de else "GUI-Workerstatus ist anwendungsspezifisch; gefundene Systemprozesse sind nur Hinweise, kein Beweis.",
                "system_process_candidates": process_candidates[:100],
                "truncated": len(process_candidates) > 100,
                "errors": process_errors,
            }

            # Inspect only directories already present. Do not clone, fetch, checkout or modify Git.
            candidate_roots = []
            for value in (os.environ.get("SIMPLEBUILD_DIR"), r"C:\Simplebuild", os.path.dirname(os.path.abspath(__file__))):
                if value and value not in candidate_roots:
                    candidate_roots.append(value)
            for tool in ("s3_gorgone", "s3_speedy005", "s4", "ncam"):
                matches = []
                for root in candidate_roots:
                    for candidate in (os.path.join(root, tool), root if os.path.basename(root).lower() == tool.lower() else None):
                        if candidate and os.path.isdir(candidate):
                            matches.append({"path": candidate, "git_dir": os.path.exists(os.path.join(candidate, ".git"))})
                report["tools"][tool] = {"found": bool(matches), "locations": matches}
            log_dir = getattr(self, "build_log_dir", None) or os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_logs")
            report["log_directory"] = log_dir
            # Actionable hints are advisory only; diagnostics never modify the system.
            recommendations = []
            missing_tools = [name for name, value in tool_paths.items() if value is None]
            if "git" in missing_tools:
                recommendations.append({
                    "severity": "warning",
                    "code": "GIT_NOT_FOUND",
                    "message": "Git wurde nicht im PATH gefunden. Installation und PATH prüfen." if is_de else "Git was not found on PATH. Check the installation and PATH.",
                })
            if not any(os.path.isdir(os.path.join(root, name)) for root in candidate_roots for name in ("s3_gorgone", "s3_speedy005", "s4", "ncam")):
                recommendations.append({
                    "severity": "warning",
                    "code": "PROJECT_DIRS_NOT_FOUND",
                    "message": "Keiner der erwarteten Projektordner wurde an den geprüften Orten gefunden. Projektpfad/SIMPLEBUILD_DIR prüfen." if is_de else "No expected project folders were found in checked locations. Check the project path/SIMPLEBUILD_DIR.",
                })
            if not os.path.isdir(log_dir):
                recommendations.append({
                    "severity": "info",
                    "code": "LOG_DIR_MISSING",
                    "message": "Der Build-Log-Ordner existiert noch nicht oder liegt an einem anderen Ort." if is_de else "The build-log directory does not exist yet or is located elsewhere.",
                })
            failed_logs = [item.get("name", "") for item in report.get("build_logs", []) if "FAILED" in str(item.get("status", "")).upper() or "FEHLGESCHLAGEN" in str(item.get("status", "")).upper() or "ERROR" in str(item.get("status", "")).upper() or "FEHLER" in str(item.get("status", "")).upper()]
            if failed_logs:
                recommendations.append({
                    "severity": "warning",
                    "code": "BUILD_LOG_ERRORS",
                    "message": ("Fehlerindikatoren in Build-Logs prüfen: " if is_de else "Review error indicators in build logs: ") + ", ".join(failed_logs[:8]),
                })
            report["recommendations"] = recommendations
            try:
                for name in sorted(os.listdir(log_dir), key=lambda n: os.path.getmtime(os.path.join(log_dir, n)) if os.path.isfile(os.path.join(log_dir, n)) else 0, reverse=True):
                    path = os.path.join(log_dir, name)
                    if not os.path.isfile(path) or not name.lower().endswith(".log"):
                        continue
                    status = "UNKNOWN" if not is_de else "UNBEKANNT"
                    try:
                        # Read only the tail of large logs: diagnostics should stay
                        # responsive even when a build log is several hundred MB.
                        max_scan_bytes = 1024 * 1024
                        with open(path, "rb") as f:
                            f.seek(0, os.SEEK_END)
                            file_size = f.tell()
                            scan_size = min(file_size, max_scan_bytes)
                            f.seek(-scan_size, os.SEEK_END)
                            content = f.read(scan_size).decode("utf-8", errors="replace")
                        log_truncated_for_scan = file_size > max_scan_bytes
                        if "SIMPLEBUILD_FINISHED:exit=0" in content:
                            status = "SUCCESS (marker)" if not is_de else "ERFOLGREICH (Marker)"
                        elif "SIMPLEBUILD_FINISHED:exit=" in content:
                            status = "FAILED (marker)" if not is_de else "FEHLGESCHLAGEN (Marker)"
                        elif "SIMPLEBUILD_STARTED" in content:
                            status = "STARTED, completion marker missing" if not is_de else "GESTARTET, Abschlussmarker fehlt"
                        elif any(x in content.lower() for x in ("fatal error:", "undefined reference", "command not found", "make: ***")):
                            status = "ERROR INDICATORS FOUND" if not is_de else "FEHLERHINWEISE gefunden"
                        report["build_logs"].append({"name": name, "path": path, "status": status, "bytes": file_size, "scan_bytes": scan_size, "scan_truncated": log_truncated_for_scan, "modified": datetime.fromtimestamp(os.path.getmtime(path)).astimezone().isoformat()})
                    except OSError as exc:
                        report["build_logs"].append({"name": name, "path": path, "status": "READ ERROR" if not is_de else "LESEFEHLER", "error": str(exc)})
            except OSError as exc:
                report["log_scan_error"] = str(exc)
            return report

        def refresh():
            # A failed optional probe must not close the diagnostics window.
            try:
                report = collect_report()
            except Exception as exc:
                error_text = f"{type(exc).__name__}: {exc}"
                summary.setText(
                    ("Diagnose konnte nicht vollständig erstellt werden. Details stehen unten." if is_de else
                     "Diagnostics could not be completed. Details are shown below.")
                )
                output.setPlainText(error_text)
                return {"created_at": datetime.now().astimezone().isoformat(),
                        "diagnostic_error": error_text, "recommendations": []}
            system = report.get("system", {})
            missing = system.get("missing_common_tools", [])
            repos = report.get("tools", {})
            found_repos = [name for name, data in repos.items() if data.get("found")]
            logs = report.get("build_logs", [])
            running = [item.get("name", "worker") for item in report.get("process_monitor", {}).get("tracked_gui_workers", []) if item.get("state") == "RUNNING"]
            if is_de:
                summary_lines = [
                    f"Werkzeuge: {system.get('available_tool_count', 0)}/{len(system.get('tools_on_path', {}))} gefunden",
                    "Fehlende Werkzeuge: " + (", ".join(missing) if missing else "keine der geprüften Standardwerkzeuge"),
                    "Repository-/Projektordner gefunden: " + (", ".join(found_repos) if found_repos else "keine der geprüften Ordner"),
                    f"Build-Logs: {len(logs)} gefunden",
                    "Aktive GUI-Worker: " + (", ".join(running) if running else "keine erkannt"),
                    "Empfehlungen: " + (str(len(report.get("recommendations", []))) if report.get("recommendations") else "keine zusätzlichen Hinweise"),
                ]
            else:
                summary_lines = [
                    f"Tools: {system.get('available_tool_count', 0)}/{len(system.get('tools_on_path', {}))} found",
                    "Missing tools: " + (", ".join(missing) if missing else "none of the checked common tools"),
                    "Project/repository folders found: " + (", ".join(found_repos) if found_repos else "none of the checked folders"),
                    f"Build logs: {len(logs)} found",
                    "Active GUI workers: " + (", ".join(running) if running else "none detected"),
                    "Recommendations: " + (str(len(report.get("recommendations", []))) if report.get("recommendations") else "no additional hints"),
                ]
            summary.setText("\n".join(summary_lines))
            output.setPlainText(json.dumps(report, ensure_ascii=False, indent=2))
            return report

        def save_report():
            try:
                report = collect_report()
            except Exception as exc:
                QMessageBox.warning(
                    dialog, "Diagnosefehler" if is_de else "Diagnostic error",
                    ("Der Bericht konnte nicht erstellt werden: " if is_de else
                     "The report could not be generated: ") + f"{type(exc).__name__}: {exc}"
                )
                return
            suggested = f"simplebuild_diagnose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path, _ = QFileDialog.getSaveFileName(dialog, "Diagnosebericht speichern" if is_de else "Save diagnostic report", suggested, "JSON (*.json)")
            if not path:
                return
            try:
                # Exclusive create avoids overwriting an existing report.
                with open(path, "x", encoding="utf-8") as handle:
                    json.dump(report, handle, ensure_ascii=False, indent=2)
                QMessageBox.information(dialog, "Gespeichert" if is_de else "Saved", path)
            except FileExistsError:
                QMessageBox.warning(dialog, "Datei existiert" if is_de else "File exists", "Die Datei existiert bereits; bitte einen anderen Namen wählen." if is_de else "That file already exists; choose another name.")
            except OSError as exc:
                QMessageBox.critical(dialog, "Fehler" if is_de else "Error", str(exc))

        buttons = QHBoxLayout()
        refresh_button = QPushButton("Jetzt aktualisieren" if is_de else "Refresh now")
        refresh_button.setToolTip("System, Werkzeuge und Build-Logs erneut lesend prüfen." if is_de else "Re-check system, tools and build logs without modifying them.")
        refresh_button.clicked.connect(refresh)
        save_button = QPushButton("Bericht speichern…" if is_de else "Save report…")
        save_button.setToolTip("Aktuelle Diagnose als JSON-Datei exportieren." if is_de else "Export the current diagnostics as a JSON file.")
        save_button.clicked.connect(save_report)
        auto_refresh_button = QPushButton("Live-Aktualisierung: AUS" if is_de else "Live refresh: OFF")
        auto_refresh_button.setCheckable(True)
        auto_refresh_button.setToolTip(
            "Aktualisiert Diagnose und Log-Status alle 5 Sekunden. Startet oder beendet keine Builds."
            if is_de else
            "Refreshes diagnostics and log status every 5 seconds. Does not start or stop builds."
        )
        refresh_timer = QTimer(dialog)
        refresh_timer.setInterval(5000)
        refresh_timer.timeout.connect(refresh)

        def toggle_auto_refresh(enabled):
            if enabled:
                refresh_timer.start()
                auto_refresh_button.setText("Live-Aktualisierung: EIN" if is_de else "Live refresh: ON")
                refresh()
            else:
                refresh_timer.stop()
                auto_refresh_button.setText("Live-Aktualisierung: AUS" if is_de else "Live refresh: OFF")

        auto_refresh_button.toggled.connect(toggle_auto_refresh)
        close_button = QPushButton("Schließen" if is_de else "Close")
        close_button.setToolTip("Build-Log-Verlauf schließen." if is_de else "Close build log history.")
        close_button.clicked.connect(dialog.accept)
        event_history_button = QPushButton("Ereignishistorie…" if is_de else "Event history…")
        event_history_button.setToolTip("Gespeicherte Fehler, Warnungen und Erfolge filtern und exportieren." if is_de else "Filter and export saved errors, warnings and successes.")
        event_history_button.clicked.connect(self.open_event_history_viewer)
        buttons.addWidget(event_history_button)
        buttons.addWidget(refresh_button)
        buttons.addWidget(auto_refresh_button)
        buttons.addWidget(save_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        refresh()
        dialog.finished.connect(refresh_timer.stop)
        dialog.exec()


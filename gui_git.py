"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerGitMixin:
    """Patch Manager Git"""

    def show_commits(self, info_widget=None, progress_callback=None, num_commits=None):
        """
        Zeigt die letzten Commits an.

        Ablauf:
        1. TEMP_REPO prüfen.
        2. Wenn TEMP_REPO ein gültiges Git-Repository ist:
           -> lokale Commits lesen.
        3. Wenn TEMP_REPO nicht existiert oder kein Git-Repository ist:
           -> Repository temporär online klonen.
        4. Commits anzeigen.
        5. Progressbar und Sound aktualisieren.
        6. Temporäres Repository immer wieder löschen.

        Unterstützt:
        - PyQt6 QTextEdit
        - QSpinBox / QDoubleSpinBox / Integer für num_commits
        - Deutsch / Englisch
        - progress_callback
        - Regenbogen-Progressbar
        - Fehlerstatus
        """

        # ------------------------------------------------------------
        # Final Label verstecken
        # ------------------------------------------------------------
        if hasattr(self, "hide_final_label"):
            try:
                self.hide_final_label()
            except Exception:
                pass

        # ------------------------------------------------------------
        # Imports
        # ------------------------------------------------------------
        from PyQt6.QtWidgets import QTextEdit, QApplication
        from PyQt6.QtCore import QTimer

        import os
        import tempfile
        import shutil
        import subprocess

        # ------------------------------------------------------------
        # Sprache
        # ------------------------------------------------------------
        lang = getattr(self, "LANG", "de").lower()
        is_de = lang.startswith("de")

        # ------------------------------------------------------------
        # Info-Widget bestimmen
        # ------------------------------------------------------------
        if not isinstance(info_widget, QTextEdit):
            info_widget = getattr(self, "info_text", None)

        # ------------------------------------------------------------
        # Progressbar
        # ------------------------------------------------------------
        pbar = getattr(self, "progress_bar", None)

        # ------------------------------------------------------------
        # Anzahl Commits bestimmen
        #
        # Erlaubt:
        #   num_commits = 10
        #   num_commits = QSpinBox
        #   num_commits = None -> self.commit_spin
        # ------------------------------------------------------------
        try:
            if hasattr(num_commits, "value") and callable(num_commits.value):
                total_commits = int(num_commits.value())

            elif num_commits is not None:
                total_commits = int(num_commits)

            else:
                commit_spin = getattr(self, "commit_spin", None)

                if hasattr(commit_spin, "value") and callable(commit_spin.value):
                    total_commits = int(commit_spin.value())
                else:
                    total_commits = 10

        except (TypeError, ValueError):
            total_commits = 10

        # Sinnvolle Grenzen
        total_commits = max(1, min(total_commits, 1000))

        # ------------------------------------------------------------
        # Hilfsfunktion: Logging
        # ------------------------------------------------------------
        def log(text, level="info"):
            try:
                if info_widget is not None and hasattr(self, "append_info"):
                    self.append_info(info_widget, text, level)
                else:
                    print(f"[{level.upper()}] {text}")
            except Exception:
                print(f"[{level.upper()}] {text}")

        # ------------------------------------------------------------
        # Hilfsfunktion: Progressbar
        # ------------------------------------------------------------
        def set_progress(value, text=None, is_err=False):
            if pbar is None:
                return

            try:
                value = max(0, min(100, int(value)))

                rainbow = (
                    "qlineargradient("
                    "x1:0, y1:0, x2:1, y2:0,"
                    "stop:0 #FF0000,"
                    "stop:0.2 #FF7F00,"
                    "stop:0.4 #FFFF00,"
                    "stop:0.6 #00FF00,"
                    "stop:0.8 #0000FF,"
                    "stop:1 #8B00FF"
                    ")"
                )

                if is_err:
                    style = """
                        QProgressBar {
                            text-align: center;
                            font-weight: bold;
                            border: 2px solid #500;
                            border-radius: 6px;
                            background-color: #111;
                            color: #FF0000;
                            font-size: 15pt;
                        }

                        QProgressBar::chunk {
                            background-color: #800;
                            border-radius: 4px;
                        }
                    """
                else:
                    style = f"""
                        QProgressBar {{
                            text-align: center;
                            font-weight: bold;
                            border: 2px solid #222;
                            border-radius: 6px;
                            background-color: #111;
                            color: black;
                            font-size: 15pt;
                        }}

                        QProgressBar::chunk {{
                            background: {rainbow};
                            border-radius: 4px;
                        }}
                    """

                pbar.setStyleSheet(style)
                pbar.setValue(value)

                if text:
                    pbar.setFormat(str(text))
                else:
                    pbar.setFormat("%p%")

                pbar.show()

                QApplication.processEvents()

                if progress_callback:
                    try:
                        progress_callback(value)
                    except Exception:
                        pass

            except Exception as e:
                print(f"[WARNING] Progressbar error: {e}")

        # ------------------------------------------------------------
        # Hilfsfunktion: Progressbar am Ende
        # ------------------------------------------------------------
        def finalize_pbar(text, visible_seconds=3):
            if pbar is None:
                return

            try:
                pbar.setValue(100)
                pbar.setFormat(str(text))
                pbar.show()

                QApplication.processEvents()

                def reset_progress():
                    try:
                        pbar.setStyleSheet(
                            """
                            QProgressBar {
                                text-align: center;
                                font-weight: bold;
                                border: 2px solid #222;
                                border-radius: 6px;
                                background-color: #111;
                                color: black;
                                font-size: 15pt;
                            }

                            QProgressBar::chunk {
                                background-color: transparent;
                            }
                            """
                        )

                        pbar.setValue(0)
                        pbar.setFormat("%p%")

                        if progress_callback:
                            try:
                                progress_callback(0)
                            except Exception:
                                pass

                    except Exception:
                        pass

                QTimer.singleShot(
                    int(visible_seconds * 1000),
                    reset_progress
                )

            except Exception:
                pass

        # ------------------------------------------------------------
        # Hilfsfunktion: Sound
        # ------------------------------------------------------------
        def play_commit_sound(success=True):
            try:
                sound_file = (
                    "message-new-instant.oga"
                    if success
                    else
                    "dialog-error.oga"
                )

                if "safe_play" in globals():
                    safe_play(sound_file)

                elif hasattr(self, "safe_play"):
                    self.safe_play(sound_file)

            except Exception:
                pass

        # ------------------------------------------------------------
        # Hilfsfunktion: Git-Befehl
        # ------------------------------------------------------------
        def run_git_command(args, cwd=None):
            """
            Führt einen Git-Befehl aus und gibt:
                success, stdout, stderr
            zurück.
            """

            try:
                result = subprocess.run(
                    args,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )

                stdout = result.stdout.strip()
                stderr = result.stderr.strip()

                # Fehlerdiagnose: Exit-Code und verständlicher Fallback,
                # damit fehlgeschlagene Git-Schritte leichter erkennbar sind.
                if result.returncode != 0:
                    detail = stderr or stdout or (
                        "Git hat keine Fehlerdetails ausgegeben."
                        if is_de
                        else "Git did not provide error details."
                    )
                    stderr = (
                        f"Git-Befehl fehlgeschlagen (Exit-Code {result.returncode}): {detail}"
                        if is_de
                        else f"Git command failed (exit code {result.returncode}): {detail}"
                    )

                return (
                    result.returncode == 0,
                    stdout,
                    stderr,
                )

            except FileNotFoundError:
                return (
                    False,
                    "",
                    "Git wurde nicht gefunden. Bitte Git installieren."
                    if is_de
                    else "Git was not found. Please install Git.",
                )

            except Exception as e:
                return (
                    False,
                    "",
                    str(e),
                )

        # ------------------------------------------------------------
        # START
        # ------------------------------------------------------------
        set_progress(
            5,
            "Bereite Commit-Anzeige vor..."
            if is_de
            else
            "Preparing commit display..."
        )

        log(
            TEXTS.get(lang, {}).get(
                "loading_commits",
                "Lade Commits..."
                if is_de
                else
                "Loading commits..."
            ),
            "warning",
        )

        # ------------------------------------------------------------
        # Repository-Daten
        # ------------------------------------------------------------
        repo_url = "https://git.streamboard.tv/common/oscam.git"
        branch = "master"

        temp_dir = None
        output = ""

        # ------------------------------------------------------------
        # TEMP_REPO aus globals / self holen
        # ------------------------------------------------------------
        try:
            local_repo = TEMP_REPO
        except NameError:
            local_repo = getattr(self, "TEMP_REPO", None)

        # ------------------------------------------------------------
        # Prüfen, ob TEMP_REPO gültig ist
        # ------------------------------------------------------------
        local_repo_valid = False

        if local_repo and os.path.isdir(local_repo):

            set_progress(
                15,
                "Prüfe lokales Repository..."
                if is_de
                else
                "Checking local repository..."
            )

            success, stdout, stderr = run_git_command(
                [
                    "git",
                    "-C",
                    local_repo,
                    "rev-parse",
                    "--is-inside-work-tree",
                ]
            )

            if success and stdout.lower() == "true":
                local_repo_valid = True

        # ============================================================
        # HAUPTVERARBEIT
        # ============================================================
        try:

            # ========================================================
            # FALL 1: Lokales Git-Repository
            # ========================================================
            if local_repo_valid:

                log(
                    "📁 Lokales Git-Repository gefunden."
                    if is_de
                    else
                    "📁 Local Git repository found.",
                    "info",
                )

                set_progress(
                    35,
                    "Lese lokale Commits..."
                    if is_de
                    else
                    "Reading local commits..."
                )

                success, stdout, stderr = run_git_command(
                    [
                        "git",
                        "-C",
                        local_repo,
                        "log",
                        f"-n{total_commits}",
                        "--oneline",
                    ]
                )

                if not success:

                    log(
                        f"❌ Git-Fehler: {stderr or 'Unbekannter Fehler'}",
                        "error",
                    )

                    set_progress(
                        100,
                        "❌ Git-Fehler"
                        if is_de
                        else
                        "❌ Git error",
                        is_err=True,
                    )

                    play_commit_sound(False)
                    return

                output = stdout

            # ========================================================
            # FALL 2: Kein gültiges lokales Repository
            #         -> Online Clone
            # ========================================================
            else:

                if local_repo and os.path.exists(local_repo):

                    log(
                        "⚠ TEMP_REPO existiert, ist aber kein gültiges "
                        "Git-Repository."
                        if is_de
                        else
                        "⚠ TEMP_REPO exists but is not a valid "
                        "Git repository.",
                        "warning",
                    )

                    log(
                        "🌐 Verwende Online-Repository."
                        if is_de
                        else
                        "🌐 Using online repository.",
                        "info",
                    )

                else:

                    log(
                        "🌐 Kein lokales Repository gefunden."
                        if is_de
                        else
                        "🌐 No local repository found.",
                        "info",
                    )

                # ----------------------------------------------------
                # Temporäres Verzeichnis erstellen
                # ----------------------------------------------------
                temp_dir = tempfile.mkdtemp(
                    prefix="oscam_git_"
                )

                log(
                    f"📂 Temporäres Verzeichnis: {temp_dir}",
                    "info",
                )

                set_progress(
                    35,
                    "Klone Repository..."
                    if is_de
                    else
                    "Cloning repository..."
                )

                # ----------------------------------------------------
                # Online Clone
                # ----------------------------------------------------
                success, stdout, stderr = run_git_command(
                    [
                        "git",
                        "clone",
                        "--depth",
                        str(total_commits),
                        "--branch",
                        branch,
                        repo_url,
                        temp_dir,
                    ]
                )

                if not success:

                    error_text = (
                        stderr
                        or stdout
                        or (
                            "Unbekannter Fehler beim Klonen."
                            if is_de
                            else
                            "Unknown clone error."
                        )
                    )

                    log(
                        f"❌ Fehler beim Klonen: {error_text}",
                        "error",
                    )

                    set_progress(
                        100,
                        "❌ Clone Fehler"
                        if is_de
                        else
                        "❌ Clone error",
                        is_err=True,
                    )

                    play_commit_sound(False)
                    return

                # ----------------------------------------------------
                # Clone erfolgreich
                # ----------------------------------------------------
                set_progress(
                    65,
                    "Repository geladen..."
                    if is_de
                    else
                    "Repository loaded..."
                )

                log(
                    "✅ Repository erfolgreich geklont."
                    if is_de
                    else
                    "✅ Repository cloned successfully.",
                    "success",
                )

                # ----------------------------------------------------
                # Commits lesen
                # ----------------------------------------------------
                set_progress(
                    75,
                    "Lese Online-Commits..."
                    if is_de
                    else
                    "Reading online commits..."
                )

                success, stdout, stderr = run_git_command(
                    [
                        "git",
                        "-C",
                        temp_dir,
                        "log",
                        f"-n{total_commits}",
                        "--oneline",
                    ]
                )

                if not success:

                    error_text = (
                        stderr
                        or stdout
                        or (
                            "Unbekannter Git-Fehler."
                            if is_de
                            else
                            "Unknown Git error."
                        )
                    )

                    log(
                        f"❌ Fehler beim Lesen der Commits: {error_text}",
                        "error",
                    )

                    set_progress(
                        100,
                        "❌ Fehler"
                        if is_de
                        else
                        "❌ Error",
                        is_err=True,
                    )

                    play_commit_sound(False)
                    return

                output = stdout

            # ========================================================
            # AUSGABE VERARBEITEN
            # ========================================================
            set_progress(
                90,
                "Verarbeite Commits..."
                if is_de
                else
                "Processing commits..."
            )

            lines = [
                line.strip()
                for line in output.splitlines()
                if line.strip()
            ]

            # --------------------------------------------------------
            # Keine Commits
            # --------------------------------------------------------
            if not lines:

                log(
                    "⚠ Keine Commits gefunden."
                    if is_de
                    else
                    "⚠ No commits found.",
                    "warning",
                )

                set_progress(
                    100,
                    "⚠ Keine Commits"
                    if is_de
                    else
                    "⚠ No commits",
                    is_err=True,
                )

                play_commit_sound(False)

                return

            # --------------------------------------------------------
            # Commits anzeigen
            # --------------------------------------------------------
            for line in lines:
                log(
                    f"• {line}",
                    "info"
                )

            # --------------------------------------------------------
            # Erfolg
            # --------------------------------------------------------
            loaded_text = TEXTS.get(lang, {}).get(
                "commits_loaded",
                "Commits erfolgreich geladen"
                if is_de
                else
                "Commits loaded successfully"
            )

            log(
                f"✅ {loaded_text} ({len(lines)})",
                "success",
            )

            set_progress(
                100,
                "✅ Commits geladen"
                if is_de
                else
                "✅ Commits loaded"
            )

            play_commit_sound(True)

            finalize_pbar(
                "✅ Fertig!"
                if is_de
                else
                "✅ Done!",
                visible_seconds=3
            )

        # ============================================================
        # ALLGEMEINER FEHLER
        # ============================================================
        except Exception as e:

            error_text = str(e)

            log(
                f"❌ Fehler: {error_text}",
                "error"
            )

            set_progress(
                100,
                f"❌ Fehler: {error_text}",
                is_err=True
            )

            play_commit_sound(False)

        # ============================================================
        # CLEANUP
        # ============================================================
        finally:

            if temp_dir and os.path.exists(temp_dir):

                try:

                    shutil.rmtree(
                        temp_dir,
                        ignore_errors=True
                    )

                    log(
                        "🧹 Temporäres Repository gelöscht."
                        if is_de
                        else
                        "🧹 Temporary repository removed.",
                        "info",
                    )

                except Exception as cleanup_error:

                    log(
                        f"⚠ Cleanup-Fehler: {cleanup_error}",
                        "warning",
                    )

    def oscam_emu_git_clear(self, info_widget=None, progress_callback=None):
        """Zentrales Logging für die Emu-Git Bereinigung – mit Neon-Regenbogen & Abschluss-Puls."""

        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer

        # --- Final Label verstecken ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        info_widget = info_widget or getattr(self, "info_text", None)
        lang = getattr(self, "LANG", "de").lower()[:2]
        pbar = getattr(self, "progress_bar", None)

        # --- Neon-Styles ---
        STYLE_BASE = """
            QProgressBar {{
                border: 2px solid #444444;
                border-radius: 8px;
                background-color: {bg_color};
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

        # --- Hilfsfunktion für ProgressBar Updates ---
        def update_p(val, is_err=False, text=None):
            if pbar:
                chunk = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #800, stop:1 #F00)" if is_err else RAINBOW_GRADIENT
                t_color = "#FF0000" if is_err else "black"
            
                pbar.setStyleSheet(STYLE_BASE.format(bg_color="#0A0A0A", text_color=t_color, chunk_color=chunk))
                pbar.setValue(val)
                pbar.setFormat(text if text else f"{val}%")
                pbar.show()
            if progress_callback:
                try: progress_callback(val)
                except: pass
            QApplication.processEvents()

        # --- Startmeldung ---
        update_p(10)
        # Annahme: TEXTS ist global
        start_msg = TEXTS.get(lang, {}).get("oscam_emu_git_clearing", "🔹 Emu-Git wird geleert...")
        if hasattr(self, "append_info"):
            self.append_info(info_widget, start_msg, "info")

        try:
            # --- Bereinigung starten ---
            update_p(50)
            # Die zentrale Funktion wirklich ausführen. Der frühere Fallback
            # meldete Erfolg, obwohl keine Bereinigung stattgefunden hatte.
            from patch_operations import clean_patch_folder

            result = clean_patch_folder(
                gui_instance=self,
                info_widget=info_widget,
                progress_callback=progress_callback,
            )

            # --- Ergebnis auswerten ---
            if result is True or result == "success":
                msg = TEXTS.get(lang, {}).get("oscam_emu_git_cleared", "✅ Bereinigung erfolgreich!")
                if hasattr(self, "append_info"):
                    self.append_info(info_widget, msg, "success")
            
                bar_txt = "✅ Ordner geleert" if lang == "de" else "✅ Folder cleared"

                # Sanfter Grüner Puls am Ende
                def pulse_green(times=4):
                    state = {"i": 0}

                    def toggle():
                        # Wechselt zwischen Neon-Grün und dem dunklen Hintergrund
                        bg = "#39FF14" if state["i"] % 2 == 0 else "#0A0A0A"
                        if pbar:
                            pbar.setStyleSheet(STYLE_BASE.format(bg_color=bg, text_color="black", chunk_color=RAINBOW_GRADIENT))
                    
                        state["i"] += 1
                        if state["i"] < times * 2:
                            QTimer.singleShot(200, toggle)
                        else:
                            if pbar: pbar.setFormat(bar_txt)

                    toggle()

                pulse_green()
                update_p(100)
                if "safe_play" in globals(): safe_play("complete.oga")

            elif result == "not_found":
                msg = "ℹ️ " + ("Ordner bereits leer." if lang == "de" else "Folder already empty.")
                if hasattr(self, "append_info"):
                    self.append_info(info_widget, msg, "info")
            
                bar_txt = "ℹ️ Bereits leer" if lang == "de" else "ℹ️ Already empty"
                update_p(100, text=bar_txt)
                if "safe_play" in globals(): safe_play("dialog-information.oga")

            else:
                raise Exception("Deletion failed")

        except Exception as e:
            if hasattr(self, "append_info"):
                self.append_info(info_widget, f"❌ Fehler: {e}", "error")
            bar_txt = "❌ Fehler" if lang == "de" else "❌ Error"
            update_p(100, is_err=True, text=bar_txt)
            if "safe_play" in globals(): safe_play("dialog-error.oga")

        finally:
            QApplication.processEvents()

    def get_local_revision(self):
        """
        Liefert die aktuelle OSCam-Revision.

        Priorität:

        1. Aktueller Streamboard-Git-Stand aus TEMP_REPO
        2. oscam_rev.txt neben dem Patch Manager
        3. "?" wenn keine Revision ermittelt werden kann

        WICHTIG:

            TEMP_REPO
                = OSCam / Streamboard

            PATCH_EMU_GIT_DIR
                = OSCam-Emu

        Deshalb darf für die aktuelle OSCam-Revision
        NICHT PATCH_EMU_GIT_DIR verwendet werden.
        """

        import os
        import re

        # ============================================================
        # 1. AKTUELLEN STREAMBOARD-GIT-STAND VERWENDEN
        # ============================================================

        try:

            repo_dir = TEMP_REPO

            git_dir = os.path.join(
                repo_dir,
                ".git"
            )

            if os.path.isdir(git_dir):

                # ----------------------------------------------------
                # HEAD des Streamboard-Repositories
                # ----------------------------------------------------

                commit = git_commit_id(
                    repo_dir,
                    "HEAD"
                )

                # ----------------------------------------------------
                # OSCam-Version aus globals.h
                # ----------------------------------------------------

                version = get_oscam_version(
                    repo_dir,
                    commit
                )

                if version:

                    version_text = str(
                        version
                    ).strip()

                    # ------------------------------------------------
                    # Beispiel:
                    #
                    # 2.26.09-11968
                    #
                    # Ergebnis:
                    #
                    # 11968
                    # ------------------------------------------------

                    match = re.search(
                        r"-(\d+)$",
                        version_text
                    )

                    if match:

                        revision = match.group(1)

                        if revision.isdigit():

                            # ----------------------------------------
                            # Aktuelle Revision auch lokal speichern
                            # ----------------------------------------

                            try:
                                self.save_local_revision(
                                    revision
                                )
                            except Exception:
                                pass

                            return revision

        except Exception:
            pass

        # ============================================================
        # 2. oscam_rev.txt ALS FALLBACK
        # ============================================================

        try:

            script_dir = os.path.dirname(
                os.path.realpath(__file__)
            )

            rev_file = os.path.join(
                script_dir,
                "oscam_rev.txt"
            )

            if os.path.isfile(rev_file):

                with open(
                    rev_file,
                    "r",
                    encoding="utf-8"
                ) as f:

                    content = f.read().strip()

                # ----------------------------------------------------
                # Nur reine Zahlen akzeptieren
                # ----------------------------------------------------

                if content.isdigit():

                    return content

        except Exception:
            pass

        # ============================================================
        # 3. KEIN WERT VERFÜGBAR
        # ============================================================

        return "?"

    def get_latest_remote_revision(self):
        """
        Ermittelt die aktuellste OSCam-Revision aus dem
        bereits geladenen Streamboard-Git.

        Bevorzugt wird das lokale TEMP_REPO verwendet.

        Falls TEMP_REPO nicht verfügbar ist, wird versucht,
        das Streamboard-Git direkt zu aktualisieren.
        """

        import os
        import re

        # ============================================================
        # 1. TEMP_REPO verwenden
        # ============================================================

        try:

            repo_dir = TEMP_REPO

            git_dir = os.path.join(
                repo_dir,
                ".git"
            )

            if os.path.isdir(git_dir):

                # ----------------------------------------------------
                # Remote aktualisieren
                # ----------------------------------------------------

                try:

                    git_command(
                        [
                            "fetch",
                            "--no-tags",
                            "--prune",
                            "origin"
                        ],
                        cwd=repo_dir,
                        timeout=1200
                    )

                except Exception:
                    pass

                # ----------------------------------------------------
                # Remote HEAD bestimmen
                # ----------------------------------------------------

                ref = "origin/master"

                try:

                    result = git_command(
                        [
                            "symbolic-ref",
                            "--short",
                            "refs/remotes/origin/HEAD"
                        ],
                        cwd=repo_dir,
                        allowed_returncodes=(0, 1)
                    )

                    remote_head = (
                        result.stdout
                        or ""
                    ).strip()

                    if remote_head:

                        ref = remote_head

                except Exception:
                    pass

                # ----------------------------------------------------
                # Commit bestimmen
                # ----------------------------------------------------

                try:

                    commit = git_commit_id(
                        repo_dir,
                        ref
                    )

                except Exception:

                    commit = git_commit_id(
                        repo_dir,
                        "HEAD"
                    )

                # ----------------------------------------------------
                # Version auslesen
                # ----------------------------------------------------

                version = get_oscam_version(
                    repo_dir,
                    commit
                )

                if version:

                    match = re.search(
                        r"-(\d+)$",
                        str(version).strip()
                    )

                    if match:

                        revision = match.group(1)

                        if revision.isdigit():

                            return revision

        except Exception:
            pass

        # ============================================================
        # 2. FALLBACK: HTTP
        # ============================================================

        try:

            import requests

            url = (
                "https://git.streamboard.tv/"
            )

            headers = {
                "User-Agent":
                    "OSCam-Patch-Manager"
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:

                matches = re.findall(
                    r"r(\d{5,7})",
                    response.text
                )

                if matches:

                    # ------------------------------------------------
                    # Nicht einfach den ersten Treffer blind verwenden.
                    # Höchste gefundene Revision verwenden.
                    # ------------------------------------------------

                    revisions = [
                        int(value)
                        for value in matches
                        if value.isdigit()
                    ]

                    if revisions:

                        return str(
                            max(revisions)
                        )

        except Exception:
            pass

        return None

    def save_local_revision(self, revision):
        """
        Speichert die aktuelle OSCam-Revision in:

            <Plugin-Verzeichnis>/oscam_rev.txt

        Nicht os.getcwd() verwenden, da das Arbeitsverzeichnis
        beim Start der Anwendung ein anderes Verzeichnis sein kann.
        """

        import os

        try:

            # ========================================================
            # Revision validieren
            # ========================================================

            revision = str(
                revision
            ).strip()

            if not revision.isdigit():

                return False

            # ========================================================
            # Immer Plugin-Verzeichnis verwenden
            # ========================================================

            script_dir = os.path.dirname(
                os.path.realpath(__file__)
            )

            rev_file = os.path.join(
                script_dir,
                "oscam_rev.txt"
            )

            # ========================================================
            # Speichern
            # ========================================================

            with open(
                rev_file,
                "w",
                encoding="utf-8",
                newline="\n"
            ) as f:

                f.write(
                    revision
                )

            return True

        except Exception as e:

            print(
                f"Fehler beim Speichern der Revision: {e}"
            )

    def start_oscam_update_check(self):
        """Wird aufgerufen, um den Vergleich zu starten."""
        # 1. Lokale Rev holen (aus Datei oder Fallback)
        self.current_rev = self.get_local_revision()

        # 2. Remote Rev von Streamboard holen
        remote_rev = self.get_latest_remote_revision()

        if remote_rev:
            try:
                # Prüfen ob die Online-Nummer größer als die lokale ist
                update_available = int(remote_rev) > int(self.current_rev)
                self.on_update_check_finished(update_available, remote_rev)
            except ValueError:
                self.on_update_check_finished(False, self.current_rev)
        else:
            # Fehlerfall: Nur lokalen Stand zeigen
            self.on_update_check_finished(False, self.current_rev)

    def change_modifier_name(self):
        """Öffnet Autor-Dialog mit Regenbogen-Progress, Sound und DE/EN Support."""

        # --- Final-Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        from PyQt6.QtWidgets import QInputDialog, QLineEdit, QApplication
        from PyQt6.QtCore import QTimer

        # 1. SETUP & SPRACHE
        current_author = getattr(self, "patch_modifier", "speedy005")
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        # Lokalisierte Texte
        T_TITLE = "Patch Autor" if is_de else "Patch Author"
        T_LABEL = "Name des Autors:" if is_de else "Author Name:"
        T_SAVING = "Speichere Autor..." if is_de else "Saving Author..."
        T_DONE = "Autor geändert!" if is_de else "Author changed!"
        T_CANCEL = "Abgebrochen" if is_de else "Cancelled"

        # RESET-FUNKTION (Zurück zu Orange/Gold)
        def restore_style():
            if pbar:
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

        # --- SOUND BEIM ÖFFNEN ---
        if "safe_play" in globals():
            safe_play("dialog-information.oga")

        # 2. REGENBOGEN-PROGRESS STARTEN
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
                    border-radius: 6px; background-color: #111; color: black; font-size: 15pt;
                }}
                QProgressBar::chunk {{ background-color: {rainbow}; border-radius: 4px; }}
            """
            )
            pbar.setFormat(f"👤 {T_SAVING} %p%")
            pbar.setValue(20)
            pbar.show()
            QApplication.processEvents()

        # 3. DIALOG KONFIGURIEREN
        dialog = QInputDialog(self)
        dialog.setWindowTitle(T_TITLE)
        dialog.setLabelText(T_LABEL)
        dialog.setTextValue(current_author)
        dialog.setOkButtonText("OK")
        dialog.setCancelButtonText("Abbrechen" if is_de else "Cancel")

        if dialog.exec():
            new_name = dialog.textValue().strip()
            if new_name:
                if pbar:
                    pbar.setValue(60)
                self.patch_modifier = new_name

                if hasattr(self, "cfg"):
                    self.cfg["patch_modifier"] = self.patch_modifier
                    try:
                        if "save_config" in globals():
                            globals()["save_config"](self.cfg, gui_instance=self)

                        if hasattr(self, "update_language"):
                            self.update_language()

                        # --- ERFOLG ---
                        if "safe_play" in globals():
                            safe_play("complete.oga")
                        if pbar:
                            pbar.setValue(100)
                            pbar.setFormat(f"✅ {T_DONE}")
                            QApplication.processEvents()

                    except Exception as e:
                        if "safe_play" in globals():
                            safe_play("dialog-error.oga")
                        if pbar:
                            pbar.setStyleSheet(
                                "QProgressBar { color: red; font-weight: 900; }"
                            )

                # Auto-Reset nach Erfolg
                QTimer.singleShot(3000, restore_style)
        else:
            # --- 4. SPEZIELLER ABBRUCH-ABLAUF ---
            if "safe_play" in globals():
                safe_play("dialog-warning.oga")

            if pbar:
                # Erst auf 100% füllen (Regenbogen)
                pbar.setValue(100)
                pbar.setFormat("100%")
                pbar.repaint()
                QApplication.processEvents()

                # Nach 400ms: Auf 0 setzen und rote Meldung zeigen
                def show_cancel_msg():
                    pbar.setValue(0)
                    pbar.setFormat(f"❌ {T_CANCEL}")
                    # Rotes Highlight für den Fehler/Abbruch
                    pbar.setStyleSheet(
                        f"""
                        QProgressBar {{ 
                            text-align: center; color: red; font-weight: 900; 
                            font-size: 15pt; border: 2px solid red; background: #111; 
                        }}
                    """
                    )
                    pbar.repaint()
                    QApplication.processEvents()
                    # Nach weiteren 2 Sekunden endgültiger Reset zu Orange/Gold
                    QTimer.singleShot(2000, restore_style)

                QTimer.singleShot(400, show_cancel_msg)

    def commit_value_changed(self, value):
        """Speichert die Commit-Anzahl über den zentralen Config-Manager."""
        try:
            value = max(1, min(int(value), 1000))
            saved = save_config(
                {"commit_count": value},
                gui_instance=self,
                silent=True,
            )
            if not saved:
                raise RuntimeError("Die Konfiguration konnte nicht gespeichert werden.")

            self.append_info(
                self.info_text,
                f"Commit-Anzahl auf {value} gesetzt (gespeichert)",
                "success",
            )
        except Exception as exc:
            self.append_info(
                self.info_text,
                f"❌ Fehler beim Speichern der Commit-Anzahl: {exc}",
                "error",
            )

    def run_git_pull(self):
        """Führt das Git-Update aus und nutzt die vorhandene append_info Logik."""
        try:
            # Git Pull ausführen und Output abfangen
            process = subprocess.run(
                ["git", "-C", TEMP_REPO, "pull"],
                capture_output=True,
                text=True,
                check=True,
            )

            self.header_label.setText(" System aktuell")

            # Erfolgsmeldung in den Infoscreen (Level 'success' für Grün)
            self.append_info("OSCam Repo wurde erfolgreich aktualisiert!", "success")

            # Falls Git Änderungen meldet, diese als 'white' oder 'raw' anzeigen
            if process.stdout and "Already up to date" not in process.stdout:
                self.append_info(process.stdout.strip(), "white")

        except subprocess.CalledProcessError as e:
            self.header_label.setText(" Update Fehler!")
            # Fehlermeldung in den Infoscreen (Level 'error' für Rot)
            self.append_info(f"Git Fehler: {e.stderr.strip()}", "error")

        except Exception as e:
            self.header_label.setText(" Fehler!")
            self.append_info(f"Unerwarteter Fehler: {str(e)}", "error")

    def log_to_info(self, message, color="white"):
        """Hilfsmethode zum Schreiben in den Infoscreen (QTextEdit)."""
        # Falls dein QTextEdit 'infoscreen' heißt:
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        html_text = f'<span style="color:gray;">[{timestamp}]</span> <span style="color:{color};">{message}</span>'
        self.infoscreen.append(html_text)
        # Automatisch nach unten scrollen
        self.infoscreen.moveCursor(QTextCursor.MoveOperation.End)

    def check_for_new_commit(self):
        """
        Prüft den aktuellsten Commit von Streamboard.

        Der Netzwerk/Git-Check läuft in einem QThread,
        damit die PyQt-Oberfläche nicht einfriert.

        Repository:
            https://git.streamboard.tv/common/oscam.git
        Branch:
            master
        """

        from PyQt6.QtCore import QThread, pyqtSignal
        from PyQt6.QtWidgets import QMessageBox, QApplication
        import subprocess

        # ---------------------------------------------------------
        # Final Label verstecken
        # ---------------------------------------------------------
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        # ---------------------------------------------------------
        # Sprache
        # ---------------------------------------------------------
        lang = getattr(self, "LANG", "de").lower()
        self.TEXT = globals().get("TEXTS", {}).get(lang, {})
        is_de = lang.startswith("de")

        # ---------------------------------------------------------
        # ProgressBar
        # ---------------------------------------------------------
        pbar = getattr(self, "progress_bar", None)

        rainbow = (
            "qlineargradient("
            "x1:0, y1:0, x2:1, y2:0, "
            "stop:0 #FF0000, "
            "stop:0.2 #FF7F00, "
            "stop:0.4 #FFFF00, "
            "stop:0.6 #00FF00, "
            "stop:0.8 #0000FF, "
            "stop:1 #8B00FF)"
        )

        def set_progress(value, text=None):
            if pbar is None:
                return

            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center;
                    font-weight: bold;
                    border: 2px solid #222;
                    border-radius: 6px;
                    background-color: #111;
                    color: black;
                    font-size: 15pt;
                }}

                QProgressBar::chunk {{
                    background-color: {rainbow};
                    border-radius: 4px;
                }}
                """
            )

            pbar.setValue(value)

            if text is not None:
                pbar.setFormat(text)

            pbar.show()
            QApplication.processEvents()

        def finalize_pbar(text, visible_seconds=3):
            if pbar is None:
                return

            pbar.setStyleSheet(
                f"""
                QProgressBar {{
                    text-align: center;
                    font-weight: bold;
                    border: 2px solid #222;
                    border-radius: 6px;
                    background-color: #111;
                    color: black;
                    font-size: 15pt;
                }}

                QProgressBar::chunk {{
                    background-color: {rainbow};
                    border-radius: 4px;
                }}
                """
            )

            pbar.setValue(100)
            pbar.setFormat(text)

            from PyQt6.QtCore import QTimer

            def clear_bar():
                if pbar is None:
                    return

                pbar.setStyleSheet(
                    """
                    QProgressBar {
                        text-align: center;
                        font-weight: bold;
                        border: 2px solid #222;
                        border-radius: 6px;
                        background-color: #111;
                        color: black;
                        font-size: 15pt;
                    }

                    QProgressBar::chunk {
                        background-color: transparent;
                    }
                    """
                )

                pbar.setValue(0)
                pbar.setFormat("")

            QTimer.singleShot(
                visible_seconds * 1000,
                clear_bar
            )

        # ---------------------------------------------------------
        # Git Worker
        # ---------------------------------------------------------
        class CommitWorker(QThread):

            success = pyqtSignal(str)
            error = pyqtSignal(str)

            def run(self):
                try:
                    repo_url = (
                        "https://git.streamboard.tv/"
                        "common/oscam.git"
                    )

                    result = subprocess.run(
                        [
                            "git",
                            "ls-remote",
                            repo_url,
                            "refs/heads/master"
                        ],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=20
                    )

                    if result.returncode != 0:
                        error_text = (
                            result.stderr.strip()
                            or "git ls-remote fehlgeschlagen."
                        )

                        self.error.emit(error_text)
                        return

                    output = result.stdout.strip()

                    if not output:
                        self.error.emit(
                            "Keine Antwort von Streamboard."
                        )
                        return

                    # Erwartet:
                    # HASH<TAB>refs/heads/master
                    parts = output.split()

                    if not parts:
                        self.error.emit(
                            "Kein Commit-Hash erhalten."
                        )
                        return

                    commit_hash = parts[0].strip().lower()

                    # SHA-1 muss 40 Zeichen haben
                    if len(commit_hash) != 40:
                        self.error.emit(
                            f"Ungültiger Commit-Hash: {commit_hash}"
                        )
                        return

                    self.success.emit(commit_hash)

                except subprocess.TimeoutExpired:
                    self.error.emit(
                        "Zeitüberschreitung bei der Verbindung."
                    )

                except FileNotFoundError:
                    self.error.emit(
                        "Git wurde nicht gefunden. "
                        "Bitte prüfen, ob Git installiert ist."
                    )

                except Exception as e:
                    self.error.emit(str(e))

        # ---------------------------------------------------------
        # Progress starten
        # ---------------------------------------------------------
        if pbar:
            set_progress(
                10,
                "🔍 Prüfe Streamboard..."
                if is_de
                else
                "Checking Streamboard..."
            )

            set_progress(
                30,
                "🌐 Verbinde mit Streamboard..."
                if is_de
                else
                "🌐 Connecting to Streamboard..."
            )

        # ---------------------------------------------------------
        # Worker erzeugen
        # ---------------------------------------------------------
        worker = CommitWorker(self)

        # Referenz behalten, damit Python den Thread nicht
        # vorzeitig freigibt.
        self._commit_check_worker = worker

        # ---------------------------------------------------------
        # Erfolgreicher Check
        # ---------------------------------------------------------
        
      
        def commit_received(newest_hash):

            try:
                if pbar:
                    set_progress(75)

                # -------------------------------------------------
                # NEUER COMMIT VON STREAMBOARD
                # -------------------------------------------------
                new_hash = str(
                    newest_hash
                ).strip().lower()

                # -------------------------------------------------
                # BISHERIGER AKTUELLER COMMIT AUS CONFIG
                # -------------------------------------------------
                old_hash = str(
                    self.cfg.get(
                        "last_stream_commit",
                        ""
                    )
                ).strip().lower()

                # -------------------------------------------------
                # ANZEIGE
                # -------------------------------------------------
                new_display = (
                    new_hash[:8]
                    if new_hash
                    else "---"
                )

                old_display = (
                    old_hash[:8]
                    if old_hash
                    else "---"
                )

                # -------------------------------------------------
                # TEXTE
                # -------------------------------------------------
                msg_new = self.TEXT.get(
                    "check_commit_new_found",
                    "Neuer Commit gefunden!"
                )

                msg_up = self.TEXT.get(
                    "check_commit_up_to_date",
                    "Kein neuer Commit vorhanden."
                )

                lbl_new = self.TEXT.get(
                    "check_commit_new_hash",
                    "Neu:"
                )

                lbl_old = self.TEXT.get(
                    "check_commit_old_hash",
                    "Alt:"
                )

                # -------------------------------------------------
                # PRÜFEN
                # -------------------------------------------------
                is_new_commit = (
                    new_hash != old_hash
                )

                print(
                    "[COMMIT] Streamboard:",
                    new_hash,
                    flush=True
                )

                print(
                    "[COMMIT] bisher last_stream_commit:",
                    old_hash,
                    flush=True
                )

                print(
                    "[COMMIT] neuer Commit:",
                    is_new_commit,
                    flush=True
                )

                # =================================================
                # NEUER COMMIT
                # =================================================
                if is_new_commit:

                    safe_play(
                        "complete.oga"
                    )

                    self.log_message(
                        "<span style='color:cyan;'>"
                        f"🆕 {msg_new} "
                        f"({new_display})"
                        "</span>"
                    )

                    info_text = (
                        f"{msg_new}\n\n"
                        f"{lbl_new} {new_display}\n"
                        f"{lbl_old} {old_display}"
                    )

                # =================================================
                # KEIN NEUER COMMIT
                # =================================================
                else:

                    safe_play(
                        "dialog-information.oga"
                    )

                    self.log_message(
                        "<span style='color:cyan;'>"
                        f"ℹ️ {msg_up} "
                        f"({new_display})"
                        "</span>"
                    )

                    info_text = (
                        f"{msg_up}\n\n"
                        f"{lbl_new} {new_display}\n"
                        f"{lbl_old} {old_display}"
                    )

                # -------------------------------------------------
                # DIALOG
                # -------------------------------------------------
                QMessageBox.information(
                    self,
                    self.TEXT.get(
                        "check_commit_title",
                        "OSCam Commit-Check"
                    ),
                    info_text
                )

                
                # =================================================
                # COMMIT-HISTORIE AKTUALISIEREN
                # NUR wenn tatsächlich ein neuer Commit vorhanden ist
                # =================================================

                if is_new_commit:

                    # Bisheriger aktueller Commit wird zum vorherigen
                    self.cfg[
                        "previous_stream_commit"
                    ] = old_hash

                    # Neuer Streamboard-Commit wird aktuell
                    self.cfg[
                        "last_stream_commit"
                    ] = new_hash

                    print(
                        "[COMMIT] Neuer Commit erkannt",
                        flush=True
                    )

                    print(
                        "[COMMIT] previous_stream_commit:",
                        self.cfg[
                            "previous_stream_commit"
                        ],
                        flush=True
                    )

                    print(
                        "[COMMIT] last_stream_commit:",
                        self.cfg[
                            "last_stream_commit"
                        ],
                        flush=True
                    )

                    # -------------------------------------------------
                    # CONFIG NUR BEI NEUEM COMMIT SPEICHERN
                    # -------------------------------------------------
                    save_config_func = globals().get(
                        "save_config"
                    )

                    if not save_config_func:
                        raise RuntimeError(
                            "save_config wurde nicht gefunden."
                        )

                    result = save_config_func(
                        self.cfg,
                        gui_instance=self,
                        silent=True
                    )

                    print(
                        "[COMMIT] save_config:",
                        result,
                        flush=True
                    )

                else:

                    print(
                        "[COMMIT] Kein neuer Commit - "
                        "Historie bleibt unverändert.",
                        flush=True
                    )


                # -------------------------------------------------
                # CONFIG SPEICHERN
                # -------------------------------------------------
                save_config_func = globals().get(
                    "save_config"
                )

                if not save_config_func:
                    raise RuntimeError(
                        "save_config wurde nicht gefunden."
                    )

                result = save_config_func(
                    self.cfg,
                    gui_instance=self,
                    silent=True
                )

                print(
                    "[COMMIT] save_config:",
                    result,
                    flush=True
                )

                # -------------------------------------------------
                # PROGRESS
                # -------------------------------------------------
                if pbar:

                    if is_new_commit:

                        finalize_pbar(
                            f"🆕 {msg_new}",
                            3
                        )

                    else:

                        finalize_pbar(
                            f"✅ {msg_up}",
                            3
                        )

            except Exception as e:

                safe_play(
                    "dialog-error.oga"
                )

                error_text = str(e)

                self.log_message(
                    "<span style='color:red;'>"
                    f"❌ {error_text}"
                    "</span>"
                )

                QMessageBox.critical(
                    self,
                    self.TEXT.get(
                        "check_commit_title",
                        "OSCam Commit-Check"
                    ),
                    error_text
                )

                if pbar:
                    finalize_pbar(
                        "❌ Fehler"
                    )






        # ---------------------------------------------------------
        # Fehler vom Worker
        # ---------------------------------------------------------
        def commit_error(error_text):

            safe_play(
                "dialog-error.oga"
            )

            err_lbl = self.TEXT.get(
                "check_commit_error",
                "Fehler beim Check:"
            )

            self.log_message(
                "<span style='color:red;'>"
                f"❌ {err_lbl} {error_text}"
                "</span>"
            )

            QMessageBox.critical(
                self,
                self.TEXT.get(
                    "check_commit_title",
                    "OSCam Commit-Check"
                ),
                f"{err_lbl}\n{error_text}"
            )

            if pbar:
                finalize_pbar(
                    "❌ Fehler"
                )

        # ---------------------------------------------------------
        # Signale verbinden
        # ---------------------------------------------------------
        worker.success.connect(
            commit_received
        )

        worker.error.connect(
            commit_error
        )

        # ---------------------------------------------------------
        # Thread nach Ende aufräumen
        # ---------------------------------------------------------
        def worker_finished():
            self._commit_check_worker = None

        worker.finished.connect(
            worker_finished
        )

        # ---------------------------------------------------------
        # Start
        # ---------------------------------------------------------
        worker.start()

    def check_emu_credentials(self):
        cfg = load_github_config()
        if not all([cfg.get("emu_repo_url"), cfg.get("username"), cfg.get("token")]):
            lang = getattr(self, "LANG", LANG)
            self.append_info(
                self.info_text,
                TEXTS[lang].get(
                    "github_emu_credentials_missing", "GitHub-Emu-Zugangsdaten fehlen!"
                ),
                "warning",
            )

    def edit_emu_github_config(self, info_widget=None, progress_callback=None):
        """
        Öffnet den GitHub-Konfigurationsdialog mit Regenbogen-ProgressBar,
        schwarzer Schrift, Sound und zweisprachigem UI.
        """
        from PyQt6.QtWidgets import QFormLayout, QLabel, QDialogButtonBox, QApplication
        from PyQt6.QtCore import QTimer

        # --- Final Label verstecken ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        widget = info_widget or getattr(self, "info_text", None)
        pbar = getattr(self, "progress_bar", None)
        current_lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = current_lang == "de"

        # --- Styles ---
        rainbow = (
            "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
            "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
        )
        style_rainbow = f"""
            QProgressBar {{
                text-align: center;
                font-weight: bold;
                border: 2px solid #222;
                border-radius: 6px;
                background-color: #111;
                color: black;
                font-size: 11pt;
            }}
            QProgressBar::chunk {{
                background-color: {rainbow};
                border-radius: 4px;
            }}
        """
        style_fade = """
            QProgressBar {
                text-align: center;
                font-weight: bold;
                border: 2px solid #222;
                border-radius: 6px;
                background-color: #111;
                color: black;
                font-size: 11pt;
            }
            QProgressBar::chunk { background-color: transparent; }
        """

        # --- Helper-Funktionen ---
        def set_progress(val, txt=None):
            if pbar:
                pbar.setStyleSheet(style_rainbow)
                pbar.setValue(val)
                pbar.setFormat(txt if txt else "%p%")
                pbar.show()
            if progress_callback:
                try:
                    progress_callback(val)
                except:
                    pass
            QApplication.processEvents()

        def finalize_pbar(text, visible_seconds=3):
            if pbar:
                pbar.setValue(100)
                pbar.setFormat(text)
                QTimer.singleShot(
                    visible_seconds * 1000, lambda: pbar.setStyleSheet(style_fade)
                )
                QTimer.singleShot(visible_seconds * 1000, lambda: pbar.setValue(0))
                if progress_callback:
                    QTimer.singleShot(
                        visible_seconds * 1000, lambda: progress_callback(0)
                    )

        def play_sound(action="open"):
            if "safe_play" in globals():
                sound_map = {"open": "dialog-information.oga", "save": "complete.oga"}
                safe_play(sound_map.get(action, "complete.oga"))

        def get_txt(key, default=""):
            lang_pkg = TEXTS.get(current_lang, TEXTS.get("de", {}))
            return lang_pkg.get(key, default)

        # --- Start Progress ---
        set_progress(
            20,
            "⏳ "
            + (
                get_txt("loading_config", "Konfiguration wird geladen...")
                if is_de
                else "Loading configuration..."
            ),
        )
        play_sound("open")

        dialog = GithubConfigDialog(self)
        set_progress(50)

        # UI Texte anpassen
        layout = dialog.layout()
        if isinstance(layout, QFormLayout):
            mapping = [
                (dialog.patch_repo, "patch_repo_label", "Patch Repo:"),
                (dialog.patch_branch, "patch_branch_label", "Patch Branch:"),
                (dialog.emu_repo, "emu_repo_label", "EMU Repo:"),
                (dialog.emu_branch, "emu_branch_label", "EMU Branch:"),
                (dialog.username, "github_username_label", "GitHub User:"),
                (dialog.token, "github_token_label", "Token:"),
                (dialog.user_name, "github_user_name_label", "Git Name:"),
                (dialog.user_email, "github_user_email_label", "Git Email:"),
            ]
            for field, key, default in mapping:
                label = layout.labelForField(field)
                if label and isinstance(label, QLabel):
                    label.setText(get_txt(key, default))

        # Buttons anpassen
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            save_btn = button_box.button(QDialogButtonBox.StandardButton.Save)
            cancel_btn = button_box.button(QDialogButtonBox.StandardButton.Cancel)
            if save_btn:
                save_btn.setText(get_txt("save", "Speichern"))
            if cancel_btn:
                cancel_btn.setText(get_txt("cancel", "Abbrechen"))

        set_progress(
            80, "🔧 " + (get_txt("config_ready", "Bereit") if is_de else "Ready")
        )

        # --- Dialog ausführen ---
        if dialog.exec():
            msg = get_txt("github_config_saved", "GitHub Konfiguration gespeichert.")
            self.append_info(widget, msg, "success")
            play_sound("save")
            finalize_pbar(
                "✅ " + (get_txt("saved", "Gespeichert!") if is_de else "Saved!")
            )
        else:
            finalize_pbar("%p%")


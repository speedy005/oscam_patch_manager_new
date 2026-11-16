"""OSCam Patch Manager module fragment: Repository upload and remote integration."""

# Explicit module imports (kept broad for compatibility with legacy callbacks).
import ctypes
import glob
import importlib.util
import io
import json
import locale
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from PyQt6.QtCore import QDateTime, QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect, QSize, QThread, QTime, QTimer, QUrl, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPolygon, QTextCursor
from PyQt6.QtWidgets import QApplication, QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QFrame, QGraphicsColorizeEffect, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLayout, QLineEdit, QMessageBox, QProgressBar, QPushButton, QSizePolicy, QSlider, QTextEdit, QVBoxLayout, QWidget, QWidgetItem
from datetime import datetime, timezone

from translations import TEXTS
from workers import safe_play
from patch_format import load_github_config
from paths import PATCH_EMU_GIT_DIR

# ===================== GITHUB UPLOAD OSCAM-EMU FOLDER =====================

def github_upload_oscam_emu_folder(
    gui_instance=None,
    info_widget=None,
    progress_callback=None
):
    """
    Sicherer Upload aus PATCH_EMU_GIT_DIR über einen temporären Klon.
    Das Quellrepository wird niemals verändert.
    """

    import io
    import os
    import shutil
    import subprocess
    import tarfile
    import tempfile

    from PyQt6.QtWidgets import QApplication, QTextEdit

    target_url = "https://github.com/speedy005/Oscam-emu.git"
    source_dir = os.path.abspath(os.path.expanduser(str(PATCH_EMU_GIT_DIR or "")))

    widget = info_widget or getattr(gui_instance, "info_text", None)
    pbar = getattr(gui_instance, "progress_bar", None)
    lang = str(getattr(gui_instance, "LANG", "de")).lower()[:2]
    is_de = lang == "de"

    temp_root = None
    askpass_dir = None
    env = None
    last_progress = 0

    def tr(key, de_text, en_text):
        try:
            value = TEXTS.get(lang, {}).get(key)
            if value:
                return value
        except Exception:
            pass
        return de_text if is_de else en_text

    def log(message, level="info"):
        try:
            if gui_instance and hasattr(gui_instance, "append_info"):
                gui_instance.append_info(widget, str(message), level)
            elif isinstance(widget, QTextEdit):
                color = {
                    "success": "#39FF14",
                    "warning": "orange",
                    "error": "red"
                }.get(level, "gray")
                widget.append(
                    f'<span style="color:{color}">{message}</span>'
                )
        except Exception:
            pass

        try:
            QApplication.processEvents()
        except Exception:
            pass

    def progress(value, message=None, error=False):
        nonlocal last_progress
        last_progress = value

        try:
            if pbar:
                color = "#FF0000" if error else "#00FFFF"
                pbar.setStyleSheet(
                    "QProgressBar {"
                    "border:2px solid #444;border-radius:8px;"
                    "background:#0A0A0A;color:white;"
                    "text-align:center;font-weight:bold;"
                    "min-height:35px;}"
                    f"QProgressBar::chunk {{background:{color};}}"
                )
                pbar.setValue(int(value))
                pbar.setFormat(message or f"{value}%")
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

    def run_git(args, cwd, check=True):
        result = subprocess.run(
            ["git"] + list(args),
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if check and result.returncode != 0:
            message = (result.stderr or result.stdout or "Unbekannter Git-Fehler").strip()
            raise RuntimeError(message)
        return result

    def remote_sha(cwd, branch):
        result = run_git(
            ["ls-remote", target_url, f"refs/heads/{branch}"],
            cwd
        )
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 2 and fields[1] == f"refs/heads/{branch}":
                return fields[0]
        return None

    def cleanup():
        nonlocal temp_root, askpass_dir, env

        if env is not None:
            for key in (
                "OSC_GITHUB_USERNAME",
                "OSC_GITHUB_TOKEN",
                "GIT_USERNAME",
                "GIT_ASKPASS"
            ):
                env.pop(key, None)

        if temp_root and os.path.isdir(temp_root):
            shutil.rmtree(temp_root, ignore_errors=True)

        if askpass_dir and os.path.isdir(askpass_dir):
            shutil.rmtree(askpass_dir, ignore_errors=True)

        temp_root = None
        askpass_dir = None
        env = None

    def play_sound(success):
        try:
            safe_play("complete.oga" if success else "dialog-error.oga")
        except Exception:
            pass

    try:
        if gui_instance and hasattr(gui_instance, "hide_final_label"):
            try:
                gui_instance.hide_final_label()
            except Exception:
                pass

        progress(5, "⏳ GitHub-Upload wird vorbereitet...")

        cfg = load_github_config()
        if not isinstance(cfg, dict):
            raise RuntimeError("GitHub-Konfiguration ist ungültig.")

        username = str(cfg.get("username") or "").strip()
        token = str(cfg.get("token") or "").strip()
        user_name = str(cfg.get("user_name") or "").strip()
        user_email = str(cfg.get("user_email") or "").strip()
        branch = str(cfg.get("emu_branch") or "master").strip()

        if not username or not token:
            raise RuntimeError("GitHub Username oder Token fehlt in der Config.")

        if not user_name or not user_email:
            raise RuntimeError("Git user.name oder user.email fehlt in der Config.")

        if not source_dir or not os.path.isdir(source_dir):
            raise RuntimeError(f"Quellordner existiert nicht: {source_dir}")

        if any(c.isspace() for c in branch):
            raise RuntimeError("Ungültiger Git-Branch.")

        check_branch = subprocess.run(
            ["git", "check-ref-format", "--branch", branch],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if check_branch.returncode != 0:
            raise RuntimeError("Der konfigurierte Git-Branch ist ungültig.")

        # Sicherstellen, dass die Quelle tatsächlich ein Git-Repository ist.
        source_top = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if source_top.returncode != 0:
            raise RuntimeError("Der OSCam-Emu-Quellordner ist kein Git-Repository.")

        if os.path.realpath(source_top.stdout.strip()) != os.path.realpath(source_dir):
            raise RuntimeError("Der konfigurierte Quellordner ist nicht die Repository-Wurzel.")

        # Inhaltliche Änderungen und unversionierte Dateien nicht stillschweigend hochladen.
        diff_check = subprocess.run(
            ["git", "diff", "--ignore-space-at-eol", "--quiet", "HEAD", "--"],
            cwd=source_dir
        )
        if diff_check.returncode != 0:
            raise RuntimeError(
                "Das Quellrepository enthält inhaltliche Änderungen. "
                "Upload aus Sicherheitsgründen abgebrochen."
            )

        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if untracked.returncode != 0:
            raise RuntimeError("Unversionierte Dateien konnten nicht geprüft werden.")
        if untracked.stdout.strip():
            raise RuntimeError(
                "Das Quellrepository enthält unversionierte Dateien. "
                "Bitte zuerst prüfen."
            )

        source_head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if source_head.returncode != 0:
            raise RuntimeError("Quell-Commit konnte nicht ermittelt werden.")
        source_head = source_head.stdout.strip()

        # Submodul-Gitlink aus dem Quell-HEAD lesen.
        wiki_result = subprocess.run(
            ["git", "ls-tree", "HEAD", "wiki"],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if wiki_result.returncode != 0:
            raise RuntimeError("Wiki-Submodul konnte nicht geprüft werden.")

        wiki_sha = None
        for line in wiki_result.stdout.splitlines():
            if "\twiki" in line and line.startswith("160000 commit "):
                wiki_sha = line.split()[2]
                break

        # ASKPASS ausschließlich im temporären Verzeichnis.
        temp_root = tempfile.mkdtemp(prefix="oscam_emu_upload_")
        askpass_dir = os.path.join(temp_root, "askpass")
        os.makedirs(askpass_dir)

        askpass_script = os.path.join(askpass_dir, "askpass.py")
        with open(askpass_script, "w", encoding="utf-8") as handle:
            handle.write(
                "import os, sys\n"
                "p = ' '.join(sys.argv[1:]).lower()\n"
                "if 'username' in p or 'user' in p:\n"
                "    print(os.environ.get('OSC_GITHUB_USERNAME', ''), end='')\n"
                "else:\n"
                "    print(os.environ.get('OSC_GITHUB_TOKEN', ''), end='')\n"
            )

        if os.name == "nt":
            askpass = os.path.join(askpass_dir, "askpass.cmd")
            with open(askpass, "w", encoding="utf-8") as handle:
                handle.write(
                    "@echo off\r\n"
                    f'"{sys.executable}" "{askpass_script}" %*\r\n'
                )
        else:
            askpass = os.path.join(askpass_dir, "askpass.sh")
            with open(askpass, "w", encoding="utf-8") as handle:
                handle.write(
                    "#!/bin/sh\n"
                    f'exec "{sys.executable}" "{askpass_script}" "$@"\n'
                )
            os.chmod(askpass, 0o700)

        env = os.environ.copy()
        env.update({
            "OSC_GITHUB_USERNAME": username,
            "OSC_GITHUB_TOKEN": token,
            "GIT_USERNAME": username,
            "GIT_ASKPASS": askpass,
            "GIT_ASKPASS_REQUIRE": "force",
            "GIT_TERMINAL_PROMPT": "0"
        })

        progress(15, "🔎 GitHub-Ziel wird geprüft...")
        log(f"Quelle: {source_dir}")
        log(f"GitHub-Ziel: {target_url}")
        log(f"Branch: {branch}")

        initial_sha = remote_sha(temp_root, branch)
        if not initial_sha:
            raise RuntimeError(
                f"Der GitHub-Branch '{branch}' existiert nicht. "
                "Es wird kein neuer Branch automatisch angelegt."
            )

        # Separate Arbeitskopie – niemals im Quellrepository arbeiten.
        repo_dir = os.path.join(temp_root, "github_worktree")

        progress(25, "📥 GitHub-Repository wird temporär geklont...")
        run_git(
            ["clone", "--branch", branch, "--single-branch", target_url, repo_dir],
            temp_root
        )

        cloned_head = run_git(["rev-parse", "HEAD"], repo_dir).stdout.strip()
        if cloned_head != initial_sha:
            raise RuntimeError(
                "GitHub wurde während des Klonens verändert. "
                "Bitte Upload erneut starten."
            )

        # Vorhandenes GitHub-README sichern.
        readme_path = os.path.join(repo_dir, "README.md")
        saved_readme = None
        if os.path.isfile(readme_path):
            with open(readme_path, "rb") as handle:
                saved_readme = handle.read()

        # Originalen GitHub-.github-Ordner vollständig sichern.
        github_dir = os.path.join(repo_dir, ".github")
        saved_github_dir = os.path.join(temp_root, "saved_github")
        if os.path.isdir(github_dir):
            shutil.copytree(github_dir, saved_github_dir, symlinks=True)

        # Git-Archiv des geprüften Quell-HEAD erstellen.
        progress(40, "📦 OSCam-Emu-Quellstand wird vorbereitet...")
        archive = subprocess.run(
            ["git", "archive", "--format=tar", "HEAD"],
            cwd=source_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        if archive.returncode != 0:
            raise RuntimeError(
                archive.stderr.decode("utf-8", errors="replace")
            )

        # Im temporären Klon alte Nutzdateien entfernen, .git behalten.
        for name in os.listdir(repo_dir):
            if name == ".git":
                continue
            path = os.path.join(repo_dir, name)
            if os.path.islink(path) or os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)

        # Archiv sicher in den temporären Klon entpacken.
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            members = tar.getmembers()
            root = os.path.realpath(repo_dir)
            for member in members:
                destination = os.path.realpath(
                    os.path.join(repo_dir, member.name)
                )
                if os.path.commonpath([root, destination]) != root:
                    raise RuntimeError("Ungültiger Pfad im Quellarchiv.")
            tar.extractall(path=repo_dir, members=members)

        # Originalen .github-Ordner aus dem GitHub-Ziel wiederherstellen.
        if os.path.isdir(saved_github_dir):
            restored_github_dir = os.path.join(repo_dir, ".github")
            if os.path.lexists(restored_github_dir):
                if os.path.islink(restored_github_dir) or os.path.isfile(restored_github_dir):
                    os.remove(restored_github_dir)
                else:
                    shutil.rmtree(restored_github_dir)
            shutil.copytree(saved_github_dir, restored_github_dir, symlinks=True)

        # README aus dem GitHub-Ziel wiederherstellen.
        if saved_readme is not None:
            with open(readme_path, "wb") as handle:
                handle.write(saved_readme)

        # Dateien im temporären Klon stagen.
        run_git(["add", "-f", "-A"], repo_dir)

        # Git-Submodulreferenz wieder als Gitlink eintragen.
        if wiki_sha:
            run_git(
                ["update-index", "--add", "--cacheinfo",
                 f"160000,{wiki_sha},wiki"],
                repo_dir
            )

        staged = run_git(["diff", "--cached", "--quiet"], repo_dir, check=False)
        if staged.returncode == 0:
            progress(100, "ℹ️ Keine Änderungen – GitHub ist bereits aktuell.")
            log("Keine Änderungen zum Hochladen.", "success")
            play_sound(True)
            return

        if staged.returncode != 1:
            raise RuntimeError("Änderungen im temporären Klon konnten nicht geprüft werden.")

        progress(65, "📝 Upload-Commit wird erstellt...")
        run_git(
            [
                "-c", f"user.name={user_name}",
                "-c", f"user.email={user_email}",
                "commit", "-m", "Update OSCam-Emu source"
            ],
            repo_dir
        )

        local_commit = run_git(["rev-parse", "HEAD"], repo_dir).stdout.strip()

        # Unmittelbar vor dem Push prüfen, ob das Ziel noch unverändert ist.
        progress(80, "🔐 GitHub-Stand wird vor dem Push erneut geprüft...")
        current_sha = remote_sha(temp_root, branch)
        if current_sha != initial_sha:
            raise RuntimeError(
                "GitHub wurde zwischenzeitlich verändert. "
                "Der Push wurde zum Schutz vor Überschreiben abgebrochen."
            )

        progress(90, "🚀 Änderungen werden zu GitHub übertragen...")
        run_git(
            ["push", "origin", f"HEAD:refs/heads/{branch}"],
            repo_dir
        )

        # Remote-Ergebnis verifizieren.
        progress(96, "🔍 Upload wird überprüft...")
        final_sha = remote_sha(temp_root, branch)
        if final_sha != local_commit:
            raise RuntimeError(
                "Push wurde ausgeführt, aber die abschließende "
                "GitHub-Prüfung stimmt nicht mit dem lokalen Commit überein."
            )

        progress(
            100,
            tr(
                "github_upload_success",
                "✅ OSCam-Emu erfolgreich zu GitHub hochgeladen!",
                "✅ OSCam-Emu successfully uploaded to GitHub!"
            )
        )
        log(f"GitHub-Commit: {final_sha}", "success")
        log("Das lokale Quellrepository wurde nicht verändert.", "success")
        play_sound(True)

    except Exception as exc:
        message = str(exc)
        try:
            if "token" in locals() and token:
                message = message.replace(token, "***TOKEN***")
            if "username" in locals() and username and token:
                message = message.replace(
                    f"{username}:{token}",
                    f"{username}:***TOKEN***"
                )
        except Exception:
            pass

        progress(
            last_progress,
            tr(
                "github_upload_failed",
                "❌ GitHub-Upload fehlgeschlagen",
                "❌ GitHub upload failed"
            ),
            error=True
        )
        log(f"Upload-Fehler: {message}", "error")
        play_sound(False)

    finally:
        cleanup()


# =====================
# GITHUB CONFIG DIALOG
# =====================

# Kompatibilitäts-Export: Die GUI verwendet run_bash aus diesem Modul.
# Die Implementierung liegt zentral in patch_format, damit sie nicht dupliziert wird.
from patch_format import run_bash  # noqa: E402

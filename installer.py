#!/usr/bin/env python3
"""Cross-platform installer for OSCam Patch Manager New.

Run this script from the repository root. It copies application files to a
user-selected directory, excluding installer files and .png/.zip/.md/.php files.
"""
from __future__ import annotations

import locale
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_URL = "https://github.com/speedy005/oscam_patch_manager_new"
BLOCKED_EXTENSIONS = {".png", ".zip", ".md", ".php"}
INSTALLER_FILES = {
    "installer.py", "installer.sh", "installer.bat",
    "install.sh", "install.bat", "install.py",
}
SKIP_DIRS = {".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "venv", "env"}

TEXT = {
    "en": {
        "title": "OSCam Patch Manager — Installer",
        "language": "Language: [E]nglish / [D]eutsch (default: English): ",
        "welcome": "This installer copies the application to a directory you choose.",
        "source": "Source directory: {}",
        "path": "Installation path (press Enter for the default) [{}]: ",
        "missing": "Error: required application file not found: {}",
        "same": "Error: the installation directory must not be the source repository or a subdirectory of it.",
        "confirm": "Install to this directory? [Y/n]: ",
        "cancel": "Installation cancelled.",
        "copying": "Copying application files…",
        "excluded": "Excluded files: .png, .zip, .md, .php, installer-related files, and development/cache folders.",
        "deps": "Install Python dependencies from requirements.txt now? [Y/n]: ",
        "pip_start": "Installing Python dependencies…",
        "pip_fail": "Warning: dependency installation failed. You can retry with: python -m pip install -r requirements.txt",
        "pip_skip": "Dependency installation skipped.",
        "done": "Installation complete!",
        "installed": "Installed to: {}",
        "run": "Start the app with: {}",
        "no_req": "requirements.txt was not found; dependencies were not installed.",
        "blocked_dest": "Error: the destination already contains files with excluded extensions. Choose an empty folder or remove these files first: {}",
        "error": "Installation failed: {}",
    },
    "de": {
        "title": "OSCam Patch Manager — Installer",
        "language": "Sprache: [D]eutsch / [E]nglish (Standard: Deutsch): ",
        "welcome": "Dieser Installer kopiert die Anwendung in einen Ordner deiner Wahl.",
        "source": "Quellordner: {}",
        "path": "Installationspfad (Enter für Standardpfad) [{}]: ",
        "missing": "Fehler: benötigte Anwendungsdatei nicht gefunden: {}",
        "same": "Fehler: Der Installationsordner darf nicht das Quell-Repository oder ein Unterordner davon sein.",
        "confirm": "In diesen Ordner installieren? [J/n]: ",
        "cancel": "Installation abgebrochen.",
        "copying": "Anwendungsdateien werden kopiert…",
        "excluded": "Ausgeschlossen: .png, .zip, .md, .php, Installer-Dateien sowie Entwicklungs-/Cache-Ordner.",
        "deps": "Python-Abhängigkeiten aus requirements.txt jetzt installieren? [J/n]: ",
        "pip_start": "Python-Abhängigkeiten werden installiert…",
        "pip_fail": "Warnung: Installation der Abhängigkeiten fehlgeschlagen. Erneut versuchen mit: python -m pip install -r requirements.txt",
        "pip_skip": "Installation der Abhängigkeiten übersprungen.",
        "done": "Installation abgeschlossen!",
        "installed": "Installiert nach: {}",
        "run": "Programm starten mit: {}",
        "no_req": "requirements.txt wurde nicht gefunden; Abhängigkeiten wurden nicht installiert.",
        "blocked_dest": "Fehler: Im Zielordner liegen bereits Dateien mit ausgeschlossenen Endungen. Bitte einen leeren Ordner wählen oder diese Dateien vorher entfernen: {}",
        "error": "Installation fehlgeschlagen: {}",
    },
}


def detect_language() -> str:
    try:
        lang = (locale.getlocale()[0] or "").lower()
    except (ValueError, TypeError):
        lang = ""
    return "de" if lang.startswith("de") else "en"


def ask_yes_no(prompt: str, lang: str, default: bool = True) -> bool:
    answer = input(prompt).strip().lower()
    if not answer:
        return default
    yes = {"y", "yes", "j", "ja", "d", "e"}
    no = {"n", "no", "nein"}
    return answer in (yes if default else no)


def is_installer_file(path: Path) -> bool:
    name = path.name.lower()
    if name in INSTALLER_FILES:
        return True
    # Keep any future installer-specific scripts/docs out of the installed app.
    return name.startswith("installer_") or name.startswith("install_helper")


def should_skip(path: Path, source: Path) -> bool:
    rel = path.relative_to(source)
    if any(part in SKIP_DIRS for part in rel.parts):
        return True
    if path.is_file() and path.suffix.lower() in BLOCKED_EXTENSIONS:
        return True
    if path.is_file() and is_installer_file(path):
        return True
    return False


def install(source: Path, destination: Path, lang: str) -> int:
    t = TEXT[lang]
    source = source.resolve()
    destination = destination.expanduser().resolve()

    required = ["main.py", "requirements.txt"]
    if not (source / "main.py").is_file():
        print(t["missing"].format("main.py"))
        return 1

    if destination == source or source in destination.parents:
        print(t["same"])
        return 1

    print("\n" + t["title"])
    print("=" * len(t["title"]))
    print(t["welcome"])
    print(t["source"].format(source))
    print(t["excluded"])
    if not ask_yes_no(t["confirm"], lang, True):
        print(t["cancel"])
        return 0

    try:
        destination.mkdir(parents=True, exist_ok=True)
        # Avoid deleting user data: require a clean destination if it already
        # contains files with extensions that are forbidden in the install tree.
        conflicts = [p for p in destination.rglob("*")
                     if p.is_file() and p.suffix.lower() in BLOCKED_EXTENSIONS]
        if conflicts:
            preview = ", ".join(str(p) for p in conflicts[:5])
            if len(conflicts) > 5:
                preview += f" (+{len(conflicts) - 5} more)"
            print(t["blocked_dest"].format(preview))
            return 1

        print(t["copying"])
        copied = 0
        for current, dirs, files in os.walk(source):
            current_path = Path(current)
            rel_dir = current_path.relative_to(source)
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not is_installer_file(Path(d))]
            target_dir = destination / rel_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            for filename in files:
                src_file = current_path / filename
                if should_skip(src_file, source):
                    continue
                # Never copy files into the installer's own source tree.
                dest_file = destination / src_file.relative_to(source)
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                copied += 1

        req = destination / "requirements.txt"
        if req.is_file():
            if ask_yes_no(t["deps"], lang, True):
                print(t["pip_start"])
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--user", "-r", str(req)],
                    check=False,
                )
                if result.returncode != 0:
                    print(t["pip_fail"])
            else:
                print(t["pip_skip"])
        else:
            print(t["no_req"])

        launcher = "start_windows.bat" if os.name == "nt" else "start_linux.sh"
        launcher_path = destination / launcher
        if os.name != "nt" and launcher_path.exists():
            try:
                launcher_path.chmod(launcher_path.stat().st_mode | 0o111)
            except OSError:
                pass
        print("\n" + t["done"])
        print(t["installed"].format(destination))
        if (destination / "main.py").exists():
            if os.name == "nt":
                command = f'cd /d "{destination}" && python main.py'
            else:
                command = f'cd "{destination}" && python3 main.py'
            print(t["run"].format(command))
        print(f"Files copied: {copied}")
        return 0
    except (OSError, shutil.Error) as exc:
        print(t["error"].format(exc))
        return 1


def main() -> int:
    lang = detect_language()
    prompt = TEXT[lang]["language"]
    answer = input(prompt).strip().lower()
    if answer:
        if answer.startswith(("d", "j")):
            lang = "de"
        elif answer.startswith("e"):
            lang = "en"

    source = Path(__file__).resolve().parent
    default = Path.home() / "OSCamPatchManager"
    chosen = input(TEXT[lang]["path"].format(default)).strip()
    destination = Path(chosen.strip('"')) if chosen else default
    return install(source, destination, lang)


if __name__ == "__main__":
    raise SystemExit(main())

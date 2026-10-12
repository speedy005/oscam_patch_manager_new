
#!/usr/bin/env python3
"""Cross-platform installer for OSCam Emu Patch Manager."""

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

OWNER = "speedy005"
REPO = "oscam_patch_manager_new"
BRANCH = "master"

API_URL = (
    f"https://api.github.com/repos/{OWNER}/{REPO}"
    f"/git/trees/{BRANCH}?recursive=1"
)
RAW_URL = (
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/"
)

SKIP_EXTENSIONS = {".png", ".zip", ".md", ".php"}
SKIP_DIRS = {
    ".git", ".github", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".venv", "venv", "env", "node_modules",
}
SKIP_FILES = {
    "installer.py", "installer.sh", "installer.bat",
    "install.py", "install.sh", "install.bat",
    "version.txt",
}

IS_WINDOWS = platform.system() == "Windows"
LANG = "en"

TEXT = {
    "en": {
        "title": "OSCam Emu Patch Manager Installer",
        "language": "Choose language: [1] English  [2] Deutsch",
        "folder": "Choose installation folder",
        "path": "Installation path",
        "confirm": "Install into this directory? [y/N]: ",
        "overwrite": (
            "Existing files found. Overwrite matching project files? [y/N]: "
        ),
        "cancel": "Installation cancelled.",
        "loading": "Reading GitHub repository...",
        "download": "Downloading",
        "deps": "Installing Python dependencies...",
        "done": "Installation completed.",
        "failed": "Installation failed",
        "missing_main": "main.py was not found in the repository.",
        "no_files": "No project files were found.",
        "python": "Python 3.9 or newer is required.",
        "launcher": "Start the application using",
        "kept": "Keeping existing file",
        "venv_remove": "Removing old virtual environment...",
        "requirements_missing": (
            "requirements.txt not found; skipping dependency installation."
        ),
        "linux_pip_error": (
            "Linux blocked the package installation. This system may use "
            "PEP 668 to protect its Python installation. Install the required "
            "packages using your distribution's supported method."
        ),
    },
    "de": {
        "title": "OSCam Emu Patch Manager Installation",
        "language": "Sprache wählen: [1] Englisch  [2] Deutsch",
        "folder": "Installationsordner auswählen",
        "path": "Installationspfad",
        "confirm": "In dieses Verzeichnis installieren? [j/N]: ",
        "overwrite": (
            "Vorhandene Dateien gefunden. "
            "Passende Projektdateien überschreiben? [j/N]: "
        ),
        "cancel": "Installation abgebrochen.",
        "loading": "Lese GitHub-Repository...",
        "download": "Lade herunter",
        "deps": "Installiere Python-Abhängigkeiten...",
        "done": "Installation abgeschlossen.",
        "failed": "Installation fehlgeschlagen",
        "missing_main": "main.py wurde im Repository nicht gefunden.",
        "no_files": "Keine Projektdateien gefunden.",
        "python": "Python 3.9 oder neuer wird benötigt.",
        "launcher": "Starte die Anwendung mit",
        "kept": "Vorhandene Datei bleibt erhalten",
        "venv_remove": "Entferne alte virtuelle Umgebung...",
        "requirements_missing": (
            "requirements.txt nicht gefunden; "
            "Paketinstallation wird übersprungen."
        ),
        "linux_pip_error": (
            "Linux hat die Paketinstallation blockiert. "
            "Dieses System schützt Python möglicherweise mit PEP 668. "
            "Installiere die benötigten Pakete mit der von deiner "
            "Distribution unterstützten Methode."
        ),
    },
}


def detect_language():
    locale = (
        os.environ.get("LC_ALL")
        or os.environ.get("LC_MESSAGES")
        or os.environ.get("LANG")
        or ""
    ).lower()
    return "de" if locale.startswith("de") else "en"


def choose_language():
    default = detect_language()
    print(TEXT[default]["language"])
    answer = input("> ").strip()

    if answer == "1":
        return "en"
    if answer == "2":
        return "de"
    return default


def yes(answer):
    return answer.strip().lower() in {"y", "yes", "j", "ja"}


def choose_folder(default, lang):
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        selected = filedialog.askdirectory(
            title=TEXT[lang]["folder"],
            initialdir=str(default),
            mustexist=False,
        )
        root.destroy()

        if selected:
            return Path(selected).expanduser().resolve()
    except Exception:
        pass

    entered = input(f'{TEXT[lang]["path"]} [{default}]: ').strip()
    return Path(entered or str(default)).expanduser().resolve()


def github_get(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OSCam-Emu-Patch-Manager-Installer",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def should_skip(relative_path):
    path = Path(relative_path)
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()

    if parts & SKIP_DIRS:
        return True
    if name in SKIP_FILES:
        return True
    if path.suffix.lower() in SKIP_EXTENSIONS:
        return True

    return False


def get_repository_files():
    data = json.loads(github_get(API_URL).decode("utf-8"))

    if data.get("truncated"):
        raise RuntimeError("GitHub returned an incomplete file list.")

    files = [
        item["path"]
        for item in data.get("tree", [])
        if item.get("type") == "blob"
        and not should_skip(item.get("path", ""))
    ]

    if not files:
        raise RuntimeError(TEXT[LANG]["no_files"])

    if "main.py" not in files:
        raise RuntimeError(TEXT[LANG]["missing_main"])

    return files


def download_project(files, destination, overwrite, lang):
    root = destination.resolve()

    for relative in files:
        target = (root / relative).resolve()

        # Prevent repository paths from escaping the install folder.
        if not target.is_relative_to(root):
            raise RuntimeError(f"Unsafe repository path: {relative}")

        if target.exists() and not overwrite:
            print(f'{TEXT[lang]["kept"]}: {relative}')
            continue

        url = RAW_URL + quote(relative, safe="/")
        print(f'{TEXT[lang]["download"]}: {relative}')
        content = github_get(url)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def find_pip_command():
    """Return a Python executable that has pip available."""
    if IS_WINDOWS:
        candidates = [["py", "-3"], ["python"]]
    else:
        candidates = [["python3"]]

    for candidate in candidates:
        try:
            result = subprocess.run(
                candidate + ["-m", "pip", "--version"],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return candidate
        except OSError:
            continue

    raise RuntimeError(
        "Python 3 with pip is required. Install Python and pip, then retry."
    )


def install_dependencies(destination, lang):
    requirements = destination / "requirements.txt"

    if not requirements.is_file():
        print(TEXT[lang]["requirements_missing"])
        return

    python_command = find_pip_command()

    print(TEXT[lang]["deps"])

    command = python_command + [
        "-m", "pip", "install",
    ]

    # Windows: install for the selected Python installation.
    # Linux: prefer per-user installation to avoid modifying OS packages.
    if not IS_WINDOWS:
        command.append("--user")

    command += ["-r", str(requirements)]

    result = subprocess.run(command, check=False)

    if result.returncode != 0:
        if not IS_WINDOWS:
            raise RuntimeError(TEXT[lang]["linux_pip_error"])

        raise RuntimeError(
            "Dependency installation failed. Check Python, pip, "
            "your internet connection and requirements.txt."
        )


def remove_virtual_environment(destination, lang):
    venv_dir = destination / ".venv"

    if venv_dir.exists():
        print(TEXT[lang]["venv_remove"])
        shutil.rmtree(venv_dir)


def write_launchers(destination):
    if IS_WINDOWS:
        launcher = destination / "start_windows.bat"
        launcher.write_text(
            "@echo off\r\n"
            "setlocal\r\n"
            'cd /d "%~dp0"\r\n'
            "py -3 main.py %*\r\n"
            "if errorlevel 1 pause\r\n",
            encoding="utf-8",
        )
    else:
        launcher = destination / "start_linux.sh"
        launcher.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            'SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
            'cd "$SCRIPT_DIR"\n'
            'exec python3 main.py "$@"\n',
            encoding="utf-8",
        )
        launcher.chmod(launcher.stat().st_mode | 0o111)


def main():
    global LANG

    if sys.version_info < (3, 9):
        print(TEXT[detect_language()]["python"])
        return 1

    LANG = choose_language()
    text = TEXT[LANG]

    print(f'\n{text["title"]}\n')

    default = Path.home() / "OSCamEmuPatchManager"
    destination = choose_folder(default, LANG)

    if destination == Path(destination.anchor):
        print("Choose a normal directory, not a filesystem root.")
        return 1

    print(f"\n{destination}")

    if not yes(input(text["confirm"])):
        print(text["cancel"])
        return 0

    destination.mkdir(parents=True, exist_ok=True)

    existing = any(destination.iterdir())
    overwrite = False

    if existing:
        overwrite = yes(input(text["overwrite"]))

    try:
        print(text["loading"])
        files = get_repository_files()

        download_project(files, destination, overwrite, LANG)

        # Install dependencies before removing any previous virtual environment.
        install_dependencies(destination, LANG)

        # Launchers use system Python, not .venv.
        write_launchers(destination)

        # Remove a previous .venv only after successful installation steps.
        remove_virtual_environment(destination, LANG)

        print(f'\n{text["done"]}')
        print(f'{text["launcher"]}:')

        if IS_WINDOWS:
            print(destination / "start_windows.bat")
        else:
            print(f'sh "{destination / "start_linux.sh"}"')

        return 0

    except (
        OSError,
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f'\n{text["failed"]}: {error}', file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

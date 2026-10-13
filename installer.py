#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSCam Patch Manager – plattformübergreifender Installer
Windows und Linux, Python 3.9+

Ablauf:
1. Repository-Dateien von GitHub herunterladen.
2. Python 3 prüfen.
3. Abhängigkeiten systemweit prüfen/installieren versuchen.
4. Wenn die Systeminstallation vollständig ist, .venv entfernen.
5. Andernfalls .venv erstellen/behalten und dort Abhängigkeiten installieren.
6. Startskript für das gewählte Python erzeugen.

Hinweis:
Systemweite Paketinstallation wird ohne sudo/Administrator-Eskalation versucht.
Wenn sie durch Berechtigungen oder PEP 668 blockiert ist, wird .venv verwendet.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import json
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Projektkonfiguration
# ---------------------------------------------------------------------------

OWNER = "speedy005"
REPO = "oscam_patch_manager_new"
BRANCH = "master"

API_URL = (
    f"https://api.github.com/repos/{OWNER}/{REPO}"
    f"/git/trees/{urllib.parse.quote(BRANCH, safe='')}?recursive=1"
)
RAW_URL = (
    f"https://raw.githubusercontent.com/{OWNER}/{REPO}/"
    f"{urllib.parse.quote(BRANCH, safe='')}/"
)

MIN_PYTHON = (3, 9)
REQUEST_TIMEOUT = 30

SKIP_DIRS = {
    ".git", ".github", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".venv", "venv", "env", "node_modules",
}
SKIP_FILES = {
    "installer.py", "installer.sh", "installer.bat",
    "install.py", "install.sh", "install.bat",
    "version.txt",
}
SKIP_EXTENSIONS = {".zip", ".php"}


# ---------------------------------------------------------------------------
# Sprache und Ausgabe
# ---------------------------------------------------------------------------

LANG = "de"


TEXTS = {
    "de": {
        "title": "OSCam Patch Manager – Installer",
        "language": "Sprache wählen: [1] Deutsch  [2] English",
        "path": "Installationsordner eingeben (leer = aktueller Ordner): ",
        "exists": "Der Ordner enthält bereits Dateien. Vorhandene Dateien überschreiben? [j/N]: ",
        "download": "Lade Projektdateien herunter ...",
        "downloaded": "Heruntergeladen",
        "python_check": "Prüfe Python 3 ...",
        "python_missing": "Python 3.9 oder neuer wurde nicht gefunden. Bitte Python installieren und erneut starten.",
        "system_check": "Prüfe und installiere Abhängigkeiten systemweit ...",
        "system_ok": "System-Python und Abhängigkeiten sind verwendbar.",
        "venv_fallback": "Systeminstallation nicht möglich oder unvollständig. Verwende .venv.",
        "venv_create": "Erstelle bzw. prüfe .venv ...",
        "venv_ok": "Virtuelle Umgebung und Abhängigkeiten sind bereit.",
        "venv_removed": ".venv wurde entfernt, da die Systemumgebung ausreicht.",
        "launcher": "Starterskript erstellt.",
        "success": "Installation abgeschlossen.",
        "launch": "Starten mit",
        "failed": "FEHLER",
        "cancel": "Installation abgebrochen.",
        "main_missing": "Im GitHub-Repository wurde keine main.py gefunden.",
        "tree_error": "GitHub-Dateiliste konnte nicht geladen werden.",
        "download_error": "Download fehlgeschlagen",
        "pip_missing": "pip ist für den gefundenen Python-Interpreter nicht verfügbar.",
        "no_requirements": "Keine requirements.txt gefunden; es werden keine Pakete installiert.",
        "done": "Fertig.",
    },
    "en": {
        "title": "OSCam Patch Manager – Installer",
        "language": "Choose language: [1] Deutsch  [2] English",
        "path": "Installation folder (empty = current folder): ",
        "exists": "The folder already contains files. Overwrite existing files? [y/N]: ",
        "download": "Downloading project files ...",
        "downloaded": "Downloaded",
        "python_check": "Checking Python 3 ...",
        "python_missing": "Python 3.9 or newer was not found. Install Python and run again.",
        "system_check": "Checking and attempting to install system-wide dependencies ...",
        "system_ok": "System Python and dependencies are ready.",
        "venv_fallback": "System installation failed or is incomplete. Using .venv.",
        "venv_create": "Creating/checking .venv ...",
        "venv_ok": "Virtual environment and dependencies are ready.",
        "venv_removed": ".venv was removed because the system environment is sufficient.",
        "launcher": "Launcher created.",
        "success": "Installation complete.",
        "launch": "Launch with",
        "failed": "ERROR",
        "cancel": "Installation cancelled.",
        "main_missing": "main.py was not found in the GitHub repository.",
        "tree_error": "Could not load the GitHub file list.",
        "download_error": "Download failed",
        "pip_missing": "pip is not available for the detected Python interpreter.",
        "no_requirements": "No requirements.txt found; no packages will be installed.",
        "done": "Done.",
    },
}


def tr(key: str) -> str:
    return TEXTS[LANG].get(key, key)


def pause() -> None:
    try:
        input("\nPress Enter to exit..." if LANG == "en" else "\nZum Beenden Enter drücken...")
    except (EOFError, KeyboardInterrupt):
        pass


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return default
    if not answer:
        return default
    return answer in ({"y", "yes", "j", "ja"})


def run_command(
    command: list[str],
    cwd: Optional[Path] = None,
    *,
    quiet: bool = False,
    timeout: Optional[int] = None,
) -> bool:
    """Run a command safely. Return True when its exit code is zero."""
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        if result.stdout and not quiet:
            print(result.stdout.rstrip())
        elif result.stdout and not quiet:
            print(result.stdout.rstrip())
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError) as exc:
        if not quiet:
            print(f"{tr('failed')}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Python-Interpreter erkennen
# ---------------------------------------------------------------------------

def python_version_ok(command: list[str]) -> bool:
    code = (
        "import sys; "
        f"raise SystemExit(0 if sys.version_info >= {MIN_PYTHON!r} "
        "and sys.version_info.major == 3 else 1)"
    )
    return run_command(command + ["-c", code], quiet=True, timeout=10)


def find_system_python() -> Optional[list[str]]:
    """Return a command prefix that invokes Python 3.9+."""
    if os.name == "nt":
        candidates = [["py", "-3"], ["python3"], ["python"]]
    else:
        candidates = [["python3"], ["python"]]

    for candidate in candidates:
        if python_version_ok(candidate):
            return candidate
    return None


def interpreter_has_pip(python_cmd: list[str]) -> bool:
    return run_command(
        python_cmd + ["-m", "pip", "--version"],
        quiet=True,
        timeout=15,
    )


# ---------------------------------------------------------------------------
# GitHub-Dateien abrufen
# ---------------------------------------------------------------------------

def github_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "OSCam-Patch-Manager-Installer",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read()
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Unexpected GitHub API response")
    return data


def get_repository_files() -> list[str]:
    data = github_json(API_URL)
    if data.get("truncated"):
        raise RuntimeError("GitHub returned a truncated repository tree.")

    files: list[str] = []
    for item in data.get("tree", []):
        if item.get("type") != "blob":
            continue

        raw_path = item.get("path", "")
        if not raw_path:
            continue

        path = Path(raw_path)
        parts = set(path.parts)

        if parts.intersection(SKIP_DIRS):
            continue
        if path.name in SKIP_FILES:
            continue
        if path.suffix.lower() in SKIP_EXTENSIONS:
            continue

        # Exclude absolute paths and path traversal.
        if path.is_absolute() or ".." in path.parts:
            continue

        files.append(path.as_posix())

    if "main.py" not in files:
        raise RuntimeError(tr("main_missing"))

    return sorted(set(files))


def download_file(relative_path: str, root: Path, overwrite: bool) -> bool:
    """Download one file while preventing paths outside the installation root."""
    rel = Path(relative_path)
    destination = (root / rel).resolve()

    try:
        destination.relative_to(root.resolve())
    except ValueError:
        raise RuntimeError(f"Unsafe repository path: {relative_path}")

    if destination.exists() and not overwrite:
        print(f"  Skip: {relative_path}")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded_path = "/".join(
        urllib.parse.quote(part, safe="") for part in rel.parts
    )
    url = RAW_URL + encoded_path
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "OSCam-Patch-Manager-Installer"},
    )

    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                content = response.read()
            temporary = destination.with_name(destination.name + ".download")
            temporary.write_bytes(content)
            temporary.replace(destination)
            return True
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(1 + attempt)

    raise RuntimeError(f"{tr('download_error')}: {relative_path}: {last_error}")


def download_project(root: Path, overwrite: bool) -> None:
    print(tr("download"))
    files = get_repository_files()
    total = len(files)
    downloaded = 0

    for index, relative_path in enumerate(files, start=1):
        try:
            if download_file(relative_path, root, overwrite):
                downloaded += 1
            print(f"[{index}/{total}] {relative_path}")
        except Exception as exc:
            raise RuntimeError(str(exc)) from exc

    if not (root / "main.py").is_file():
        raise RuntimeError(tr("main_missing"))

    print(f"{tr('downloaded')}: {downloaded}/{total}")


# ---------------------------------------------------------------------------
# Abhängigkeiten installieren und Umgebung auswählen
# ---------------------------------------------------------------------------

def requirements_distribution_names(requirements: Path) -> Optional[list[str]]:
    """
    Extract ordinary distribution names from requirements.txt.
    Return None for editable/VCS/local-path requirements that need pip to resolve.
    """
    names: list[str] = []
    try:
        lines = requirements.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(("-r ", "--requirement ", "-e ", "--editable ", "--")):
            return None
        # Remove inline comments and environment markers.
        line = line.split(" #", 1)[0].strip()
        line = line.split(";", 1)[0].strip()
        if not line:
            continue
        # Direct URL/VCS/local file requirements cannot be reliably checked
        # with pip show using only the text before the URL.
        if "://" in line or line.startswith((".", "/", "\\\\")):
            return None
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", line)
        if not match:
            return None
        names.append(match.group(1))

    return names


def system_requirements_already_satisfied(
    python_cmd: list[str], requirements: Path, project_dir: Path
) -> bool:
    """Check installed distributions before attempting any system modification."""
    names = requirements_distribution_names(requirements)
    if names is None:
        return False

    for name in names:
        if not run_command(
            python_cmd + ["-m", "pip", "show", name],
            cwd=project_dir,
            quiet=True,
            timeout=20,
        ):
            return False

    # pip check catches broken dependency relationships. This check does not
    # enforce version specifiers in requirements.txt, so pip install is still
    # attempted when the simple installed-package check is inconclusive.
    return run_command(
        python_cmd + ["-m", "pip", "check"],
        cwd=project_dir,
        quiet=True,
        timeout=120,
    )


def pip_install_requirements(python_cmd: list[str], project_dir: Path) -> bool:
    requirements = project_dir / "requirements.txt"
    if not requirements.is_file():
        print(tr("no_requirements"))
        return True

    if not interpreter_has_pip(python_cmd):
        print(tr("pip_missing"))
        return False

    # If packages are already installed and consistent, avoid changing the
    # system environment. This also allows externally-managed Linux Python
    # installations to be used without invoking pip install.
    if system_requirements_already_satisfied(python_cmd, requirements, project_dir):
        return True

    # Try installing missing/outdated dependencies. On PEP 668 systems this
    # may be rejected; the caller then safely falls back to .venv.
    installed = run_command(
        python_cmd + ["-m", "pip", "install", "-r", str(requirements)],
        cwd=project_dir,
        timeout=900,
    )
    if not installed:
        return False

    return run_command(
        python_cmd + ["-m", "pip", "check"],
        cwd=project_dir,
        timeout=120,
    )


def get_venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def configure_python_environment(project_dir: Path, system_python: list[str]) -> list[str]:
    """
    Prefer system Python only if requirements install and pip check succeed.
    Remove .venv only after the system environment passes those checks.
    """
    venv_dir = project_dir / ".venv"
    print(tr("system_check"))

    if pip_install_requirements(system_python, project_dir):
        print(tr("system_ok"))
        if venv_dir.exists():
            try:
                shutil.rmtree(venv_dir)
                print(tr("venv_removed"))
            except OSError as exc:
                print(f"Warning: Could not remove {venv_dir}: {exc}")
                # System Python works, so do not use the stale venv.
        return system_python

    print(tr("venv_fallback"))
    print(tr("venv_create"))

    if not venv_dir.exists():
        created = run_command(
            system_python + ["-m", "venv", str(venv_dir)],
            cwd=project_dir,
            timeout=120,
        )
        if not created:
            raise RuntimeError(
                "Could not create .venv. On Linux, install the distribution's "
                "python3-venv package, then run the installer again."
            )

    venv_python = get_venv_python(venv_dir)
    if not venv_python.is_file():
        raise RuntimeError(
            f"The Python executable is missing from {venv_dir}. "
            "Remove this incomplete .venv directory and rerun the installer."
        )

    venv_command = [str(venv_python)]
    if not pip_install_requirements(venv_command, project_dir):
        raise RuntimeError(
            "Dependency installation failed in .venv as well. "
            "Check your internet connection and requirements.txt."
        )

    print(tr("venv_ok"))
    return venv_command


# ---------------------------------------------------------------------------
# Startskripte schreiben
# ---------------------------------------------------------------------------

def write_launchers(project_dir: Path, python_command: list[str]) -> None:
    # Launchers use the environment selected by the installer.
    if python_command and Path(python_command[0]).name.lower() in {
        "python.exe", "python", "python3"
    }:
        # A direct path to .venv/python is used for venv installations.
        python_executable = python_command[0]
    else:
        # Commands such as ["py", "-3"] are resolved by the shell.
        python_executable = None

    venv_python = get_venv_python(project_dir / ".venv")
    if venv_python.exists() and python_executable and Path(python_executable).resolve() == venv_python.resolve():
        use_venv = True
    else:
        use_venv = False

    if os.name == "nt":
        launcher = project_dir / "start_windows.bat"
        if use_venv:
            python_line = '".venv\\Scripts\\python.exe" main.py %*'
        elif python_command == ["py", "-3"]:
            python_line = "py -3 main.py %*"
        elif python_command == ["python3"]:
            python_line = "python3 main.py %*"
        else:
            python_line = "python main.py %*"

        content = (
            "@echo off\r\n"
            "cd /d \"%~dp0\"\r\n"
            f"{python_line}\r\n"
            "if errorlevel 1 pause\r\n"
        )
        launcher.write_text(content, encoding="utf-8")
        print(f"{tr('launcher')} {launcher.name}")
    else:
        launcher = project_dir / "start_linux.sh"
        if use_venv:
            python_line = 'exec "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/main.py" "$@"'
        else:
            # Use the detected command, shell-quoted conservatively.
            if python_command == ["py", "-3"]:
                executable = "py -3"
            elif python_command == ["python3"]:
                executable = "python3"
            else:
                executable = "python"
            python_line = f'exec {executable} "$SCRIPT_DIR/main.py" "$@"'

        content = (
            "#!/bin/sh\n"
            'SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\n'
            'cd "$SCRIPT_DIR" || exit 1\n'
            f"{python_line}\n"
        )
        launcher.write_text(content, encoding="utf-8")
        try:
            launcher.chmod(0o755)
        except OSError:
            pass
        print(f"{tr('launcher')} {launcher.name}")


def verify_selected_python(python_command: list[str], project_dir: Path) -> None:
    """Basic final checks: selected interpreter runs and imports main."""
    if not run_command(
        python_command + ["-c", "import sys; print(sys.version)"],
        cwd=project_dir,
        timeout=15,
    ):
        raise RuntimeError("The selected Python interpreter could not be started.")

    # Compile check catches syntax errors without starting the GUI.
    if not run_command(
        python_command + ["-m", "py_compile", "main.py"],
        cwd=project_dir,
        timeout=30,
    ):
        raise RuntimeError(
            "main.py did not pass the Python syntax check. "
            "The files were downloaded, but the application may not start."
        )


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def choose_language() -> None:
    global LANG
    print(TEXTS["de"]["language"])
    try:
        answer = input("> ").strip()
    except (EOFError, KeyboardInterrupt):
        answer = "1"
    LANG = "en" if answer == "2" else "de"


def main() -> int:
    choose_language()
    print("=" * 60)
    print(tr("title"))
    print("=" * 60)

    if sys.version_info < MIN_PYTHON or sys.version_info.major != 3:
        print(
            "Der Installer benötigt selbst Python 3.9 oder neuer."
            if LANG == "de"
            else "The installer itself requires Python 3.9 or newer."
        )
        return 1

    system_python = find_system_python()
    if system_python is None:
        print(tr("python_missing"))
        return 1

    print(tr("python_check"))
    run_command(system_python + ["--version"], quiet=False, timeout=10)

    try:
        entered_path = input(tr("path")).strip()
    except (EOFError, KeyboardInterrupt):
        print(tr("cancel"))
        return 1

    root = Path(entered_path).expanduser() if entered_path else Path.cwd()
    root = root.resolve()

    if root.exists() and not root.is_dir():
        print(f"{tr('failed')}: Installation path is not a directory: {root}")
        return 1

    root.mkdir(parents=True, exist_ok=True)

    has_existing_files = any(root.iterdir())
    overwrite = True
    if has_existing_files:
        overwrite = ask_yes_no(tr("exists"), default=False)

    try:
        download_project(root, overwrite)
        python_command = configure_python_environment(root, system_python)
        verify_selected_python(python_command, root)
        write_launchers(root, python_command)

        print("\n" + "=" * 60)
        print(tr("success"))
        print(f"{tr('launch')}:")
        if os.name == "nt":
            print(f'  "{root / "start_windows.bat"}"')
        else:
            print(f'  "{root / "start_linux.sh"}"')
        print(f"Installationsordner: {root}" if LANG == "de" else f"Install folder: {root}")
        print(tr("done"))
        return 0

    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
            OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"\n{tr('failed')}: {exc}")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
    except KeyboardInterrupt:
        print("\n" + tr("cancel"))
        exit_code = 130
    if exit_code != 0:
        pause()
    raise SystemExit(exit_code)

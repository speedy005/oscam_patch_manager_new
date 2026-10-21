# -*- coding: utf-8 -*-
"""
Cross-platform Simplebuild launcher.

Windows:
- Prüft WSL2 und Ubuntu.
- Fordert die Installation bei Bedarf an.
- Belässt die Quell-Repositories an ihren Windows-Pfaden.
- Klont oder aktualisiert die ausgewählten Repositories.
- Startet Simplebuild in einem separaten WSL2-Konsolenfenster.
- Startet das ausgewählte Skript mit ./s3 menu oder ./s4 menu.
- Verwendet kein MSYS2.

Linux:
- Startet Simplebuild in einem nativen Terminal.
"""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional


REPOSITORIES = {
    "s3": "https://github.com/gorgone/s3_releases.git",
    "s4": "https://git.streamboard.tv/common/simplebuild4.git",
    "ncam": "https://github.com/speedy005/s3_ncam_bonecrew_test.git",
}

WSL_DISTRO = "Ubuntu"


def _log_func(log: Optional[Callable[[str], None]] = None):
    return log or print


def _run(
    command,
    *,
    log,
    check=True,
    cwd=None,
    capture=True,
    env=None,
):
    command = [str(item) for item in command]

    log("Starte: " + subprocess.list2cmdline(command))

    result = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        errors="replace",
        check=False,
    )

    if capture and result.stdout:
        log(result.stdout.rstrip())

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Befehl fehlgeschlagen (Exit-Code {result.returncode}): "
            f"{subprocess.list2cmdline(command)}"
        )

    return result


def _find_wsl() -> str:
    """Findet wsl.exe auf Windows."""

    if platform.system() != "Windows":
        raise RuntimeError("WSL wird nur unter Windows benötigt.")

    candidates = [
        shutil.which("wsl.exe"),
        str(
            Path(os.environ.get("WINDIR", r"C:\Windows"))
            / "System32"
            / "wsl.exe"
        ),
    ]

    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate

    raise RuntimeError(
        "wsl.exe wurde nicht gefunden. Installiere WSL über PowerShell "
        "mit 'wsl --install -d Ubuntu'."
    )


def _wsl(arguments, *, log, check=True, capture=True):
    """Führt einen Befehl in WSL aus."""

    return _run(
        [_find_wsl(), *arguments],
        log=log,
        check=check,
        capture=capture,
    )


def _clean_wsl_output(value):
    """Entfernt typische WSL-Ausgabe-Artefakte."""

    return (
        (value or "")
        .replace("\x00", "")
        .replace("\ufeff", "")
        .strip()
    )


def ensure_wsl(log: Optional[Callable[[str], None]] = None) -> None:
    """Prüft, ob Ubuntu installiert und über WSL2 erreichbar ist."""

    if platform.system() != "Windows":
        return

    log = _log_func(log)
    wsl_exe = _find_wsl()

    status = _run(
        [wsl_exe, "--status"],
        log=log,
        check=False,
    )

    if status.returncode != 0:
        _run(
            [wsl_exe, "--install", "-d", WSL_DISTRO],
            log=log,
            check=False,
        )
        raise RuntimeError(
            "Die WSL-Installation wurde angefordert. Schließe die "
            "Installation ab und öffne Ubuntu zur Einrichtung."
        )

    distros_result = _wsl(
        ["--list", "--quiet"],
        log=log,
        check=False,
    )

    distros = [
        line.strip()
        for line in _clean_wsl_output(
            distros_result.stdout
        ).splitlines()
        if line.strip()
    ]

    if not any(
        item.lower() == WSL_DISTRO.lower()
        for item in distros
    ):
        _run(
            [wsl_exe, "--install", "-d", WSL_DISTRO],
            log=log,
            check=False,
        )
        raise RuntimeError(
            "Ubuntu wurde zur Installation angefordert. Öffne Ubuntu "
            "nach der Installation und richte den Linux-Benutzer ein."
        )

    versions = _wsl(
        ["--list", "--verbose"],
        log=log,
        check=False,
    )

    version_text = _clean_wsl_output(versions.stdout)

    ubuntu_line = next(
        (
            line
            for line in version_text.splitlines()
            if WSL_DISTRO.lower() in line.lower()
        ),
        "",
    )

    if not ubuntu_line:
        raise RuntimeError(
            "Die Ubuntu-Version konnte nicht ermittelt werden. "
            "Prüfe 'wsl --list --verbose'."
        )

    if not ubuntu_line.rstrip().endswith("2"):
        log("Ubuntu wird auf WSL2 umgestellt.")
        _wsl(
            ["--set-version", WSL_DISTRO, "2"],
            log=log,
        )

    ready = _wsl(
        [
            "-d",
            WSL_DISTRO,
            "--",
            "bash",
            "-lc",
            "printf WSL_READY",
        ],
        log=log,
        check=False,
    )

    if (
        ready.returncode != 0
        or "WSL_READY" not in _clean_wsl_output(ready.stdout)
    ):
        raise RuntimeError(
            "Ubuntu ist noch nicht vollständig eingerichtet. Öffne "
            "Ubuntu über das Startmenü und schließe die Einrichtung ab."
        )

    log("WSL2 und Ubuntu sind verfügbar.")


def _script_candidates(tool: str):
    """Erwartete Startskriptnamen je Repository."""

    if tool == "s4":
        return ("s4",)

    # s3 und ncam verwenden ./s3 menu.
    return ("s3",)


def _find_script(root: Path, tool: str):
    """Sucht das erwartete Skript im Repository und Unterordnern."""

    folders = (
        "",
        "simplebuild4",
        "s3_ncam_bonecrew",
        "s3",
    )

    for folder in folders:
        base = root / folder if folder else root

        for name in _script_candidates(tool):
            candidate = base / name

            if candidate.is_file():
                return candidate

    return None


def ensure_repository(tool: str, destination, log=None) -> Path:
    """Klonen oder aktualisieren, ohne lokale Änderungen zu verwerfen."""

    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(
            f"Unbekanntes Tool {tool!r}; "
            f"erlaubt: {', '.join(REPOSITORIES)}"
        )

    dest = Path(destination).expanduser().resolve()
    git = shutil.which("git") or shutil.which("git.exe")

    if not git:
        raise RuntimeError(
            "Git wurde nicht gefunden. Installiere Git oder ergänze "
            "Git im PATH."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)

    if (dest / ".git").is_dir():
        _run(
            [
                git,
                "-C",
                str(dest),
                "remote",
                "set-url",
                "origin",
                REPOSITORIES[tool],
            ],
            log=log,
        )

        _run(
            [
                git,
                "-C",
                str(dest),
                "fetch",
                "--all",
                "--prune",
            ],
            log=log,
        )

        log(
            "Repository vorhanden; Fetch abgeschlossen. "
            "Lokale Änderungen bleiben erhalten."
        )
        return dest

    if dest.exists() and any(dest.iterdir()):
        if _find_script(dest, tool) is not None:
            log(
                "Verwende vorhandenes Quellverzeichnis ohne "
                f"Git-Metadaten: {dest}"
            )
            return dest

        raise RuntimeError(
            f"Zielverzeichnis ist nicht leer und kein Git-Repository: "
            f"{dest}. Sichere den Inhalt oder wähle einen leeren Ordner."
        )

    _run(
        [git, "clone", REPOSITORIES[tool], str(dest)],
        log=log,
    )

    log("Repository geklont; keine Patches angewendet.")
    return dest


def prepare_tool(tool: str, destination, log=None) -> Path:
    """Bereitet das Repository vor und prüft WSL unter Windows."""

    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(f"Unbekanntes Tool: {tool}")

    if platform.system() == "Windows":
        ensure_wsl(log=log)

    path = ensure_repository(tool, destination, log=log)
    log(f"{tool} ist bereit: {path}")

    return path


def _wsl_path(path: Path, log) -> str:
    """Konvertiert einen Windows-Pfad in einen absoluten WSL-Pfad."""

    windows_path = str(path.resolve()).replace("\\", "/")

    result = _wsl(
        [
            "-d",
            WSL_DISTRO,
            "--",
            "wslpath",
            "-a",
            windows_path,
        ],
        log=log,
    )

    converted = _clean_wsl_output(result.stdout)

    if not converted or not converted.startswith("/"):
        raise RuntimeError(
            "Windows-Pfad konnte nicht nach WSL konvertiert werden: "
            f"{path}. Ausgabe: {converted!r}"
        )

    return converted


def bash_quote(value):
    """Quotiert einen Wert sicher für Bash."""

    return shlex.quote(str(value))


def _launch_native_linux(tool: str, source: Path, log) -> None:
    """Startet das Menü in einem nativen Linux-Terminal."""

    script = _find_script(source, tool)

    if script is None:
        raise FileNotFoundError(
            f"Kein Startskript für {tool} in {source} gefunden."
        )

    command = (
        f"cd {shlex.quote(str(script.parent))} && "
        f"exec ./{shlex.quote(script.name)} menu"
    )

    terminals = [
        (
            "gnome-terminal",
            ["gnome-terminal", "--", "bash", "-lc", command],
        ),
        (
            "konsole",
            ["konsole", "-e", "bash", "-lc", command],
        ),
        (
            "xfce4-terminal",
            [
                "xfce4-terminal",
                "--command",
                f"bash -lc {shlex.quote(command)}",
            ],
        ),
        (
            "xterm",
            ["xterm", "-e", "bash", "-lc", command],
        ),
    ]

    for executable, arguments in terminals:
        if shutil.which(executable):
            subprocess.Popen(arguments, start_new_session=True)
            log(f"Starte {tool} unter Linux: ./{script.name} menu")
            return

    raise RuntimeError(
        "Kein unterstützter Terminal-Emulator gefunden. Installiere "
        "beispielsweise xterm, gnome-terminal oder konsole."
    )


def launch_tool_menu(tool: str, source: Path, log=None) -> None:
    """Startet ./s3 menu oder ./s4 menu in einem separaten Terminal."""

    log = _log_func(log)
    tool = str(tool).lower().strip()
    source = Path(source).expanduser().resolve()

    if tool not in REPOSITORIES:
        raise ValueError(f"Unbekanntes Tool: {tool}")

    script = _find_script(source, tool)

    if script is None:
        expected = "./s4" if tool == "s4" else "./s3"
        raise FileNotFoundError(
            f"Startskript {expected} wurde für {tool} "
            f"im Repository {source} nicht gefunden."
        )

    if platform.system() != "Windows":
        _launch_native_linux(tool, source, log)
        return

    ensure_wsl(log=log)

    
    wsl_source = _wsl_path(source, log)

    # Das Repository-Verzeichnis ist die Arbeitsbasis.
    # Die Startdatei heißt s3 beziehungsweise s4.
    script_name = "s4" if tool == "s4" else "s3"

    linux_command = (
        f"cd {bash_quote(wsl_source)} || exec bash; "
        f"if [ ! -f {bash_quote('./' + script_name)} ]; then "
        f"echo {bash_quote('Startdatei nicht gefunden: ' + script_name)}; "
        "pwd; ls -la; exec bash; "
        "fi; "
        f"chmod +x {bash_quote('./' + script_name)}; "
        f"./{script_name} menu; "
        "result=$?; "
        "echo; "
        'echo "Simplebuild wurde beendet (Exit-Code: $result)."; '
        "exec bash"
    )

    command = [
        _find_wsl(),
        "-d",
        WSL_DISTRO,
        "--",
        "bash",
        "-lc",
        linux_command,
    ]

    log(f"WSL-Quellpfad: {wsl_source!r}")
    log(f"WSL-Tool: {tool!r}")
    log(f"Startbefehl: ./{script_name} menu")
    log("Starte Simplebuild in einem neuen WSL2-Konsolenfenster.")

    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    process = subprocess.Popen(
        command,
        creationflags=creationflags,
    )

    log(f"WSL-Prozess gestartet, PID={process.pid}")



def launch_simplebuild(tool_path, menu_arg="menu", log=None) -> None:
    """Kompatibler Einstiegspunkt für ältere Aufrufer."""

    path = Path(tool_path).expanduser().resolve()

    if menu_arg != "menu":
        raise ValueError("Der unterstützte Menüparameter ist 'menu'.")

    source = path if path.is_dir() else path.parent
    lower = str(source).lower()

    if "simplebuild4" in lower or "s4" in lower:
        tool = "s4"
    elif "ncam" in lower or "bonecrew" in lower:
        tool = "ncam"
    else:
        tool = "s3"

    launch_tool_menu(tool, source, log=log)


if __name__ == "__main__":
    print(
        "Dieses Modul wird von der Oberfläche importiert. "
        "Rufe prepare_tool() und launch_tool_menu() aus der GUI auf."
    )

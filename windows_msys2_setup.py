
# -*- coding: utf-8 -*-
"""
Cross-platform Simplebuild launcher.

Windows:
- Prüft WSL2 und Ubuntu.
- Klont nur, wenn das Zielverzeichnis noch nicht existiert.
- Verwendet vorhandene Repository-Kopien weiter.
- Aktualisiert Git-Referenzen, ohne lokale Änderungen zu überschreiben.
- Bei einem fehlgeschlagenen Fetch kann ein vorhandenes Repository
  weiterhin lokal gestartet werden.
- Startet Simplebuild in einem separaten WSL-Konsolenfenster.

Linux:
- Startet Simplebuild in einem nativen Terminal.

Startbefehle:
- S3:   ./s3 menu
- S4:   ./s4
- NCam: ./s3 menu
"""

from __future__ import annotations

import os
import platform
import shlex
import shutil
import subprocess
import base64
from pathlib import Path
from typing import Callable, Optional


REPOSITORIES = {
    "s3": "https://github.com/gorgone/s3_releases.git",
    "s4": "https://git.streamboard.tv/common/simplebuild4.git",
    "ncam": "https://github.com/speedy005/s3_ncam_bonecrew_test.git",
}

WSL_DISTRO = "Ubuntu"


def _log_func(log=None):
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
    """Führt einen Prozess aus und zeigt seine Ausgabe an."""

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

    output = (result.stdout or "").strip() if capture else ""

    if output:
        log(output)

    if check and result.returncode != 0:
        raise RuntimeError(
            f"Befehl fehlgeschlagen (Exit-Code {result.returncode}):\n"
            f"{subprocess.list2cmdline(command)}\n"
            f"Ausgabe:\n{output or '(keine Ausgabe)'}"
        )

    return result


def _find_wsl() -> str:
    """Findet wsl.exe unter Windows."""

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
        "wsl.exe wurde nicht gefunden. Installiere WSL mit:\n"
        "wsl --install -d Ubuntu"
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
    return (
        (value or "")
        .replace("\x00", "")
        .replace("\ufeff", "")
        .strip()
    )


def ensure_wsl(log=None) -> None:
    """Prüft Ubuntu und stellt sicher, dass die Distribution WSL2 nutzt."""

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
            "Die WSL-Installation wurde angefordert. "
            "Schließe die Installation ab und öffne Ubuntu."
        )

    result = _wsl(
        ["--list", "--quiet"],
        log=log,
        check=False,
    )

    distros = [
        line.strip()
        for line in _clean_wsl_output(result.stdout).splitlines()
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
            "Ubuntu wurde zur Installation angefordert. "
            "Öffne Ubuntu nach der Installation und richte "
            "deinen Linux-Benutzer ein."
        )

    result = _wsl(
        ["--list", "--verbose"],
        log=log,
        check=False,
    )

    ubuntu_line = next(
        (
            line
            for line in _clean_wsl_output(result.stdout).splitlines()
            if WSL_DISTRO.lower() in line.lower()
        ),
        "",
    )

    if not ubuntu_line:
        raise RuntimeError(
            "Ubuntu konnte nicht erkannt werden. Prüfe "
            "'wsl --list --verbose' in PowerShell."
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
            "Ubuntu ist noch nicht vollständig eingerichtet. "
            "Öffne Ubuntu über das Startmenü und schließe "
            "die Einrichtung ab."
        )

    log("WSL2 und Ubuntu sind verfügbar.")


def _script_candidates(tool: str):
    """Erwartete Startskripte."""

    if tool == "s4":
        return ("s4",)

    return ("s3",)


def _find_script(root: Path, tool: str):
    """Sucht das Startskript im Repository und bekannten Unterordnern."""

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
    """
    Verwendet vorhandene Quellen oder klont ein neues Repository.

    Bestehende Git-Repositories werden nur gefetcht.
    Es werden keine lokalen Änderungen zurückgesetzt.
    """

    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(
            f"Unbekanntes Tool {tool!r}. Erlaubt: "
            f"{', '.join(REPOSITORIES)}"
        )

    dest = Path(destination).expanduser().resolve()

    git = shutil.which("git") or shutil.which("git.exe")

    if not git:
        raise RuntimeError(
            "Git wurde nicht gefunden. Installiere Git "
            "oder ergänze Git im PATH."
        )

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Vorhandenes Git-Repository: nicht erneut klonen.
    if (dest / ".git").exists():
        log(f"Vorhandenes Git-Repository: {dest}")

        # Die Repository-Adresse bei Bedarf korrigieren.
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

        # Nur origin abrufen.
        # Bei einem Serverfehler darf eine vorhandene lokale
        # Kopie weiterhin gestartet werden.
        try:
            _run(
                [
                    git,
                    "-C",
                    str(dest),
                    "fetch",
                    "origin",
                    "--prune",
                ],
                log=log,
            )

            log("Git-Fetch erfolgreich.")

        except RuntimeError as exc:
            log(
                "WARNUNG: Git-Fetch fehlgeschlagen. "
                "Die vorhandenen lokalen Dateien bleiben erhalten."
            )
            log(str(exc))
            log(
                "Es wird mit dem lokalen Repository weitergearbeitet. "
                "Es wurden keine neuen Commits übernommen."
            )

        return dest

    # Vorhandenes Verzeichnis ohne Git-Metadaten.
    if dest.exists() and any(dest.iterdir()):
        if _find_script(dest, tool) is not None:
            log(
                "Verwende vorhandenes Quellverzeichnis ohne "
                f"Git-Metadaten: {dest}"
            )
            return dest

        raise RuntimeError(
            "Das Zielverzeichnis ist nicht leer und kein "
            f"Git-Repository:\n{dest}\n"
            "Bitte sichere den Inhalt oder wähle einen anderen Ordner."
        )

    # Nur bei fehlendem oder leerem Zielverzeichnis klonen.
    log(f"Klone {tool} nach {dest}")

    _run(
        [
            git,
            "clone",
            REPOSITORIES[tool],
            str(dest),
        ],
        log=log,
    )

    log(f"{tool} wurde erfolgreich geklont.")

    return dest


def prepare_tool(tool: str, destination, log=None) -> Path:
    """Prüft WSL und bereitet ausschließlich das ausgewählte Tool vor."""

    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(f"Unbekanntes Tool: {tool}")

    if platform.system() == "Windows":
        ensure_wsl(log=log)

    path = ensure_repository(
        tool,
        destination,
        log=log,
    )

    log(f"{tool} ist bereit: {path}")

    return path




def _wsl_path(path: Path, log) -> str:
    """Konvertiert einen Windows-Pfad zuverlässig in einen WSL-Pfad."""

    windows_path = str(path.expanduser().resolve())
    wsl_exe = _find_wsl()

    # Windows-Pfad sicher als Base64 übertragen, damit Backslashes
    # und Sonderzeichen nicht durch die Argumentübergabe verloren gehen.
    import base64
    encoded_path = base64.b64encode(
        windows_path.encode("utf-8")
    ).decode("ascii")

    result = _run(
        [
            wsl_exe,
            "-d",
            WSL_DISTRO,
            "--exec",
            "bash",
            "-lc",
            'printf %s "$1" | base64 -d | '
            'xargs -0 -r -I {} wslpath -a "{}"',
            "wslpath",
            encoded_path,
        ],
        log=log,
        check=False,
        capture=True,
    )

    converted = _clean_wsl_output(result.stdout)

    if result.returncode != 0 or not converted.startswith("/"):
        raise RuntimeError(
            "Windows-Pfad konnte nicht nach WSL konvertiert werden.\n"
            f"Windows-Pfad: {windows_path}\n"
            f"Exit-Code: {result.returncode}\n"
            f"Ausgabe: {converted!r}"
        )

    return converted




def bash_quote(value):
    """Sicheres Quoting für Bash."""

    return shlex.quote(str(value))


def _start_command(tool: str) -> str:
    """Liefert den korrekten Startbefehl für das ausgewählte Tool."""

    if tool == "s4":
        return "./s4"

    return "./s3 menu"


def _launch_native_linux(tool: str, source: Path, log) -> None:
    """Startet Simplebuild in einem nativen Linux-Terminal."""

    script = _find_script(source, tool)

    if script is None:
        raise FileNotFoundError(
            f"Kein Startskript für {tool} in {source} gefunden."
        )

    start_command = _start_command(tool)

    command = (
        f"cd {bash_quote(str(script.parent))} && "
        f"chmod +x {bash_quote(script.name)} && "
        f"{start_command}; "
        "result=$?; "
        'echo "Simplebuild beendet (Exit-Code: $result)."; '
        "exec bash"
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
                f"bash -lc {bash_quote(command)}",
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
            log(f"Starte {tool} unter Linux: {start_command}")
            return

    raise RuntimeError(
        "Kein unterstützter Terminal-Emulator gefunden. "
        "Installiere beispielsweise xterm, gnome-terminal oder konsole."
    )


def launch_tool_menu(tool: str, source: Path, log=None) -> None:
    """Startet das ausgewählte Tool in einem separaten Terminal."""

    log = _log_func(log)
    tool = str(tool).lower().strip()
    source = Path(source).expanduser().resolve()

    if tool not in REPOSITORIES:
        raise ValueError(f"Unbekanntes Tool: {tool}")

    script = _find_script(source, tool)

    if script is None:
        raise FileNotFoundError(
            f"Startskript für {tool} wurde in {source} nicht gefunden."
        )

    start_command = _start_command(tool)

    if platform.system() != "Windows":
        _launch_native_linux(tool, source, log)
        return

    ensure_wsl(log=log)

    # Wichtig: Das Startskript kann in einem Unterordner liegen.
    wsl_script_dir = _wsl_path(script.parent, log)
    script_name = script.name

    linux_command = (
        f"cd {bash_quote(wsl_script_dir)} || exec bash; "
        f"if [ ! -f {bash_quote('./' + script_name)} ]; then "
        f"echo {bash_quote('Startdatei nicht gefunden: ' + script_name)}; "
        "pwd; ls -la; exec bash; "
        "fi; "
        f"chmod +x {bash_quote(script_name)}; "
        f"{start_command}; "
        "result=$?; "
        "echo; "
        'echo "Simplebuild beendet (Exit-Code: $result)."; '
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

    log(f"WSL-Quellpfad: {wsl_script_dir}")
    log(f"WSL-Tool: {tool}")
    log(f"Startbefehl: {start_command}")
    log("Starte Simplebuild in einem neuen WSL-Konsolenfenster.")

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
        raise ValueError(
            "Der unterstützte Menüparameter ist 'menu'."
        )

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
        "Dieses Modul wird von der Oberfläche importiert.\n"
        "Rufe prepare_tool() und launch_tool_menu() aus der GUI auf."
    )

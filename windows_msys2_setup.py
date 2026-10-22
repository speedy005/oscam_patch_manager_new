# -*- coding: utf-8 -*-
"""
Cross-platform Simplebuild launcher.

Windows:
- Prüft WSL2 und Ubuntu.
- Klont nur, wenn das Zielverzeichnis fehlt oder leer ist.
- Verwendet vorhandene Repository-Kopien weiter.
- Aktualisiert Git-Referenzen, ohne lokale Änderungen zu überschreiben.
- Bei fehlgeschlagenem Fetch kann ein vorhandenes Repository lokal
  weiterverwendet werden.
- Startet Simplebuild in einem separaten WSL-Konsolenfenster.

Linux:
- Verwendet die vorhandenen Quellen und startet Simplebuild in einem
  nativen Terminal.

Startbefehle:
- S3:   ./s3 menu
- S4:   ./s4
- NCam: ./s3 menu

Hinweis:
Dieses Modul installiert keine zusätzlichen Ubuntu-Buildpakete.
"""

from __future__ import annotations

import base64
import os
import platform
import shlex
import shutil
import subprocess
from pathlib import Path


REPOSITORIES = {
    "s3": "https://github.com/gorgone/s3_releases.git",
    "s4": "https://git.streamboard.tv/common/simplebuild4.git",
    "ncam": "https://github.com/speedy005/s3_ncam_bonecrew_test.git",
}

WSL_DISTRO = "Ubuntu"


def _log_func(log=None):
    """Gibt eine Log-Funktion zurück."""
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
    """Führt einen Prozess aus und protokolliert seine Ausgabe."""
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
    """Führt einen Befehl über wsl.exe aus."""
    return _run(
        [_find_wsl(), *arguments],
        log=log,
        check=check,
        capture=capture,
    )


def _clean_wsl_output(value) -> str:
    """Entfernt typische Steuerzeichen aus der WSL-Ausgabe."""
    return (
        (value or "")
        .replace("\x00", "")
        .replace("\ufeff", "")
        .replace("\r", "")
        .strip()
    )


def _ask_install_wsl(log, reason: str) -> bool:
    """
    Fragt unter Windows nach, ob WSL/Ubuntu installiert werden soll.
    Verwendet einen GUI-Dialog; bei nicht verfügbarer GUI erfolgt
    eine Rückfrage in der Konsole.
    """
    question = (
        f"{reason}\n\n"
        "Soll jetzt die Installation von WSL2 und Ubuntu angefordert werden?\n\n"
        "Hinweis: Windows kann Administratorrechte oder einen Neustart "
        "verlangen. Die Ubuntu-Ersteinrichtung muss gegebenenfalls danach "
        "manuell abgeschlossen werden."
    )

    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        try:
            answer = messagebox.askyesno(
                "WSL2 und Ubuntu installieren?",
                question,
                parent=root,
                icon="question",
            )
        finally:
            root.destroy()

        return bool(answer)

    except Exception as exc:
        log(
            "GUI-Abfrage für WSL konnte nicht geöffnet werden; "
            f"wechsle zur Konsolenabfrage. Details: {exc}"
        )
        print(question)
        try:
            answer = input("Jetzt installieren? [j/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer in {"j", "ja", "y", "yes"}


def ensure_wsl(log=None) -> None:
    """Prüft Ubuntu/WSL2 und fragt vor einer erforderlichen Installation nach."""
    if platform.system() != "Windows":
        return

    log = _log_func(log)
    wsl_exe = _find_wsl()

    status = _run(
        [wsl_exe, "--status"],
        log=log,
        check=False,
    )

    # Ein fehlgeschlagener Status kann bedeuten, dass WSL noch nicht
    # eingerichtet ist. Vor der Installationsanforderung immer nachfragen.
    if status.returncode != 0:
        reason = (
            "WSL ist noch nicht eingerichtet oder konnte nicht gestartet "
            "werden."
        )
        if not _ask_install_wsl(log, reason):
            raise RuntimeError(
                "Installation abgebrochen. WSL2 und Ubuntu wurden "
                "nicht durch dieses Programm installiert."
            )

        install = _run(
            [wsl_exe, "--install", "-d", WSL_DISTRO],
            log=log,
            check=False,
        )
        if install.returncode != 0:
            raise RuntimeError(
                "Die Installation von WSL2/Ubuntu konnte nicht erfolgreich "
                "angefordert werden. Führe PowerShell gegebenenfalls als "
                "Administrator aus und starte 'wsl --install -d Ubuntu'."
            )
        raise RuntimeError(
            "Die Installation von WSL2 und Ubuntu wurde angefordert. "
            "Schließe die Windows-/Ubuntu-Einrichtung ab und starte das "
            "Tool anschließend erneut. Ein Neustart kann erforderlich sein."
        )

    result = _wsl(
        ["--list", "--quiet"],
        log=log,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Die installierten WSL-Distributionen konnten nicht abgerufen "
            "werden. Prüfe 'wsl --list --verbose' in PowerShell."
        )

    distros = [
        line.strip().lstrip("*").strip()
        for line in _clean_wsl_output(result.stdout).splitlines()
        if line.strip()
    ]

    if not any(item.lower() == WSL_DISTRO.lower() for item in distros):
        reason = (
            "WSL ist vorhanden, aber die Ubuntu-Distribution wurde nicht "
            "gefunden."
        )
        if not _ask_install_wsl(log, reason):
            raise RuntimeError(
                "Installation abgebrochen. Ubuntu wurde nicht installiert."
            )

        install = _run(
            [wsl_exe, "--install", "-d", WSL_DISTRO],
            log=log,
            check=False,
        )
        if install.returncode != 0:
            raise RuntimeError(
                "Ubuntu konnte nicht zur Installation angefordert werden. "
                "Führe PowerShell gegebenenfalls als Administrator aus und "
                "starte 'wsl --install -d Ubuntu'."
            )
        raise RuntimeError(
            "Ubuntu wurde zur Installation angefordert. Öffne Ubuntu nach "
            "der Installation, richte deinen Linux-Benutzer ein und starte "
            "das Tool anschließend erneut. Ein Neustart kann erforderlich "
            "sein."
        )

    result = _wsl(
        ["--list", "--verbose"],
        log=log,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Der WSL-Status von Ubuntu konnte nicht ermittelt werden. "
            "Prüfe 'wsl --list --verbose' in PowerShell."
        )

    ubuntu_line = next(
        (
            line.strip()
            for line in _clean_wsl_output(result.stdout).splitlines()
            if line.strip().lstrip("*").strip().split()
            and line.strip().lstrip("*").strip().split()[0].lower()
            == WSL_DISTRO.lower()
        ),
        "",
    )

    if not ubuntu_line:
        raise RuntimeError(
            "Ubuntu konnte in der WSL-Liste nicht erkannt werden. "
            "Prüfe 'wsl --list --verbose' in PowerShell."
        )

    # Die letzte Spalte der Ausgabe von `wsl --list --verbose` ist die Version.
    columns = ubuntu_line.lstrip("*").split()
    wsl_version = columns[-1] if columns else ""

    if wsl_version != "2":
        log("Ubuntu wird auf WSL2 umgestellt.")
        _wsl(
            ["--set-version", WSL_DISTRO, "2"],
            log=log,
        )

    ready = _wsl(
        [
            "-d",
            WSL_DISTRO,
            "--exec",
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
            "Öffne Ubuntu über das Startmenü, schließe die Einrichtung ab "
            "und starte das Tool erneut."
        )

    log("WSL2 und Ubuntu sind verfügbar.")


def _script_candidates(tool: str):
    """Liefert die erwarteten Namen der Startskripte."""
    if tool == "s4":
        return ("s4",)
    return ("s3",)


def _find_script(root: Path, tool: str):
    """Sucht das Startskript im Repository und bekannten Unterordnern."""
    folders = ("", "simplebuild4", "s3_ncam_bonecrew", "s3")

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

    Bestehende Git-Repositories werden geprüft und nur gefetcht.
    Lokale Änderungen werden nicht zurückgesetzt oder automatisch gemergt.
    Ein fehlgeschlagener Fetch verhindert die Nutzung vorhandener Dateien
    nicht. Quellordner ohne Git-Metadaten werden nur dann wiederverwendet,
    wenn darin ein bekanntes Startskript gefunden wird.
    """
    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(
            f"Unbekanntes Tool {tool!r}. Erlaubt: "
            f"{', '.join(REPOSITORIES)}"
        )

    dest = Path(destination).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    git = shutil.which("git") or shutil.which("git.exe")
    if not git:
        raise RuntimeError(
            "Git wurde nicht gefunden. Installiere Git "
            "oder ergänze Git im PATH."
        )

    # Vorhandenes Git-Repository.
    if (dest / ".git").exists():
        log(f"Vorhandenes Git-Repository: {dest}")

        try:
            _run(
                [
                    git, "-C", str(dest),
                    "rev-parse", "--is-inside-work-tree",
                ],
                log=log,
            )
        except RuntimeError as exc:
            raise RuntimeError(
                f"Das Git-Verzeichnis ist ungültig:\n{dest}\n{exc}"
            ) from exc

        # Origin nur korrigieren, wenn die Änderung möglich ist.
        try:
            _run(
                [
                    git, "-C", str(dest),
                    "remote", "set-url", "origin", REPOSITORIES[tool],
                ],
                log=log,
            )
        except RuntimeError as exc:
            log(
                "WARNUNG: Die origin-URL konnte nicht gesetzt werden. "
                "Es wird versucht, das vorhandene Repository zu verwenden."
            )
            log(str(exc))

        # Nur Referenzen abrufen. Kein pull/reset/checkout.
        try:
            _run(
                [
                    git, "-C", str(dest),
                    "fetch", "origin", "--prune",
                ],
                log=log,
            )
            log(
                "Git-Fetch erfolgreich. Die ausgecheckten Dateien wurden "
                "nicht automatisch aktualisiert."
            )
        except RuntimeError as exc:
            log(
                "WARNUNG: Git-Fetch fehlgeschlagen. "
                "Die vorhandenen lokalen Dateien bleiben erhalten."
            )
            log(str(exc))
            log("Es wird mit dem vorhandenen lokalen Stand weitergearbeitet.")

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
        [git, "clone", REPOSITORIES[tool], str(dest)],
        log=log,
    )
    log(f"{tool} wurde erfolgreich geklont.")
    return dest


def prepare_tool(tool: str, destination, log=None) -> Path:
    """Prüft WSL unter Windows und bereitet das ausgewählte Tool vor."""
    log = _log_func(log)
    tool = str(tool).lower().strip()

    if tool not in REPOSITORIES:
        raise ValueError(
            f"Unbekanntes Tool {tool!r}. Erlaubt: "
            f"{', '.join(REPOSITORIES)}"
        )

    if platform.system() == "Windows":
        ensure_wsl(log=log)

    path = ensure_repository(tool, destination, log=log)
    log(f"{tool} ist bereit: {path}")
    return path


def _wsl_path(path: Path, log) -> str:
    """Konvertiert einen Windows-Pfad sicher in einen WSL-Pfad."""
    windows_path = str(path.expanduser().resolve())
    encoded_path = base64.b64encode(
        windows_path.encode("utf-8")
    ).decode("ascii")

    result = _run(
        [
            _find_wsl(),
            "-d", WSL_DISTRO,
            "--exec", "bash", "-lc",
            'decoded=$(printf "%s" "$1" | base64 -d) && wslpath -a "$decoded"',
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


def bash_quote(value) -> str:
    """Sicheres Quoting für Bash."""
    return shlex.quote(str(value))


def _start_command(tool: str) -> str:
    """Liefert den Startbefehl für das ausgewählte Tool."""
    if tool == "s4":
        return "./s4"
    return "./s3 menu"




def _launch_native_linux(tool: str, source: Path, log) -> None:
    """Startet Simplebuild nativ unter Linux in einem neuen Terminal."""
    script = _find_script(source, tool)

    if script is None:
        raise FileNotFoundError(
            f"Kein Startskript für {tool} in {source} gefunden."
        )

    start_command = _start_command(tool)

    command = (
        f"cd {bash_quote(str(script.parent))} || exit 1; "
        f"chmod +x {bash_quote(script.name)} || exit 1; "
        f"{start_command}; "
        "result=$?; "
        'echo; echo "Simplebuild beendet (Exit-Code: $result)."; '
        "exec bash"
    )

    terminals = [
        ("x-terminal-emulator", ["-e", "bash", "-lc", command]),
        ("gnome-terminal", ["--", "bash", "-lc", command]),
    ]

    errors = []

    for executable, arguments in terminals:
        path = shutil.which(executable)

        if not path:
            log(f"Nicht im PATH gefunden: {executable}")
            continue

        try:
            process = subprocess.Popen(
                [path, *arguments],
                start_new_session=True,
                close_fds=True,
            )

            log(
                f"Terminal-Aufruf gesendet: {path} "
                f"(PID {process.pid})"
            )
            log(f"Tool: {tool}; Startbefehl: {start_command}")
            return

        except OSError as exc:
            message = f"{executable}: {exc}"
            errors.append(message)
            log(f"Terminalstart fehlgeschlagen: {message}")

    raise RuntimeError(
        "Kein Terminal konnte gestartet werden.\n"
        + (
            "\n".join(errors)
            if errors
            else "Kein unterstützter Terminal-Emulator im PATH gefunden."
        )
    )




def launch_tool_menu(tool: str, source: Path, log=None) -> None:
    """Startet das ausgewählte Tool in einem separaten Terminal."""
    log = _log_func(log)
    tool = str(tool).lower().strip()
    source = Path(source).expanduser().resolve()

    if tool not in REPOSITORIES:
        raise ValueError(
            f"Unbekanntes Tool {tool!r}. Erlaubt: "
            f"{', '.join(REPOSITORIES)}"
        )

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

    # Das Startskript kann in einem Unterordner liegen.
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
        "-d", WSL_DISTRO,
        "--", "bash", "-lc", linux_command,
    ]

    log(f"WSL-Quellpfad: {wsl_script_dir}")
    log(f"WSL-Tool: {tool}")
    log(f"Startbefehl: {start_command}")
    log("Starte Simplebuild in einem neuen WSL-Konsolenfenster.")

    creationflags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    process = subprocess.Popen(command, creationflags=creationflags)
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
        "Dieses Modul wird von der Oberfläche importiert.\n"
        "Rufe prepare_tool() und launch_tool_menu() aus der GUI auf."
    )

from pathlib import Path
import shutil
import sys

path = Path("startup.py")
if not path.is_file():
    sys.exit("FEHLER: startup.py nicht gefunden.")

content = path.read_text(encoding="utf-8")

start = content.find("def _ensure_linux_qtsvg():")
end = content.find("\ndef main():", start)

if start < 0 or end < 0:
    sys.exit("ABBRUCH: Installationsfunktion oder main() nicht gefunden.")

new_function = r'''
def _ensure_qtsvg():
    """Installiert PyQt6.QtSvg passend zum Betriebssystem."""
    system = platform.system()

    try:
        from PyQt6.QtSvg import QSvgRenderer
        return True
    except ImportError:
        pass

    answer = QMessageBox.question(
        None,
        "QtSvg-Komponente fehlt",
        "Die QtSvg-Komponente fehlt.\n\n"
        "Soll sie jetzt automatisch installiert werden?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )

    if answer != QMessageBox.StandardButton.Yes:
        return False

    is_wsl = (
        system == "Linux"
        and (
            "microsoft" in platform.release().lower()
            or bool(os.environ.get("WSL_INTEROP"))
            or bool(os.environ.get("WSL_DISTRO_NAME"))
        )
    )

    try:
        # Windows, macOS und virtuelle Python-Umgebungen:
        # Installation in genau der aktiven Python-Umgebung.
        is_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)

        if system in ("Windows", "Darwin") or is_venv:
            command = [
                sys.executable, "-m", "pip",
                "install", "--upgrade", "PyQt6"
            ]
            result = subprocess.run(command, check=False)

        elif system == "Linux":
            # Linux-System-Python: passenden Paketmanager verwenden.
            if shutil.which("apt-get"):
                package_command = [
                    "apt-get", "install", "-y",
                    "python3-pyqt6.qtsvg"
                ]
                update_command = ["apt-get", "update"]

            elif shutil.which("dnf"):
                package_command = [
                    "dnf", "install", "-y", "python3-pyqt6"
                ]
                update_command = ["dnf", "makecache"]

            elif shutil.which("pacman"):
                package_command = [
                    "pacman", "-S", "--noconfirm", "python-pyqt6"
                ]
                update_command = ["pacman", "-Sy"]

            elif shutil.which("zypper"):
                package_command = [
                    "zypper", "--non-interactive",
                    "install", "python3-qt6"
                ]
                update_command = ["zypper", "refresh"]

            else:
                package_command = None
                update_command = None

            result = None

            if package_command:
                if is_wsl:
                    launcher = shutil.which("sudo")
                elif shutil.which("pkexec"):
                    launcher = shutil.which("pkexec")
                else:
                    launcher = shutil.which("sudo")

                if launcher:
                    update_result = subprocess.run(
                        [launcher] + update_command,
                        check=False
                    )

                    if update_result.returncode == 0:
                        result = subprocess.run(
                            [launcher] + package_command,
                            check=False
                        )

            # Fallback: pip in der aktiven Python-Umgebung.
            if result is None or result.returncode != 0:
                result = subprocess.run(
                    [
                        sys.executable, "-m", "pip",
                        "install", "PyQt6"
                    ],
                    check=False
                )
        else:
            QMessageBox.warning(
                None,
                "Nicht unterstütztes Betriebssystem",
                f"Automatische QtSvg-Installation für {system} "
                "ist nicht eingerichtet."
            )
            return False

        if result.returncode != 0:
            QMessageBox.warning(
                None,
                "Installation fehlgeschlagen",
                "QtSvg konnte nicht automatisch installiert werden.\n\n"
                "Bitte prüfe die Administratorrechte und die "
                "Python-Paketinstallation."
            )
            return False

        # Installation tatsächlich überprüfen.
        from PyQt6.QtSvg import QSvgRenderer

        QMessageBox.information(
            None,
            "Installation erfolgreich",
            "QtSvg wurde installiert.\n"
            "Der OSCam Patch Manager wird neu gestartet."
        )

        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as exc:
        QMessageBox.warning(
            None,
            "QtSvg-Installationsfehler",
            str(exc)
        )
        return False

    return True

'''

new_content = content[:start] + new_function + content[end:]

old_call = 'if system == "Linux" and not _ensure_linux_qtsvg():'
new_call = 'if not _ensure_qtsvg():'

if new_content.count(old_call) != 1:
    sys.exit("ABBRUCH: Der bisherige Funktionsaufruf wurde nicht eindeutig gefunden.")

new_content = new_content.replace(old_call, new_call, 1)

backup = Path("startup.py.bak_qtsvg_crossplatform")
if backup.exists():
    sys.exit(f"ABBRUCH: Sicherung existiert bereits: {backup}")

shutil.copy2(path, backup)
path.write_text(new_content, encoding="utf-8")

print("Plattformübergreifende QtSvg-Installation eingefügt.")
print(f"Sicherung: {backup}")

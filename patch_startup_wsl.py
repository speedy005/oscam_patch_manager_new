from pathlib import Path
import shutil
import sys

path = Path("startup.py")
content = path.read_text(encoding="utf-8")

old = '''    except ImportError:
        pass

    answer = QMessageBox.question(
'''

new = '''    except ImportError:
        pass

    # WSL: Keine automatische Installation über PolicyKit/pkexec.
    is_wsl = (
        "microsoft" in platform.release().lower()
        or bool(os.environ.get("WSL_INTEROP"))
        or bool(os.environ.get("WSL_DISTRO_NAME"))
    )

    if is_wsl:
        QMessageBox.warning(
            None,
            "QtSvg fehlt",
            "Die QtSvg-Komponente ist nicht installiert.\\n\\n"
            "Bitte im WSL-Terminal manuell installieren:\\n"
            "sudo apt update\\n"
            "sudo apt install -y python3-pyqt6.qtsvg\\n\\n"
            "Danach den OSCam Patch Manager erneut starten."
        )
        return False

    answer = QMessageBox.question(
'''

if content.count(old) != 1:
    sys.exit("ABBRUCH: Einfügestelle nicht eindeutig gefunden.")

backup = Path("startup.py.bak_wsl_qtsvg")
if backup.exists():
    sys.exit(f"ABBRUCH: Sicherung existiert bereits: {backup}")

shutil.copy2(path, backup)
path.write_text(content.replace(old, new, 1), encoding="utf-8")

print("WSL-QtSvg-Korrektur erfolgreich.")
print(f"Sicherung: {backup}")

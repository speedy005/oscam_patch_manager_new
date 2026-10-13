# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches – von der Erstellung und Prüfung bis zur lokalen Anwendung und Veröffentlichung auf GitHub.

[🇩🇪 Deutsch](#deutsch) · [🇬🇧 English](#english) · [📦 GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

**OSCam Emu Patch Manager** ist ein Python-basiertes Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches und zugehörigen Git-Arbeitsabläufen.

## ✨ Funktionen

- 🧩 Patches erstellen, prüfen und anwenden
- 📦 Patches sichern und als ZIP-Datei exportieren
- ✏️ Patch-Header und Metadaten bearbeiten
- 🖥️ Grafische Oberfläche mit PyQt6
- 🌐 Git- und GitHub-Funktionen, soweit implementiert
- 🐍 Python-Installer für Windows und Linux
- 🌍 Deutsche und englische Sprachoptionen, sofern unterstützt
- ⚙️ Einrichtung der Python-Umgebung und Abhängigkeiten, soweit implementiert

## 📋 Voraussetzungen

- Python **3.9 oder neuer**
- Internetverbindung
- Windows 10/11 oder Linux
- Schreibrechte im Installationsverzeichnis
- Git, sofern von den verwendeten Funktionen benötigt

Python herunterladen: [python.org](https://www.python.org/downloads/)

Unter Windows während der Installation nach Möglichkeit **Add Python to PATH** aktivieren.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

**1. Python überprüfen**

Öffne die Eingabeaufforderung (`Win + R` → `cmd`):

```bat
py -3 --version
```

**2. Installer direkt von GitHub herunterladen und starten**

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

Der Befehl lädt `installer.py` herunter und startet ihn mit Python 3.

**3. Installation abschließen**

Folge den Anweisungen des Installers, wähle dein Installationsverzeichnis und prüfe eventuelle Überschreibungsabfragen.

**4. Anwendung starten**

Falls vorhanden, starte im Installationsverzeichnis:

```bat
start_windows.bat
```

### 🐧 Linux

**1. Voraussetzungen installieren**

Für Debian, Ubuntu und Linux Mint:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

**2. Installer herunterladen und starten**

```bash
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

**3. Anwendung starten**

Wechsle in das Installationsverzeichnis und führe aus, sofern vorhanden:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

## ⚙️ Installer und ausgeschlossene Dateien

Der Installer lädt ausgewählte Dateien einzeln von GitHub herunter. Je nach Implementierung richtet er eine virtuelle Python-Umgebung unter `.venv` ein, installiert Abhängigkeiten aus `requirements.txt` und erstellt Startskripte.

Die konfigurierte Ausschlussliste umfasst:

- **Dateiendungen:** `.png`, `.zip`, `.md`, `.php`
- **Verzeichnisse:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer-Dateien:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Wichtig:** Ausgeschlossene PNG-Dateien können Icons oder andere Ressourcen enthalten. Prüfe deshalb, ob die Anwendung ohne diese Dateien funktioniert.

## 🔄 Aktualisierung

Führe den Installationsbefehl erneut aus, um den Installer erneut herunterzuladen.

- Eine erneute Installation garantiert nicht, dass alle vorhandenen Dateien aktualisiert werden.
- Abgelehnte Überschreibungen können alte Dateien zurücklassen.
- Nicht mehr benötigte Dateien werden möglicherweise nicht automatisch gelöscht.
- Sichere eigene Änderungen und Konfigurationen vor jedem Update.

## 🛠️ Fehlerbehebung

| Problem | Lösung |
|---|---|
| `py` wird nicht erkannt | Python installieren und PATH prüfen. Alternativ `python installer.py` versuchen. |
| `python3` fehlt | Python über den Linux-Paketmanager installieren. |
| `curl` fehlt | Installer manuell über die [GitHub-Dateiseite](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py) herunterladen. |
| `venv` fehlt | Unter Debian/Ubuntu `sudo apt install python3-venv` ausführen. |
| Abhängigkeiten fehlen | Installer-Ausgabe und `requirements.txt` prüfen, sofern vorhanden. |
| `SyntaxError` oder `UnicodeDecodeError` | Originaldatei direkt herunterladen und bearbeitete Python-Dateien als UTF-8 speichern. |
| Installation schlägt fehl | Internetverbindung, Python-Version, Schreibrechte und vollständige Fehlermeldung prüfen. |

## 🔒 Sicherheit

- Quellcode vor der Ausführung prüfen.
- Vor Patch-Operationen und Updates Sicherungen erstellen.
- Änderungen vor dem Commit mit `git diff` kontrollieren.
- GitHub-Tokens und Zugangsdaten niemals veröffentlichen.
- Bereinigungsoperationen nur in geprüften Verzeichnissen durchführen.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und Pull Requests sind willkommen. Bitte gib bei Fehlern die Reproduktionsschritte, das Betriebssystem, die Python-Version und relevante Fehlermeldungen an. Entferne Zugangsdaten und Tokens vor dem Teilen.

## ⚠️ Disclaimer

Dieses Projekt wird ohne Garantie bereitgestellt. Die Kompatibilität hängt vom System, dem Quellcode und der Konfiguration ab. Sichere wichtige Dateien, bevor du Änderungen an einer bestehenden Installation vornimmst.

## 📦 Projektlinks

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [Installer anzeigen](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py)
- [Installer direkt herunterladen](https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** is a Python-based desktop toolkit for managing OSCam-Emu patches and related Git workflows.

## ✨ Features

- 🧩 Create, check, and apply patches
- 📦 Back up and export patches as ZIP files
- ✏️ Edit patch headers and metadata
- 🖥️ PyQt6 graphical interface
- 🌐 Git and GitHub functionality where implemented
- 🐍 Python installer for Windows and Linux
- 🌍 German and English language options where supported
- ⚙️ Python environment and dependency setup where implemented

## 📋 Requirements

- Python **3.9 or newer**
- Internet connection
- Windows 10/11 or Linux
- Write permissions for the installation directory
- Git if required by the selected features

Download Python: [python.org](https://www.python.org/downloads/)

On Windows, enable **Add Python to PATH** during installation if available.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

**1. Check Python**

Open Command Prompt (`Win + R` → `cmd`):

```bat
py -3 --version
```

**2. Download and run the installer directly from GitHub**

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

This downloads `installer.py` and launches it using Python 3.

**3. Complete setup**

Follow the installer's instructions, choose your installation directory, and review any overwrite prompts.

**4. Launch the application**

If the startup script exists, run it from the installation directory:

```bat
start_windows.bat
```

### 🐧 Linux

**1. Install prerequisites**

For Debian, Ubuntu, and Linux Mint:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

**2. Download and run the installer**

```bash
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

**3. Launch the application**

Navigate to the installation directory and run the following commands if the script exists:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

## ⚙️ Installer and Excluded Files

The installer downloads selected files individually from GitHub. Depending on its implementation, it creates a virtual Python environment under `.venv`, installs dependencies from `requirements.txt`, and generates startup scripts.

The configured exclusion list includes:

- **File extensions:** `.png`, `.zip`, `.md`, `.php`
- **Directories:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer files:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Important:** Excluded PNG files may contain application icons or other resources. Verify that the application works without them.

## 🔄 Updating

Run the installation command again to download the installer again.

- Re-running the installer does not guarantee that every existing file will be updated.
- Files may remain unchanged if overwriting is declined.
- Obsolete files may not be removed automatically.
- Back up local changes and configuration files before updating.

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `py` is not recognized | Install Python and check PATH. Alternatively, try `python installer.py`. |
| `python3` is missing | Install Python through your Linux package manager. |
| `curl` is missing | Download the installer manually from the [GitHub file page](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py). |
| `venv` is missing | On Debian/Ubuntu, run `sudo apt install python3-venv`. |
| Missing dependencies | Check the installer output and `requirements.txt`, if available. |
| `SyntaxError` or `UnicodeDecodeError` | Download the original file and save edited Python files as UTF-8. |
| Installation fails | Check internet access, Python version, directory permissions, and the full error message. |

## 🔒 Security

- Review source code before running it.
- Back up files before patching or updating.
- Review changes with `git diff` before committing.
- Never publish GitHub tokens or credentials.
- Run cleanup operations only in verified directories.

## 🤝 Contributing

Bug reports, reproducible test cases, and pull requests are welcome. Please include reproduction steps, your operating system, Python version, and relevant error messages. Remove credentials and tokens before sharing.

## ⚠️ Disclaimer

This project is provided without warranties. Compatibility depends on your system, source tree, and configuration. Back up important files before modifying an existing installation.

## 📦 Project Links

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [View Installer](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py)
- [Download Installer Directly](https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡  
**Built with Python 3 · PyQt6 · Git · GitHub**

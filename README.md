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

Es unterstützt den Patch-Workflow von der Erstellung und Prüfung über die lokale Anwendung bis hin zur Verwaltung und Veröffentlichung von Änderungen. Welche Funktionen verfügbar sind, hängt von der jeweiligen Implementierung und Konfiguration ab.

## ✨ Funktionen

- 🧩 Patches erstellen, prüfen und anwenden
- 📦 Patches sichern und als ZIP-Datei exportieren
- ✏️ Patch-Header und Metadaten bearbeiten
- 🖥️ Grafische Oberfläche mit PyQt6
- 🌐 Git- und GitHub-Funktionen, soweit implementiert
- 🐍 Python-Installer für Windows und Linux
- 🌍 Deutsche und englische Sprachoptionen, sofern unterstützt
- ⚙️ Einrichtung der Python-Umgebung und Abhängigkeiten, soweit implementiert
- 🛠️ Linux-/WSL2-Build-Unterstützung für benötigte Build-Werkzeuge, sofern vom jeweiligen Build-Workflow verwendet

## 📋 Voraussetzungen

- Python **3.9 oder neuer**
- Internetverbindung für Download und gegebenenfalls GitHub-Funktionen
- Windows 10/11 oder eine unterstützte Linux-Distribution
- Schreibrechte im Installationsverzeichnis
- Git, sofern von den verwendeten Funktionen benötigt
- Ubuntu unter WSL2 für Build-Workflows, die ausdrücklich WSL verwenden
- Zusätzliche Build-Werkzeuge, wenn sie vom jeweiligen SDK oder Build-Skript benötigt werden

Python herunterladen: [python.org](https://www.python.org/downloads/)

Unter Windows während der Installation nach Möglichkeit **Add Python to PATH** aktivieren.

> **Hinweis:** Die Python-Anwendung und die Linux-Build-Umgebung sind zwei getrennte Bereiche. Wird ein Build unter WSL2 ausgeführt, müssen benötigte Linux-Werkzeuge innerhalb der verwendeten WSL-Distribution installiert sein. Eine Installation unter Windows allein reicht dafür nicht aus.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1. Python überprüfen

Öffne die Eingabeaufforderung (`Win + R` → `cmd`):

```bat
py -3 --version
```

Falls Python nicht gefunden wird, installiere Python über [python.org](https://www.python.org/downloads/) und prüfe anschließend den PATH.

#### 2. Installer herunterladen und starten

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

Der Befehl lädt `installer.py` herunter und startet es mit Python 3.

#### 3. Installation abschließen

Folge den Anweisungen des Installers. Wähle dein Installationsverzeichnis und prüfe eventuelle Überschreibungsabfragen sorgfältig.

#### 4. Anwendung starten

Wechsle in das Installationsverzeichnis. Falls das Startskript vorhanden ist, führe es aus:

```bat
start_windows.bat
```

### 🐧 Linux

#### 1. Voraussetzungen installieren

Für Debian, Ubuntu und Linux Mint:

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  git \
  meson \
  ninja-build \
  gettext
```

Diese Pakete stellen grundlegende Python-Werkzeuge, Git und zusätzliche Build-Werkzeuge bereit.

| Paket | Zweck |
|---|---|
| `python3` | Python-Laufzeit |
| `python3-venv` | Virtuelle Python-Umgebungen |
| `python3-pip` | Installation von Python-Paketen |
| `curl` | Herunterladen des Installers |
| `git` | Versionsverwaltung und Patch-Arbeitsabläufe |
| `meson` | Build-System für Projekte, die Meson verwenden |
| `ninja-build` | Build-Werkzeug, das häufig mit Meson eingesetzt wird |
| `gettext` | Übersetzungs- und Internationalisierungswerkzeuge |

**Wichtig:** Diese Paketliste ist eine grundlegende Ausgangsbasis. Abhängig vom SDK, dem Build-Skript und den aktivierten OSCam-Funktionen können weitere Pakete erforderlich sein.

#### 2. Installer herunterladen und starten

```bash
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

Folge den Anweisungen des Installers und prüfe die ausgegebenen Meldungen.

#### 3. Anwendung starten

Wechsle in das Installationsverzeichnis und führe das Startskript aus, sofern es vorhanden ist:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

### 🐧 Windows mit WSL2 und Ubuntu

Wenn du den OSCam-Build über WSL2 ausführst, müssen die benötigten Linux-Werkzeuge in der Ubuntu-Distribution installiert sein, die das Build-Skript startet.

Öffne Ubuntu unter WSL2 und führe aus:

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  git \
  meson \
  ninja-build \
  gettext
```

Prüfe danach die Verfügbarkeit der Build-Werkzeuge:

```bash
meson --version
ninja --version
gettext --version
git --version
```

Falls ein Befehl weiterhin mit `command not found` abbricht, prüfe, ob du die Pakete in der richtigen WSL-Distribution installiert hast und ob das Build-Skript dieselbe Umgebung verwendet.

**Hinweis zu OpenPLi-SDKs:** Die Installation dieser Werkzeuge behebt nur fehlende Programme aus dieser Liste. Ein OpenEmbedded-/OpenPLi-SDK kann zusätzliche Compiler, Bibliotheken, Header oder SDK-spezifische Abhängigkeiten benötigen.

## ⚙️ Installer und ausgeschlossene Dateien

Der Installer lädt ausgewählte Dateien einzeln von GitHub herunter. Je nach tatsächlicher Implementierung kann er eine virtuelle Python-Umgebung unter `.venv` einrichten, Abhängigkeiten aus `requirements.txt` installieren und Startskripte erstellen.

Die konfigurierte Ausschlussliste umfasst:

- **Dateiendungen:** `.png`, `.zip`, `.md`, `.php`
- **Verzeichnisse:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer-Dateien:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Wichtig:** Ausgeschlossene PNG-Dateien können Icons oder andere Ressourcen enthalten. Prüfe deshalb, ob die Anwendung ohne diese Dateien korrekt funktioniert.

Die tatsächliche Auswahl der heruntergeladenen Dateien und das Verhalten bei vorhandenen Dateien hängen von der Implementierung des Installers ab.

## 🔄 Aktualisierung

Führe den Installationsbefehl erneut aus, um den Installer erneut herunterzuladen und auszuführen.

Beachte dabei:

- Eine erneute Installation garantiert nicht, dass alle vorhandenen Dateien aktualisiert werden.
- Abgelehnte Überschreibungen können alte Dateien zurücklassen.
- Nicht mehr benötigte Dateien werden möglicherweise nicht automatisch gelöscht.
- Eigene Änderungen und Konfigurationen sollten vor jedem Update gesichert werden.
- Prüfe nach dem Update, ob die benötigten Abhängigkeiten weiterhin verfügbar sind.

## 🛠️ Fehlerbehebung

| Problem | Lösung |
|---|---|
| `py` wird nicht erkannt | Python installieren und PATH prüfen. Alternativ `python installer.py` verwenden, falls verfügbar. |
| `python3` fehlt | Python über den Linux-Paketmanager installieren. |
| `curl` fehlt | `sudo apt install curl` ausführen oder den Installer manuell über die [GitHub-Dateiseite](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py) beziehen. |
| `venv` fehlt | Unter Debian/Ubuntu `sudo apt install python3-venv` ausführen. |
| `meson: command not found` | `sudo apt update && sudo apt install -y meson` ausführen. |
| `ninja: command not found` | `sudo apt install -y ninja-build` ausführen. |
| `gettext` oder Übersetzungswerkzeuge fehlen | `sudo apt install -y gettext` ausführen. |
| `git: command not found` | `sudo apt install -y git` ausführen. |
| Build unter WSL schlägt wegen fehlender Werkzeuge fehl | Pakete in der Ubuntu-WSL-Distribution installieren, in der das Build-Skript tatsächlich läuft. |
| Compiler oder Header fehlen | Die SDK-Dokumentation und die vom Build-Skript benötigten Abhängigkeiten prüfen. |
| Python-Abhängigkeiten fehlen | Installer-Ausgabe und `requirements.txt` prüfen, sofern vorhanden. |
| `SyntaxError` oder `UnicodeDecodeError` | Originaldatei erneut herunterladen und bearbeitete Python-Dateien als UTF-8 speichern. |
| Installation schlägt fehl | Internetverbindung, Python-Version, Schreibrechte und vollständige Fehlermeldung prüfen. |

### Beispiel: Fehlendes Meson beheben

Wenn der Build mit dieser Meldung abbricht:

```text
bash: line 13: meson: command not found
Command failed (exit 127)
```

ist Meson in der aktuellen Linux-Umgebung nicht verfügbar. Unter Ubuntu oder WSL2 kannst du es so installieren:

```bash
sudo apt update
sudo apt install -y meson ninja-build gettext
```

Prüfe anschließend:

```bash
meson --version
ninja --version
gettext --version
```

Starte danach den Build erneut. Falls weitere Werkzeuge fehlen, prüfe die nächste Fehlermeldung und ergänze die erforderlichen Abhängigkeiten gezielt.

## 🔒 Sicherheit

- Quellcode vor der Ausführung prüfen.
- Vor Patch-Operationen und Updates Sicherungen erstellen.
- Änderungen vor dem Commit mit `git diff` kontrollieren.
- GitHub-Tokens und Zugangsdaten niemals veröffentlichen.
- Bereinigungsoperationen nur in geprüften Verzeichnissen durchführen.
- Installationsskripte nur aus vertrauenswürdigen Quellen beziehen.
- Vor dem Überschreiben bestehender Dateien prüfen, ob lokale Änderungen erhalten bleiben müssen.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und Pull Requests sind willkommen.

Bitte gib bei Fehlern folgende Informationen an:

- Reproduktionsschritte
- Betriebssystem und gegebenenfalls WSL-Version
- Python-Version
- Verwendetes SDK oder Build-Profil
- Relevante Fehlermeldungen und Build-Logs

Entferne Zugangsdaten, Tokens und andere vertrauliche Informationen vor dem Teilen.

## ⚠️ Disclaimer

Dieses Projekt wird ohne Garantie bereitgestellt. Die Kompatibilität hängt vom System, dem Quellcode, der Firmware, dem SDK und der jeweiligen Konfiguration ab.

Sichere wichtige Dateien, bevor du Änderungen an einer bestehenden Installation vornimmst. Eine erfolgreiche Kompilierung garantiert nicht, dass die erzeugte Binary auf jedem Zielgerät lauffähig ist.

## 📦 Projektlinks

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [Installer anzeigen](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py)
- [Installer direkt herunterladen](https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** is a Python-based desktop toolkit for managing OSCam-Emu patches and related Git workflows.

It supports the patch workflow from creation and validation to local application and the management or publication of changes. Available features depend on the actual implementation and configuration.

## ✨ Features

- 🧩 Create, check, and apply patches
- 📦 Back up patches and export them as ZIP files
- ✏️ Edit patch headers and metadata
- 🖥️ PyQt6 graphical interface
- 🌐 Git and GitHub functionality where implemented
- 🐍 Python installer for Windows and Linux
- 🌍 German and English language options where supported
- ⚙️ Python environment and dependency setup where implemented
- 🛠️ Linux/WSL2 build support for required build tools where used by the selected workflow

## 📋 Requirements

- Python **3.9 or newer**
- Internet access for downloads and any required GitHub operations
- Windows 10/11 or a supported Linux distribution
- Write permissions for the installation directory
- Git if required by the selected features
- Ubuntu under WSL2 for build workflows that explicitly use WSL
- Additional build tools when required by the selected SDK or build script

Download Python: [python.org](https://www.python.org/downloads/)

On Windows, enable **Add Python to PATH** during installation if available.

> **Note:** The Python application and the Linux build environment are separate. If a build runs under WSL2, its required Linux tools must be installed inside the WSL distribution used by the build script. Installing those tools on Windows alone is not sufficient.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1. Check Python

Open Command Prompt (`Win + R` → `cmd`):

```bat
py -3 --version
```

If Python is not found, install it from [python.org](https://www.python.org/downloads/) and check your PATH.

#### 2. Download and run the installer

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

This downloads `installer.py` and runs it using Python 3.

#### 3. Complete setup

Follow the installer's instructions. Choose your installation directory and review any overwrite prompts carefully.

#### 4. Launch the application

Navigate to the installation directory. If the startup script exists, run:

```bat
start_windows.bat
```

### 🐧 Linux

#### 1. Install prerequisites

For Debian, Ubuntu, and Linux Mint:

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  git \
  meson \
  ninja-build \
  gettext
```

These packages provide basic Python tools, Git, and additional build utilities.

| Package | Purpose |
|---|---|
| `python3` | Python runtime |
| `python3-venv` | Virtual Python environments |
| `python3-pip` | Python package installation |
| `curl` | Download the installer |
| `git` | Version control and patch workflows |
| `meson` | Build system for projects that use Meson |
| `ninja-build` | Build tool commonly used with Meson |
| `gettext` | Translation and internationalization tools |

**Important:** This package list is a baseline, not a guarantee of every build dependency. Additional packages may be required depending on the SDK, build script, and enabled OSCam features.

#### 2. Download and run the installer

```bash
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

Follow the installer prompts and review its output.

#### 3. Launch the application

Navigate to the installation directory and run the startup script if it exists:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

### 🐧 Windows with WSL2 and Ubuntu

If you build OSCam through WSL2, the required Linux tools must be installed inside the Ubuntu distribution that runs the build script.

Open Ubuntu under WSL2 and run:

```bash
sudo apt update
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  curl \
  git \
  meson \
  ninja-build \
  gettext
```

Then verify that the build tools are available:

```bash
meson --version
ninja --version
gettext --version
git --version
```

If a command still fails with `command not found`, check that the packages were installed in the correct WSL distribution and that the build script uses the same environment.

**OpenPLi SDK note:** Installing these tools only addresses missing commands from this list. An OpenEmbedded/OpenPLi SDK may require additional compilers, libraries, headers, or SDK-specific dependencies.

## ⚙️ Installer and Excluded Files

The installer downloads selected files individually from GitHub. Depending on its actual implementation, it may create a virtual Python environment under `.venv`, install dependencies from `requirements.txt`, and create startup scripts.

The configured exclusion list includes:

- **File extensions:** `.png`, `.zip`, `.md`, `.php`
- **Directories:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer files:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Important:** Excluded PNG files may contain application icons or other resources. Verify that the application works correctly without those files.

The actual file selection and overwrite behavior depend on the installer's implementation.

## 🔄 Updating

Run the installation command again to download and run the installer again.

Keep in mind:

- Re-running the installer does not guarantee that every existing file will be updated.
- Files may remain unchanged if overwriting is declined.
- Obsolete files may not be removed automatically.
- Back up local changes and configuration files before updating.
- Check that required dependencies remain available after updating.

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `py` is not recognized | Install Python and check PATH. Alternatively, use `python installer.py` if available. |
| `python3` is missing | Install Python through your Linux package manager. |
| `curl` is missing | Run `sudo apt install curl` or download the installer manually from the [GitHub file page](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py). |
| `venv` is missing | On Debian/Ubuntu, run `sudo apt install python3-venv`. |
| `meson: command not found` | Run `sudo apt update && sudo apt install -y meson`. |
| `ninja: command not found` | Run `sudo apt install -y ninja-build`. |
| `gettext` or translation tools are missing | Run `sudo apt install -y gettext`. |
| `git: command not found` | Run `sudo apt install -y git`. |
| Build fails under WSL because tools are missing | Install the packages inside the Ubuntu WSL distribution that actually runs the build script. |
| Compiler or headers are missing | Check the SDK documentation and the dependencies required by the build script. |
| Python dependencies are missing | Check the installer output and `requirements.txt`, if available. |
| `SyntaxError` or `UnicodeDecodeError` | Download the original file again and save edited Python files as UTF-8. |
| Installation fails | Check internet access, Python version, directory permissions, and the complete error message. |

### Example: Fixing a missing Meson installation

If a build stops with:

```text
bash: line 13: meson: command not found
Command failed (exit 127)
```

Meson is not available in the current Linux environment. On Ubuntu or WSL2, install it with:

```bash
sudo apt update
sudo apt install -y meson ninja-build gettext
```

Then verify the tools:

```bash
meson --version
ninja --version
gettext --version
```

Restart the build. If more tools are missing, inspect the next error and add the required dependencies as needed.

## 🔒 Security

- Review source code before running it.
- Back up files before patching or updating.
- Review changes with `git diff` before committing.
- Never publish GitHub tokens or credentials.
- Run cleanup operations only in verified directories.
- Obtain installation scripts from trusted sources.
- Before overwriting existing files, check whether local changes must be preserved.

## 🤝 Contributing

Bug reports, reproducible test cases, and pull requests are welcome.

When reporting a problem, include:

- Steps to reproduce
- Operating system and WSL version, if applicable
- Python version
- SDK or build profile
- Relevant error messages and build logs

Remove credentials, tokens, and other confidential information before sharing.

## ⚠️ Disclaimer

This project is provided without warranties. Compatibility depends on the system, source tree, firmware, SDK, and configuration.

Back up important files before modifying an existing installation. A successful compilation does not guarantee that the resulting binary will run on every target device.

## 📦 Project Links

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [View Installer](https://github.com/speedy005/oscam_patch_manager_new/blob/master/installer.py)
- [Download Installer Directly](https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡  
**Built with Python 3 · PyQt6 · Git · GitHub**

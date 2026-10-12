# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung des OSCam-Emu-Patch-Workflows – von der Erstellung und Prüfung von Patches über lokale Änderungen bis hin zur Veröffentlichung auf GitHub.

[🇩🇪 Deutsch](#-deutsch) · [🇬🇧 English](#-english) · [📦 GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

Der **OSCam Emu Patch Manager** ist ein Desktop-Werkzeug für die Verwaltung von OSCam-Emu-Patches und zugehörigen Git-Workflows.

Das Projekt kombiniert eine grafische Oberfläche mit Werkzeugen zur Patch-Verwaltung, lokalen Git-Operationen und GitHub-bezogenen Arbeitsabläufen.

Der separate Python-Installer unterstützt die Installation unter Windows und Linux. Er lädt die benötigten Projektdateien direkt aus dem GitHub-Repository herunter, erstellt eine virtuelle Python-Umgebung und installiert – sofern eine `requirements.txt` vorhanden ist – die aufgeführten Abhängigkeiten.

## ✨ Funktionen

### 🧩 Patch-Verwaltung

- Erstellen und Aktualisieren von Patches für die unterstützten OSCam-Quellcode-Repositories.
- Prüfen und Anwenden von Patches.
- Sichern und Verpacken von Patches als ZIP-Dateien innerhalb der Anwendung.
- Bearbeiten von Patch-Headern und Metadaten.
- Verwalten temporärer Patch-Arbeitsverzeichnisse.

Die konkret verfügbaren Patch-Funktionen richten sich nach der installierten Programmversion.

### 🌐 Git- und GitHub-Integration

- Unterstützung von Git-basierten Arbeitsabläufen.
- Konfiguration von Repository-URLs und Branches.
- Git-Identität für lokale Git-Operationen konfigurieren.
- GitHub-bezogene Upload-Funktionen, sofern sie in der installierten Version vorhanden und eingerichtet sind.
- Status- und Fehlermeldungen innerhalb der Anwendung verfolgen.

**Sicherheitshinweis:** GitHub-Tokens dürfen nicht in öffentlichen Dateien oder im Repository veröffentlicht werden. Prüfe Änderungen und Upload-Ziele vor der Veröffentlichung.

### 🎨 Desktop-Oberfläche

- Grafische Benutzeroberfläche auf Basis von PyQt6.
- Deutsche und englische Texte, soweit in der jeweiligen Programmversion implementiert.
- Statusmeldungen und Fortschrittsanzeigen, soweit vom jeweiligen Vorgang unterstützt.
- Konfigurationsmöglichkeiten der Anwendung.

### 📦 Plattformübergreifender Python-Installer

Der Installer unterstützt Windows und Linux, sofern Python 3 und die erforderlichen Systemkomponenten verfügbar sind.

- Auswahl zwischen Deutsch und Englisch.
- Sprache anhand der System-Locale vorauswählen.
- Installationsverzeichnis frei wählen.
- Projektdateien einzeln von GitHub herunterladen.
- PNG-, ZIP-, Markdown- und PHP-Dateien überspringen.
- Git-Metadaten, Cache-Verzeichnisse und virtuelle Umgebungen aus dem Repository überspringen.
- Eine lokale virtuelle Python-Umgebung unter `.venv` erstellen.
- Abhängigkeiten aus `requirements.txt` installieren, sofern vorhanden.
- Passenden Anwendungsstarter für Windows oder Linux erzeugen.
- Vorhandene Dateien nicht ohne entsprechende Bestätigung überschreiben.

Der Installer lädt nicht das vollständige Repository als ZIP herunter.

## 📋 Voraussetzungen

- Python 3.9 oder neuer für die beschriebene Installer-Version.
- Internetzugang zum Abrufen der Dateien und Python-Pakete.
- Schreibrechte für das gewählte Installationsverzeichnis.
- Eine Git-Installation, falls die Anwendung Git-Befehle verwendet.
- Unter Linux gegebenenfalls das zusätzliche Betriebssystempaket für `venv`.
- Für bestimmte Python-Pakete können zusätzliche Systembibliotheken erforderlich sein.

**Hinweis:** Python selbst wird durch die hier beschriebene Installer-Version nicht automatisch installiert. Wenn Python fehlt, muss es zuerst über den offiziellen Python-Installer oder den Paketmanager des Betriebssystems installiert werden.

## 🚀 Installation

### 🪟 Windows

1. Installiere Python 3.9 oder neuer. Aktiviere bei Bedarf die Option, Python dem `PATH` hinzuzufügen.
2. Öffne PowerShell in dem Ordner, in dem du den Installer speichern möchtest.
3. Lade ausschließlich `installer.py` herunter:

```powershell
py -3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

4. Starte den Installer:

```powershell
py -3 installer.py
```

5. Wähle die Sprache und das gewünschte Installationsverzeichnis.
6. Warte, bis der Download und die Installation der Abhängigkeiten abgeschlossen sind.

Starte die Anwendung anschließend über die im Installationsverzeichnis erzeugte Datei:

```text
start_windows.bat
```

Falls `py -3` nicht verfügbar ist, kannst du `python` verwenden, sofern es auf Python 3 verweist.

### 🐧 Linux

1. Prüfe die Python-Version:

```bash
python3 --version
```

2. Lade ausschließlich `installer.py` herunter:

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

3. Starte den Installer:

```bash
python3 installer.py
```

4. Wähle Sprache und Installationsverzeichnis.
5. Warte, bis die Projektdateien heruntergeladen und die Abhängigkeiten installiert wurden.

Starte anschließend die Anwendung über:

```bash
./start_linux.sh
```

Falls die Ausführungsberechtigung fehlt:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

### ⚙️ Was macht der Installer?

1. Der Benutzer lädt zunächst nur `installer.py` herunter.
2. Der Installer erkennt die Systemsprache und bietet Deutsch oder Englisch an.
3. Der Benutzer wählt das Installationsverzeichnis.
4. Der Installer liest die Dateiliste des konfigurierten GitHub-Repositorys.
5. Er überspringt definierte Dateien und Verzeichnisse.
6. Die ausgewählten Projektdateien werden einzeln heruntergeladen.
7. Eine virtuelle Python-Umgebung wird im Installationsverzeichnis erstellt.
8. Vorhandene Python-Abhängigkeiten werden aus `requirements.txt` installiert.
9. Der plattformspezifische Anwendungsstarter wird erzeugt.

Die Installation setzt voraus, dass der konfigurierte GitHub-Branch erreichbar ist und die erwarteten Projektdateien enthält.

### 🚫 Vom Installer ausgeschlossene Dateien

Folgende Dateiendungen werden nicht heruntergeladen:

- `.png`
- `.zip`
- `.md`
- `.php`

Ausgeschlossene Verzeichnisse:

- `.git`
- `.github`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.venv`
- `venv`
- `env`
- `node_modules`

Ausgeschlossene Installer-Dateien:

- `installer.py`
- `installer.sh`
- `installer.bat`
- `install.py`
- `install.sh`
- `install.bat`

**Wichtig:** PNG-Dateien werden auch dann übersprungen, wenn sie als Ressourcen oder Icons in der Anwendung verwendet werden. Die Anwendung sollte deshalb keine zwingend benötigten PNG-Dateien voraussetzen.

## 🗂️ Installationsverzeichnis

Ein typisches Installationsverzeichnis sieht folgendermaßen aus:

```text
OSCamEmuPatchManager/
├── .venv/
├── main.py
├── requirements.txt
├── start_windows.bat    # Windows
├── start_linux.sh       # Linux
└── weitere Projektdateien
```

Die tatsächliche Dateistruktur hängt vom Inhalt des GitHub-Repositorys ab. Die Starter verwenden die Python-Umgebung aus `.venv`.

## 🔄 Aktualisierung und vorhandene Dateien

Der Installer kann bereits vorhandene Projektdateien erkennen und vor dem Überschreiben nachfragen.

Beachte:

- Bestehende Dateien können bei einer erneuten Installation erhalten bleiben.
- Es wird kein vollständiger automatischer Abgleich mit allen bereits installierten Dateien durchgeführt.
- Entfernte Dateien aus älteren Versionen werden nicht automatisch bereinigt.
- Sichere wichtige Konfigurationen, Zugangsdaten und lokale Änderungen vor einer Aktualisierung.

## ⚙️ Ersteinrichtung

1. Starte die Anwendung über den erzeugten Starter.
2. Prüfe die Konfiguration und die verwendeten Repository-Pfade.
3. Richte Git und gegebenenfalls GitHub-Zugangsdaten ein.
4. Kontrolliere Branches und Zielverzeichnisse.
5. Teste den Arbeitsablauf zunächst mit einer nicht destruktiven Operation.
6. Prüfe Änderungen, bevor du sie übernimmst oder veröffentlichst.

## 🛡️ Sicherheit und verantwortungsvolle Nutzung

Patch- und Repository-Operationen können lokale Dateien verändern.

- Erstelle vor größeren Änderungen eine Sicherung oder einen Git-Checkpoint.
- Prüfe Repository, Branch und Zielpfade vor jeder Operation.
- Kontrolliere Änderungen mit Git-Diff.
- Führe Bereinigungen nur in eindeutig geprüften Verzeichnissen aus.
- Halte GitHub-Tokens geheim.
- Verwende nur die notwendigen Zugriffsrechte.
- Veröffentliche keine privaten Konfigurationsdateien oder Zugangsdaten.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und gezielte Verbesserungen sind willkommen.

Bitte beschreibe bei einem Fehlerbericht:

- Das erwartete und tatsächliche Verhalten.
- Die Schritte zur Reproduktion.
- Das verwendete Betriebssystem und die Python-Version.
- Relevante Fehlermeldungen ohne Zugangsdaten oder Tokens.

## 🎯 Projektziel

OSCam-Patch- und Repository-Verwaltung einfacher, übersichtlicher und zuverlässiger machen.

⭐ **Gefällt dir das Projekt? Gib ihm einen Stern auf GitHub!**

[➡️ Repository öffnen](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** is a desktop toolkit for managing OSCam-Emu patches and related Git workflows.

The project combines a graphical interface with tools for patch management, local Git operations, and GitHub-related workflows.

The separate Python installer supports Windows and Linux. It downloads selected project files directly from GitHub, creates a virtual Python environment, and installs dependencies listed in `requirements.txt`, when available.

## ✨ Features

### 🧩 Patch Management

- Create and update patches for supported OSCam source repositories.
- Check and apply patches.
- Back up and package patches as ZIP files within the application.
- Edit patch headers and metadata.
- Manage temporary patch work directories.

The exact available patch operations depend on the installed application version.

### 🌐 Git & GitHub Integration

- Support for Git-based workflows.
- Configure repository URLs and branches.
- Configure the Git identity used for local operations.
- GitHub-related upload functionality when implemented and configured in the installed version.
- Monitor status and error messages within the application.

**Security note:** Never publish GitHub tokens in public files or repositories. Verify changes and upload destinations before publishing.

### 🎨 Desktop Interface

- PyQt6 graphical user interface.
- German and English text where implemented in the relevant version.
- Status messages and progress indicators where supported by the operation.
- Application configuration options.

### 📦 Cross-Platform Python Installer

The installer supports Windows and Linux when Python 3 and the required system components are available.

- English and German language selection.
- Automatic language preselection based on the system locale.
- Custom installation directory.
- Individual project-file downloads from GitHub.
- Skips PNG, ZIP, Markdown, and PHP files.
- Skips Git metadata, cache directories, and virtual environments.
- Creates a local Python virtual environment under `.venv`.
- Installs dependencies from `requirements.txt`, when available.
- Generates the appropriate Windows or Linux application launcher.
- Does not overwrite existing files without confirmation.

The installer does not download the entire repository as a ZIP archive.

## 📋 Requirements

- Python 3.9 or newer for the described installer version.
- Internet access to retrieve project files and Python packages.
- Write permission for the selected installation directory.
- Git if the application uses Git commands.
- On Linux, the additional `venv` operating-system package may be required.
- Some Python packages may require additional system libraries.

**Note:** This installer does not automatically install Python itself. If Python is missing, install it first using the official Python installer or your operating system's package manager.

## 🚀 Installation

### 🪟 Windows

1. Install Python 3.9 or newer. Enable the option to add Python to `PATH` if needed.
2. Open PowerShell in the directory where you want to save the installer.
3. Download only `installer.py`:

```powershell
py -3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

4. Run the installer:

```powershell
py -3 installer.py
```

5. Select your language and installation directory.
6. Wait for the project files and dependencies to finish installing.

Launch the application using the generated file in the installation directory:

```text
start_windows.bat
```

If `py -3` is unavailable, use `python` if it points to Python 3.

### 🐧 Linux

1. Check your Python version:

```bash
python3 --version
```

2. Download only `installer.py`:

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

3. Run the installer:

```bash
python3 installer.py
```

4. Select your language and installation directory.
5. Wait for the project files and dependencies to finish installing.

Launch the application using:

```bash
./start_linux.sh
```

If the executable permission is missing:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

### ⚙️ What Does the Installer Do?

1. The user initially downloads only `installer.py`.
2. The installer detects the system locale and offers English or German.
3. The user selects the installation directory.
4. The installer reads the file list from the configured GitHub repository.
5. It skips the configured files and directories.
6. Selected project files are downloaded individually.
7. A Python virtual environment is created in the installation directory.
8. Dependencies are installed from `requirements.txt` when available.
9. The platform-specific application launcher is generated.

Installation requires the configured GitHub branch to be accessible and to contain the expected project files.

### 🚫 Files Excluded by the Installer

The following file extensions are not downloaded:

- `.png`
- `.zip`
- `.md`
- `.php`

Excluded directories:

- `.git`
- `.github`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.venv`
- `venv`
- `env`
- `node_modules`

Excluded installer files:

- `installer.py`
- `installer.sh`
- `installer.bat`
- `install.py`
- `install.sh`
- `install.bat`

**Important:** PNG files are skipped even if they are used as application resources or icons. The application should not depend on required PNG files being present.

## 🗂️ Installation Directory

A typical installation directory looks like this:

```text
OSCamEmuPatchManager/
├── .venv/
├── main.py
├── requirements.txt
├── start_windows.bat    # Windows
├── start_linux.sh       # Linux
└── additional project files
```

The actual file structure depends on the contents of the GitHub repository. The generated launchers use the Python environment in `.venv`.

## 🔄 Updates and Existing Files

The installer can detect existing project files and ask before overwriting them.

Please note:

- Existing files may be preserved during a subsequent installation.
- A complete automatic comparison against every installed file is not performed.
- Files removed from newer repository versions are not automatically cleaned up.
- Back up important configuration files, credentials, and local changes before updating.

## ⚙️ First-Time Setup

1. Launch the application using the generated launcher.
2. Verify the configuration and repository paths.
3. Configure Git and GitHub credentials if required.
4. Check branches and destination directories.
5. Start with a non-destructive operation.
6. Review changes before applying or publishing them.

## 🛡️ Security and Responsible Use

Patch and repository operations may modify local files.

- Create a backup or Git checkpoint before major changes.
- Verify the repository, branch, and destination paths before each operation.
- Review changes using Git diff.
- Run cleanup operations only in verified directories.
- Keep GitHub tokens private.
- Use only the required access permissions.
- Never publish private configuration files or credentials.

## 🤝 Contributing

Bug reports, reproducible test cases, and focused improvements are welcome.

Please include the following in bug reports:

- Expected and actual behavior.
- Steps to reproduce the issue.
- Operating system and Python version.
- Relevant error messages without credentials or tokens.

## 🎯 Mission

Make OSCam patch and repository management simpler, clearer, and more reliable.

⭐ **Like the project? Give it a star on GitHub!**

[➡️ Open the Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡  
**Built with Python 3 · PyQt6 · Git · GitHub**

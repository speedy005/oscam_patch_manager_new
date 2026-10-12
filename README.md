# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung des OSCam-Emu-Patch-Workflows – von der Erstellung und Prüfung von Patches über lokale Änderungen bis hin zur Veröffentlichung auf GitHub.

🇩🇪 Deutsch · 🇬🇧 English · [📦 GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

**OSCam Emu Patch Manager** ist ein Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches und zugehörigen Git-Arbeitsabläufen.

Das Projekt kombiniert eine grafische Benutzeroberfläche mit Werkzeugen zur Patch-Verwaltung, lokalen Git-Operationen und GitHub-bezogenen Arbeitsabläufen.

Der separate Python-Installer ist für Windows und Linux vorgesehen. Er lädt ausgewählte Projektdateien einzeln aus dem GitHub-Repository herunter, erstellt eine virtuelle Python-Umgebung und installiert Abhängigkeiten aus `requirements.txt`, sofern diese Datei vorhanden ist.

> Hinweis: Die verfügbaren Funktionen hängen von der installierten Programmversion und deren Konfiguration ab.

## ✨ Funktionen

### 🧩 Patch-Verwaltung

- Erstellen und Aktualisieren von Patches für unterstützte OSCam-Quellcode-Repositories.
- Prüfen und Anwenden von Patches.
- Sichern und Verpacken von Patches als ZIP-Dateien innerhalb der Anwendung.
- Bearbeiten von Patch-Headern und Metadaten.
- Verwalten temporärer Patch-Arbeitsverzeichnisse.

### 🌐 Git- und GitHub-Integration

- Unterstützung Git-basierter Arbeitsabläufe.
- Konfiguration von Repository-URLs und Branches.
- Konfiguration der Git-Identität für lokale Git-Operationen.
- GitHub-bezogene Upload-Funktionen, sofern diese in der installierten Version implementiert und eingerichtet sind.
- Anzeige von Statusmeldungen und Fehlern, soweit unterstützt.

**Sicherheit:** GitHub-Tokens dürfen nicht in öffentlichen Dateien oder im Repository veröffentlicht werden. Prüfe Änderungen und Upload-Ziele vor jeder Veröffentlichung.

### 🎨 Desktop-Oberfläche

- Grafische Benutzeroberfläche auf Basis von PyQt6.
- Deutsche und englische Texte, soweit in der jeweiligen Version implementiert.
- Statusmeldungen und Fortschrittsanzeigen, sofern unterstützt.
- Konfigurationsmöglichkeiten der Anwendung.

### 📦 Plattformübergreifender Python-Installer

- Unterstützung für Windows und Linux.
- Auswahl zwischen Deutsch und Englisch.
- Vorauswahl der Sprache anhand der System-Locale.
- Frei wählbares Installationsverzeichnis.
- Einzelner Download ausgewählter Projektdateien von GitHub.
- Ausschluss von PNG-, ZIP-, Markdown- und PHP-Dateien.
- Ausschluss definierter Cache-Verzeichnisse, Git-Metadaten und virtueller Umgebungen.
- Erstellung einer virtuellen Python-Umgebung unter `.venv`.
- Installation der Abhängigkeiten aus `requirements.txt`, sofern vorhanden.
- Erstellung eines plattformspezifischen Startskripts.
- Nachfrage vor dem Überschreiben vorhandener Projektdateien.

Der Installer lädt das Projekt nicht als vollständiges ZIP-Archiv herunter.

## 📋 Voraussetzungen

- Python 3.9 oder neuer.
- Internetzugang für GitHub und Python-Pakete.
- Schreibrechte im ausgewählten Installationsverzeichnis.
- Git, sofern die Anwendung Git-Befehle verwendet.
- Unter Linux gegebenenfalls das zusätzliche Paket für `venv`.
- Für bestimmte Python-Pakete möglicherweise zusätzliche Systembibliotheken.

**Wichtig:** Der Installer installiert Python nicht automatisch. Python muss vorher über die offizielle Python-Website oder den Paketmanager des Betriebssystems installiert werden.

## 🚀 Installation

### 🪟 Windows

**1. Python installieren**

Lade Python 3.9 oder neuer von der offiziellen Website herunter:

https://www.python.org/downloads/windows/

Aktiviere während der Installation nach Möglichkeit die Option, Python zum `PATH` hinzuzufügen.

Prüfe anschließend in PowerShell:

```powershell
py -3 --version
```

**2. Installer herunterladen**

Öffne PowerShell in dem Ordner, in dem du den Installer speichern möchtest, und führe aus:

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" `
  -OutFile "installer.py"
```

Damit wird zunächst nur `installer.py` heruntergeladen.

**3. Installer starten**

```powershell
py -3 installer.py
```

Falls `py -3` nicht verfügbar ist, versuche:

```powershell
python installer.py
```

**4. Installation abschließen**

- Wähle Deutsch oder Englisch.
- Wähle dein gewünschtes Installationsverzeichnis.
- Bestätige gegebenenfalls das Überschreiben vorhandener Dateien.
- Warte, bis die Projektdateien heruntergeladen und die Abhängigkeiten installiert wurden.

**5. Anwendung starten**

Öffne das Installationsverzeichnis und starte:

```text
start_windows.bat
```

### 🐧 Linux

**1. Python prüfen**

```bash
python3 --version
```

Benötigt wird Python 3.9 oder neuer.

**2. Voraussetzungen installieren**

Debian, Ubuntu und Linux Mint:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

Fedora:

```bash
sudo dnf install -y python3 python3-pip curl
```

Arch Linux und Manjaro:

```bash
sudo pacman -S --needed python curl
```

**3. Installer herunterladen**

```bash
mkdir -p "$HOME/oscam-installer"
cd "$HOME/oscam-installer"

curl -fL \
  "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" \
  -o installer.py
```

Alternativ kannst du `wget` verwenden, sofern es installiert ist:

```bash
wget -O installer.py \
  "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py"
```

**4. Installer starten**

```bash
python3 installer.py
```

Wähle die Sprache und das Installationsverzeichnis. Der Installer lädt anschließend die ausgewählten Projektdateien herunter und richtet die Python-Umgebung ein.

**5. Anwendung starten**

Wechsle in das ausgewählte Installationsverzeichnis und führe aus:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

Falls `venv` nicht verfügbar ist, installiere das passende Paket für deine Python-Version. Unter Debian oder Ubuntu kann dies beispielsweise `python3-venv` oder ein versionsspezifisches Paket wie `python3.12-venv` sein.

## ⚙️ Was macht der Installer?

1. Der Benutzer lädt zunächst nur `installer.py` herunter.
2. Der Installer bietet Deutsch oder Englisch an und kann die Systemsprache vorauswählen.
3. Der Benutzer wählt das Installationsverzeichnis.
4. Der Installer ruft die Dateiliste des konfigurierten GitHub-Branches `master` ab.
5. Definierte Dateien und Verzeichnisse werden übersprungen.
6. Ausgewählte Projektdateien werden einzeln heruntergeladen.
7. Im Installationsverzeichnis wird `.venv` erstellt.
8. Die Abhängigkeiten aus `requirements.txt` werden installiert, sofern vorhanden.
9. Ein Startskript für das jeweilige Betriebssystem wird erzeugt.

Die Installation setzt voraus, dass das Repository erreichbar ist und die erwarteten Projektdateien enthält.

## 🚫 Vom Installer ausgeschlossene Dateien

**Ausgeschlossene Dateiendungen:**

- `.png`
- `.zip`
- `.md`
- `.php`

**Ausgeschlossene Verzeichnisse:**

- `.git`
- `.github`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.venv`
- `venv`
- `env`
- `node_modules`

**Ausgeschlossene Installer-Dateien:**

- `installer.py`
- `installer.sh`
- `installer.bat`
- `install.py`
- `install.sh`
- `install.bat`

**Wichtig:** PNG-Dateien werden auch dann übersprungen, wenn sie als Icons oder Ressourcen verwendet werden. Die Anwendung muss deshalb ohne zwingend benötigte PNG-Dateien funktionieren.

## 🗂️ Installationsverzeichnis

Ein mögliches Installationsverzeichnis sieht folgendermaßen aus:

```text
OSCamEmuPatchManager/
├── .venv/
├── main.py
├── requirements.txt
├── start_windows.bat
├── start_linux.sh
└── weitere Projektdateien
```

Die tatsächliche Dateistruktur hängt vom Inhalt des Repositorys ab. Die Startskripte verwenden die Python-Umgebung unter `.venv`.

## 🔄 Aktualisierung und vorhandene Dateien

Bei einer erneuten Installation kann der Installer vorhandene Dateien erkennen und vor dem Überschreiben nachfragen.

Bitte beachte:

- Bestehende Dateien können erhalten bleiben, wenn das Überschreiben abgelehnt wird.
- Es erfolgt kein vollständiger automatischer Abgleich aller installierten Dateien.
- Entfernte Dateien aus älteren Versionen werden nicht automatisch gelöscht.
- Sichere eigene Änderungen und Konfigurationsdateien vor einer Aktualisierung.

## 🛡️ Sicherheit und verantwortungsvolle Nutzung

Patch- und Repository-Operationen können lokale Dateien verändern.

- Erstelle vor größeren Änderungen eine Sicherung oder einen Git-Checkpoint.
- Prüfe Repository, Branch und Zielpfade vor jeder Operation.
- Kontrolliere Änderungen mit `git diff`.
- Führe Bereinigungen nur in eindeutig geprüften Verzeichnissen aus.
- Halte GitHub-Tokens geheim.
- Verwende nur die erforderlichen Zugriffsrechte.
- Veröffentliche keine privaten Konfigurationen oder Zugangsdaten.

## 🛠️ Fehlerbehebung

**Python wird nicht gefunden**

Installiere Python 3.9 oder neuer und prüfe, ob es über die Kommandozeile erreichbar ist.

**Linux: `venv` fehlt**

Auf Debian oder Ubuntu:

```bash
sudo apt install python3-venv
```

Falls erforderlich, installiere das zu deiner Python-Version passende Paket.

**Linux: `Permission denied`**

```bash
chmod +x start_linux.sh
./start_linux.sh
```

**Download fehlgeschlagen**

Prüfe die Internetverbindung und stelle sicher, dass GitHub erreichbar ist.

**Installation der Abhängigkeiten fehlgeschlagen**

Prüfe die Fehlermeldung, die Python-Version und mögliche fehlende Systembibliotheken.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und gezielte Verbesserungen sind willkommen.

Ein hilfreicher Fehlerbericht enthält:

- Erwartetes und tatsächliches Verhalten.
- Schritte zur Reproduktion.
- Betriebssystem und Python-Version.
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

The separate Python installer is designed for Windows and Linux. It downloads selected project files individually from GitHub, creates a virtual Python environment, and installs dependencies listed in `requirements.txt`, when available.

> Note: Available functionality depends on the installed application version and its configuration.

## ✨ Features

### 🧩 Patch Management

- Create and update patches for supported OSCam source repositories.
- Check and apply patches.
- Back up and package patches as ZIP files within the application.
- Edit patch headers and metadata.
- Manage temporary patch work directories.

### 🌐 Git & GitHub Integration

- Support for Git-based workflows.
- Configure repository URLs and branches.
- Configure the Git identity used for local operations.
- GitHub-related upload functionality when implemented and configured in the installed version.
- Display status messages and errors where supported.

**Security:** Never publish GitHub tokens in public files or repositories. Verify changes and upload destinations before publishing.

### 🎨 Desktop Interface

- PyQt6 graphical user interface.
- German and English text where implemented in the relevant version.
- Status messages and progress indicators where supported.
- Application configuration options.

### 📦 Cross-Platform Python Installer

- Designed for Windows and Linux.
- English and German language selection.
- Language preselection based on the system locale.
- Custom installation directory.
- Individual downloads of selected project files from GitHub.
- Excludes PNG, ZIP, Markdown, and PHP files.
- Excludes configured cache directories, Git metadata, and virtual environments.
- Creates a local Python virtual environment under `.venv`.
- Installs dependencies from `requirements.txt`, when available.
- Generates a platform-specific startup script.
- Asks before overwriting existing project files.

The installer does not download the entire repository as a ZIP archive.

## 📋 Requirements

- Python 3.9 or newer.
- Internet access to retrieve project files and Python packages.
- Write permission for the selected installation directory.
- Git if the application uses Git commands.
- On Linux, the additional `venv` operating-system package may be required.
- Some Python packages may require additional system libraries.

**Important:** The installer does not install Python itself. If Python is missing, install it first using the official Python website or your operating system's package manager.

## 🚀 Installation

### 🪟 Windows

**1. Install Python**

Download Python 3.9 or newer from the official website:

https://www.python.org/downloads/windows/

If possible, enable the option to add Python to `PATH`.

Check your installation in PowerShell:

```powershell
py -3 --version
```

**2. Download the installer**

Open PowerShell in the directory where you want to save the installer and run:

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" `
  -OutFile "installer.py"
```

This initially downloads only `installer.py`.

**3. Run the installer**

```powershell
py -3 installer.py
```

If `py -3` is unavailable, try:

```powershell
python installer.py
```

**4. Complete the installation**

- Select English or German.
- Choose your installation directory.
- Confirm any overwrite prompts.
- Wait for the selected project files and dependencies to finish installing.

**5. Start the application**

Open the installation directory and run:

```text
start_windows.bat
```

### 🐧 Linux

**1. Check Python**

```bash
python3 --version
```

Python 3.9 or newer is required.

**2. Install prerequisites**

Debian, Ubuntu, and Linux Mint:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl
```

Fedora:

```bash
sudo dnf install -y python3 python3-pip curl
```

Arch Linux and Manjaro:

```bash
sudo pacman -S --needed python curl
```

**3. Download the installer**

```bash
mkdir -p "$HOME/oscam-installer"
cd "$HOME/oscam-installer"

curl -fL \
  "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" \
  -o installer.py
```

Alternatively, use `wget` if it is installed:

```bash
wget -O installer.py \
  "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py"
```

**4. Run the installer**

```bash
python3 installer.py
```

Select your language and installation directory. The installer then downloads the selected project files and sets up the Python environment.

**5. Start the application**

Navigate to the selected installation directory and run:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

If `venv` is unavailable, install the appropriate package for your Python version. On Debian or Ubuntu, this may be `python3-venv` or a version-specific package such as `python3.12-venv`.

## ⚙️ What Does the Installer Do?

1. The user initially downloads only `installer.py`.
2. The installer offers English or German and may preselect a language based on the system locale.
3. The user selects the installation directory.
4. The installer retrieves the file list from the configured GitHub branch, `master`.
5. Configured files and directories are skipped.
6. Selected project files are downloaded individually.
7. A virtual environment is created under `.venv`.
8. Dependencies are installed from `requirements.txt`, when available.
9. A startup script is generated for the target operating system.

Installation requires the GitHub repository to be accessible and contain the expected project files.

## 🚫 Files Excluded by the Installer

**Excluded file extensions:**

- `.png`
- `.zip`
- `.md`
- `.php`

**Excluded directories:**

- `.git`
- `.github`
- `__pycache__`
- `.pytest_cache`
- `.mypy_cache`
- `.venv`
- `venv`
- `env`
- `node_modules`

**Excluded installer files:**

- `installer.py`
- `installer.sh`
- `installer.bat`
- `install.py`
- `install.sh`
- `install.bat`

**Important:** PNG files are skipped even if they are used as application icons or resources. The application must therefore work without any required PNG files.

## 🗂️ Installation Directory

A possible installation directory looks like this:

```text
OSCamEmuPatchManager/
├── .venv/
├── main.py
├── requirements.txt
├── start_windows.bat
├── start_linux.sh
└── additional project files
```

The actual file structure depends on the contents of the repository. The generated launchers use the Python environment under `.venv`.

## 🔄 Updates and Existing Files

During a subsequent installation, the installer may detect existing files and ask before overwriting them.

Please note:

- Existing files may be preserved if overwriting is declined.
- A complete automatic comparison against all installed files is not performed.
- Files removed from newer repository versions are not automatically deleted.
- Back up local changes and configuration files before updating.

## 🛡️ Security and Responsible Use

Patch and repository operations may modify local files.

- Create a backup or Git checkpoint before major changes.
- Verify the repository, branch, and destination paths before each operation.
- Review changes using `git diff`.
- Run cleanup operations only in verified directories.
- Keep GitHub tokens private.
- Use only the required access permissions.
- Never publish private configuration files or credentials.

## 🛠️ Troubleshooting

**Python is not found**

Install Python 3.9 or newer and make sure it is accessible from the command line.

**Linux: `venv` is missing**

On Debian or Ubuntu:

```bash
sudo apt install python3-venv
```

If necessary, install the package matching your Python version.

**Linux: `Permission denied`**

```bash
chmod +x start_linux.sh
./start_linux.sh
```

**Download failed**

Check your internet connection and make sure GitHub is accessible.

**Dependency installation failed**

Check the error message, your Python version, and any missing system libraries.

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

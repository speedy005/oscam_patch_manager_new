# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung des OSCam-Emu-Patch-Workflows – von der Erstellung und Prüfung von Patches über lokale Änderungen bis hin zur Veröffentlichung auf GitHub.

[🇩🇪 Deutsch](#-deutsch) · [🇬🇧 English](#-english) · [📦 GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

Der **OSCam Emu Patch Manager** vereint Patch-Verwaltung, Git-Werkzeuge, GitHub-Upload-Funktionen und eine konfigurierbare Desktop-Oberfläche in einer Anwendung.

Das Ziel ist ein übersichtlicher, zuverlässiger Workflow, mit dem sich OSCam-Emu-Patches erstellen, aktualisieren, überprüfen, anwenden, sichern und veröffentlichen lassen.

Mit dem zusätzlichen Python-Installer kannst du die Anwendung unter Linux oder Windows installieren, ohne das gesamte Repository manuell klonen oder als ZIP herunterladen zu müssen.

## ✨ Funktionen

### 🧩 Patch-Verwaltung

- Erstellen von Patches aus den relevanten OSCam-Quellcode-Repositories.
- Aktualisieren vorhandener Patches bei Änderungen am Quellcode.
- Prüfen von Patches vor der Anwendung.
- Anwenden von Patches auf ein lokales OSCam-Emu-Git-Repository.
- Sichern und Verpacken von Patches als ZIP-Dateien.
- Bereinigen temporärer Patch-Arbeitsverzeichnisse.
- Bearbeiten von Patch-Headern und Metadaten.

### 🌐 Git- und GitHub-Integration

- Lokale Git-Repositories verwalten und letzte Commits prüfen.
- Repository-URLs, Branches und Git-Identität konfigurieren.
- GitHub-Zugangsdaten für Uploads konfigurieren.
- Patch-Dateien in ein konfiguriertes GitHub-Repository hochladen.
- Repository-Inhalte über die vorhandene Upload-Funktion veröffentlichen.
- Fortschritt, Status und Ausgaben direkt in der Anwendung verfolgen.

> **Hinweis zum Patch-Upload:** Der Patch-Datei-Upload ist darauf ausgelegt, `oscam-emu.patch` zu aktualisieren, ohne absichtlich andere Dateien im Ziel-Repository zu überschreiben.

### 🎨 Moderne Desktop-Oberfläche

- 🖥️ Grafische Benutzeroberfläche auf Basis von PyQt6.
- 🌍 Deutsch und Englisch.
- 🎨 Anpassbare Farben und Fortschrittsbalken.
- 📊 Statusmeldungen und Fortschrittsanzeige.
- ⚙️ Konfigurations- und Hilfefunktionen.
- 🔄 Update-Prüfung und Neustartoptionen.

### 📦 Zweisprachiger Python-Installer

- Download ausschließlich der Installer-Datei beim ersten Schritt.
- Automatische Vorauswahl der Sprache anhand der Systemsprache.
- Manuelle Sprachwahl beim Start.
- Frei wählbares Installationsverzeichnis.
- Optionales Installieren der Abhängigkeiten aus `requirements.txt`.
- Ausschluss ausgewählter Dateien und Entwicklungsverzeichnisse.
- Schutz bereits vorhandener ausgeschlossener Dateien vor ungefragtem Löschen.
- Unterstützung für Linux und Windows.

## 📋 Voraussetzungen

- Python 3.10 oder neuer empfohlen.
- Git muss installiert und über `PATH` erreichbar sein.
- Internetzugang zum Abrufen der benötigten Projektdateien.
- Schreibrechte für das gewählte Installationsverzeichnis.
- Für GitHub-Uploads: ein Token mit den notwendigen Berechtigungen.

## 🚀 Installation

### 🐧 Linux

**1. Python 3 prüfen**

```bash
python3 --version
```

**2. Nur den Installer herunterladen**

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

**3. Installer starten**

```bash
python3 installer.py
```

Folge den Anweisungen, wähle die Sprache und lege das gewünschte Installationsverzeichnis fest.

### 🪟 Windows

Öffne PowerShell im gewünschten Download-Verzeichnis.

**1. Python 3 prüfen**

```powershell
py -3 --version
```

**2. Nur den Installer herunterladen**

```powershell
py -3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

**3. Installer starten**

```powershell
py -3 installer.py
```

Falls `py -3` nicht verfügbar ist, verwende `python`, sofern Python 3 korrekt installiert ist.

### ⚙️ Was macht der Installer?

1. Lädt zunächst ausschließlich `installer.py` herunter.
2. Erkennt die Systemsprache und bietet Deutsch oder Englisch an.
3. Ermöglicht die Auswahl des Installationsverzeichnisses.
4. Ruft beim Installieren die benötigten Projektdateien ab.
5. Überspringt definierte Dateien und Verzeichnisse.
6. Kann die benötigten Python-Abhängigkeiten installieren.
7. Meldet vorhandene ausgeschlossene Dateien, statt sie ungefragt zu löschen.

**Dateifilter:**

- `.png`
- `.zip`
- `.md`
- `.php`

**Ausgeschlossene Verzeichnisse und Dateien:**

- `.git`
- `__pycache__`
- Virtuelle Python-Umgebungen
- `installer.py`
- `installer.sh`
- `installer.bat`

Die Filter müssen in der tatsächlichen Installer-Implementierung umgesetzt sein. Die initiale Download-Anweisung lädt nur die einzelne Python-Datei; die Installationslogik entscheidet anschließend, welche weiteren Dateien benötigt werden.

## 🛠️ Abhängigkeiten und Programmstart

Wenn du das Projekt bereits lokal vorliegen hast, kannst du die Abhängigkeiten direkt installieren.

```bash
python -m pip install -r requirements.txt
```

Starte anschließend die Anwendung:

```bash
python main.py
```

Alternativ:

- **Windows:** `start_windows.bat`
- **Linux:** `./start_linux.sh`

Unter Linux kann der Starter bei Bedarf ausführbar gemacht werden:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

## ⚙️ Ersteinrichtung

1. Starte die Anwendung.
2. Öffne die GitHub- oder Konfigurationseinstellungen.
3. Trage die gewünschten Repository-URLs und Branches ein.
4. Konfiguriere Git-Benutzername und E-Mail-Adresse.
5. Hinterlege bei Bedarf ein GitHub-Token.
6. Prüfe die lokalen Repository- und Patch-Pfade.
7. Beginne mit einer Patch-Prüfung oder einem anderen möglichst nicht destruktiven Vorgang.

## 🗂️ Projektstruktur

| Datei | Aufgabe |
|---|---|
| `main.py` | Haupteinstiegspunkt der Anwendung |
| `startup.py` | Startablauf, Rechteprüfung und Qt-Ereignisschleife |
| `gui.py` | Hauptfenster und GUI-Aktionen |
| `workers.py` | Hintergrund- und Installations-Worker |
| `system_check.py` | Systemprüfung |
| `paths.py` | Anwendungs-, Repository- und Patch-Pfade |
| `config_manager.py` | Laden und Speichern der Konfiguration |
| `translations.py` | Deutsche und englische Texte |
| `themes.py` | Farben und Themes |
| `ui_components.py` | Wiederverwendbare Qt-Komponenten |
| `dialogs_splash.py` | Dialoge und Splashscreen |
| `git_manager.py` | Git-Aufrufe, Branches und Revisionen |
| `patch_format.py` | Patch-Format und Header |
| `patch_operations.py` | Erstellen, Prüfen, Sichern und Anwenden von Patches |
| `github_patch_upload.py` | Patch-Datei-Upload |
| `github_repo_upload.py` | Repository-Upload |
| `bootstrap.py` | Umgebungs- und Abhängigkeitsprüfungen |
| `requirements.txt` | Python-Abhängigkeiten |
| `installer.py` | Zweisprachiger Installationsprozess |
| `installer.sh` | Optionaler Linux-Starter |
| `installer.bat` | Optionaler Windows-Starter |

Die tatsächliche Dateiliste kann sich abhängig von der Version unterscheiden.

## 🛡️ Sicherheit und verantwortungsvolle Nutzung

Patch- und Repository-Operationen können lokale Dateien verändern oder löschen.

- Erstelle vor Änderungen eine Sicherung oder einen sauberen Git-Checkpoint.
- Prüfe Repository, Branch und Zielpfade vor jeder Operation.
- Kontrolliere nach Änderungen das Git-Diff.
- Führe Bereinigungen nur in eindeutig geprüften Verzeichnissen aus.
- Halte GitHub-Tokens geheim.
- Verwende nur die Berechtigungen, die für den jeweiligen Workflow erforderlich sind.
- Speichere keine Zugangsdaten oder privaten Konfigurationsdateien in einem öffentlichen Repository.

Prüfe erzeugte Patches und Änderungen, bevor du sie übernimmst oder veröffentlichst.

## 🧱 Architektur

Das Projekt ist modular aufgebaut, um Funktionen nach Verantwortlichkeiten zu trennen und die Wartbarkeit zu verbessern.

Der öffentliche Programmstart erfolgt über `main.py`. Die konkrete Import- und Modulstruktur sollte anhand des aktuellen Quellcodes geprüft werden, da ältere und neuere Versionen unterschiedliche Übergangsarchitekturen verwenden können.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und gezielte Verbesserungen sind willkommen.

Bitte beschreibe bei einem Beitrag:

- Welches Problem gelöst wird.
- Wie es reproduziert oder getestet werden kann.
- Welche relevanten Fehlermeldungen auftreten.

Entferne Zugangsdaten, Tokens und private Repository-Informationen aus Logs, bevor du sie teilst.

## 🎯 Projektziel

OSCam-Patch- und Repository-Verwaltung einfacher, übersichtlicher und zuverlässiger machen.

⭐ **Gefällt dir das Projekt? Gib ihm einen Stern auf GitHub!**

[➡️ Repository öffnen](https://github.com/speedy005/oscam_patch_manager_new)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** combines patch management, Git utilities, GitHub upload tools, and a configurable desktop interface in one application.

Its goal is to provide a clear and reliable workflow for creating, refreshing, checking, applying, backing up, and publishing OSCam-Emu patches.

With the additional Python installer, you can install the application on Linux or Windows without manually cloning or downloading the entire repository.

## ✨ Features

### 🧩 Patch Management

- Create patches from the relevant OSCam source repositories.
- Refresh existing patches when source code changes.
- Check patches before applying them.
- Apply patches to a local OSCam-Emu Git repository.
- Back up and package patches as ZIP files.
- Clean temporary patch work directories.
- Edit patch headers and metadata.

### 🌐 Git & GitHub Integration

- Manage local Git repositories and inspect recent commits.
- Configure repository URLs, branches, and Git identity.
- Configure GitHub credentials for uploads.
- Upload patch files to a configured GitHub repository.
- Publish repository contents through the available upload workflow.
- Monitor progress, status messages, and operation output directly in the application.

> **Patch upload note:** The patch-file upload workflow is designed to update `oscam-emu.patch` without intentionally overwriting unrelated files in the target repository.

### 🎨 Modern Desktop Interface

- 🖥️ PyQt6 graphical user interface.
- 🌍 English and German.
- 🎨 Customizable colors and progress bars.
- 📊 Progress indicators and status messages.
- ⚙️ Configuration and help options.
- 🔄 Update checks and restart options.

### 📦 Bilingual Python Installer

- Downloads only the installer file during the initial step.
- Automatically selects a language based on the system locale.
- Allows users to change the language at startup.
- Supports a custom installation directory.
- Optionally installs dependencies from `requirements.txt`.
- Excludes selected files and development directories.
- Protects existing excluded files from being deleted without permission.
- Supports Linux and Windows.

## 📋 Requirements

- Python 3.10 or newer recommended.
- Git installed and available on `PATH`.
- Internet access to retrieve the required project files.
- Write permissions for the selected installation directory.
- For GitHub uploads: a token with the required permissions.

## 🚀 Installation

### 🐧 Linux

**1. Check Python 3**

```bash
python3 --version
```

**2. Download only the installer**

```bash
python3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

**3. Run the installer**

```bash
python3 installer.py
```

Follow the prompts, select your language, and choose your installation directory.

### 🪟 Windows

Open PowerShell in your preferred download directory.

**1. Check Python 3**

```powershell
py -3 --version
```

**2. Download only the installer**

```powershell
py -3 -c "import urllib.request; urllib.request.urlretrieve('https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/main/installer.py', 'installer.py')"
```

**3. Run the installer**

```powershell
py -3 installer.py
```

If `py -3` is unavailable, use `python` if Python 3 is correctly installed.

### ⚙️ What Does the Installer Do?

1. Downloads only `installer.py` initially.
2. Detects the system language and offers English or German.
3. Lets you choose the installation directory.
4. Retrieves the required project files during installation.
5. Skips the configured files and directories.
6. Can install the required Python dependencies.
7. Reports existing excluded files instead of deleting them without permission.

**Excluded file extensions:**

- `.png`
- `.zip`
- `.md`
- `.php`

**Excluded directories and files:**

- `.git`
- `__pycache__`
- Python virtual environments
- `installer.py`
- `installer.sh`
- `installer.bat`

These filters must be implemented in the actual installer. The initial download command retrieves only the individual Python file; the installer determines which additional project files are required.

## 🛠️ Dependencies and Application Startup

If you already have a local copy of the project, install its dependencies with:

```bash
python -m pip install -r requirements.txt
```

Launch the application:

```bash
python main.py
```

Alternatively:

- **Windows:** `start_windows.bat`
- **Linux:** `./start_linux.sh`

On Linux, make the launcher executable if necessary:

```bash
chmod +x start_linux.sh
./start_linux.sh
```

## ⚙️ First-Time Setup

1. Start the application.
2. Open the GitHub or configuration settings.
3. Enter the repository URLs and branches you want to use.
4. Configure your Git username and email.
5. Add a GitHub token if uploads are required.
6. Verify the local repository and patch paths.
7. Start with a patch check or another non-destructive operation.

## 🗂️ Project Structure

| File | Responsibility |
|---|---|
| `main.py` | Main application entry point |
| `startup.py` | Startup flow, permission checks, and Qt event loop |
| `gui.py` | Main window and GUI actions |
| `workers.py` | Background and installation workers |
| `system_check.py` | System checks |
| `paths.py` | Application, repository, and patch paths |
| `config_manager.py` | Configuration loading and saving |
| `translations.py` | German and English translations |
| `themes.py` | Colors and themes |
| `ui_components.py` | Reusable Qt components |
| `dialogs_splash.py` | Dialogs and splash screen |
| `git_manager.py` | Git operations, branches, and revisions |
| `patch_format.py` | Patch formatting and headers |
| `patch_operations.py` | Patch creation, checking, backup, and application |
| `github_patch_upload.py` | Patch-file upload |
| `github_repo_upload.py` | Repository upload |
| `bootstrap.py` | Environment and dependency checks |
| `requirements.txt` | Python dependencies |
| `installer.py` | Bilingual installation process |
| `installer.sh` | Optional Linux launcher |
| `installer.bat` | Optional Windows launcher |

The actual file list may vary between versions.

## 🛡️ Security and Responsible Use

Patch and repository operations may modify or remove local files.

- Create a backup or clean Git checkpoint before making changes.
- Verify the repository, branch, and destination paths before each operation.
- Review the Git diff after changes.
- Run cleanup operations only against verified directories.
- Keep GitHub tokens private.
- Use only the permissions required for your workflow.
- Never commit credentials or private configuration files to a public repository.

Always review generated patches and repository changes before accepting or publishing them.

## 🧱 Architecture

The project uses a modular structure to separate responsibilities and improve maintainability.

The public application entry point is `main.py`. The exact import and module structure should be verified against the current source code, as older and newer versions may use different transitional architectures.

## 🤝 Contributing

Bug reports, reproducible test cases, and focused improvements are welcome.

When submitting a contribution, please include:

- The problem your change addresses.
- Steps to reproduce or test it.
- Relevant error messages.

Remove credentials, tokens, and private repository information from logs before sharing them.

## 🎯 Mission

Make OSCam patch and repository management simpler, clearer, and more reliable.

⭐ **Like the project? Give it a star on GitHub!**

[➡️ View Repository](https://github.com/speedy005/oscam_patch_manager_new)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡  
**Built with Python 3 · PyQt6 · Git · GitHub**

# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
*Install. Manage. Patch. Publish.*

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches – von der Erstellung und Prüfung über die lokale Anwendung bis hin zur Veröffentlichung von Änderungen.

🇩🇪 Deutsch · 🇬🇧 English · 📦 GitHub Repository

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

**OSCam Emu Patch Manager** ist ein Python-basiertes Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches und zugehörigen Git-Arbeitsabläufen.

Die Anwendung bietet eine grafische Oberfläche für unterstützte Patch-, Backup-, Konfigurations- und Build-Aufgaben. Der konkrete Funktionsumfang hängt von der installierten Version, der Konfiguration und den verfügbaren externen Werkzeugen ab.

## ✨ Funktionen

- 🧩 Patches erstellen, prüfen und anwenden
- 📦 Backups erstellen und als ZIP-Datei exportieren
- ✏️ Patch-Header und Metadaten bearbeiten
- 🖥️ Grafische Oberfläche auf Basis von PyQt6
- 🌐 Git- und GitHub-Funktionen, sofern konfiguriert und verfügbar
- 📁 Arbeitsordner auswählen und dauerhaft speichern
- ⚙️ Python-Umgebungen und Abhängigkeiten verwalten
- 🛠️ Linux- und WSL2-Unterstützung für geeignete Build-Workflows
- 🔍 Build-Werkzeuge und Abhängigkeiten prüfen
- 🔒 Unterstützte Dateien und Verzeichnisse bei Backups ausschließen

## 📋 Voraussetzungen

### Windows

- Windows 10 oder Windows 11
- Eine unterstützte Python-Version
- Internetzugang für Installationsdownloads und gegebenenfalls GitHub-Funktionen
- Schreibrechte im Installations- und Arbeitsverzeichnis

### Linux und WSL2

- Eine unterstützte Linux-Distribution, beispielsweise Ubuntu
- Python 3, `pip` und `venv`
- PyQt6 und die tatsächlich benötigten Python-Abhängigkeiten
- Systembibliotheken für die grafische Oberfläche
- Git und gegebenenfalls zusätzliche Build-Werkzeuge
- WSLg oder eine andere geeignete grafische Umgebung, wenn die GUI unter WSL ausgeführt wird

Für OSCam-Emu-Builds können weitere Bibliotheken, Header, Compiler oder ein projektspezifisches SDK erforderlich sein.

Python herunterladen: https://www.python.org/downloads/

> **Wichtig:** Windows-Python und die Python-Umgebung in WSL2 sind getrennte Installationen. Python-Pakete, die unter Windows installiert wurden, stehen einer Linux-Anwendung nicht automatisch zur Verfügung.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1. Python prüfen

Öffne die Eingabeaufforderung (`Win + R` → `cmd`) und führe aus:

```bat
py -3 --version
```

Wenn der Befehl nicht erkannt wird, installiere Python von der offiziellen Website und prüfe die PATH-Konfiguration.

#### 2. Installer herunterladen

Wenn der Installer in der verwendeten Repository-Version verfügbar ist, kann er beispielsweise so heruntergeladen werden:

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py"
```

Prüfe die Herkunft der Datei und starte sie anschließend:

```bat
py -3 "%TEMP%\oscam_installer.py"
```

Verwende diesen Downloadpfad nur, wenn der Installer unter dieser Adresse tatsächlich vorhanden und für deine Version vorgesehen ist.

#### 3. Installation abschließen

- Folge den Anweisungen des Installers.
- Wähle das gewünschte Installationsverzeichnis.
- Prüfe Überschreibungsabfragen sorgfältig.
- Sichere vorhandene Konfigurationen und eigene Änderungen.
- Kontrolliere die Ausgabe auf fehlende Abhängigkeiten.

#### 4. Anwendung starten

Wechsle im Terminal in das tatsächlich verwendete Installationsverzeichnis.

Prüfe zuerst, welche Startdateien vorhanden sind:

```bat
dir *.bat
dir *.py
```

Führe anschließend das für diese Version vorgesehene Startskript aus. Falls `start_windows.bat` vorhanden ist:

```bat
start_windows.bat
```

Nicht jede Version muss dieselben Startdateien enthalten.

### 🐧 Linux: Ubuntu, Debian und Linux Mint

#### 1. Systempakete installieren

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

Für Build-Workflows, die Meson und Ninja verwenden:

```bash
sudo apt install -y meson ninja-build gettext
```

Diese Pakete stellen eine grundlegende Python-Umgebung, Compiler-Werkzeuge und ausgewählte Systembibliotheken bereit. Sie ersetzen keine projektspezifische SDK-Installation.

#### 2. Projektverzeichnis öffnen

Wechsle in das Verzeichnis, in dem sich das Projekt befindet.

Beispiel mit einem frei wählbaren Pfad:

```bash
cd "/pfad/zum/projekt"
```

Prüfe anschließend den Inhalt:

```bash
pwd
ls -la
```

Passe den Beispielpfad an deine Installation an. Verwende keinen Beispielpfad, der nicht zu deinem System gehört.

#### 3. Virtuelle Python-Umgebung einrichten

Erstelle die virtuelle Umgebung, sofern sie noch nicht existiert:

```bash
python3 -m venv .venv
```

Aktiviere sie:

```bash
source .venv/bin/activate
```

Aktualisiere `pip`:

```bash
python -m pip install --upgrade pip
```

Installiere anschließend die Abhängigkeiten anhand der Dateien, die tatsächlich im Projekt vorhanden sind.

Wenn eine `requirements.txt` existiert:

```bash
python -m pip install -r requirements.txt
```

Falls keine solche Datei vorhanden ist, prüfe die Installationsanweisungen und Python-Imports des Projekts. Installiere keine nicht dokumentierten Abhängigkeiten auf Verdacht.

#### 4. Anwendung starten

Prüfe, ob der Programmeinstiegspunkt vorhanden ist:

```bash
ls -l main.py
```

Wenn die Datei existiert und die Abhängigkeiten installiert sind:

```bash
python main.py
```

Die virtuelle Umgebung muss in jeder neuen Terminalsitzung erneut aktiviert werden.

### 🐧 Windows mit WSL2 und Ubuntu

WSL2 ermöglicht den Betrieb einer Linux-Umgebung unter Windows. Linux-Build-Werkzeuge und Python-Abhängigkeiten müssen innerhalb der tatsächlich verwendeten WSL-Distribution eingerichtet werden.

#### 1. WSL prüfen

Öffne PowerShell unter Windows:

```powershell
wsl --status
wsl --list --verbose
```

Wenn Ubuntu noch nicht installiert ist, kann die Installation in einer PowerShell-Sitzung mit Administratorrechten gestartet werden:

```powershell
wsl --install -d Ubuntu
```

Schließe anschließend gegebenenfalls die Windows-Ersteinrichtung ab.

#### 2. Ubuntu öffnen

Öffne Ubuntu über das Windows-Startmenü oder starte es aus PowerShell:

```powershell
wsl -d Ubuntu
```

Alle nachfolgenden Linux-Befehle werden im Ubuntu-Terminal ausgeführt.

#### 3. WSL-Abhängigkeiten installieren

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

Für zusätzliche Build-Workflows:

```bash
sudo apt install -y meson ninja-build gettext
```

**Warum `libpulse0`?** Die Bibliothek stellt die Laufzeitkomponente `libpulse.so.0` bereit. Sie kann für GUI- oder Audiokomponenten benötigt werden. Installiere weitere Bibliotheken anhand der konkreten Fehlermeldungen.

Wenn `sudo` ein Passwort verlangt, verwende das Passwort deines Ubuntu-Linux-Benutzers. Bei der Eingabe werden keine Zeichen angezeigt. Das ist normal. Das Ubuntu-Passwort ist nicht automatisch dein Windows-Passwort.

#### 4. Projektverzeichnis auswählen

Wechsle in das Verzeichnis, in dem das Projekt tatsächlich gespeichert ist.

Für ein Windows-Laufwerk ist der Zugriff in WSL häufig über `/mnt/<laufwerk>/...` möglich. Beispiel:

```bash
cd "/mnt/<laufwerk>/pfad/zum/projekt"
```

Ersetze den Beispielpfad durch deinen tatsächlichen Speicherort.

Alternativ kannst du das Projekt im Linux-Dateisystem von WSL speichern.

Prüfe anschließend:

```bash
pwd
ls -la
```

#### 5. Python-Umgebung einrichten

Wenn die virtuelle Umgebung noch nicht vorhanden ist:

```bash
python3 -m venv .venv
```

Aktiviere sie und aktualisiere `pip`:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
```

Falls die Anwendung eine `requirements.txt` enthält:

```bash
python -m pip install -r requirements.txt
```

Wenn keine Abhängigkeitsdatei vorhanden ist, prüfe die Dokumentation und den tatsächlichen Projektcode.

#### 6. Grafische Oberfläche starten

Unter Windows 11 und unterstützten Windows-10-Konfigurationen kann WSLg Linux-GUI-Anwendungen bereitstellen.

Prüfe, ob der Programmeinstiegspunkt vorhanden ist:

```bash
ls -l main.py
```

Starte die Anwendung innerhalb der aktivierten virtuellen Umgebung:

```bash
python main.py
```

Wenn `No module named PyQt6` erscheint, fehlen Python-Abhängigkeiten in der aktiven Umgebung.

Wenn `libpulse.so.0` fehlt, installiere:

```bash
sudo apt install -y libpulse0
```

Wenn kein Fenster erscheint, prüfe die WSL-Version, die grafische Unterstützung und die vollständige Fehlermeldung.

#### 7. OSCam-Emu-Build vorbereiten

Die Anforderungen für das eigentliche Build hängen vom verwendeten Skript und SDK ab.

Falls ein Build-Skript namens `s3` vorhanden ist, prüfe es zunächst:

```bash
file ./s3
head -n 1 ./s3
bash -n ./s3
```

Wenn die Datei Windows-Zeilenenden (`CRLF`) verwendet, kann sie mit folgendem Befehl korrigiert werden:

```bash
dos2unix ./s3
```

Weitere Shell-Skripte können gezielt geprüft werden. Konvertiere nur Dateien, bei denen eine Korrektur erforderlich ist.

Wenn die Syntaxprüfung erfolgreich ist, verwende das Skript entsprechend seiner eigenen Dokumentation. Beispielsweise kann ein Menüaufruf vorgesehen sein:

```bash
chmod +x ./s3
./s3 menu
```

Dieser Aufruf gilt nur, wenn das Skript und der betreffende Menümodus in der verwendeten Projektversion vorhanden sind.

> **Hinweis zum OpenPLi-/OpenEmbedded-SDK:** Die allgemeinen Ubuntu-Pakete ersetzen kein vollständiges Cross-Compile-SDK. Je nach Zielplattform werden ein passender Cross-Compiler, SDK-Umgebungsvariablen, Bibliotheken, Header und weitere Abhängigkeiten benötigt.

## 🧰 Windows-Batch-Dateien und Linux-Shell-Skripte

Windows-Batch-Dateien (`.bat` und `.cmd`) und Linux-Shell-Skripte (`.sh`) sind unterschiedliche Skriptformate.

### Unter Windows

Prüfe die vorhandenen Batch-Dateien im Projektverzeichnis:

```bat
dir *.bat
dir *.cmd
```

Führe nur ein Startskript aus, das in der verwendeten Version vorhanden ist und für Windows vorgesehen ist.

### Unter Linux und WSL2

Suche nach Shell-Skripten:

```bash
find . -maxdepth 3 -type f -name "*.sh" -not -path "./.git/*"
```

Ein Shell-Skript kann beispielsweise so gestartet werden:

```bash
bash ./skript.sh
```

Wenn das Skript ausführbar sein soll:

```bash
chmod +x ./skript.sh
./skript.sh
```

Ersetze `skript.sh` durch den tatsächlichen Dateinamen.

Eine `.bat`-Datei ist kein natives Linux-Startskript. Verwende unter WSL den vorgesehenen Python-Einstiegspunkt oder ein vorhandenes Shell-Skript. Windows-Programme können bei entsprechender WSL-Konfiguration separat über Windows gestartet werden.

## 🔧 CRLF-Zeilenenden korrigieren

Windows verwendet häufig `CRLF`-Zeilenenden, während Linux-Shell-Skripte üblicherweise `LF` verwenden.

Typische Fehlermeldungen sind:

```text
/bin/bash^M: bad interpreter: No such file or directory
```

```text
$'\r': command not found
```

Prüfe das betroffene Skript:

```bash
file ./skript.sh
```

Konvertiere es bei Bedarf:

```bash
dos2unix ./skript.sh
```

Prüfe weitere Dateien einzeln, wenn sie von Shell-Skripten eingebunden werden.

**Wichtig:** Verwende `dos2unix` nicht pauschal auf ZIP-Dateien, Bildern, Binärdateien oder kompilierten Dateien.

## 📦 Zusätzliche OSCam-Build-Abhängigkeiten

Je nach Build-Skript können zusätzliche Entwicklungsbibliotheken erforderlich sein. Beispiele für mögliche Pakete sind:

```bash
sudo apt install -y \
    autoconf \
    automake \
    autoconf-archive \
    libtool-bin \
    pkg-config \
    jq \
    bzip2 \
    libssl-dev \
    libpcsclite-dev \
    libccid \
    libusb-1.0-0-dev
```

Diese Pakete sind **nicht für jeden Build zwingend erforderlich**. Installiere nur die Pakete, die das jeweilige Build-Skript oder SDK benötigt.

Bei einem fehlenden Paket kannst du dessen Verfügbarkeit prüfen:

```bash
sudo apt update
apt-cache policy libusb-1.0-0-dev
```

## 🛠️ Fehlerbehebung

| Problem | Mögliche Lösung |
| --- | --- |
| `py` wird unter Windows nicht erkannt | Python installieren und PATH prüfen. |
| `python3` fehlt | Python über den Linux-Paketmanager installieren. |
| `python` wird nach dem Öffnen eines Terminals nicht gefunden | Die virtuelle Umgebung mit `source .venv/bin/activate` aktivieren. |
| `venv` fehlt | `sudo apt install -y python3-venv` ausführen. |
| `No module named PyQt6` | Abhängigkeiten in der aktiven virtuellen Umgebung installieren. |
| `libpulse.so.0` fehlt | `sudo apt install -y libpulse0` ausführen. |
| `curl: command not found` | `sudo apt install -y curl` ausführen. |
| `git: command not found` | `sudo apt install -y git` ausführen. |
| `meson: command not found` | `sudo apt install -y meson` ausführen. |
| `ninja: command not found` | `sudo apt install -y ninja-build` ausführen. |
| `/bin/bash^M: bad interpreter` | Das betroffene Shell-Skript mit `dos2unix` korrigieren. |
| `Permission denied` | Pfad, Dateirechte und Startbefehl prüfen. |
| Eine `.bat`-Datei startet nicht unter Linux | Das für WSL oder Linux vorgesehene Startverfahren verwenden. |
| Build-Werkzeuge oder Header fehlen | Build-Skript, SDK-Dokumentation und Fehlermeldung prüfen. |
| GUI öffnet sich nicht | WSLg, GUI-Abhängigkeiten, virtuelle Umgebung und Fehlermeldung prüfen. |
| Installation schlägt fehl | Python-Version, Netzwerk, Schreibrechte und vollständige Fehlermeldung kontrollieren. |

## 🔄 Aktualisierung

Vor jedem Update:

- Sichere Konfigurationen und eigene Änderungen.
- Sichere wichtige Patches und Backups.
- Prüfe, ob Dateien überschrieben werden.
- Prüfe, ob der Installer alle benötigten Dateien aktualisiert.
- Prüfe die Python-Abhängigkeiten nach der Aktualisierung.

Eine erneute Installation garantiert nicht, dass alte Dateien entfernt oder sämtliche vorhandenen Dateien aktualisiert werden.

## 🔒 Sicherheit

- Quellcode vor der Ausführung prüfen.
- Vor Patch-Operationen und Updates Backups erstellen.
- Änderungen vor einem Commit mit `git diff` kontrollieren.
- GitHub-Tokens und Zugangsdaten niemals veröffentlichen.
- Bereinigungsoperationen nur in geprüften Verzeichnissen ausführen.
- Installationsskripte ausschließlich aus vertrauenswürdigen Quellen beziehen.
- Vor dem Überschreiben prüfen, ob lokale Änderungen erhalten bleiben müssen.
- Symbolische Links und externe Verzeichnisse bei Backups sorgfältig behandeln.

## 🤝 Mitwirken

Fehlerberichte, reproduzierbare Testfälle und Pull Requests sind willkommen.

Bitte gib bei Fehlern folgende Informationen an:

- Reproduktionsschritte
- Betriebssystem und gegebenenfalls WSL-Version
- Python-Version
- Verwendetes SDK oder Build-Profil
- Relevante Fehlermeldungen und Build-Logs
- Betroffene Skripte und deren Zeilenenden, sofern relevant

Entferne Zugangsdaten, Tokens und andere vertrauliche Informationen vor dem Teilen.

## ⚠️ Disclaimer

Dieses Projekt wird ohne Garantie bereitgestellt. Kompatibilität und Funktionalität hängen vom Betriebssystem, Quellcode, SDK, der Firmware und der jeweiligen Konfiguration ab.

Sichere wichtige Dateien, bevor du Änderungen an einer bestehenden Installation vornimmst. Eine erfolgreiche Kompilierung garantiert nicht, dass die erzeugte Binärdatei auf jedem Zielgerät lauffähig ist.

## 📦 Projektlinks

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [Python herunterladen](https://www.python.org/downloads/)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** is a Python-based desktop toolkit for managing OSCam-Emu patches and related Git workflows.

The application provides a graphical interface for supported patch, backup, configuration, and build tasks. The available functionality depends on the installed version, configuration, and external tools.

## ✨ Features

- 🧩 Create, validate, and apply patches
- 📦 Create backups and export them as ZIP archives
- ✏️ Edit patch headers and metadata
- 🖥️ PyQt6 graphical interface
- 🌐 Git and GitHub features where configured and available
- 📁 Select and persist the working directory
- ⚙️ Manage Python environments and dependencies
- 🛠️ Linux and WSL2 support for suitable build workflows
- 🔍 Check build tools and dependencies
- 🔒 Exclude supported files and directories from backups

## 📋 Requirements

### Windows

- Windows 10 or Windows 11
- A supported Python version
- Internet access for installation downloads and any required GitHub operations
- Write permissions for the installation and working directories

### Linux and WSL2

- A supported Linux distribution, such as Ubuntu
- Python 3, `pip`, and `venv`
- PyQt6 and the Python dependencies actually required by the project
- System libraries for the graphical interface
- Git and any additional build tools required
- WSLg or another suitable graphical environment when running the GUI under WSL

OSCam-Emu builds may require additional libraries, headers, compilers, or a project-specific SDK.

Download Python: https://www.python.org/downloads/

> **Important:** Windows Python and Python inside WSL2 are separate installations. Python packages installed on Windows are not automatically available to Linux applications.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1. Check Python

Open Command Prompt (`Win + R` → `cmd`) and run:

```bat
py -3 --version
```

If the command is not recognized, install Python from the official website and check your PATH configuration.

#### 2. Download the installer

If the installer is available in the repository version you are using, it can be downloaded as follows:

```bat
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py"
```

Verify the source and then run it:

```bat
py -3 "%TEMP%\oscam_installer.py"
```

Use this download path only if the installer actually exists at that address and is intended for your version.

#### 3. Complete setup

- Follow the installer's instructions.
- Choose the desired installation directory.
- Review overwrite prompts carefully.
- Back up existing configuration and local changes.
- Check the output for missing dependencies.

#### 4. Launch the application

Navigate to the actual installation directory.

First, check which startup files are available:

```bat
dir *.bat
dir *.py
```

Run the startup script intended for your version. If `start_windows.bat` exists:

```bat
start_windows.bat
```

Not every version necessarily includes the same startup files.

### 🐧 Linux: Ubuntu, Debian, and Linux Mint

#### 1. Install system packages

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

For build workflows that use Meson and Ninja:

```bash
sudo apt install -y meson ninja-build gettext
```

These packages provide a basic Python environment, compiler tools, and selected system libraries. They do not replace a project-specific SDK installation.

#### 2. Open the project directory

Navigate to the directory containing the project.

Example using a generic path:

```bash
cd "/path/to/project"
```

Check the contents:

```bash
pwd
ls -la
```

Replace the example path with your actual installation location.

#### 3. Set up the Python environment

Create the virtual environment if it does not already exist:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Upgrade `pip`:

```bash
python -m pip install --upgrade pip
```

Install dependencies using the files actually provided by the project.

If `requirements.txt` exists:

```bash
python -m pip install -r requirements.txt
```

If it does not exist, check the project installation instructions and Python imports. Do not guess undocumented dependencies.

#### 4. Launch the application

Check that the entry point exists:

```bash
ls -l main.py
```

If the file exists and the dependencies are installed:

```bash
python main.py
```

Activate the virtual environment again in every new terminal session.

### 🐧 Windows with WSL2 and Ubuntu

WSL2 provides a Linux environment on Windows. Linux build tools and Python dependencies must be installed inside the WSL distribution actually being used.

#### 1. Check WSL

Open PowerShell on Windows:

```powershell
wsl --status
wsl --list --verbose
```

If Ubuntu is not installed, installation can be started from an elevated PowerShell session:

```powershell
wsl --install -d Ubuntu
```

Complete the Windows setup process if necessary.

#### 2. Open Ubuntu

Open Ubuntu from the Windows Start menu or launch it from PowerShell:

```powershell
wsl -d Ubuntu
```

Run all subsequent Linux commands inside the Ubuntu terminal.

#### 3. Install WSL dependencies

```bash
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    git \
    curl \
    ca-certificates \
    dos2unix \
    libpulse0
```

For additional build workflows:

```bash
sudo apt install -y meson ninja-build gettext
```

**Why `libpulse0`?** This package provides the runtime library `libpulse.so.0`, which may be needed by GUI or audio components. Install additional libraries according to the actual error messages.

If `sudo` requests a password, use the password for your Ubuntu Linux user. No characters are displayed while typing. This is normal. The Ubuntu password is not automatically your Windows password.

#### 4. Choose the project directory

Navigate to the directory where the project is actually stored.

For a Windows drive, WSL commonly provides access through `/mnt/<drive>/...`. Example:

```bash
cd "/mnt/<drive>/path/to/project"
```

Replace the example path with your actual location.

Alternatively, store the project in the WSL Linux filesystem.

Verify the directory:

```bash
pwd
ls -la
```

#### 5. Set up Python

If the virtual environment does not exist:

```bash
python3 -m venv .venv
```

Activate it and upgrade `pip`:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
```

If the application contains `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

If no dependency file exists, check the documentation and actual project code.

#### 6. Launch the graphical interface

WSLg can provide Linux GUI support under Windows 11 and supported Windows 10 configurations.

Check that the entry point exists:

```bash
ls -l main.py
```

Launch the application with the virtual environment activated:

```bash
python main.py
```

If `No module named PyQt6` appears, Python dependencies are missing from the active environment.

If `libpulse.so.0` is missing, install:

```bash
sudo apt install -y libpulse0
```

If no window appears, check the WSL version, graphical support, and complete error message.

#### 7. Prepare OSCam-Emu builds

Build requirements depend on the script and SDK being used.

If a build script named `s3` exists, check it first:

```bash
file ./s3
head -n 1 ./s3
bash -n ./s3
```

If the file uses Windows line endings (`CRLF`), correct it with:

```bash
dos2unix ./s3
```

Other shell scripts can be checked individually. Convert only files that need correction.

If the syntax check succeeds, follow the script's own documentation. For example, it may provide a menu command:

```bash
chmod +x ./s3
./s3 menu
```

Use this command only if the script and menu mode exist in the version being used.

> **OpenPLi/OpenEmbedded SDK:** Standard Ubuntu packages do not replace a complete cross-compilation SDK. Depending on the target platform, a cross-compiler, SDK environment variables, libraries, headers, and other dependencies may be required.

## 🧰 Windows batch files and Linux shell scripts

Windows batch files (`.bat` and `.cmd`) and Linux shell scripts (`.sh`) are different script formats.

### On Windows

Check for batch files in the project directory:

```bat
dir *.bat
dir *.cmd
```

Run only a startup script that exists in the version being used and is intended for Windows.

### On Linux and WSL2

Search for shell scripts:

```bash
find . -maxdepth 3 -type f -name "*.sh" -not -path "./.git/*"
```

A shell script can be started with:

```bash
bash ./script.sh
```

To make it executable:

```bash
chmod +x ./script.sh
./script.sh
```

Replace `script.sh` with the actual filename.

A `.bat` file is not a native Linux startup script. Under WSL, use the intended Python entry point or an existing shell script. Windows programs can be launched separately when the WSL configuration supports it.

## 🔧 Fixing CRLF line endings

Windows commonly uses `CRLF` line endings, while Linux shell scripts normally use `LF`.

Typical errors include:

```text
/bin/bash^M: bad interpreter: No such file or directory
```

```text
$'\r': command not found
```

Check the affected script:

```bash
file ./script.sh
```

Convert it if necessary:

```bash
dos2unix ./script.sh
```

Check other files individually if they are sourced by shell scripts.

**Important:** Do not run `dos2unix` indiscriminately on ZIP files, images, binary files, or compiled files.

## 📦 Additional OSCam build dependencies

Depending on the build script, additional development libraries may be required. Examples of possible packages include:

```bash
sudo apt install -y \
    autoconf \
    automake \
    autoconf-archive \
    libtool-bin \
    pkg-config \
    jq \
    bzip2 \
    libssl-dev \
    libpcsclite-dev \
    libccid \
    libusb-1.0-0-dev
```

These packages are **not required for every build**. Install only the packages required by the specific build script or SDK.

If a package is missing, check its availability:

```bash
sudo apt update
apt-cache policy libusb-1.0-0-dev
```

## 🛠️ Troubleshooting

| Problem | Possible solution |
| --- | --- |
| `py` is not recognized on Windows | Install Python and check PATH. |
| `python3` is missing | Install Python using the Linux package manager. |
| `python` is not found in a new terminal | Activate the virtual environment with `source .venv/bin/activate`. |
| `venv` is missing | Run `sudo apt install -y python3-venv`. |
| `No module named PyQt6` | Install dependencies in the active virtual environment. |
| `libpulse.so.0` is missing | Run `sudo apt install -y libpulse0`. |
| `curl: command not found` | Run `sudo apt install -y curl`. |
| `git: command not found` | Run `sudo apt install -y git`. |
| `meson: command not found` | Run `sudo apt install -y meson`. |
| `ninja: command not found` | Run `sudo apt install -y ninja-build`. |
| `/bin/bash^M: bad interpreter` | Correct the affected shell script with `dos2unix`. |
| `Permission denied` | Check the path, file permissions, and startup command. |
| A `.bat` file does not start under Linux | Use the intended WSL or Linux startup method. |
| Build tools or headers are missing | Check the build script, SDK documentation, and error message. |
| GUI does not open | Check WSLg, GUI dependencies, the virtual environment, and the error message. |
| Installation fails | Check Python version, network access, write permissions, and the complete error message. |

## 🔄 Updating

Before every update:

- Back up configuration and local changes.
- Back up important patches and archives.
- Check whether files may be overwritten.
- Verify that the installer updates all required files.
- Recheck Python dependencies after updating.

Reinstalling does not guarantee that old files are removed or all existing files are updated.

## 🔒 Security

- Review source code before running it.
- Back up files before patching and updating.
- Review changes with `git diff` before committing.
- Never publish GitHub tokens or credentials.
- Run cleanup operations only in verified directories.
- Obtain installation scripts only from trusted sources.
- Check whether local changes must be preserved before overwriting.
- Handle symbolic links and external directories carefully when creating backups.

## 🤝 Contributing

Bug reports, reproducible test cases, and pull requests are welcome.

When reporting an issue, include:

- Steps to reproduce
- Operating system and WSL version, if applicable
- Python version
- SDK or build profile
- Relevant error messages and build logs
- Affected scripts and their line endings, where relevant

Remove credentials, tokens, and other confidential information before sharing.

## ⚠️ Disclaimer

This project is provided without warranties. Compatibility and functionality depend on the operating system, source code, SDK, firmware, and configuration.

Back up important files before modifying an existing installation. Successful compilation does not guarantee that the resulting binary will run on every target device.

## 📦 Project Links

- [GitHub Repository](https://github.com/speedy005/oscam_patch_manager_new)
- [Download Python](https://www.python.org/downloads/)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡  
**Built with Python 3 · PyQt6 · Git · GitHub**

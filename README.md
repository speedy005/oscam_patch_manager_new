# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**\
_Install. Manage. Patch. Publish._

A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patches to applying changes locally and publishing updates to GitHub.

Ein Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches – von der Erstellung und Prüfung bis zur lokalen Anwendung und Veröffentlichung auf GitHub.

🇩🇪 Deutsch · 🇬🇧 English · 📦 GitHub Repository

---

# 🇩🇪 Deutsch

## 📖 Über das Projekt

**OSCam Emu Patch Manager** ist ein Python-basiertes Desktop-Werkzeug zur Verwaltung von OSCam-Emu-Patches und zugehörigen Git-Arbeitsabläufen.

Es unterstützt den Patch-Workflow von der Erstellung und Prüfung über die lokale Anwendung bis hin zur Verwaltung und Veröffentlichung von Änderungen. Welche Funktionen verfügbar sind, hängt von der tatsächlichen Implementierung, der Konfiguration und den verwendeten Build-Werkzeugen ab.

## ✨ Funktionen

- 🧩 Patches erstellen, prüfen und anwenden
- 📦 Backups erstellen und als ZIP-Datei exportieren
- ✏️ Patch-Header und Metadaten bearbeiten
- 🖥️ Grafische Oberfläche mit PyQt6
- 🌐 Git- und GitHub-Funktionen, sofern implementiert und konfiguriert
- 🐍 Python-Installer für Windows und Linux
- 🌍 Deutsche und englische Sprachoptionen, sofern unterstützt
- ⚙️ Python-Umgebungen und Abhängigkeiten einrichten
- 🛠️ Linux- und WSL2-Unterstützung für Build-Workflows
- 🔍 Build-Werkzeuge und Abhängigkeiten prüfen
- 🔒 Projektdateien und konfigurierte Verzeichnisse bei Backups gezielt ausschließen

## 📋 Voraussetzungen

- Python **3.9 oder neuer**, sofern von der konkreten Anwendung unterstützt
- Windows 10/11 oder eine unterstützte Linux-Distribution
- Internetverbindung für Downloads und gegebenenfalls GitHub-Funktionen
- Schreibrechte im Installationsverzeichnis
- Git, sofern von den verwendeten Funktionen benötigt
- Ubuntu unter WSL2 für Build-Workflows, die ausdrücklich WSL verwenden
- Zusätzliche Compiler, Bibliotheken und Header, sofern sie vom SDK oder Build-Skript benötigt werden

Python herunterladen: [python.org](<https://www.python.org/downloads/>)

Unter Windows während der Installation nach Möglichkeit **Add Python to PATH** aktivieren.

> **Wichtig:** Die Python-Anwendung unter Windows und die Linux-Build-Umgebung unter WSL2 sind getrennte Umgebungen. Benötigte Linux-Pakete müssen innerhalb der Ubuntu-Distribution installiert sein, in der das Build-Skript ausgeführt wird.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1\. Python überprüfen

Öffne die Eingabeaufforderung (`Win + R` → `cmd`) und führe aus:

bat

```
py -3 --version
```

Falls `py` nicht erkannt wird, installiere Python über [python.org](<https://www.python.org/downloads/>) und prüfe den PATH.

#### 2\. Installer herunterladen und starten

bat

```
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

Der Befehl lädt den Installer herunter und startet ihn mit Python 3.

#### 3\. Installation abschließen

- Folge den Anweisungen des Installers.
- Wähle das gewünschte Installationsverzeichnis.
- Prüfe Überschreibungsabfragen sorgfältig.
- Sichere vorhandene Konfigurationsdateien und eigene Änderungen.
- Kontrolliere die Ausgabe auf fehlende Python-Abhängigkeiten.

#### 4\. Anwendung starten

Wechsle in das tatsächlich verwendete Installationsverzeichnis. Wenn das Startskript vorhanden ist, führe es aus:

bat

```
start_windows.bat
```

Der Dateiname kann je nach Projektversion abweichen. Verwende nur ein Startskript, das im Installationsverzeichnis tatsächlich vorhanden ist.

### 🐧 Linux: Ubuntu, Debian und Linux Mint

#### 1\. Paketlisten aktualisieren

bash

```
sudo apt update
```

#### 2\. Grundlegende Pakete installieren

bash

```
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  curl \
  ca-certificates \
  git \
  dos2unix \
  meson \
  ninja-build \
  gettext
```

Diese Pakete stellen die grundlegende Python-Umgebung, Compiler-Werkzeuge, Git und zusätzliche Build-Hilfsmittel bereit.

| Paket | Zweck |
| --- | --- |
| `python3` | Python-Laufzeit |
| `python3-venv` | Virtuelle Python-Umgebungen |
| `python3-pip` | Python-Paketinstallation |
| `python3-dev` | Python-Header für native Erweiterungen |
| `build-essential` | GCC, G++, Make und grundlegende Build-Werkzeuge |
| `curl` | Dateien über HTTP(S) herunterladen |
| `ca-certificates` | Zertifikate für sichere HTTPS-Verbindungen |
| `git` | Versionsverwaltung und Patch-Arbeitsabläufe |
| `dos2unix` | Windows-Zeilenenden in Unix-Zeilenenden umwandeln |
| `meson` | Build-System für Projekte, die Meson verwenden |
| `ninja-build` | Build-Werkzeug, häufig zusammen mit Meson |
| `gettext` | Übersetzungs- und Internationalisierungswerkzeuge |

**Hinweis:** Diese Liste deckt grundlegende Werkzeuge ab. Sie garantiert nicht, dass alle Abhängigkeiten eines bestimmten OSCam-Emu-Builds oder SDKs installiert sind.

#### 3\. Installation überprüfen

bash

```
python3 --version
python3 -m pip --version
git --version
gcc --version
g++ --version
make --version
meson --version
ninja --version
gettext --version
```

Wenn ein einzelner Befehl mit `command not found` abbricht, installiere das zugehörige Paket und prüfe anschließend erneut.

#### 4\. Installer herunterladen und starten

bash

```
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

Folge den Anweisungen und prüfe, ob der Installer Abhängigkeiten erfolgreich eingerichtet hat.

#### 5\. Anwendung starten

Wechsle in das Installationsverzeichnis. Wenn das Startskript vorhanden ist:

bash

```
chmod +x start_linux.sh
./start_linux.sh
```

Der Dateiname ist abhängig von der tatsächlich installierten Projektversion.

### 🐧 Windows mit WSL2 und Ubuntu

WSL2 ermöglicht die Ausführung einer Linux-Umgebung unter Windows. Für Linux-Builds müssen die benötigten Werkzeuge in der tatsächlich verwendeten WSL-Distribution installiert sein.

#### 1\. WSL-Status prüfen

Öffne PowerShell unter Windows:

powershell

```
wsl --status
wsl --list --verbose
```

Stelle sicher, dass Ubuntu installiert ist und die vorgesehene WSL-Version verwendet wird.

Falls Ubuntu noch nicht installiert ist, kann eine Installation über PowerShell mit Administratorrechten erforderlich sein:

powershell

```
wsl --install -d Ubuntu
```

Starte Windows gegebenenfalls neu und schließe die Ubuntu-Ersteinrichtung ab.

#### 2\. Ubuntu öffnen

Öffne Ubuntu über das Windows-Startmenü oder führe in PowerShell aus:

powershell

```
wsl -d Ubuntu
```

Führe die folgenden Linux-Befehle anschließend **im Ubuntu-Terminal** aus, nicht in PowerShell und nicht in der Windows-Eingabeaufforderung.

#### 3\. Linux-Werkzeuge installieren

bash

```
sudo apt update

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  curl \
  ca-certificates \
  git \
  dos2unix \
  meson \
  ninja-build \
  gettext
```

Falls `sudo` ein Passwort verlangt, gib das bei der Ubuntu-Ersteinrichtung für deinen Linux-Benutzer festgelegte Passwort ein. Bei der Eingabe werden keine Zeichen angezeigt. Das ist normal.

**Das Ubuntu-Passwort ist nicht automatisch dein Windows-Passwort.**

#### 4\. Werkzeuge überprüfen

bash

```
python3 --version
python3 -m pip --version
git --version
gcc --version
g++ --version
make --version
meson --version
ninja --version
gettext --version
```

#### 5\. In das Projektverzeichnis wechseln

Wechsle in das Verzeichnis, in dem sich das Projekt tatsächlich befindet.

Für ein Projekt auf einem Windows-Laufwerk ist der Zugriff über `/mnt/<laufwerksbuchstabe>/...` möglich. Das folgende Beispiel ist nur ein Muster und muss an das eigene Verzeichnis angepasst werden:

bash

```
cd "/mnt/<laufwerksbuchstabe>/Pfad/zum/Projekt"
```

Alternativ kann das Projekt in einem Linux-Verzeichnis innerhalb von WSL gespeichert werden.

Prüfe danach das Verzeichnis:

bash

```
pwd
ls -la
```

Wenn die Datei `s3` vorhanden ist, kannst du sie mit den folgenden Schritten prüfen.

#### 6\. Build-Skript vorbereiten

Prüfe zunächst, ob Windows-Zeilenenden vorhanden sind:

bash

```
file ./s3
```

Falls das Skript mit CRLF-Zeilenenden gespeichert ist, konvertiere es:

bash

```
dos2unix ./s3
```

Um weitere Shell-Skripte im Projekt zu korrigieren, verwende:

bash

```
find . -type f -name "*.sh" -not -path "./.git/*" \
  -exec dos2unix {} +
```

Auch das Hauptskript `s3` kann unabhängig von der Dateiendung betroffen sein. Daher wird es separat konvertiert.

Prüfe anschließend die erste Zeile:

bash

```
head -n 1 ./s3
```

Prüfe die Shell-Syntax:

bash

```
bash -n ./s3
```

Wenn die Syntaxprüfung erfolgreich ist, starte das Skript entsprechend seiner Dokumentation, beispielsweise:

bash

```
chmod +x ./s3
./s3 menu
```

Falls das Skript weitere Shell-Dateien lädt, müssen auch diese korrekte Unix-Zeilenenden besitzen.

#### 7\. Fehlende Build-Abhängigkeiten behandeln

Wenn ein Build beispielsweise mit folgender Meldung abbricht:

text

```
meson: command not found
```

installiere Meson und Ninja:

bash

```
sudo apt update
sudo apt install -y meson ninja-build
```

Prüfe danach:

bash

```
meson --version
ninja --version
```

Weitere fehlende Programme müssen anhand der jeweiligen Fehlermeldung ermittelt werden.

> **OpenPLi-/OpenEmbedded-SDK:** Die allgemeinen Ubuntu-Pakete ersetzen kein vollständiges SDK. Ein Build kann zusätzlich einen passenden Cross-Compiler, SDK-Umgebungsvariablen, Bibliotheken, Header und projektspezifische Abhängigkeiten benötigen.

## 🔧 CRLF-Zeilenenden korrigieren

Ein häufiges Problem beim Ausführen von Shell-Skripten aus Windows-Verzeichnissen sind Windows-Zeilenenden (`CRLF`) anstelle der unter Linux üblichen Unix-Zeilenenden (`LF`).

Typische Fehlermeldungen:

text

```
/bin/bash^M: bad interpreter: No such file or directory
```

text

```
$'\r': command not found
```

text

```
syntax error near unexpected token `$'{\r''
```

### Empfohlene Vorgehensweise

Wechsle zuerst in das tatsächliche Projektverzeichnis:

bash

```
cd "/Pfad/zum/Projekt"
```

Dies ist nur ein Beispiel. Verwende den Pfad, in dem sich dein Projekt befindet.

Konvertiere das Hauptskript:

bash

```
dos2unix ./s3
```

Konvertiere alle regulären Shell-Skripte außerhalb von `.git`:

bash

```
find . -type f -name "*.sh" -not -path "./.git/*" \
  -exec dos2unix {} +
```

Wenn das Projekt zusätzlich Dateien ohne `.sh`-Endung enthält, die von Shell-Skripten eingebunden werden, müssen diese bei Bedarf ebenfalls korrigiert werden.

Eine Suche nach Dateien mit CRLF-Zeilenenden ist beispielsweise mit folgendem Befehl möglich:

bash

```
grep -rlIZ $'\r' . --exclude-dir=.git
```

Die Ausgabe enthält Dateien, in denen das Suchmuster gefunden wurde. Eine gefundene Datei muss nicht zwingend ein Shell-Skript sein; deshalb sollten Dateien nicht pauschal ohne Prüfung konvertiert werden.

Wenn ausschließlich bekannte Textdateien mit CRLF-Zeilenenden korrigiert werden sollen, kann `dos2unix` gezielt auf diese Dateien angewendet werden.

**Wichtig:** Verwende `dos2unix` nicht pauschal auf Binärdateien, ZIP-Archiven, Bildern oder kompilierten Dateien.

## 📦 Zusätzliche Abhängigkeiten für OSCam-Builds

Je nach Build-Skript und verwendeten Bibliotheken können zusätzliche Pakete notwendig sein.

Einige häufig benötigte Werkzeuge und Entwicklungsbibliotheken sind:

bash

```
sudo apt install -y \
  gcc \
  g++ \
  make \
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
  lib32z1
```

Diese Liste ist optional und ersetzt keine Prüfung der konkreten Build-Anforderungen.

Für USB-bezogene Funktionen wird häufig das Entwicklungspaket `libusb-1.0-0-dev` benötigt. Der korrekte Paketname unter Ubuntu ist nicht `libusb-1.0.0-dev`.

Installation:

bash

```
sudo apt install -y libusb-1.0-0-dev
```

Falls Ubuntu das Paket nicht findet, prüfe zunächst die Paketquellen und die Verfügbarkeit für die verwendete Distribution:

bash

```
sudo apt update
apt-cache policy libusb-1.0-0-dev
apt-cache search libusb
```

Nicht jedes Paket wird in jeder Distribution oder jedem Repository angeboten. Installiere keine beliebigen Pakete mit ähnlichen Namen, ohne zu prüfen, ob sie tatsächlich die benötigte Bibliothek bereitstellen.

### Paketinstallation reparieren

Falls eine Paketinstallation unterbrochen wurde:

bash

```
sudo dpkg --configure -a
sudo apt --fix-broken install
sudo apt update
```

Danach kannst du die gewünschte Paketinstallation erneut ausführen.

Wenn ein Paketmanager-Prozess nicht mehr reagiert, prüfe zuerst den Status:

bash

```
ps aux | grep -E 'apt|dpkg' | grep -v grep
```

Beende keine Paketmanager-Prozesse unüberlegt. Eine unterbrochene Installation kann den Paketstatus beschädigen. Wenn ein Prozess lediglich angehalten wurde, muss zunächst geklärt werden, warum er angehalten wurde, bevor er fortgesetzt oder beendet wird.

## ⚙️ Installer und ausgeschlossene Dateien

Der Installer lädt ausgewählte Dateien von GitHub herunter. Die tatsächlich heruntergeladenen Dateien, die Behandlung vorhandener Dateien und die Einrichtung der Python-Umgebung hängen von der jeweiligen Implementierung des Installers ab.

Wenn der Installer eine Ausschlussliste verwendet, muss diese mit der tatsächlichen Implementierung übereinstimmen.

Die hier dokumentierte Beispiel-Ausschlussliste umfasst:

- **Dateiendungen:** `.png`, `.zip`, `.md`, `.php`
- **Verzeichnisse:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer-Dateien:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Wichtig:** Ausgeschlossene PNG-Dateien können Icons oder andere notwendige Ressourcen enthalten. Werden sie nicht installiert, kann die Anwendung möglicherweise unvollständig sein. Prüfe deshalb, ob diese Ausschlüsse tatsächlich zum gewünschten Installationsverhalten passen.

Wenn eine virtuelle Umgebung verwendet wird, sollten Python-Abhängigkeiten möglichst innerhalb dieser Umgebung installiert werden.

Beispiel:

bash

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Falls das Projekt eine `requirements.txt` enthält:

bash

```
python -m pip install -r requirements.txt
```

Installiere keine erfundene oder nicht vorhandene Abhängigkeitsdatei. Prüfe zuerst, welche Datei das Projekt tatsächlich verwendet.

## 🔄 Aktualisierung

Lade die aktuelle Version über den vorgesehenen Installationsweg herunter oder aktualisiere sie mit dem im Projekt vorgesehenen Mechanismus.

Vor jedem Update:

- Sichere eigene Änderungen und Konfigurationsdateien.
- Sichere wichtige Patches und Backups.
- Prüfe, ob lokale Änderungen überschrieben werden könnten.
- Prüfe, ob der Installer tatsächlich alle benötigten Dateien aktualisiert.
- Prüfe die Abhängigkeiten nach dem Update erneut.

Eine erneute Installation garantiert nicht, dass alte Dateien ersetzt oder nicht mehr benötigte Dateien entfernt werden. Abweichungen zwischen der installierten Version und der aktuellen Projektversion müssen gegebenenfalls manuell geprüft werden.

## 🛠️ Fehlerbehebung

| Problem | Lösung |
| --- | --- |
| `py` wird unter Windows nicht erkannt | Python installieren und PATH prüfen. |
| `python3` fehlt | Python über den Paketmanager der verwendeten Linux-Distribution installieren. |
| `python3-pip` fehlt | `sudo apt update` und `sudo apt install -y python3-pip` ausführen. |
| `venv` fehlt | `sudo apt install -y python3-venv` ausführen. |
| `curl: command not found` | `sudo apt install -y curl` ausführen. |
| `git: command not found` | `sudo apt install -y git` ausführen. |
| `meson: command not found` | `sudo apt install -y meson` ausführen. |
| `ninja: command not found` | `sudo apt install -y ninja-build` ausführen. |
| `gettext` fehlt | `sudo apt install -y gettext` ausführen. |
| `libusb-1.0.0-dev` wird nicht gefunden | Den korrekten Paketnamen `libusb-1.0-0-dev` prüfen. |
| `/bin/bash^M: bad interpreter` | Das betroffene Skript mit `dos2unix` konvertieren. |
| `$'\r': command not found` | CRLF-Zeilenenden in den betroffenen Textdateien korrigieren. |
| `./s3: No such file or directory` | Mit `pwd` und `ls -la` das aktuelle Verzeichnis und den tatsächlichen Dateinamen prüfen. |
| `Permission denied` | Berechtigungen prüfen und gegebenenfalls `chmod +x ./s3` verwenden. |
| `sudo: Authentication failed` | Das Ubuntu-Linux-Passwort verwenden; die Eingabe bleibt unsichtbar. |
| `apt` hängt oder wurde unterbrochen | Paketmanager-Status prüfen und bei Bedarf `sudo dpkg --configure -a` ausführen. |
| Compiler oder Header fehlen | Build-Skript, SDK-Dokumentation und erforderliche Entwicklungsbibliotheken prüfen. |
| Python-Abhängigkeiten fehlen | `requirements.txt` und die Ausgabe des Installers prüfen, sofern vorhanden. |
| `SyntaxError` oder `UnicodeDecodeError` | Die betroffene Datei prüfen und gegebenenfalls in UTF-8 erneut speichern. |
| Build schlägt unter WSL fehl | Prüfen, ob die Pakete in der richtigen WSL-Distribution installiert sind. |
| Installation schlägt fehl | Internetverbindung, Schreibrechte, Python-Version und vollständige Fehlermeldung kontrollieren. |

## 🔒 Sicherheit

- Quellcode vor der Ausführung prüfen.
- Vor Patch-Operationen und Updates Sicherungen erstellen.
- Änderungen vor dem Commit mit `git diff` kontrollieren.
- GitHub-Tokens und Zugangsdaten niemals veröffentlichen.
- Bereinigungsoperationen nur in geprüften Verzeichnissen durchführen.
- Installationsskripte ausschließlich aus vertrauenswürdigen Quellen beziehen.
- Vor dem Überschreiben bestehender Dateien prüfen, ob lokale Änderungen erhalten bleiben müssen.
- Externe und symbolische Verzeichnislinks bei Backups sorgfältig behandeln.
- Bei automatischen Updates die Integrität der heruntergeladenen Dateien prüfen.

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

- GitHub Repository
- Installer anzeigen
- Installer direkt herunterladen
- [Python herunterladen](<https://www.python.org/downloads/>)

---

# 🇬🇧 English

## 📖 About the Project

**OSCam Emu Patch Manager** is a Python-based desktop toolkit for managing OSCam-Emu patches and related Git workflows.

It supports the patch workflow from creation and validation to local application and the management or publication of changes. Available features depend on the actual implementation, configuration, and build tools in use.

## ✨ Features

- 🧩 Create, validate, and apply patches
- 📦 Create backups and export them as ZIP archives
- ✏️ Edit patch headers and metadata
- 🖥️ PyQt6 graphical interface
- 🌐 Git and GitHub functionality where implemented and configured
- 🐍 Python installer for Windows and Linux
- 🌍 German and English language options where supported
- ⚙️ Set up Python environments and dependencies
- 🛠️ Linux and WSL2 support for build workflows
- 🔍 Check build tools and dependencies
- 🔒 Exclude selected project directories and configured paths from backups

## 📋 Requirements

- Python **3.9 or newer**, provided the specific application version supports it
- Windows 10/11 or a supported Linux distribution
- Internet access for downloads and any required GitHub operations
- Write permissions for the installation directory
- Git if required by the selected features
- Ubuntu under WSL2 for build workflows that explicitly use WSL
- Additional compilers, libraries, and headers when required by the selected SDK or build script

Download Python: [python.org](<https://www.python.org/downloads/>)

On Windows, enable **Add Python to PATH** during installation if available.

> **Important:** The Windows Python application and the WSL2 Linux build environment are separate environments. Required Linux packages must be installed inside the Ubuntu distribution that actually runs the build script.

## 🚀 Installation

### 🪟 Windows 10 / Windows 11

#### 1\. Check Python

Open Command Prompt (`Win + R` → `cmd`) and run:

bat

```
py -3 --version
```

If `py` is not recognized, install Python from [python.org](<https://www.python.org/downloads/>) and check your PATH.

#### 2\. Download and run the installer

bat

```
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o "%TEMP%\oscam_installer.py" && py -3 "%TEMP%\oscam_installer.py"
```

This downloads the installer and runs it with Python 3.

#### 3\. Complete setup

- Follow the installer's instructions.
- Choose the desired installation directory.
- Review overwrite prompts carefully.
- Back up existing configuration files and local changes.
- Check the output for missing Python dependencies.

#### 4\. Launch the application

Navigate to the actual installation directory. If the startup script exists, run:

bat

```
start_windows.bat
```

The filename may differ between project versions. Only run a startup script that actually exists in the installation directory.

### 🐧 Linux: Ubuntu, Debian, and Linux Mint

#### 1\. Update package lists

bash

```
sudo apt update
```

#### 2\. Install basic packages

bash

```
sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  curl \
  ca-certificates \
  git \
  dos2unix \
  meson \
  ninja-build \
  gettext
```

These packages provide the basic Python environment, compiler tools, Git, and additional build utilities.

| Package | Purpose |
| --- | --- |
| `python3` | Python runtime |
| `python3-venv` | Virtual Python environments |
| `python3-pip` | Python package installation |
| `python3-dev` | Python headers for native extensions |
| `build-essential` | GCC, G++, Make, and basic build tools |
| `curl` | Download files over HTTP(S) |
| `ca-certificates` | Certificates for secure HTTPS connections |
| `git` | Version control and patch workflows |
| `dos2unix` | Convert Windows line endings to Unix line endings |
| `meson` | Build system for projects that use Meson |
| `ninja-build` | Build tool commonly used with Meson |
| `gettext` | Translation and internationalization tools |

**Note:** This is a baseline package list. It does not guarantee that every dependency of a particular OSCam-Emu build or SDK is installed.

#### 3\. Verify the installation

bash

```
python3 --version
python3 -m pip --version
git --version
gcc --version
g++ --version
make --version
meson --version
ninja --version
gettext --version
```

If an individual command fails with `command not found`, install its corresponding package and check again.

#### 4\. Download and run the installer

bash

```
curl -fL "https://raw.githubusercontent.com/speedy005/oscam_patch_manager_new/master/installer.py" -o installer.py
python3 installer.py
```

Follow the instructions and verify that the installer successfully sets up the required dependencies.

#### 5\. Launch the application

Navigate to the installation directory. If the startup script exists, run:

bash

```
chmod +x start_linux.sh
./start_linux.sh
```

The filename depends on the actual installed project version.

### 🐧 Windows with WSL2 and Ubuntu

WSL2 provides a Linux environment on Windows. For Linux builds, the required tools must be installed inside the WSL distribution actually used by the build script.

#### 1\. Check WSL status

Open PowerShell on Windows:

powershell

```
wsl --status
wsl --list --verbose
```

Make sure Ubuntu is installed and the intended WSL version is being used.

If Ubuntu is not installed, installation may be required from an elevated PowerShell window:

powershell

```
wsl --install -d Ubuntu
```

Restart Windows if necessary and complete the Ubuntu first-run setup.

#### 2\. Open Ubuntu

Open Ubuntu from the Windows Start menu or run the following in PowerShell:

powershell

```
wsl -d Ubuntu
```

Run the following Linux commands **inside the Ubuntu terminal**, not in PowerShell or Windows Command Prompt.

#### 3\. Install Linux tools

bash

```
sudo apt update

sudo apt install -y \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  build-essential \
  curl \
  ca-certificates \
  git \
  dos2unix \
  meson \
  ninja-build \
  gettext
```

If `sudo` requests a password, enter the password configured for your Ubuntu Linux user during first-run setup. No characters are displayed while typing; this is normal.

**The Ubuntu password is not automatically the same as your Windows password.**

#### 4\. Verify the tools

bash

```
python3 --version
python3 -m pip --version
git --version
gcc --version
g++ --version
make --version
meson --version
ninja --version
gettext --version
```

#### 5\. Navigate to the project directory

Change to the directory that actually contains the project.

For a project stored on a Windows drive, WSL can access it through `/mnt/<drive-letter>/...`. The following is only a template and must be adapted to your own directory:

bash

```
cd "/mnt/<drive-letter>/path/to/project"
```

Alternatively, the project can be stored inside the Linux filesystem in WSL.

Verify the directory:

bash

```
pwd
ls -la
```

If the `s3` file exists, continue with the following checks.

#### 6\. Prepare the build script

First, check whether Windows line endings are present:

bash

```
file ./s3
```

If the script uses CRLF line endings, convert it:

bash

```
dos2unix ./s3
```

To convert other shell scripts in the project:

bash

```
find . -type f -name "*.sh" -not -path "./.git/*" \
  -exec dos2unix {} +
```

The main script `s3` may be affected even though it has no `.sh` extension, so it is converted separately.

Check its first line:

bash

```
head -n 1 ./s3
```

Check shell syntax:

bash

```
bash -n ./s3
```

If the syntax check succeeds, start the script according to its documentation, for example:

bash

```
chmod +x ./s3
./s3 menu
```

If the script sources additional shell files, those files must also use valid Unix line endings.

#### 7\. Handle missing build dependencies

If a build fails with a message such as:

text

```
meson: command not found
```

install Meson and Ninja:

bash

```
sudo apt update
sudo apt install -y meson ninja-build
```

Then verify:

bash

```
meson --version
ninja --version
```

Determine any additional missing programs from the actual error messages.

> **OpenPLi/OpenEmbedded SDK:** The standard Ubuntu packages are not a replacement for a complete SDK. A build may additionally require a suitable cross-compiler, SDK environment variables, libraries, headers, and project-specific dependencies.

## 🔧 Fixing CRLF Line Endings

A common problem when running shell scripts from Windows directories is the use of Windows line endings (`CRLF`) instead of the Unix line endings (`LF`) expected by Linux tools.

Typical error messages include:

text

```
/bin/bash^M: bad interpreter: No such file or directory
```

text

```
$'\r': command not found
```

text

```
syntax error near unexpected token `$'{\r''
```

### Recommended procedure

First, navigate to the actual project directory:

bash

```
cd "/path/to/project"
```

This is only an example. Use the directory containing your project.

Convert the main script:

bash

```
dos2unix ./s3
```

Convert regular shell scripts outside `.git`:

bash

```
find . -type f -name "*.sh" -not -path "./.git/*" \
  -exec dos2unix {} +
```

If the project contains additional files without a `.sh` extension that are sourced by shell scripts, those files may also need conversion.

You can search for files containing CRLF characters with:

bash

```
grep -rlIZ $'\r' . --exclude-dir=.git
```

The output lists files containing the search pattern. A matching file is not necessarily a shell script, so files should not be converted indiscriminately.

If only known text files with CRLF line endings should be corrected, apply `dos2unix` to those files explicitly.

**Important:** Do not apply `dos2unix` indiscriminately to binary files, ZIP archives, images, or compiled files.

## 📦 Additional Dependencies for OSCam Builds

Depending on the build script and libraries used, additional packages may be required.

Common tools and development libraries include:

bash

```
sudo apt install -y \
  gcc \
  g++ \
  make \
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
  lib32z1
```

This list is optional and does not replace checking the actual build requirements.

For USB-related functionality, the development package `libusb-1.0-0-dev` is often required. The correct Ubuntu package name is not `libusb-1.0.0-dev`.

Install it with:

bash

```
sudo apt install -y libusb-1.0-0-dev
```

If Ubuntu cannot find the package, first check the package sources and its availability for your distribution:

bash

```
sudo apt update
apt-cache policy libusb-1.0-0-dev
apt-cache search libusb
```

Not every package is available in every distribution or repository. Do not install similarly named packages without verifying that they provide the required library.

### Repairing package installation

If a package installation was interrupted:

bash

```
sudo dpkg --configure -a
sudo apt --fix-broken install
sudo apt update
```

Then retry the required package installation.

If a package manager process appears unresponsive, check its status first:

bash

```
ps aux | grep -E 'apt|dpkg' | grep -v grep
```

Do not terminate package manager processes without understanding their state. An interrupted installation can leave the package database inconsistent. If a process has merely been suspended, determine why before resuming or terminating it.

## ⚙️ Installer and Excluded Files

The installer downloads selected files from GitHub. The actual file selection, handling of existing files, and Python environment setup depend on the installer's implementation.

If the installer uses an exclusion list, the documented list must match the actual implementation.

The example exclusion list documented here includes:

- **File extensions:** `.png`, `.zip`, `.md`, `.php`
- **Directories:** `.git`, `.github`, `__pycache__`, `.pytest_cache`, `.mypy_cache`, `.venv`, `venv`, `env`, `node_modules`
- **Installer files:** `installer.py`, `installer.sh`, `installer.bat`, `install.py`, `install.sh`, `install.bat`

**Important:** Excluded PNG files may contain application icons or other required resources. Omitting them may leave the application incomplete. Verify that these exclusions match the intended installation behavior.

If a virtual environment is used, install Python dependencies inside that environment whenever possible.

Example:

bash

```
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

If the project contains a `requirements.txt` file:

bash

```
python -m pip install -r requirements.txt
```

Do not install dependencies from a file that does not exist. First check which dependency file the project actually uses.

## 🔄 Updating

Download the current version through the intended installation method or use the update mechanism provided by the project.

Before every update:

- Back up local changes and configuration files.
- Back up important patches and archives.
- Check whether local changes could be overwritten.
- Verify that the installer actually updates all required files.
- Recheck dependencies after the update.

Running the installer again does not guarantee that old files will be replaced or obsolete files removed. Differences between the installed version and the current project version may need to be reviewed manually.

## 🛠️ Troubleshooting

| Problem | Solution |
| --- | --- |
| `py` is not recognized on Windows | Install Python and check PATH. |
| `python3` is missing | Install Python using the package manager for the Linux distribution in use. |
| `python3-pip` is missing | Run `sudo apt update` and `sudo apt install -y python3-pip`. |
| `venv` is missing | Run `sudo apt install -y python3-venv`. |
| `curl: command not found` | Run `sudo apt install -y curl`. |
| `git: command not found` | Run `sudo apt install -y git`. |
| `meson: command not found` | Run `sudo apt install -y meson`. |
| `ninja: command not found` | Run `sudo apt install -y ninja-build`. |
| `gettext` is missing | Run `sudo apt install -y gettext`. |
| `libusb-1.0.0-dev` cannot be found | Check the correct package name: `libusb-1.0-0-dev`. |
| `/bin/bash^M: bad interpreter` | Convert the affected script with `dos2unix`. |
| `$'\r': command not found` | Correct CRLF line endings in the affected text files. |
| `./s3: No such file or directory` | Use `pwd` and `ls -la` to check the current directory and actual filename. |
| `Permission denied` | Check permissions and, if appropriate, use `chmod +x ./s3`. |
| `sudo: Authentication failed` | Use the Ubuntu Linux password; typed characters are not displayed. |
| `apt` hangs or was interrupted | Check package manager status and run `sudo dpkg --configure -a` if needed. |
| Compiler or headers are missing | Check the build script, SDK documentation, and required development libraries. |
| Python dependencies are missing | Check `requirements.txt` and the installer output, if available. |
| `SyntaxError` or `UnicodeDecodeError` | Inspect the affected file and, if necessary, save it again as UTF-8. |
| Build fails under WSL | Check whether packages were installed in the correct WSL distribution. |
| Installation fails | Check internet access, write permissions, Python version, and the complete error message. |

## 🔒 Security

- Review source code before running it.
- Back up files before patching or updating.
- Review changes with `git diff` before committing.
- Never publish GitHub tokens or credentials.
- Run cleanup operations only in verified directories.
- Obtain installation scripts only from trusted sources.
- Check whether local changes must be preserved before overwriting existing files.
- Handle external and symbolic directory links carefully when creating backups.
- Verify the integrity of downloaded files during automated updates.

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

Back up important files before modifying an existing installation. A successful compilation does not guarantee that the resulting binary will run on every target device.

## 📦 Project Links

- GitHub Repository
- View Installer
- Download Installer Directly
- [Download Python](<https://www.python.org/downloads/>)

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡\
**Built with Python 3 · PyQt6 · Git · GitHub**



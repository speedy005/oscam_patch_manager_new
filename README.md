# ⚡ OSCam Emu Patch Manager

**Build it. Check it. Ship it.**  
A desktop toolkit for managing the OSCam-Emu patch workflow — from creating and validating patch files to applying changes locally and publishing updates to GitHub.

The app combines patch operations, Git repository helpers, GitHub upload tools, and a configurable Qt interface in one place, so you can spend less time juggling scripts and more time managing your patch workflow.

## ✨ What can it do?

### 🧩 Patch workflow
- **Create patches** from the relevant OSCam source repositories.
- **Refresh existing patches** when the source changes.
- **Check patches** before applying them.
- **Apply patches** to a local OSCam-Emu Git repository.
- **Back up and package patches** as ZIP files.
- **Clean temporary patch-work directories** while preserving important files.
- **Edit patch header metadata** and keep patch descriptions up to date.

### 🌐 Git & GitHub integration
- Work with local Git repositories and inspect recent commits.
- Configure repository URLs, branches, Git identity, and GitHub credentials in the app.
- Upload the patch file to your configured GitHub repository.
- Upload the OSCam-Emu repository content using the available repository-upload workflow.
- Review operation output and progress directly in the application.

> **Patch upload note:** The patch-file upload workflow is designed to update `oscam-emu.patch`; it does not intentionally overwrite unrelated files in the target repository.

### 🎨 A GUI that keeps you in the loop
- Desktop interface built with **PyQt6**.
- Switch between **English and German**.
- Customize interface colors and progress-bar appearance.
- See progress and status messages while tasks run.
- Use built-in configuration, help, update-check, and restart options.

## 🚀 Quick start

### Requirements

- Python 3.10+ recommended
- Git installed and available on your `PATH`
- Access to the repositories you want to work with
- A GitHub token with the permissions required for your target repository if you plan to upload

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch the app:

```bash
python main.py
```

Convenience launchers are also included:

- **Windows:** run `start_windows.bat`
- **Linux:** run `start_linux.sh` (make it executable first if needed: `chmod +x start_linux.sh`)

## ⚙️ First-time setup

1. Start the application.
2. Open the GitHub/configuration settings.
3. Enter the repository URLs and branches you want to use.
4. Configure your Git username and email, plus a GitHub token if uploads are needed.
5. Confirm the local repository and patch paths before running operations.
6. Start with a patch check or another non-destructive operation to verify your setup.
# 🚀 OSCam Patch Manager

**Manage. Patch. Update. Upload.** 🛠️

A Python-based GUI tool for managing OSCam patches, Git revisions, repositories, and GitHub uploads.

## ✨ Highlights

- 🔧 Fixed Streamboard revision checkout
- 🔄 Fixed OSCam-Emu revision management
- 📤 Fixed GitHub patch and repository uploads
- ⚙️ Improved configuration loading and repository paths
- 🖥️ Windows and Linux startup scripts
- 🐙 GitHub integration for easier workflow management

## 📥 Get Started

Clone the repository:

```bash
git clone https://github.com/speedy005/oscam_patch_manager_new.git
cd oscam_patch_manager_new
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Launch the application:

**Windows:** Run `start_windows.bat`

**Linux:**
```bash
chmod +x linux.sh
./linux.sh
```

## 🎯 Mission

Making OSCam patch and repository management simpler, smoother, and more reliable.

⭐ **Like the project? Give it a star on GitHub!**

[**View Repository →**](https://github.com/speedy005/oscam_patch_manager_new)
Keep your GitHub token private. Use a token with only the permissions needed for your workflow, and do not commit credentials or local configuration files to a public repository.

## 🗂️ Project layout

The project is split into files by responsibility while keeping a simple launch command.

| File | Responsibility |
|---|---|
| `main.py` | Main launcher |
| `startup.py` | Application startup flow |
| `gui.py` | Main desktop interface |
| `patch_operations.py` | Patch creation, checking, applying, backup, and cleanup operations |
| `git_manager.py` | Git and repository helpers |
| `github_patch_upload.py` | Patch upload workflow |
| `github_repo_upload.py` | Repository upload workflow |
| `config_manager.py` | Configuration persistence |
| `patch_format.py` | Patch formatting and related configuration helpers |
| `translations.py` | English/German interface text |
| `themes.py` | Theme and color helpers |
| `ui_components.py` | Reusable UI components |
| `workers.py` | Background task helpers |
| `paths.py` | Application paths and defaults |
| `bootstrap.py` | Shared setup and bootstrap helpers |
| `dialogs_splash.py` | Dialogs and splash-screen helpers |
| `system_check.py` | System-check functionality |

## 🛡️ Use with care

Patch and repository operations can modify or remove local files. Before applying patches, cleaning directories, or uploading changes:

- Make sure you have a backup or a clean Git checkpoint.
- Verify the selected repository, branch, and paths.
- Review the operation log and check the resulting Git diff.
- Never run cleanup against a directory unless you have confirmed it is the intended target.

The tool is provided as a workflow helper; always review generated patches and repository changes before relying on them.

## 🧱 Architecture note

This is a compatibility-first modular split of a legacy application. The files are grouped by responsibility, while `main.py` loads them in a shared namespace to preserve existing cross-file references. Some modules are therefore **not yet independently importable components**. A future refactor can replace those shared global references with explicit interfaces and imports incrementally.

## 🤝 Contributing

Bug reports, reproducible test cases, and focused improvements are welcome. When submitting a change, please include:

- What workflow or issue it addresses
- Steps to reproduce or test it
- Relevant log output with credentials and private repository details removed

Please preserve the original author and license notices when redistributing the project.

---

**Made for a smoother OSCam-Emu patch workflow.** ⚡


# OSCam Patch Manager – modulare Python-Struktur

## Start

Der externe Programmstart bleibt bewusst einfach:

```bash
python main.py
```

Unter Windows kann alternativ `start_windows.bat`, unter Linux `./start_linux.sh` verwendet werden.

## Module

- `main.py` – schlanker öffentlicher Launcher und Windows-Qt-Umgebung
- `startup.py` – Startablauf, Rechteprüfung, Splashscreen und Qt-Ereignisschleife
- `gui.py` – Hauptfenster und GUI-Aktionen
- `workers.py` – Hintergrund- und Installations-Worker
- `system_check.py` – Systemprüfung
- `paths.py` – Anwendungs-, Repository- und Patch-Pfade
- `config_manager.py` – Laden und Speichern der Anwendungskonfiguration
- `translations.py` – Sprachtexte und Sprach-Hilfsfunktionen
- `themes.py` – Farbschemata und Theme-Daten
- `ui_components.py` – wiederverwendbare Qt-Komponenten und Layouts
- `dialogs_splash.py` – Dialoge, Task-Worker, Uhr und Splashscreen
- `git_manager.py` – Git-Aufrufe, Revisionen, Branches und Tree-Operationen
- `patch_format.py` – Patch-Header/-Format und GitHub-Konfiguration
- `patch_operations.py` – Patch-Erstellung, Sicherung, Bereinigung und Anwendung
- `github_patch_upload.py` – Patch-Datei-Upload
- `github_repo_upload.py` – Repository-Upload und Bash-Hilfen
- `bootstrap.py` – Umgebungs- und Abhängigkeitsprüfungen

Die Module verwenden reguläre Python-Imports; `main.py` führt die Quelltexte nicht mehr per `exec` in einem gemeinsamen Namensraum aus. Die wenigen zyklischen Verweise zwischen Patch-Format und Patch-Operationen werden über lokale, verzögerte Imports aufgelöst.

## Abhängigkeiten und Prüfung

Die benötigten Pakete stehen in `requirements.txt`. Installation (falls noch nicht vorhanden):

```bash
python -m pip install -r requirements.txt
```

Die Python-Dateien wurden auf Syntaxfehler geprüft. Ein vollständiger GUI-Lauf konnte in der Erstellungsumgebung nicht ausgeführt werden, weil PyQt6 dort nicht installiert ist. Nach Installation der Abhängigkeiten bitte die GUI und die zentralen Arbeitsabläufe (Konfiguration laden/speichern, Patch prüfen/erstellen/anwenden, Git- und GitHub-Funktionen) auf dem Zielsystem testen.

## Lizenz / Attribution

Den ursprünglichen Copyright- und Autorenhinweis von speedy005 beibehalten. Bei Weitergabe die MIT-Lizenz und die vollständige Originalattribution erhalten.

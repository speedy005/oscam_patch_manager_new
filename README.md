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

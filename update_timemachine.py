import zipfile
import os
import stat
import json
import tempfile
import shutil
from pathlib import Path, PurePosixPath
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QSplitter, QMessageBox, QAbstractItemView
)


class UpdateTimeMachineDialog(QDialog):
    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)

        self.language = str(language).lower()[:2]
        self.is_de = self.language == "de"
        self.colors = colors or {}
        self.project_dir = Path(__file__).resolve().parent
        self.backup_dir = self.project_dir / "backup"
        self.archives = {}

        self.setWindowTitle(
            "Update-Zeitmaschine" if self.is_de else "Update Time Machine"
        )
        self.resize(1050, 700)
        self.setMinimumSize(760, 500)

        self._build_ui()
        self._apply_theme()
        self.refresh_archives()

    def tr(self, de, en):
        return de if self.is_de else en

    def _build_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel(
            self.tr(
                "UPDATE-ZEITMASCHINE – Sicherungen durchsuchen",
                "UPDATE TIME MACHINE – Browse backups"
            )
        )
        header.setStyleSheet("font-size: 19px; font-weight: bold;")
        layout.addWidget(header)

        description = QLabel(
            self.tr(
                "Vorhandene Sicherungen und deren Dateien anzeigen. "
                "Die Archive werden dabei nicht verändert.",
                "Browse existing backups and their files. "
                "The archives will not be modified."
            )
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        controls = QHBoxLayout()

        self.archive_combo = QComboBox()
        self.archive_combo.currentIndexChanged.connect(self._load_archive)
        controls.addWidget(self.archive_combo, 1)

        self.refresh_button = QPushButton(self.tr("Aktualisieren", "Refresh"))
        self.refresh_button.clicked.connect(self.refresh_archives)
        controls.addWidget(self.refresh_button)

        layout.addLayout(controls)

        self.archive_info = QLabel()
        self.archive_info.setWordWrap(True)
        layout.addWidget(self.archive_info)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.tr("Dateien suchen ...", "Search files ...")
        )
        self.search_input.textChanged.connect(self._filter_files)
        layout.addWidget(self.search_input)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.file_tree = QTreeWidget()
        self.file_tree.setColumnCount(3)
        self.file_tree.setHeaderLabels([
            self.tr("Dateiname / Pfad", "Filename / Path"),
            self.tr("Größe", "Size"),
            self.tr("Archivdatum", "Archive date"),
        ])
        self.file_tree.setAlternatingRowColors(True)
        self.file_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.file_tree.currentItemChanged.connect(self._show_preview)
        self.file_tree.setSortingEnabled(True)
        splitter.addWidget(self.file_tree)

        preview_panel = QVBoxLayout()
        preview_title = QLabel(self.tr("Dateivorschau", "File preview"))
        preview_title.setStyleSheet("font-weight: bold;")
        preview_panel.addWidget(preview_title)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            self.tr(
                "Wähle links eine Datei aus.",
                "Select a file on the left."
            )
        )
        preview_panel.addWidget(self.preview)

        preview_widget = QDialog()
        preview_widget.setLayout(preview_panel)
        splitter.addWidget(preview_widget)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel()
        footer.addWidget(self.status_label, 1)

        self.restore_button = QPushButton(
            self.tr("Auswahl wiederherstellen", "Restore selection")
        )
        self.restore_button.clicked.connect(self._restore_selected)
        footer.addWidget(self.restore_button)

        close_button = QPushButton(self.tr("Schließen", "Close"))
        close_button.clicked.connect(self.close)
        footer.addWidget(close_button)

        layout.addLayout(footer)

    def _apply_theme(self):
        bg = self.colors.get("window_bg", self.colors.get("bg", "#20242b"))
        fg = self.colors.get("fg", "#eeeeee")
        hover = self.colors.get("hover", "#3b4655")
        active = self.colors.get("active", "#52657a")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg};
                color: {fg};
            }}
            QLabel {{
                color: {fg};
            }}
            QLineEdit, QComboBox, QTreeWidget, QTextEdit {{
                background-color: {self.colors.get("bg", bg)};
                color: {fg};
                border: 1px solid {hover};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton {{
                background-color: {hover};
                color: {fg};
                border: 1px solid {active};
                border-radius: 5px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{
                background-color: {active};
            }}
            QHeaderView::section {{
                background-color: {hover};
                color: {fg};
                padding: 5px;
                border: 1px solid {active};
            }}
        """)

    @staticmethod
    def _format_size(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}"
            value /= 1024

    def refresh_archives(self):
        self.archive_combo.blockSignals(True)
        self.archive_combo.clear()
        self.archives.clear()

        definitions = [
            (
                "backup.zip",
                self.tr("Automatische Update-Sicherung", "Automatic update backup")
            ),
            (
                "backup_git.zip",
                self.tr("Manuelle Git-Sicherung", "Manual Git backup")
            ),
        ]

        found = []

        for filename, label in definitions:
            path = self.backup_dir / filename
            if not path.is_file():
                continue

            try:
                stat = path.stat()
                with zipfile.ZipFile(path, "r") as archive:
                    entries = [
                        item for item in archive.infolist()
                        if not item.is_dir()
                    ]

                timestamp = datetime.fromtimestamp(stat.st_mtime)
                self.archives[filename] = {
                    "path": path,
                    "label": label,
                    "size": stat.st_size,
                    "timestamp": timestamp,
                    "entries": entries,
                }

                found.append(filename)
                self.archive_combo.addItem(
                    f"{label} – {timestamp:%d.%m.%Y %H:%M:%S} "
                    f"({self._format_size(stat.st_size)})",
                    filename
                )

            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                QMessageBox.warning(
                    self,
                    self.tr("Backup-Fehler", "Backup error"),
                    f"{filename}\n\n{exc}"
                )

        self.archive_combo.blockSignals(False)

        if found:
            self.archive_combo.setCurrentIndex(0)
            self._load_archive()
        else:
            self.file_tree.clear()
            self.archive_info.setText(
                self.tr(
                    "Keine Sicherungen gefunden.",
                    "No backups found."
                )
            )
            self.preview.clear()
            self.status_label.setText("")

    def _load_archive(self, *_):
        filename = self.archive_combo.currentData()
        if not filename or filename not in self.archives:
            return

        data = self.archives[filename]
        self.file_tree.clear()
        self.preview.clear()

        self.archive_info.setText(
            f"{data['label']} | {data['timestamp']:%d.%m.%Y %H:%M:%S} "
            f"| {self._format_size(data['size'])} "
            f"| {len(data['entries'])} "
            f"{self.tr('Dateien', 'files')}"
        )

        for entry in data["entries"]:
            timestamp = datetime(
                *entry.date_time
            ).strftime("%d.%m.%Y %H:%M:%S")

            item = QTreeWidgetItem([
                entry.filename,
                self._format_size(entry.file_size),
                timestamp,
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, entry.filename)
            item.setData(1, Qt.ItemDataRole.UserRole, entry.file_size)
            self.file_tree.addTopLevelItem(item)

        self._filter_files()
        self.status_label.setText(
            self.tr(
                f"{len(data['entries'])} Dateien geladen.",
                f"{len(data['entries'])} files loaded."
            )
        )

    def _filter_files(self, *_):
        query = self.search_input.text().strip().casefold()
        visible = 0

        for index in range(self.file_tree.topLevelItemCount()):
            item = self.file_tree.topLevelItem(index)
            matches = query in item.text(0).casefold()
            item.setHidden(not matches)
            if matches:
                visible += 1

        self.status_label.setText(
            self.tr(
                f"{visible} Dateien angezeigt.",
                f"{visible} files displayed."
            )
        )

    def _restore_selected(self):
        selected = self.file_tree.selectedItems()
        if not selected:
            QMessageBox.information(
                self, self.tr("Hinweis", "Information"),
                self.tr("Bitte zuerst Dateien auswählen.",
                        "Please select files first.")
            )
            return

        archive_name = self.archive_combo.currentData()
        data = self.archives.get(archive_name)
        if not data:
            return

        project = self.project_dir.resolve()
        protected_dirs = {
            "backup", ".git", "oscam-emu-git", "streamboard-git",
            "__pycache__", ".venv", "venv",
        }
        protected_files = {
            "noto_color_emoji.zip", "oscam_emu_toolkit2.png",
            "oscam-patch-generator.png", "speedy_oscam_managert.png",
            "final-oscam-emu-patch-maker.png", "final-englisch.png",
            "speedy_banner.png", "readme.md", "version.txt",
            "config.json", "settings.json", "github_config.json",
            "install_counter.txt", "oscam_rev.txt",
        }

        try:
            with (project / "config.json").open("r", encoding="utf-8") as f:
                config = json.load(f)
            if not isinstance(config, dict):
                raise ValueError("config.json ist kein JSON-Objekt.")

            custom_paths = []
            for key in ("s3_custom_path", "ncam_custom_path", "s4_custom_path"):
                value = config.get(key)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"Ungültiger Schutzpfad: {key}")

                custom = Path(value.strip()).expanduser()
                if not custom.is_absolute():
                    custom = project / custom
                custom = custom.resolve(strict=False)
                custom.relative_to(project)

                if custom == project or custom in custom_paths:
                    raise ValueError(f"Ungültiger oder doppelter Schutzpfad: {key}")
                custom_paths.append(custom)

            if len(custom_paths) != 3:
                raise ValueError("Die drei Schutzpfade konnten nicht ermittelt werden.")

        except Exception as exc:
            QMessageBox.critical(
                self, self.tr("Sicherheitsprüfung", "Security check"),
                self.tr(
                    "Die Schutzregeln konnten nicht sicher geladen werden. "
                    "Wiederherstellung wurde abgebrochen.\n\n",
                    "Protected paths could not be verified. "
                    "Restore was cancelled.\n\n"
                ) + str(exc)
            )
            return

        try:
            with zipfile.ZipFile(data["path"], "r") as source:
                infos = {item.filename: item for item in source.infolist()}
                jobs = []

                for item in selected:
                    name = item.data(0, Qt.ItemDataRole.UserRole)
                    info = infos.get(name)
                    if info is None or info.is_dir():
                        raise ValueError(f"Ungültiger Archiveintrag: {name}")

                    if "\\" in name or "\x00" in name:
                        raise ValueError(f"Ungültiger Pfad: {name}")

                    rel = PurePosixPath(name)
                    if (
                        rel.is_absolute()
                        or not rel.parts
                        or ".." in rel.parts
                        or ":" in rel.parts[0]
                    ):
                        raise ValueError(f"Unsicherer ZIP-Pfad: {name}")

                    if any(
                        part.casefold() in protected_dirs
                        or "s3" in part.casefold()
                        or "s4" in part.casefold()
                        for part in rel.parts[:-1]
                    ):
                        raise ValueError(f"Geschützter Ordner: {name}")

                    if (
                        rel.name.casefold() in protected_files
                        or rel.suffix.casefold() == ".ini"
                    ):
                        raise ValueError(f"Geschützte Datei: {name}")

                    mode = info.external_attr >> 16
                    if stat.S_ISLNK(mode):
                        raise ValueError(f"Symbolischer Link nicht erlaubt: {name}")

                    destination = project.joinpath(*rel.parts)
                    destination_resolved = destination.resolve(strict=False)
                    destination_resolved.relative_to(project)

                    cursor = project
                    for part in rel.parts:
                        cursor = cursor / part
                        if cursor.is_symlink():
                            raise ValueError(f"Symbolischer Link im Zielpfad: {name}")

                    if any(
                        destination_resolved == custom
                        or custom in destination_resolved.parents
                        for custom in custom_paths
                    ):
                        raise ValueError(f"Konfigurierter Schutzordner: {name}")

                    if destination.exists() and not destination.is_file():
                        raise ValueError(f"Zieldatei ist keine reguläre Datei: {name}")

                    jobs.append((name, info, destination, destination.exists()))

                if not jobs:
                    return

                existing = [job for job in jobs if job[3]]
                names = "\n".join(
                    f"• {job[0]}" for job in jobs[:15]
                )
                if len(jobs) > 15:
                    names += f"\n… und {len(jobs) - 15} weitere"

                question = self.tr(
                    "Folgende Dateien werden wiederhergestellt:\n\n",
                    "The following files will be restored:\n\n"
                ) + names

                if existing:
                    question += self.tr(
                        f"\n\n{len(existing)} vorhandene Datei(en) werden "
                        "nach deiner Bestätigung überschrieben.",
                        f"\n\n{len(existing)} existing file(s) will be "
                        "overwritten after your confirmation."
                    )

                question += self.tr(
                    "\n\nVorhandene Zieldateien werden vorher in einer "
                    "separaten Sicherheitskopie gesichert.\nFortfahren?",
                    "\n\nExisting target files will first be saved in a "
                    "separate safety backup.\nContinue?"
                )

                confirm = QMessageBox(self)
                confirm.setIcon(QMessageBox.Icon.Question)
                confirm.setWindowTitle(
                    self.tr("Wiederherstellung bestätigen", "Confirm restore")
                )
                confirm.setText(question)

                yes_button = confirm.addButton(
                    self.tr("Ja", "Yes"),
                    QMessageBox.ButtonRole.YesRole
                )
                no_button = confirm.addButton(
                    self.tr("Nein", "No"),
                    QMessageBox.ButtonRole.NoRole
                )
                confirm.setDefaultButton(no_button)
                confirm.exec()

                if confirm.clickedButton() != yes_button:
                    return

                self.backup_dir.mkdir(parents=True, exist_ok=True)
                safety_path = None

                if existing:
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    fd, temp_name = tempfile.mkstemp(
                        prefix="restore_safety_", suffix=".tmp",
                        dir=self.backup_dir
                    )
                    os.close(fd)
                    temp_safety = Path(temp_name)
                    safety_path = self.backup_dir / f"restore_safety_{stamp}.zip"

                    try:
                        with zipfile.ZipFile(
                            temp_safety, "w", zipfile.ZIP_DEFLATED,
                            compresslevel=1
                        ) as safety:
                            for name, info, destination, existed in existing:
                                safety.write(destination, arcname=name)

                        with zipfile.ZipFile(temp_safety, "r") as check:
                            if check.testzip() is not None:
                                raise RuntimeError("Sicherheitskopie ist beschädigt.")

                        os.replace(temp_safety, safety_path)
                    except Exception:
                        temp_safety.unlink(missing_ok=True)
                        raise

                changed = []

                def atomic_copy(reader, destination):
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    fd, temp_name = tempfile.mkstemp(
                        prefix=".timemachine_", suffix=".tmp",
                        dir=destination.parent
                    )
                    temp_file = Path(temp_name)
                    try:
                        with os.fdopen(fd, "wb") as output:
                            shutil.copyfileobj(reader, output, 1024 * 1024)
                            output.flush()
                            os.fsync(output.fileno())
                        os.replace(temp_file, destination)
                    except Exception:
                        temp_file.unlink(missing_ok=True)
                        raise

                try:
                    for name, info, destination, existed in jobs:
                        with source.open(info, "r") as member:
                            atomic_copy(member, destination)
                        changed.append((name, destination, existed))

                except Exception:
                    rollback_errors = []
                    if safety_path and safety_path.exists():
                        try:
                            with zipfile.ZipFile(safety_path, "r") as safety:
                                for name, destination, existed in reversed(changed):
                                    if existed:
                                        with safety.open(name, "r") as member:
                                            atomic_copy(member, destination)
                                    else:
                                        destination.unlink(missing_ok=True)
                        except Exception as rollback_error:
                            rollback_errors.append(str(rollback_error))
                    else:
                        for name, destination, existed in reversed(changed):
                            if not existed:
                                destination.unlink(missing_ok=True)

                    detail = self.tr(
                        "Wiederherstellung fehlgeschlagen. ",
                        "Restore failed. "
                    ) + str(__import__("sys").exc_info()[1])
                    if rollback_errors:
                        detail += "\nRollback-Fehler: " + "; ".join(rollback_errors)
                    if safety_path:
                        detail += f"\nSicherheitskopie: {safety_path}"
                    raise RuntimeError(detail)

                QMessageBox.information(
                    self,
                    self.tr("Wiederherstellung abgeschlossen", "Restore complete"),
                    self.tr(
                        f"{len(jobs)} Datei(en) wurden wiederhergestellt.",
                        f"{len(jobs)} file(s) were restored."
                    ) + (
                        f"\n\nSicherheitskopie:\n{safety_path}"
                        if safety_path else ""
                    )
                )
                self.refresh_archives()

        except Exception as exc:
            QMessageBox.critical(
                self,
                self.tr("Wiederherstellungsfehler", "Restore error"),
                str(exc)
            )

    def _show_preview(self, current, previous=None):
        self.preview.clear()

        if current is None:
            return

        filename = current.data(0, Qt.ItemDataRole.UserRole)
        archive_name = self.archive_combo.currentData()

        if not filename or archive_name not in self.archives:
            return

        data = self.archives[archive_name]
        entry = next(
            (item for item in data["entries"]
             if item.filename == filename),
            None
        )

        if entry is None:
            return

        details = [
            f"{self.tr('Datei', 'File')}: {filename}",
            f"{self.tr('Größe', 'Size')}: {self._format_size(entry.file_size)}",
            f"{self.tr('Komprimiert', 'Compressed')}: "
            f"{self._format_size(entry.compress_size)}",
            f"{self.tr('CRC32', 'CRC32')}: {entry.CRC:08X}",
            "",
        ]

        suffix = Path(filename).suffix.casefold()
        text_extensions = {
            ".py", ".txt", ".md", ".json", ".ini", ".cfg",
            ".conf", ".xml", ".html", ".css", ".js", ".log",
            ".yaml", ".yml", ".sh", ".bat", ".php", ".csv",
        }

        if suffix not in text_extensions:
            details.append(
                self.tr(
                    "Keine Textvorschau für diesen Dateityp.",
                    "No text preview for this file type."
                )
            )
        elif entry.file_size > 256 * 1024:
            details.append(
                self.tr(
                    "Datei ist größer als 256 KB. Vorschau aus Sicherheits- "
                    "und Performancegründen ausgelassen.",
                    "File exceeds 256 KB. Preview omitted for safety "
                    "and performance."
                )
            )
        else:
            try:
                with zipfile.ZipFile(data["path"], "r") as archive:
                    raw = archive.read(filename)

                if b"\x00" in raw:
                    details.append(
                        self.tr(
                            "Datei enthält Binärdaten.",
                            "File contains binary data."
                        )
                    )
                else:
                    details.append(
                        raw.decode("utf-8", errors="replace")
                    )

            except (OSError, KeyError, zipfile.BadZipFile, RuntimeError) as exc:
                details.append(
                    self.tr("Vorschau fehlgeschlagen: ", "Preview failed: ")
                    + str(exc)
                )

        self.preview.setPlainText("\n".join(details))

"""Read-only backup explorer for OSCam Patch Manager."""

import tarfile
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QSplitter, QMessageBox,
)


class BackupExplorerDialog(QDialog):
    """Browse existing backups without modifying them."""

    SOURCES = [
        ("backup", "Projektarchive", "Project archives"),
        ("backups", "Automatische Sicherungen", "Automatic backups"),
        ("patch_sicherungen", "Patch-Sicherungen", "Patch backups"),
        ("s4/data/backups", "S4-Backups", "S4 backups"),
    ]

    MAX_DEPTH = 8
    MAX_PREVIEW_BYTES = 256 * 1024

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)

        self.language = str(language).lower()[:2] if str(language).lower()[:2] in ("de", "en", "it", "gr", "pl", "tr") else "en"
        self.colors = colors or {}
        self.root = Path(__file__).resolve().parent
        self.records = []

        self.setWindowTitle(self.tr("Backup-Explorer", "Backup explorer"))
        self.resize(1150, 760)
        self.setMinimumSize(850, 560)

        self._build_ui()
        self._apply_theme()
        self.refresh_backups()

    def tr(self, de, en):
        translations = {
            "Schreibgeschützte Übersicht. Dateien und Archive werden nicht verändert oder entpackt.": {
                "it": "Panoramica in sola lettura. I file e gli archivi non vengono modificati né estratti.",
                "gr": "Επισκόπηση μόνο για ανάγνωση. Τα αρχεία και οι φάκελοι δεν τροποποιούνται ούτε αποσυμπιέζονται.",
                "pl": "Widok tylko do odczytu. Pliki i archiwa nie są modyfikowane ani rozpakowywane.",
                "tr": "Salt okunur genel bakış. Dosyalar ve arşivler değiştirilmez veya çıkarılmaz.",
            },
            "Sicherungen": {"it": "Backup", "gr": "Αντίγραφα ασφαλείας", "pl": "Kopie zapasowe", "tr": "Yedekler"},
            "Gesamtgröße": {"it": "Dimensione totale", "gr": "Συνολικό μέγεθος", "pl": "Łączny rozmiar", "tr": "Toplam boyut"},
            "Dateiname oder Pfad suchen ...": {
                "it": "Cerca nome file o percorso ...", "gr": "Αναζήτηση ονόματος αρχείου ή διαδρομής ...",
                "pl": "Szukaj nazwy pliku lub ścieżki ...", "tr": "Dosya adı veya yol ara ...",
            },
            "Alle Quellen": {"it": "Tutte le fonti", "gr": "Όλες οι πηγές", "pl": "Wszystkie źródła", "tr": "Tüm kaynaklar"},
            "Aktualisieren": {"it": "Aggiorna", "gr": "Ανανέωση", "pl": "Odśwież", "tr": "Yenile"},
            "Datum": {"it": "Data", "gr": "Ημερομηνία", "pl": "Data", "tr": "Tarih"},
            "Quelle": {"it": "Fonte", "gr": "Πηγή", "pl": "Źródło", "tr": "Kaynak"},
            "Größe": {"it": "Dimensione", "gr": "Μέγεθος", "pl": "Rozmiar", "tr": "Boyut"},
            "Typ": {"it": "Tipo", "gr": "Τύπος", "pl": "Typ", "tr": "Tür"},
            "Datei / Pfad": {"it": "File / percorso", "gr": "Αρχείο / διαδρομή", "pl": "Plik / ścieżka", "tr": "Dosya / yol"},
            "Vorschau / Archivinhalt": {
                "it": "Anteprima / contenuto archivio", "gr": "Προεπισκόπηση / περιεχόμενο αρχείου",
                "pl": "Podgląd / zawartość archiwum", "tr": "Önizleme / arşiv içeriği",
            },
            "Wähle eine Sicherung aus.": {
                "it": "Seleziona un backup.", "gr": "Επιλέξτε ένα αντίγραφο ασφαλείας.",
                "pl": "Wybierz kopię zapasową.", "tr": "Bir yedek seçin.",
            },
            "Schließen": {"it": "Chiudi", "gr": "Κλείσιμο", "pl": "Zamknij", "tr": "Kapat"},
            "Projektarchive": {"it": "Archivi del progetto", "gr": "Αρχεία έργου", "pl": "Archiwa projektu", "tr": "Proje arşivleri"},
            "Automatische Sicherungen": {"it": "Backup automatici", "gr": "Αυτόματα αντίγραφα ασφαλείας", "pl": "Automatyczne kopie zapasowe", "tr": "Otomatik yedekler"},
            "Patch-Sicherungen": {"it": "Backup delle patch", "gr": "Αντίγραφα ασφαλείας patch", "pl": "Kopie zapasowe patchy", "tr": "Yama yedekleri"},
            "S4-Backups": {"it": "Backup S4", "gr": "Αντίγραφα ασφαλείας S4", "pl": "Kopie zapasowe S4", "tr": "S4 yedekleri"},
            "Inhalt – nur gelesen, nichts entpackt:": {
                "it": "Contenuto – sola lettura, nessuna estrazione:",
                "gr": "Περιεχόμενο – μόνο ανάγνωση, χωρίς αποσυμπίεση:",
                "pl": "Zawartość – tylko do odczytu, bez rozpakowywania:",
                "tr": "İçerik – salt okunur, hiçbir şey çıkarılmadı:",
            },
            "(Datei ist leer.)": {
                "it": "(Il file è vuoto.)", "gr": "(Το αρχείο είναι κενό.)",
                "pl": "(Plik jest pusty.)", "tr": "(Dosya boş.)",
            },
        }
        if self.language == "de":
            return de
        if self.language == "en":
            return en
        if de.startswith("Archiv: "):
            name = de[len("Archiv: "):]
            return {
                "it": f"Archivio: {name}", "gr": f"Αρχείο: {name}",
                "pl": f"Archiwum: {name}", "tr": f"Arşiv: {name}",
            }.get(self.language, en)
        if de.startswith("Datei ist zu groß für eine Textvorschau"):
            size = de.split("(", 1)[-1].rstrip(").")
            return {
                "it": f"Il file è troppo grande per l'anteprima testuale ({size}).",
                "gr": f"Το αρχείο είναι πολύ μεγάλο για προεπισκόπηση κειμένου ({size}).",
                "pl": f"Plik jest zbyt duży do podglądu tekstu ({size}).",
                "tr": f"Dosya metin önizlemesi için çok büyük ({size}).",
            }.get(self.language, en)
        if de.endswith("Einträge angezeigt"):
            import re
            match = re.match(r"(\d+) von (\d+) Einträgen angezeigt", de)
            if match:
                shown, total = match.groups()
                return {
                    "it": f"Visualizzati {shown} di {total} elementi",
                    "gr": f"Εμφανίζονται {shown} από {total} εγγραφές",
                    "pl": f"Wyświetlono {shown} z {total} elementów",
                    "tr": f"{total} öğeden {shown} tanesi gösteriliyor",
                }.get(self.language, en)
        if de.endswith("Einträge"):
            count = de.split()[0]
            return {
                "it": f"{count} elementi", "gr": f"{count} εγγραφές",
                "pl": f"{count} elementów", "tr": f"{count} öğe",
            }.get(self.language, en)
        if de.startswith("... weitere ") and " Einträge nicht angezeigt." in de:
            count = de.split("... weitere ", 1)[1].split()[0]
            return {
                "it": f"... altri {count} elementi non visualizzati.",
                "gr": f"... δεν εμφανίζονται {count} ακόμη εγγραφές.",
                "pl": f"... nie pokazano kolejnych {count} elementów.",
                "tr": f"... {count} öğe daha gösterilmedi.",
            }.get(self.language, en)
        if de.startswith("Archiv konnte nicht gelesen werden:"):
            error = de.split(": ", 1)[-1]
            return {
                "it": f"Impossibile leggere l'archivio: {error}",
                "gr": f"Δεν ήταν δυνατή η ανάγνωση του αρχείου: {error}",
                "pl": f"Nie można odczytać archiwum: {error}",
                "tr": f"Arşiv okunamadı: {error}",
            }.get(self.language, en)
        return translations.get(de, {}).get(self.language, en)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(self.tr(
            "BACKUP-EXPLORER – Sicherungen durchsuchen",
            "BACKUP EXPLORER – Browse backups"
        ))
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(self.tr(
            "Schreibgeschützte Übersicht. Dateien und Archive werden nicht verändert oder entpackt.",
            "Read-only overview. Files and archives are never modified or extracted."
        ))
        description.setWordWrap(True)
        layout.addWidget(description)

        stats = QGridLayout()
        self.stat_labels = {}

        for column, (key, de, en) in enumerate([
            ("total", "Sicherungen", "Backups"),
            ("archives", "Archive", "Archives"),
            ("size", "Gesamtgröße", "Total size"),
        ]):
            caption = QLabel(self.tr(de, en))
            value = QLabel("–")
            value.setStyleSheet("font-size: 19px; font-weight: bold;")
            stats.addWidget(caption, 0, column)
            stats.addWidget(value, 1, column)
            self.stat_labels[key] = value

        layout.addLayout(stats)

        controls = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            self.tr("Dateiname oder Pfad suchen ...", "Search filename or path ...")
        )
        self.search_input.textChanged.connect(self._render)
        controls.addWidget(self.search_input, 1)

        self.source_combo = QComboBox()
        self.source_combo.addItem(self.tr("Alle Quellen", "All sources"), "all")
        for key, de, en in self.SOURCES:
            self.source_combo.addItem(self.tr(de, en), key)
        self.source_combo.currentIndexChanged.connect(self._render)
        controls.addWidget(self.source_combo)

        refresh = QPushButton(self.tr("Aktualisieren", "Refresh"))
        refresh.clicked.connect(self.refresh_backups)
        controls.addWidget(refresh)
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Vertical)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self.tr("Datum", "Date"),
            self.tr("Quelle", "Source"),
            self.tr("Größe", "Size"),
            self.tr("Typ", "Type"),
            self.tr("Datei / Pfad", "File / path"),
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._show_preview)
        self.table.doubleClicked.connect(self._show_preview)

        header = self.table.horizontalHeader()
        for column in range(4):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        splitter.addWidget(self.table)

        preview_container = QDialog()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        preview_title = QLabel(self.tr("Vorschau / Archivinhalt", "Preview / archive contents"))
        preview_title.setStyleSheet("font-weight: bold;")
        preview_layout.addWidget(preview_title)

        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            self.tr("Wähle eine Sicherung aus.", "Select a backup.")
        )
        preview_layout.addWidget(self.preview)

        splitter.addWidget(preview_container)
        splitter.setSizes([420, 220])
        layout.addWidget(splitter, 1)

        footer = QHBoxLayout()
        self.status_label = QLabel()
        footer.addWidget(self.status_label, 1)

        close = QPushButton(self.tr("Schließen", "Close"))
        close.clicked.connect(self.close)
        footer.addWidget(close)
        layout.addLayout(footer)

    def _apply_theme(self):
        bg = self.colors.get("window_bg", self.colors.get("bg", "#20242b"))
        panel = self.colors.get("bg", bg)
        fg = self.colors.get("fg", "#eeeeee")
        hover = self.colors.get("hover", "#3b4655")
        active = self.colors.get("active", "#52657a")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {fg}; }}
            QLabel {{ color: {fg}; }}
            QLineEdit, QComboBox, QTableWidget, QTextEdit {{
                background-color: {panel};
                color: {fg};
                border: 1px solid {hover};
                border-radius: 5px;
                padding: 5px;
            }}
            QHeaderView::section {{
                background-color: {hover};
                color: {fg};
                padding: 6px;
                border: 1px solid {active};
            }}
            QPushButton {{
                background-color: {hover};
                color: {fg};
                border: 1px solid {active};
                border-radius: 5px;
                padding: 7px 12px;
            }}
            QPushButton:hover {{ background-color: {active}; }}
        """)

    @staticmethod
    def _format_size(size):
        value = float(size)
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if value < 1024 or unit == "TB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} TB"

    @staticmethod
    def _archive_type(path):
        name = path.name.lower()
        if name.endswith(".zip"):
            return "ZIP"
        if name.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
            return "TAR"
        return ""

    def _scan_source(self, source_key, relative_dir):
        base = self.root / relative_dir
        if not base.is_dir():
            return

        try:
            files = base.rglob("*")
            for path in files:
                try:
                    if not path.is_file():
                        continue
                    relative = path.relative_to(self.root)
                    depth = len(relative.parts) - 1
                    if depth > self.MAX_DEPTH:
                        continue

                    stat = path.stat()
                    self.records.append({
                        "path": path,
                        "relative": str(relative),
                        "source": source_key,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "type": self._archive_type(path) or path.suffix.lstrip(".").upper() or "Datei",
                    })
                except (OSError, ValueError):
                    continue
        except OSError:
            pass

    def refresh_backups(self):
        self.records = []

        for source_key, _, _ in self.SOURCES:
            self._scan_source(source_key, source_key)

        self.records.sort(
            key=lambda item: item["modified"],
            reverse=True
        )

        archives = sum(bool(self._archive_type(item["path"])) for item in self.records)
        total_size = sum(item["size"] for item in self.records)

        self.stat_labels["total"].setText(str(len(self.records)))
        self.stat_labels["archives"].setText(str(archives))
        self.stat_labels["size"].setText(self._format_size(total_size))

        self._render()

    def _render(self, *_):
        query = self.search_input.text().strip().lower()
        source = self.source_combo.currentData()

        records = [
            item for item in self.records
            if (source == "all" or item["source"] == source)
            and (not query or query in item["relative"].lower())
        ]

        self.table.setRowCount(len(records))

        source_names = {
            key: self.tr(de, en)
            for key, de, en in self.SOURCES
        }

        for row, record in enumerate(records):
            values = [
                record["modified"].astimezone().strftime("%d.%m.%Y %H:%M"),
                source_names[record["source"]],
                self._format_size(record["size"]),
                record["type"],
                record["relative"],
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, record["relative"])
                self.table.setItem(row, column, item)

        self.status_label.setText(self.tr(
            f"{len(records)} von {len(self.records)} Einträgen angezeigt",
            f"Showing {len(records)} of {len(self.records)} entries"
        ))
        self.preview.clear()

    def _show_preview(self, *_):
        row = self.table.currentRow()
        if row < 0:
            return

        path_item = self.table.item(row, 4)
        if path_item is None:
            return

        relative = path_item.data(Qt.ItemDataRole.UserRole)
        record = next(
            (item for item in self.records if item["relative"] == relative),
            None
        )
        if record is None:
            return

        path = record["path"]
        archive_type = self._archive_type(path)

        if archive_type:
            self._preview_archive(path, archive_type)
            return

        try:
            if record["size"] > self.MAX_PREVIEW_BYTES:
                self.preview.setPlainText(self.tr(
                    f"Datei ist zu groß für eine Textvorschau ({self._format_size(record['size'])}).",
                    f"File is too large for text preview ({self._format_size(record['size'])})."
                ))
                return

            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace")
            self.preview.setPlainText(text or self.tr(
                "(Datei ist leer.)", "(File is empty.)"
            ))
        except OSError as exc:
            self.preview.setPlainText(self.tr(
                f"Fehler: {exc}",
                f"Error: {exc}"
            ))

    def _preview_archive(self, path, archive_type):
        lines = [
            self.tr(
                f"Archiv: {path.name}",
                f"Archive: {path.name}"
            ),
            self.tr(
                "Inhalt – nur gelesen, nichts entpackt:",
                "Contents – read only, nothing extracted:"
            ),
            "",
        ]

        try:
            if archive_type == "ZIP":
                with zipfile.ZipFile(path, "r") as archive:
                    members = archive.infolist()
                    lines.append(f"{len(members)} Einträge")
                    for member in members[:500]:
                        if not member.is_dir():
                            lines.append(
                                f"{member.filename}  ({self._format_size(member.file_size)})"
                            )
            else:
                with tarfile.open(path, "r:*") as archive:
                    members = archive.getmembers()
                    lines.append(f"{len(members)} Einträge")
                    for member in members[:500]:
                        if member.isfile():
                            lines.append(
                                f"{member.name}  ({self._format_size(member.size)})"
                            )

            if len(members) > 500:
                lines.append(self.tr(
                    f"... weitere {len(members) - 500} Einträge nicht angezeigt.",
                    f"... {len(members) - 500} more entries not shown."
                ))

        except (OSError, zipfile.BadZipFile, tarfile.TarError) as exc:
            lines.append(self.tr(
                f"Archiv konnte nicht gelesen werden: {exc}",
                f"Could not read archive: {exc}"
            ))

        self.preview.setPlainText("\n".join(lines))

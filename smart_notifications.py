"""Persistent, read-only smart notifications for OSCam Patch Manager."""

import hashlib
import json
import re
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTextEdit,
)


class SmartNotificationsDialog(QDialog):
    """Collect build and backup alerts and persist their read state."""

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)
        self.language = str(language).lower()[:2] if str(language).lower()[:2] in ("de", "en", "it", "gr", "pl", "tr") else "en"
        self.colors = colors or {}
        self.root = Path(__file__).resolve().parent
        self.log_dir = self.root / "build_logs"
        self.backup_dir = self.root / "backup"
        self.store_path = self.root / "notifications.json"
        self.events = []
        self._load_events()

        self.setWindowTitle(self.tr("Smart-Benachrichtigungen",
                                    "Smart notifications"))
        self.resize(1050, 700)
        self.setMinimumSize(780, 520)

        self._build_ui()
        self._apply_theme()
        self.refresh_notifications()

    def tr(self, de, en):
        translations = {
            "Smart-Benachrichtigungen": ["Notifiche intelligenti", "Έξυπνες ειδοποιήσεις", "Inteligentne powiadomienia", "Akıllı Bildirimler"],
            "SMART-BENACHRICHTIGUNGEN – Systemmeldungen": ["NOTIFICHE INTELLIGENTI – Avvisi di sistema", "ΕΞΥΠΝΕΣ ΕΙΔΟΠΟΙΗΣΕΙΣ – Ειδοποιήσεις συστήματος", "INTELIGENTNE POWIADOMIENIA – Alerty systemowe", "AKILLI BİLDİRİMLER – Sistem uyarıları"],
            "Überwacht vorhandene Build-Logs und Update-Sicherungen. Meldungen und Lesestatus bleiben dauerhaft gespeichert.": ["Monitora i log di build e i backup degli aggiornamenti. Le notifiche e lo stato di lettura vengono salvati in modo permanente.", "Παρακολουθεί τα υπάρχοντα αρχεία καταγραφής build και τα αντίγραφα ασφαλείας ενημερώσεων. Οι ειδοποιήσεις και η κατάσταση ανάγνωσης αποθηκεύονται μόνιμα.", "Monitoruje istniejące logi kompilacji i kopie zapasowe aktualizacji. Powiadomienia i stan przeczytania są trwale zapisywane.", "Mevcut derleme günlüklerini ve güncelleme yedeklerini izler. Bildirimler ve okunma durumları kalıcı olarak saklanır."],
            "Meldungen": ["Notifiche", "Ειδοποιήσεις", "Powiadomienia", "Bildirimler"],
            "Ungelesen": ["Non lette", "Μη αναγνωσμένα", "Nieprzeczytane", "Okunmamış"],
            "Fehler": ["Errori", "Σφάλματα", "Błędy", "Hatalar"],
            "Warnungen": ["Avvisi", "Προειδοποιήσεις", "Ostrzeżenia", "Uyarılar"],
            "Alle Meldungen": ["Tutte le notifiche", "Όλες οι ειδοποιήσεις", "Wszystkie powiadomienia", "Tüm bildirimler"],
            "Nur Fehler": ["Solo errori", "Μόνο σφάλματα", "Tylko błędy", "Yalnızca hatalar"],
            "Nur Warnungen": ["Solo avvisi", "Μόνο προειδοποιήσεις", "Tylko ostrzeżenia", "Yalnızca uyarılar"],
            "Informationen": ["Informazioni", "Πληροφορίες", "Informacje", "Bilgiler"],
            "Prüfen / Aktualisieren": ["Scansiona / aggiorna", "Σάρωση / ανανέωση", "Skanuj / odśwież", "Tara / yenile"],
            "Alle gelesen": ["Segna tutte come lette", "Σήμανση όλων ως αναγνωσμένων", "Oznacz wszystkie jako przeczytane", "Tümünü okundu olarak işaretle"],
            "Datum": ["Data", "Ημερομηνία", "Data", "Tarih"],
            "Typ": ["Tipo", "Τύπος", "Typ", "Tür"],
            "Status": ["Stato", "Κατάσταση", "Status", "Durum"],
            "Meldung": ["Notifica", "Ειδοποίηση", "Powiadomienie", "Bildirim"],
            "Wähle eine Meldung aus.": ["Seleziona una notifica.", "Επιλέξτε μια ειδοποίηση.", "Wybierz powiadomienie.", "Bir bildirim seçin."],
            "Ausgewählte gelesen": ["Segna selezionata come letta", "Σήμανση επιλεγμένης ως αναγνωσμένης", "Oznacz wybrane jako przeczytane", "Seçileni okundu olarak işaretle"],
            "Schließen": ["Chiudi", "Κλείσιμο", "Zamknij", "Kapat"],
            "Automatische Update-Sicherung": ["Backup automatico aggiornamento", "Αυτόματο αντίγραφο ασφαλείας ενημέρωσης", "Automatyczna kopia zapasowa aktualizacji", "Otomatik güncelleme yedeği"],
            "Manuelle Git-Sicherung": ["Backup Git manuale", "Μη αυτόματο αντίγραφο ασφαλείας Git", "Ręczna kopia zapasowa Git", "Manuel Git yedeği"],
            "Größe": ["Dimensione", "Μέγεθος", "Rozmiar", "Boyut"],
            "Bytes": ["byte", "bytes", "bajtów", "bayt"],
            "Hinweis: Es wurde nur die ZIP-Inhaltsübersicht gelesen. Keine vollständige CRC-Prüfung durchgeführt.": ["Nota: è stato letto solo l'indice ZIP. Non è stata eseguita una verifica CRC completa.", "Σημείωση: διαβάστηκε μόνο ο κατάλογος ZIP. Δεν πραγματοποιήθηκε πλήρης έλεγχος CRC.", "Uwaga: odczytano tylko spis zawartości ZIP. Nie wykonano pełnej weryfikacji CRC.", "Not: Yalnızca ZIP dizini okundu. Tam CRC doğrulaması yapılmadı."],
            "Build": ["Build", "Build", "Kompilacja", "Derleme"],
            "Sicherung": ["Backup", "Αντίγραφο ασφαλείας", "Kopia zapasowa", "Yedek"],
            "System": ["Sistema", "Σύστημα", "System", "Sistem"],
            "Warnung": ["Avviso", "Προειδοποίηση", "Ostrzeżenie", "Uyarı"],
            "Info": ["Info", "Πληροφορίες", "Informacja", "Bilgi"],
        }

        if self.language == "de":
            return de
        if self.language == "en":
            return en

        index = {"it": 0, "gr": 1, "pl": 2, "tr": 3}[self.language]
        if de in translations:
            return translations[de][index]

        if de.startswith("Speichern fehlgeschlagen: "):
            detail = de.split(": ", 1)[1]
            prefixes = ["Salvataggio non riuscito: ", "Η αποθήκευση απέτυχε: ", "Nie udało się zapisać: ", "Kaydetme başarısız: "]
            return prefixes[index] + detail

        if de.startswith("Build fehlgeschlagen: "):
            name = de.split(": ", 1)[1]
            prefixes = ["Build non riuscita: ", "Αποτυχία build: ", "Kompilacja nie powiodła się: ", "Derleme başarısız: "]
            return prefixes[index] + name

        if de.startswith("Build unvollständig: "):
            name = de.split(": ", 1)[1]
            prefixes = ["Build incompleta: ", "Ατελές build: ", "Niekompletna kompilacja: ", "Eksik derleme: "]
            return prefixes[index] + name

        if de.startswith("Build-Log: "):
            lines = de.splitlines()
            result = lines[1].split(": ", 1)[1] if len(lines) > 1 and ": " in lines[1] else ""
            result_map = {
                "Fehler": ["Non riuscita", "Απέτυχε", "Niepowodzenie", "Başarısız"],
                "Kein eindeutiger Abschlussmarker": ["Nessun indicatore di completamento conclusivo", "Δεν υπάρχει σαφής δείκτης ολοκλήρωσης", "Brak jednoznacznego znacznika zakończenia", "Kesin bir tamamlanma işareti yok"],
            }
            labels = ["Log build: ", "Αρχείο καταγραφής build: ", "Log kompilacji: ", "Derleme günlüğü: "]
            result_labels = ["Risultato: ", "Αποτέλεσμα: ", "Wynik: ", "Sonuç: "]
            return labels[index] + lines[0].split(": ", 1)[1] + "\n" + result_labels[index] + result_map.get(result, [result] * 4)[index]

        if de.startswith("ZIP lesbar, ") and de.endswith(" Einträge"):
            count = de[len("ZIP lesbar, "):-len(" Einträge")]
            labels = ["ZIP leggibile, ", "Το ZIP είναι αναγνώσιμο, ", "Czytelny ZIP, ", "ZIP okunabilir, "]
            nouns = [" voci", " εγγραφές", " wpisów", " öğe"]
            return labels[index] + count + nouns[index]

        if de.startswith("Update-Sicherung vorhanden: "):
            name = de.split(": ", 1)[1]
            prefixes = ["Backup aggiornamento disponibile: ", "Υπάρχει αντίγραφο ασφαλείας ενημέρωσης: ", "Dostępna kopia zapasowa aktualizacji: ", "Güncelleme yedeği mevcut: "]
            return prefixes[index] + name

        if de.startswith("Problem mit Sicherung: "):
            name = de.split(": ", 1)[1]
            prefixes = ["Problema con il backup: ", "Πρόβλημα με το αντίγραφο ασφαλείας: ", "Problem z kopią zapasową: ", "Yedekleme sorunu: "]
            return prefixes[index] + name

        if de.startswith("Archiv kann nicht gelesen werden: "):
            detail = de.split(": ", 1)[1]
            prefixes = ["Impossibile leggere l'archivio: ", "Δεν είναι δυνατή η ανάγνωση του αρχείου: ", "Nie można odczytać archiwum: ", "Arşiv okunamıyor: "]
            return prefixes[index] + detail

        if de.endswith(" Meldungen gespeichert"):
            count = de.split(" ", 1)[0]
            labels = [" notifiche salvate", " ειδοποιήσεις αποθηκεύτηκαν", " powiadomień zapisano", " bildirim kaydedildi"]
            return count + labels[index]

        return en

    def _load_events(self):
        try:
            data = json.loads(self.store_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("events"), list):
                self.events = [
                    item for item in data["events"]
                    if isinstance(item, dict) and item.get("id")
                ]
        except (OSError, ValueError, TypeError):
            self.events = []

    def _save_events(self):
        data = {"version": 1, "events": self.events[-500:]}
        temporary = self.store_path.with_suffix(".json.tmp")
        try:
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temporary.replace(self.store_path)
        except OSError as exc:
            self.status_label.setText(
                self.tr(f"Speichern fehlgeschlagen: {exc}",
                        f"Could not save notifications: {exc}")
            )

    def _add_event(self, category, severity, title, details, fingerprint,
                   timestamp=None):
        event_id = hashlib.sha256(
            fingerprint.encode("utf-8", errors="replace")
        ).hexdigest()[:24]

        if any(item.get("id") == event_id for item in self.events):
            return False

        self.events.append({
            "id": event_id,
            "category": category,
            "severity": severity,
            "title": title,
            "details": details,
            "timestamp": timestamp or datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "read": False,
        })
        return True

    @staticmethod
    def _build_status(path):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return "incomplete"

        match = re.search(r"SIMPLEBUILD_FINISHED:exit=(-?\d+)", content)
        if match:
            return "success" if int(match.group(1)) == 0 else "failed"
        if "numeric argument required" in content:
            return "failed"
        if re.search(r"SIMPLEBUILD_FINISHED:exit=\s*(?:\r?$)",
                     content, re.M):
            return "failed"
        return "incomplete"

    def _scan_build_logs(self):
        if not self.log_dir.is_dir():
            return

        for path in self.log_dir.glob("*.log"):
            try:
                stat = path.stat()
            except OSError:
                continue

            status = self._build_status(path)
            if status == "success":
                continue

            failed = status == "failed"
            category = "build"
            severity = "error" if failed else "warning"
            title = self.tr(
                f"Build fehlgeschlagen: {path.name}" if failed
                else f"Build unvollständig: {path.name}",
                f"Build failed: {path.name}" if failed
                else f"Build incomplete: {path.name}",
            )
            details = self.tr(
                f"Build-Log: {path}\nErgebnis: "
                f"{'Fehler' if failed else 'Kein eindeutiger Abschlussmarker'}",
                f"Build log: {path}\nResult: "
                f"{'Failed' if failed else 'No conclusive finish marker'}",
            )
            fingerprint = (
                f"build|{path.name}|{status}|{stat.st_size}|{stat.st_mtime_ns}"
            )
            self._add_event(
                category, severity, title, details, fingerprint,
                datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(
                    timespec="seconds"
                ),
            )

    def _scan_backups(self):
        definitions = [
            ("backup.zip", self.tr("Automatische Update-Sicherung",
                                   "Automatic update backup")),
            ("backup_git.zip", self.tr("Manuelle Git-Sicherung",
                                       "Manual Git backup")),
        ]

        for filename, label in definitions:
            path = self.backup_dir / filename
            if not path.exists():
                continue

            try:
                stat = path.stat()
            except OSError:
                continue

            try:
                with zipfile.ZipFile(path, "r") as archive:
                    entry_count = len(archive.infolist())
                severity = "info"
                result = self.tr(
                    f"ZIP lesbar, {entry_count} Einträge",
                    f"ZIP readable, {entry_count} entries",
                )
                title = self.tr(
                    f"Update-Sicherung vorhanden: {filename}",
                    f"Update backup available: {filename}",
                )
            except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
                severity = "error"
                result = self.tr(
                    f"Archiv kann nicht gelesen werden: {exc}",
                    f"Archive cannot be read: {exc}",
                )
                title = self.tr(
                    f"Problem mit Sicherung: {filename}",
                    f"Backup problem: {filename}",
                )

            fingerprint = (
                f"backup|{filename}|{stat.st_size}|{stat.st_mtime_ns}|{severity}"
            )
            details = (
                f"{label}\n{path}\n"
                f"{self.tr('Größe', 'Size')}: {stat.st_size:,} "
                f"{self.tr('Bytes', 'Bytes')}\n"
                f"{result}\n\n"
                + self.tr(
                    "Hinweis: Es wurde nur die ZIP-Inhaltsübersicht gelesen. "
                    "Keine vollständige CRC-Prüfung durchgeführt.",
                    "Note: Only the ZIP directory was read. "
                    "No full CRC verification was performed.",
                )
            )
            self._add_event(
                "backup", severity, title, details, fingerprint,
                datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(
                    timespec="seconds"
                ),
            )

    def refresh_notifications(self):
        old_count = len(self.events)
        self._scan_build_logs()
        self._scan_backups()

        if len(self.events) != old_count:
            self._save_events()

        self.events.sort(
            key=lambda item: item.get("timestamp", ""), reverse=True
        )
        self._render()
        self.status_label.setText(self.tr(
            f"{len(self.events)} Meldungen gespeichert",
            f"{len(self.events)} notifications stored",
        ))

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(self.tr(
            "SMART-BENACHRICHTIGUNGEN – Systemmeldungen",
            "SMART NOTIFICATIONS – System alerts",
        ))
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        description = QLabel(self.tr(
            "Überwacht vorhandene Build-Logs und Update-Sicherungen. "
            "Meldungen und Lesestatus bleiben dauerhaft gespeichert.",
            "Monitors existing build logs and update backups. "
            "Notifications and read status are stored persistently.",
        ))
        description.setWordWrap(True)
        layout.addWidget(description)

        stats = QGridLayout()
        self.stat_labels = {}
        for column, (key, de, en) in enumerate([
            ("total", "Meldungen", "Notifications"),
            ("unread", "Ungelesen", "Unread"),
            ("errors", "Fehler", "Errors"),
            ("warnings", "Warnungen", "Warnings"),
        ]):
            caption = QLabel(self.tr(de, en))
            value = QLabel("0")
            value.setStyleSheet("font-size: 20px; font-weight: bold;")
            stats.addWidget(caption, 0, column)
            stats.addWidget(value, 1, column)
            self.stat_labels[key] = value
        layout.addLayout(stats)

        controls = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(self.tr("Alle Meldungen", "All notifications"),
                                  "all")
        self.filter_combo.addItem(self.tr("Ungelesen", "Unread"), "unread")
        self.filter_combo.addItem(self.tr("Nur Fehler", "Errors only"), "error")
        self.filter_combo.addItem(self.tr("Nur Warnungen", "Warnings only"),
                                  "warning")
        self.filter_combo.addItem(self.tr("Informationen", "Information"),
                                  "info")
        self.filter_combo.currentIndexChanged.connect(self._render)
        controls.addWidget(self.filter_combo, 1)

        refresh = QPushButton(self.tr("Prüfen / Aktualisieren", "Scan / refresh"))
        refresh.clicked.connect(self.refresh_notifications)
        controls.addWidget(refresh)

        mark_all = QPushButton(self.tr("Alle gelesen", "Mark all read"))
        mark_all.clicked.connect(self._mark_all_read)
        controls.addWidget(mark_all)
        layout.addLayout(controls)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            self.tr("Datum", "Date"),
            self.tr("Typ", "Type"),
            self.tr("Status", "Status"),
            self.tr("Meldung", "Notification"),
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._show_details)
        header = self.table.horizontalHeader()
        for column in range(3):
            header.setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(115)
        self.details.setPlaceholderText(
            self.tr("Wähle eine Meldung aus.", "Select a notification.")
        )
        layout.addWidget(self.details)

        footer = QHBoxLayout()
        self.status_label = QLabel()
        footer.addWidget(self.status_label, 1)

        mark_read = QPushButton(self.tr("Ausgewählte gelesen",
                                        "Mark selected read"))
        mark_read.clicked.connect(self._mark_selected_read)
        footer.addWidget(mark_read)

        close = QPushButton(self.tr("Schließen", "Close"))
        close.clicked.connect(self.close)
        footer.addWidget(close)
        layout.addLayout(footer)

    def _render(self, *_):
        selected = self.filter_combo.currentData()
        filtered = []
        for event in self.events:
            if selected == "unread" and event.get("read"):
                continue
            if selected in ("error", "warning", "info"):
                if event.get("severity") != selected:
                    continue
            filtered.append(event)

        counts = {
            "total": len(self.events),
            "unread": sum(not item.get("read") for item in self.events),
            "errors": sum(item.get("severity") == "error"
                          for item in self.events),
            "warnings": sum(item.get("severity") == "warning"
                            for item in self.events),
        }
        for key, value in counts.items():
            self.stat_labels[key].setText(str(value))

        self.table.setRowCount(len(filtered))
        for row, event in enumerate(filtered):
            try:
                stamp = datetime.fromisoformat(
                    event.get("timestamp", "")
                ).astimezone().strftime("%d.%m.%Y %H:%M")
            except ValueError:
                stamp = "–"

            category = self.tr(
                {"build": "Build", "backup": "Sicherung"}.get(
                    event.get("category"), "System"
                ),
                {"build": "Build", "backup": "Backup"}.get(
                    event.get("category"), "System"
                ),
            )
            severity = event.get("severity", "info")
            status = self.tr(
                {"error": "Fehler", "warning": "Warnung",
                 "info": "Info"}.get(severity, severity),
                severity.capitalize(),
            )
            title = event.get("title", "")
            if not event.get("read"):
                title = "● " + title

            values = [stamp, category, status, title]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, event.get("id"))
                self.table.setItem(row, column, item)

        self.details.clear()

    def _selected_event(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        event_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        return next(
            (event for event in self.events if event.get("id") == event_id),
            None,
        )

    def _show_details(self):
        event = self._selected_event()
        self.details.setPlainText(
            event.get("details", "") if event else ""
        )

    def _mark_selected_read(self):
        event = self._selected_event()
        if not event:
            return
        event["read"] = True
        self._save_events()
        self._render()

    def _mark_all_read(self):
        for event in self.events:
            event["read"] = True
        self._save_events()
        self._render()

    def _apply_theme(self):
        bg = self.colors.get(
            "window_bg", self.colors.get("bg", "#20242b")
        )
        panel = self.colors.get("bg", bg)
        fg = self.colors.get("fg", "#eeeeee")
        hover = self.colors.get("hover", "#3b4655")
        active = self.colors.get("active", "#52657a")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {bg}; color: {fg}; }}
            QLabel {{ color: {fg}; }}
            QComboBox, QTableWidget, QTextEdit {{
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

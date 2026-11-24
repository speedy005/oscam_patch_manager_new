"""Read-only Patch Radar for OSCam Control Center."""

from itertools import combinations
from pathlib import Path

from PyQt6.QtCore import Qt, QSize, QSettings
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit
)


class PatchRadarDialog(QDialog):
    VARIANTS = [
        ("S3", "s3/support/patches"),
        ("S3 Speedy005", "s3_speedy005/support/patches"),
        ("NCam Bonecrew", "s3_ncam_bonecrew/support/patches"),
        ("S4", "s4/data/patches"),
    ]

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)
        self.language = str(language).lower()[:2] if str(language).lower()[:2] in ("de", "en", "it", "gr", "pl", "tr") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self.root = Path(__file__).resolve().parent

        self.setWindowTitle("OSCam Patch Radar")
        self.resize(900, 650)
        self.setMinimumSize(740, 520)

        # Restore the last window size.
        self.settings = QSettings(
            "OSCamPatchManager", "OSCamPatchManager"
        )
        saved_size = self.settings.value("patch_radar/window_size")
        if isinstance(saved_size, QSize) and saved_size.isValid():
            if saved_size.width() >= 740 and saved_size.height() >= 520:
                self.resize(saved_size)

        layout = QVBoxLayout(self)

        title = QLabel("PATCH RADAR")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        self.lamp = QLabel("●")
        self.lamp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lamp.setStyleSheet("font-size: 48px; color: #999999;")
        layout.addWidget(self.lamp)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.output, 1)

        buttons = QHBoxLayout()
        refresh = QPushButton(self.tr_text("Erneut scannen", "Scan again"))
        refresh.clicked.connect(self.refresh_scan)
        buttons.addWidget(refresh)

        close = QPushButton(self.tr_text("Schließen", "Close"))
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        bg = self.colors.get("bg", "#1D1D1D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        window_bg = self.colors.get("window_bg", "#2F2F2F")

        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {fg}; }}
            QLabel {{ color: {fg}; background: transparent; }}
            QTextEdit {{
                background-color: {bg}; color: {fg};
                border: 1px solid {hover}; border-radius: 7px; padding: 8px;
            }}
            QPushButton {{
                color: {fg}; background-color: {bg};
                border: 1px solid {hover}; border-radius: 7px;
                padding: 7px 12px; font-weight: bold;
            }}
            QPushButton:hover {{ color: {window_bg}; background: {hover}; }}
        """)

        self.refresh_scan()

    def closeEvent(self, event):
        # Save the current window size for the next launch.
        self.settings.setValue("patch_radar/window_size", self.size())
        self.settings.sync()
        super().closeEvent(event)

    def tr_text(self, de, en):
        translations = {
            "Erneut scannen": {
                "it": "Esegui nuova scansione", "gr": "Νέα σάρωση",
                "pl": "Skanuj ponownie", "tr": "Yeniden tara",
            },
            "Schließen": {
                "it": "Chiudi", "gr": "Κλείσιμο",
                "pl": "Zamknij", "tr": "Kapat",
            },
            "SCANFEHLER – PRÜFUNG ERFORDERLICH": {
                "it": "ERRORI DI SCANSIONE – VERIFICA NECESSARIA",
                "gr": "ΣΦΑΛΜΑΤΑ ΣΑΡΩΣΗΣ – ΑΠΑΙΤΕΙΤΑΙ ΕΛΕΓΧΟΣ",
                "pl": "BŁĘDY SKANOWANIA – WYMAGANA KONTROLA",
                "tr": "TARAMA HATALARI – KONTROL GEREKLİ",
            },
            "SCAN ERFOLGREICH – PATCH-DATEIEN LESBAR": {
                "it": "SCANSIONE RIUSCITA – FILE PATCH LEGGIBILI",
                "gr": "ΕΠΙΤΥΧΗΣ ΣΑΡΩΣΗ – ΑΝΑΓΝΩΣΙΜΑ ΑΡΧΕΙΑ PATCH",
                "pl": "SKANOWANIE ZAKOŃCZONE – PLIKI PATCH CZYTELNE",
                "tr": "TARAMA BAŞARILI – YAMA DOSYALARI OKUNABİLİR",
            },
            "Keine Auffälligkeiten gefunden.": {
                "it": "Nessuna anomalia rilevata.",
                "gr": "Δεν εντοπίστηκαν προβλήματα.",
                "pl": "Nie wykryto żadnych nieprawidłowości.",
                "tr": "Herhangi bir sorun tespit edilmedi.",
            },
            "Hinweis: Überschneidungen zwischen Varianten werden "
            "nur informativ angezeigt und sind kein Fehlernachweis. "
            "Der Scan ist nur lesend und bestätigt nicht, ob ein Patch "
            "erfolgreich auf den Quellcode angewendet werden kann.": {
                "it": "Nota: le sovrapposizioni tra varianti sono solo informative "
                "e non dimostrano la presenza di errori. La scansione è in sola "
                "lettura e non verifica se una patch possa essere applicata "
                "correttamente al codice sorgente.",
                "gr": "Σημείωση: οι επικαλύψεις μεταξύ παραλλαγών είναι μόνο "
                "ενημερωτικές και δεν αποδεικνύουν σφάλμα. Η σάρωση είναι μόνο "
                "για ανάγνωση και δεν επαληθεύει αν ένα patch εφαρμόζεται "
                "επιτυχώς στον πηγαίο κώδικα.",
                "pl": "Uwaga: nakładanie się wariantów ma wyłącznie charakter "
                "informacyjny i nie dowodzi błędu. Skanowanie odbywa się tylko "
                "w trybie odczytu i nie sprawdza, czy patch można poprawnie "
                "zastosować do kodu źródłowego.",
                "tr": "Not: Varyantlar arasındaki çakışmalar yalnızca bilgilendirme "
                "amaçlıdır ve hata olduğunu kanıtlamaz. Tarama salt okunurdur; "
                "bir yamanın kaynak koda başarıyla uygulanıp uygulanamayacağını "
                "doğrulamaz.",
            },
        }
        if self.language == "de":
            return de
        if self.language == "en":
            return en
        return translations.get(de, {}).get(self.language, en)

    def refresh_scan(self):
        from patch_compatibility_scanner import _parse_patch, _overlap

        parsed = []
        errors = []
        lines = []
        total = 0

        for variant, relative in self.VARIANTS:
            folder = self.root / relative

            if not folder.is_dir():
                lines.append(f"[{ {"de": "FEHLT", "en": "MISSING", "it": "MANCANTE", "gr": "ΛΕΙΠΕΙ", "pl": "BRAK", "tr": "EKSİK"}[self.language] }] {variant}: {folder}")
                errors.append(f"{variant}: " + {
                    "de": "Verzeichnis fehlt", "en": "directory missing",
                    "it": "directory non presente", "gr": "ο κατάλογος λείπει",
                    "pl": "brak katalogu", "tr": "dizin eksik",
                }[self.language])
                continue

            try:
                files = sorted(
                    p for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in (".patch", ".diff")
                )
            except OSError as exc:
                error_label = {
                    "de": "FEHLER", "en": "ERROR", "it": "ERRORE",
                    "gr": "ΣΦΑΛΜΑ", "pl": "BŁĄD", "tr": "HATA",
                }[self.language]
                lines.append(f"[{error_label}] {variant}: {exc}")
                errors.append(str(exc))
                continue

            ok_label = {
                "de": "OK", "en": "OK", "it": "OK",
                "gr": "ΕΝΤΑΞΕΙ", "pl": "OK", "tr": "TAMAM",
            }[self.language]
            file_label = {
                "de": "Patch-Datei(en)", "en": "patch file(s)",
                "it": "file patch", "gr": "αρχεία patch",
                "pl": "plik(i) patch", "tr": "yama dosyası",
            }[self.language]
            lines.append(f"[{ok_label}] {variant}: {len(files)} {file_label}")

            for path in files:
                total += 1
                try:
                    parsed.append({
                        "variant": variant,
                        "path": path,
                        "entries": _parse_patch(path),
                    })
                except Exception as exc:
                    errors.append(f"{path}: {exc}")

        # Treffer nach Variantenpaar und betroffener Datei zusammenfassen.
        grouped = {}

        for a, b in combinations(parsed, 2):
            if a["variant"] == b["variant"]:
                continue

            pair = tuple(sorted((a["variant"], b["variant"])))

            for fa in a["entries"]:
                for fb in b["entries"]:
                    if fa["path"] != fb["path"]:
                        continue

                    duplicate_count = 0
                    conflict_count = 0

                    for ha in fa["hunks"]:
                        for hb in fb["hunks"]:
                            if ha["changes"] and ha["changes"] == hb["changes"]:
                                duplicate_count += 1
                            elif _overlap(ha, hb):
                                conflict_count += 1

                    for kind, count in (
                        ("DUPLICATE", duplicate_count),
                        ("POSSIBLE CONFLICT", conflict_count),
                    ):
                        if not count:
                            continue

                        key = (kind, pair, fa["path"])
                        grouped[key] = grouped.get(key, 0) + count

        findings = [
            (kind, pair, path, count)
            for (kind, pair, path), count in sorted(
                grouped.items(),
                key=lambda item: (item[0][0], item[0][1], item[0][2])
            )
        ]

        conflicts = sum(
            count for kind, pair, path, count in findings
            if kind == "POSSIBLE CONFLICT"
        )
        duplicates = sum(
            count for kind, pair, path, count in findings
            if kind == "DUPLICATE"
        )

        if errors:
            color = "#FF4545"
            headline = self.tr_text(
                "SCANFEHLER – PRÜFUNG ERFORDERLICH",
                "SCAN ERRORS – REVIEW REQUIRED"
            )
        else:
            color = "#39D66F"
            headline = self.tr_text(
                "SCAN ERFOLGREICH – PATCH-DATEIEN LESBAR",
                "SCAN SUCCESSFUL – PATCH FILES READABLE"
            )

        self.lamp.setStyleSheet(f"font-size: 48px; color: {color};")
        self.status.setText(headline)
        summary_templates = {
            "de": "Dateien: {} | Konflikte: {} | Doppelte Änderungen: {} | Fehler: {}",
            "en": "Files: {} | Conflicts: {} | Duplicates: {} | Errors: {}",
            "it": "File: {} | Conflitti: {} | Modifiche duplicate: {} | Errori: {}",
            "gr": "Αρχεία: {} | Συγκρούσεις: {} | Διπλές αλλαγές: {} | Σφάλματα: {}",
            "pl": "Pliki: {} | Konflikty: {} | Zduplikowane zmiany: {} | Błędy: {}",
            "tr": "Dosyalar: {} | Çakışmalar: {} | Yinelenen değişiklikler: {} | Hatalar: {}",
        }
        self.summary.setText(
            summary_templates[self.language].format(total, conflicts, duplicates, len(errors))
        )

        for kind, pair, path, count in findings:
            labels = {
                "de": {"DUPLICATE": "DOPPELT", "POSSIBLE CONFLICT": "MÖGLICHER KONFLIKT", "findings": "Treffer"},
                "en": {"DUPLICATE": "DUPLICATE", "POSSIBLE CONFLICT": "POSSIBLE CONFLICT", "findings": "findings"},
                "it": {"DUPLICATE": "DUPLICATO", "POSSIBLE CONFLICT": "POSSIBILE CONFLITTO", "findings": "risultati"},
                "gr": {"DUPLICATE": "ΔΙΠΛΟ", "POSSIBLE CONFLICT": "ΠΙΘΑΝΗ ΣΥΓΚΡΟΥΣΗ", "findings": "ευρήματα"},
                "pl": {"DUPLICATE": "DUPLIKAT", "POSSIBLE CONFLICT": "MOŻLIWY KONFLIKT", "findings": "wyniki"},
                "tr": {"DUPLICATE": "TEKRAR", "POSSIBLE CONFLICT": "OLASI ÇAKIŞMA", "findings": "bulgu"},
            }
            localized = labels[self.language]
            lines.extend([
                "",
                f"[{localized.get(kind, kind)}] {path} ({count} {localized['findings']})",
                f"  {pair[0]} <-> {pair[1]}",
            ])

        if errors:
            lines.extend(["", self.tr_text("SCANFEHLER:", "SCAN ERRORS:") if self.language == "de" else {"en": "SCAN ERRORS:", "it": "ERRORI DI SCANSIONE:", "gr": "ΣΦΑΛΜΑΤΑ ΣΑΡΩΣΗΣ:", "pl": "BŁĘDY SKANOWANIA:", "tr": "TARAMA HATALARI:"}[self.language]])
            error_label = {
                "de": "FEHLER", "en": "ERROR", "it": "ERRORE",
                "gr": "ΣΦΑΛΜΑ", "pl": "BŁĄD", "tr": "HATA",
            }[self.language]
            lines.extend(f"[{error_label}] {e}" for e in errors)

        if not findings and not errors:
            lines.append(self.tr_text(
                "Keine Auffälligkeiten gefunden.",
                "No issues detected."
            ))

        lines.extend([
            "",
            self.tr_text(
                "Hinweis: Überschneidungen zwischen Varianten werden "
                "nur informativ angezeigt und sind kein Fehlernachweis. "
                "Der Scan ist nur lesend und bestätigt nicht, ob ein Patch "
                "erfolgreich auf den Quellcode angewendet werden kann.",
                "Note: Overlaps between variants are informational only "
                "and do not prove an error. The scan is read-only and does "
                "not verify whether a patch applies successfully to source code."
            )
        ])

        self.output.setPlainText("\n".join(lines))

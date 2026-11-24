"""OSCam Patch Diff Viewer - Deutsch / English."""

import os
import html
import difflib
import subprocess

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QWidget, QLabel, QLineEdit, QPushButton,
    QFileDialog, QTextBrowser, QMessageBox
)


class PatchDiffViewer(QDialog):

    def __init__(self, parent=None, language="de"):
        super().__init__(parent)
        self.lang = str(language).lower()[:2] if str(language).lower()[:2] in ("de", "en", "it", "gr", "pl", "tr") else "en"
        self.report = ""
        self.setMinimumSize(1000, 700)
        self.build_ui()
        self.translate_ui()

    def t(self, de, en):
        translations = {
            "Bitte zwei vorhandene Patch-Dateien auswählen.": {
                "en": "Please select two existing patch files.",
                "it": "Seleziona due file patch esistenti.",
                "gr": "Επιλέξτε δύο υπάρχοντα αρχεία patch.",
                "pl": "Wybierz dwa istniejące pliki patch.",
                "tr": "Lütfen mevcut iki yama dosyası seçin.",
            },
            "Repository und beide Commits/Branches angeben.": {
                "en": "Enter the repository and both commits/branches.",
                "it": "Inserisci il repository e entrambi i commit/branch.",
                "gr": "Εισαγάγετε το αποθετήριο και τα δύο commit/branch.",
                "pl": "Podaj repozytorium oraz oba commity/branche.",
                "tr": "Depoyu ve her iki commit/branch bilgisini girin.",
            },
            "Git-Vergleich fehlgeschlagen:\\n": {
                "en": "Git comparison failed:\\n",
                "it": "Confronto Git non riuscito:\\n",
                "gr": "Η σύγκριση Git απέτυχε:\\n",
                "pl": "Porównanie Git nie powiodło się:\\n",
                "tr": "Git karşılaştırması başarısız oldu:\\n",
            },
            "Keine Unterschiede gefunden.": {
                "en": "No differences found.",
                "it": "Nessuna differenza trovata.",
                "gr": "Δεν βρέθηκαν διαφορές.",
                "pl": "Nie znaleziono różnic.",
                "tr": "Fark bulunamadı.",
            },
            "Bitte zuerst einen Vergleich ausführen.": {
                "en": "Please run a comparison first.",
                "it": "Esegui prima un confronto.",
                "gr": "Εκτελέστε πρώτα μια σύγκριση.",
                "pl": "Najpierw uruchom porównanie.",
                "tr": "Lütfen önce bir karşılaştırma yapın.",
            },
            "HTML-Bericht speichern": {
                "en": "Save HTML report",
                "it": "Salva rapporto HTML",
                "gr": "Αποθήκευση αναφοράς HTML",
                "pl": "Zapisz raport HTML",
                "tr": "HTML raporunu kaydet",
            },
            "Gespeichert: ": {
                "en": "Saved: ",
                "it": "Salvato: ",
                "gr": "Αποθηκεύτηκε: ",
                "pl": "Zapisano: ",
                "tr": "Kaydedildi: ",
            },
            "Patch vergleichen": {
                "en": "Compare patches",
                "it": "Confronta patch",
                "gr": "Σύγκριση patch",
                "pl": "Porównaj patche",
                "tr": "Yamaları karşılaştır",
            },
            "Patch-Datei auswählen": {
                "en": "Select patch file",
                "it": "Seleziona file patch",
                "gr": "Επιλογή αρχείου patch",
                "pl": "Wybierz plik patch",
                "tr": "Yama dosyası seç",
            },
            "Git-Repository auswählen": {
                "en": "Select Git repository",
                "it": "Seleziona repository Git",
                "gr": "Επιλογή αποθετηρίου Git",
                "pl": "Wybierz repozytorium Git",
                "tr": "Git deposu seç",
            },
        }
        import re
        stats = re.fullmatch(
            r"Dateien: (\d+) \| Hinzugefügt: (\d+) \| Entfernt: (\d+)",
            de
        )
        if stats:
            files, added, removed = stats.groups()
            templates = {
                "de": "Dateien: {} | Hinzugefügt: {} | Entfernt: {}",
                "en": "Files: {} | Added: {} | Removed: {}",
                "it": "File: {} | Aggiunti: {} | Rimossi: {}",
                "gr": "Αρχεία: {} | Προστέθηκαν: {} | Αφαιρέθηκαν: {}",
                "pl": "Pliki: {} | Dodano: {} | Usunięto: {}",
                "tr": "Dosyalar: {} | Eklenen: {} | Kaldırılan: {}",
            }
            return templates.get(self.lang, templates["en"]).format(
                files, added, removed
            )
        return de if self.lang == "de" else translations.get(de, {}).get(self.lang, en)

    def build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # PATCH DATEIEN
        patch_tab = QWidget()
        patch_layout = QVBoxLayout(patch_tab)
        patch_form = QFormLayout()

        self.patch_a = QLineEdit()
        self.patch_b = QLineEdit()

        patch_form.addRow("Patch A:", self.file_row(self.patch_a))
        patch_form.addRow("Patch B:", self.file_row(self.patch_b))
        patch_layout.addLayout(patch_form)

        self.patch_button = QPushButton()
        self.patch_button.clicked.connect(self.compare_patches)
        patch_layout.addWidget(self.patch_button)

        self.tabs.addTab(patch_tab, "")

        # GIT COMMITS
        git_tab = QWidget()
        git_layout = QVBoxLayout(git_tab)
        git_form = QFormLayout()

        self.repo = QLineEdit()
        self.commit_a = QLineEdit()
        self.commit_b = QLineEdit()

        git_form.addRow("Repository:", self.repo_row())
        git_form.addRow("Commit / Branch A:", self.commit_a)
        git_form.addRow("Commit / Branch B:", self.commit_b)

        git_layout.addLayout(git_form)

        self.git_button = QPushButton()
        self.git_button.clicked.connect(self.compare_commits)
        git_layout.addWidget(self.git_button)

        self.tabs.addTab(git_tab, "")

        self.status = QLabel()
        layout.addWidget(self.status)

        self.output = QTextBrowser()
        self.output.setStyleSheet(
            "QTextBrowser {background:#111820;color:#e6edf3;"
            "border:1px solid #39434d;font-family:Consolas;}"
        )
        layout.addWidget(self.output, 1)

        buttons = QHBoxLayout()
        buttons.addStretch()

        self.export_button = QPushButton()
        self.export_button.clicked.connect(self.export_html)

        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.close)

        buttons.addWidget(self.export_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def file_row(self, edit):
        widget = QWidget()
        row = QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(edit)

        button = QPushButton("...")
        button.setFixedWidth(40)
        button.clicked.connect(lambda: self.choose_file(edit))
        row.addWidget(button)
        return widget

    def repo_row(self):
        widget = QWidget()
        row = QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.repo)

        button = QPushButton("...")
        button.setFixedWidth(40)
        button.clicked.connect(self.choose_repo)
        row.addWidget(button)
        return widget

    def choose_file(self, edit):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.t("Patch-Datei auswählen", "Select patch file"),
            edit.text(),
            "Patch (*.patch *.diff);;All files (*)"
        )
        if path:
            edit.setText(path)

    def choose_repo(self):
        path = QFileDialog.getExistingDirectory(
            self, self.t("Git-Repository auswählen", "Select Git repository"),
            self.repo.text() or os.getcwd()
        )
        if path:
            self.repo.setText(path)

    def compare_patches(self):
        a = self.patch_a.text().strip()
        b = self.patch_b.text().strip()

        if not os.path.isfile(a) or not os.path.isfile(b):
            self.error(self.t(
                "Bitte zwei vorhandene Patch-Dateien auswählen.",
                "Please select two existing patch files."
            ))
            return

        try:
            with open(a, encoding="utf-8", errors="replace") as f:
                old = f.readlines()
            with open(b, encoding="utf-8", errors="replace") as f:
                new = f.readlines()

            diff = list(difflib.unified_diff(
                old, new,
                fromfile=os.path.basename(a),
                tofile=os.path.basename(b),
                lineterm=""
            ))

            added = sum(x.startswith("+") and not x.startswith("+++")
                        for x in diff)
            removed = sum(x.startswith("-") and not x.startswith("---")
                          for x in diff)

            self.show_diff(diff, 1, added, removed)

        except Exception as exc:
            self.error(str(exc))

    def git(self, args):
        result = subprocess.run(
            ["git", "-C", self.repo.text().strip(), *args],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace"
        )
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip())
        return result.stdout

    def compare_commits(self):
        repo = self.repo.text().strip()
        a = self.commit_a.text().strip()
        b = self.commit_b.text().strip()

        if not os.path.isdir(repo) or not a or not b:
            self.error(self.t(
                "Repository und beide Commits/Branches angeben.",
                "Enter the repository and both commits/branches."
            ))
            return

        try:
            self.git(["rev-parse", "--verify", a + "^{commit}"])
            self.git(["rev-parse", "--verify", b + "^{commit}"])

            diff = self.git([
                "diff", "--no-ext-diff", "--no-color",
                "--find-renames", a, b, "--"
            ])

            files = self.git([
                "diff", "--name-only", a, b, "--"
            ]).splitlines()

            stats = self.git(["diff", "--numstat", a, b, "--"])

            added = removed = 0
            for line in stats.splitlines():
                parts = line.split("\t")
                if len(parts) >= 2:
                    try:
                        added += int(parts[0])
                        removed += int(parts[1])
                    except ValueError:
                        pass

            self.show_diff(diff.splitlines(), len(files), added, removed)

        except Exception as exc:
            self.error(
                self.t("Git-Vergleich fehlgeschlagen:\n",
                       "Git comparison failed:\n") + str(exc)
            )

    def show_diff(self, lines, files, added, removed):
        output = []

        for line in lines:
            safe = html.escape(line or " ")

            if line.startswith(("+++", "---", "@@", "diff ", "index ")):
                css = "header"
            elif line.startswith("+"):
                css = "added"
            elif line.startswith("-"):
                css = "removed"
            else:
                css = "normal"

            output.append(f'<div class="{css}">{safe}</div>')

        if not output:
            output.append(self.t(
                "Keine Unterschiede gefunden.",
                "No differences found."
            ))

        self.report = """
        <!DOCTYPE html>
        <html><head><meta charset="utf-8">
        <style>
        body {background:#111820;color:#e6edf3;font-family:Consolas,monospace}
        div {white-space:pre-wrap}
        .added {color:#7ee787;background:#14251b}
        .removed {color:#ff7b72;background:#2b1719}
        .header {color:#79c0ff;font-weight:bold}
        </style></head><body>
        """ + "\n".join(output) + "</body></html>"

        self.output.setHtml(self.report)

        self.status.setText(self.t(
            f"Dateien: {files} | Hinzugefügt: {added} | Entfernt: {removed}",
            f"Files: {files} | Added: {added} | Removed: {removed}"
        ))

    def export_html(self):
        if not self.report:
            self.error(self.t(
                "Bitte zuerst einen Vergleich ausführen.",
                "Please run a comparison first."
            ))
            return

        path, _ = QFileDialog.getSaveFileName(
            self, self.t("HTML-Bericht speichern", "Save HTML report"),
            "patch_diff_report.html", "HTML (*.html)"
        )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.report)
                self.status.setText(
                    self.t("Gespeichert: ", "Saved: ") + path
                )
            except Exception as exc:
                self.error(str(exc))

    def error(self, message):
        QMessageBox.warning(
            self, self.t("Patch vergleichen", "Compare patches"), message
        )

    def translate_ui(self):
        ui = {
            "de": {
                "title": "OSCam Patch-Diff-Viewer",
                "patch_tab": "Patch-Dateien vergleichen",
                "git_tab": "Git-Commits vergleichen",
                "patch_button": "PATCHES VERGLEICHEN",
                "git_button": "COMMITS VERGLEICHEN",
                "export": "HTML-BERICHT EXPORTIEREN",
                "close": "SCHLIESSEN",
                "status": "Zwei Patch-Dateien oder Git-Commits vergleichen.",
            },
            "en": {
                "title": "OSCam Patch Diff Viewer",
                "patch_tab": "Compare patch files",
                "git_tab": "Compare Git commits",
                "patch_button": "COMPARE PATCHES",
                "git_button": "COMPARE COMMITS",
                "export": "EXPORT HTML REPORT",
                "close": "CLOSE",
                "status": "Compare two patch files or Git commits.",
            },
            "it": {
                "title": "Visualizzatore differenze patch OSCam",
                "patch_tab": "Confronta file patch",
                "git_tab": "Confronta commit Git",
                "patch_button": "CONFRONTA PATCH",
                "git_button": "CONFRONTA COMMIT",
                "export": "ESPORTA RAPPORTO HTML",
                "close": "CHIUDI",
                "status": "Confronta due file patch o commit Git.",
            },
            "gr": {
                "title": "Προβολή διαφορών patch OSCam",
                "patch_tab": "Σύγκριση αρχείων patch",
                "git_tab": "Σύγκριση Git commit",
                "patch_button": "ΣΥΓΚΡΙΣΗ PATCH",
                "git_button": "ΣΥΓΚΡΙΣΗ COMMIT",
                "export": "ΕΞΑΓΩΓΗ ΑΝΑΦΟΡΑΣ HTML",
                "close": "ΚΛΕΙΣΙΜΟ",
                "status": "Συγκρίνετε δύο αρχεία patch ή Git commit.",
            },
            "pl": {
                "title": "Przeglądarka różnic patch OSCam",
                "patch_tab": "Porównaj pliki patch",
                "git_tab": "Porównaj commity Git",
                "patch_button": "PORÓWNAJ PATCHE",
                "git_button": "PORÓWNAJ COMMITY",
                "export": "EKSPORTUJ RAPORT HTML",
                "close": "ZAMKNIJ",
                "status": "Porównaj dwa pliki patch lub commity Git.",
            },
            "tr": {
                "title": "OSCam Yama Fark Görüntüleyici",
                "patch_tab": "Yama dosyalarını karşılaştır",
                "git_tab": "Git commit'lerini karşılaştır",
                "patch_button": "YAMALARI KARŞILAŞTIR",
                "git_button": "COMMIT'LERİ KARŞILAŞTIR",
                "export": "HTML RAPORUNU DIŞA AKTAR",
                "close": "KAPAT",
                "status": "İki yama dosyasını veya Git commit'ini karşılaştırın.",
            },
        }
        t = ui.get(self.lang, ui["en"])
        self.setWindowTitle(t["title"])
        self.tabs.setTabText(0, t["patch_tab"])
        self.tabs.setTabText(1, t["git_tab"])
        self.patch_button.setText(t["patch_button"])
        self.git_button.setText(t["git_button"])
        self.export_button.setText(t["export"])
        self.close_button.setText(t["close"])
        self.status.setText(t["status"])

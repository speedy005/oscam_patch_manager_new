"""Read-only compatibility scanner for unified Git patches."""

import re
import shlex
from itertools import combinations
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QTextEdit, QFileDialog, QMessageBox
)


def _parse_patch(path):
    """Parse changed file sections and unified-diff hunks."""
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    files = []
    current = None
    hunk = None

    for line in text.splitlines():
        if line.startswith("diff --git "):
            if current is not None:
                files.append(current)

            try:
                parts = shlex.split(line)
                old_path = parts[2]
                new_path = parts[3]
            except (ValueError, IndexError):
                old_path = new_path = line

            current = {
                "path": new_path.removeprefix("b/"),
                "hunks": [],
            }
            hunk = None
            continue

        if current is None:
            continue

        match = re.match(
            r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",
            line
        )
        if match:
            hunk = {
                "old_start": int(match.group(1)),
                "old_count": int(match.group(2) or 1),
                "new_start": int(match.group(3)),
                "new_count": int(match.group(4) or 1),
                "changes": [],
            }
            current["hunks"].append(hunk)
            continue

        if hunk is not None and line.startswith(("+", "-")):
            if not line.startswith(("+++", "---")):
                hunk["changes"].append(line)

    if current is not None:
        files.append(current)

    return files


def _overlap(a, b):
    """Check overlap in original-file coordinates."""
    a_start, a_count = a["old_start"], a["old_count"]
    b_start, b_count = b["old_start"], b["old_count"]

    if a_count == 0 and b_count == 0:
        return a_start == b_start
    if a_count == 0:
        return b_start <= a_start <= b_start + b_count
    if b_count == 0:
        return a_start <= b_start <= a_start + a_count

    return max(a_start, b_start) < min(
        a_start + a_count, b_start + b_count
    )


class PatchCompatibilityDialog(QDialog):
    """Read-only compatibility analysis of selected patch files."""

    def __init__(self, parent=None, language="de", colors=None):
        super().__init__(parent)
        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self.patch_paths = []

        self.setWindowTitle(self._tr(
            "Patch-Kompatibilitätsprüfung",
            "Patch Compatibility Scanner"
        ))
        self.resize(850, 620)

        layout = QVBoxLayout(self)

        title = QLabel(self._tr(
            "PATCH COMPATIBILITY SCANNER",
            "PATCH COMPATIBILITY SCANNER"
        ))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel(self._tr(
            "Mehrere Unified-Diff-Patches gemeinsam auf Konflikte prüfen.",
            "Check multiple unified-diff patches for conflicts."
        ))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton(self._tr(
            "Patch-Dateien hinzufügen", "Add patch files"
        ))
        self.remove_button = QPushButton(self._tr(
            "Auswahl entfernen", "Remove selected"
        ))
        self.scan_button = QPushButton(self._tr(
            "Kompatibilität prüfen", "Check compatibility"
        ))
        buttons.addWidget(self.add_button)
        buttons.addWidget(self.remove_button)
        buttons.addWidget(self.scan_button)
        layout.addLayout(buttons)

        self.results = QTextEdit()
        self.results.setReadOnly(True)
        self.results.setPlaceholderText(self._tr(
            "Prüfergebnisse erscheinen hier.",
            "Scan results will appear here."
        ))
        layout.addWidget(self.results, 2)

        close_button = QPushButton(self._tr("Schließen", "Close"))
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)

        self.add_button.clicked.connect(self.add_files)
        self.remove_button.clicked.connect(self.remove_selected)
        self.scan_button.clicked.connect(self.scan)

        bg = self.colors.get("bg", "#1D1D1D")
        fg = self.colors.get("fg", "#DFFF00")
        hover = self.colors.get("hover", "#BFFF00")
        window_bg = self.colors.get("window_bg", "#2F2F2F")
        self.setStyleSheet(f"""
            QDialog {{ background-color: {window_bg}; color: {fg}; }}
            QLabel {{ color: {fg}; }}
            QListWidget, QTextEdit {{
                background-color: {bg}; color: {fg};
                border: 1px solid {hover}; border-radius: 6px;
                padding: 6px;
            }}
            QPushButton {{
                background-color: {bg}; color: {fg};
                border: 1px solid {hover}; border-radius: 6px;
                padding: 7px;
            }}
            QPushButton:hover {{
                background-color: {hover}; color: #000000;
            }}
        """)

    def _tr(self, de, en):
        return de if self.language == "de" else en

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self._tr("Patch-Dateien auswählen", "Select patch files"),
            "",
            "Patch-Dateien (*.patch *.diff);;Alle Dateien (*)"
        )
        for path in paths:
            if path not in self.patch_paths:
                self.patch_paths.append(path)
                self.file_list.addItem(path)

    def remove_selected(self):
        for item in self.file_list.selectedItems():
            row = self.file_list.row(item)
            self.file_list.takeItem(row)
            if 0 <= row < len(self.patch_paths):
                self.patch_paths.pop(row)

    def scan(self):
        if len(self.patch_paths) < 2:
            QMessageBox.information(
                self,
                self._tr("Hinweis", "Notice"),
                self._tr(
                    "Bitte mindestens zwei Patch-Dateien auswählen.",
                    "Please select at least two patch files."
                )
            )
            return

        parsed = []
        errors = []

        for path in self.patch_paths:
            try:
                parsed.append((path, _parse_patch(path)))
            except Exception as exc:
                errors.append(f"{path}: {exc}")

        if errors:
            self.results.setPlainText(
                self._tr("Lesefehler:\n", "Read errors:\n")
                + "\n".join(errors)
            )
            return

        findings = []
        compared = 0

        for (path_a, files_a), (path_b, files_b) in combinations(parsed, 2):
            map_a = {}
            map_b = {}

            for entry in files_a:
                map_a.setdefault(entry["path"], []).extend(entry["hunks"])
            for entry in files_b:
                map_b.setdefault(entry["path"], []).extend(entry["hunks"])

            for filename in sorted(set(map_a) & set(map_b)):
                for hunk_a in map_a[filename]:
                    for hunk_b in map_b[filename]:
                        compared += 1
                        changes_a = hunk_a["changes"]
                        changes_b = hunk_b["changes"]

                        if changes_a and changes_a == changes_b:
                            findings.append(
                                self._tr(
                                    "DOPPELTE ÄNDERUNG",
                                    "DUPLICATE CHANGE"
                                )
                                + f"\n{filename}\n"
                                + f"{Path(path_a).name} / {Path(path_b).name}\n"
                                + self._tr(
                                    "Ausgangszeile: ",
                                    "Original line: "
                                ) + str(hunk_a["old_start"])
                            )
                        elif _overlap(hunk_a, hunk_b):
                            findings.append(
                                self._tr(
                                    "MÖGLICHER KONFLIKT",
                                    "POSSIBLE CONFLICT"
                                )
                                + f"\n{filename}\n"
                                + f"{Path(path_a).name}: "
                                + f"{hunk_a['old_start']} "
                                + self._tr("bis ", "to ")
                                + f"{hunk_a['old_start'] + hunk_a['old_count']}\n"
                                + f"{Path(path_b).name}: "
                                + f"{hunk_b['old_start']} "
                                + self._tr("bis ", "to ")
                                + f"{hunk_b['old_start'] + hunk_b['old_count']}"
                            )

        if findings:
            result = self._tr(
                f"{len(findings)} Auffälligkeit(en) gefunden:\n\n",
                f"{len(findings)} finding(s) detected:\n\n"
            ) + "\n\n------------------------------\n\n".join(findings)
        else:
            result = self._tr(
                "Keine überlappenden oder doppelten Änderungen erkannt.\n"
                "Das ist keine Garantie für vollständige Kompatibilität.",
                "No overlapping or duplicate changes detected.\n"
                "This does not guarantee full compatibility."
            )

        summary = self._tr(
            f"\n\nGeprüfte Patch-Dateien: {len(parsed)}"
            f"\nVerglichene Hunk-Paare: {compared}"
            f"\n\nHinweis: Die Originaldateien wurden nicht verändert.",
            f"\n\nPatch files checked: {len(parsed)}"
            f"\nHunk pairs compared: {compared}"
            f"\n\nNote: Original files were not modified."
        )
        self.results.setPlainText(result + summary)

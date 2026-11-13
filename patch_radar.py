"""Read-only Patch Radar for OSCam Control Center."""

from itertools import combinations
from pathlib import Path

from PyQt6.QtCore import Qt
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
        self.language = "de" if str(language).lower().startswith("de") else "en"
        self.colors = colors if isinstance(colors, dict) else {}
        self.root = Path(__file__).resolve().parent

        self.setWindowTitle("OSCam Patch Radar")
        self.resize(900, 650)
        self.setMinimumSize(740, 520)

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

    def tr_text(self, de, en):
        return de if self.language == "de" else en

    def refresh_scan(self):
        from patch_compatibility_scanner import _parse_patch, _overlap

        parsed = []
        errors = []
        lines = []
        total = 0

        for variant, relative in self.VARIANTS:
            folder = self.root / relative

            if not folder.is_dir():
                lines.append(f"[FEHLT] {variant}: {folder}")
                errors.append(f"{variant}: directory missing")
                continue

            try:
                files = sorted(
                    p for p in folder.iterdir()
                    if p.is_file() and p.suffix.lower() in (".patch", ".diff")
                )
            except OSError as exc:
                lines.append(f"[ERROR] {variant}: {exc}")
                errors.append(str(exc))
                continue

            lines.append(f"[OK] {variant}: {len(files)} patch file(s)")

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
        self.summary.setText(
            f"Dateien: {total} | Konflikte: {conflicts} | "
            f"Doppelte Änderungen: {duplicates} | Fehler: {len(errors)}"
            if self.language == "de"
            else f"Files: {total} | Conflicts: {conflicts} | "
                 f"Duplicates: {duplicates} | Errors: {len(errors)}"
        )

        for kind, pair, path, count in findings:
            label = "Treffer" if self.language == "de" else "findings"
            lines.extend([
                "",
                f"[{kind}] {path} ({count} {label})",
                f"  {pair[0]} <-> {pair[1]}",
            ])

        if errors:
            lines.extend(["", "SCAN ERRORS:"])
            lines.extend(f"[ERROR] {e}" for e in errors)

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

from pathlib import Path
import shutil
import sys

file = Path("gui.py")

if not file.is_file():
    sys.exit("FEHLER: gui.py wurde im aktuellen Verzeichnis nicht gefunden.")

source = file.read_text(encoding="utf-8")
patched = source

replacements = [
    (
        "        self.UI_BUTTON_H = 50\n"
        "        self.UI_BADGE_H = 50\n"
        "        self.UI_PROGRESS_H = 25\n"
        "        self.UI_STATUS_H = 50\n"
        "        self.UI_RADIUS = 10",
        "        screen = QApplication.primaryScreen()\n"
        "        compact_fhd = bool(\n"
        "            screen and screen.availableGeometry().height() <= 1100\n"
        "        )\n"
        "\n"
        "        self.UI_BUTTON_H = 38 if compact_fhd else 50\n"
        "        self.UI_BADGE_H = 40 if compact_fhd else 50\n"
        "        self.UI_PROGRESS_H = 20 if compact_fhd else 25\n"
        "        self.UI_STATUS_H = 38 if compact_fhd else 50\n"
        "        self.B_HEIGHT = self.UI_BUTTON_H\n"
        "        self.UI_RADIUS = 10",
    ),
    (
        "        main_layout.setSpacing(12)\n"
        "        main_layout.setContentsMargins(12, 10, 12, 14)",
        "        main_layout.setSpacing(6 if compact_fhd else 12)\n"
        "        main_layout.setContentsMargins(\n"
        "            8 if compact_fhd else 12,\n"
        "            6 if compact_fhd else 10,\n"
        "            8 if compact_fhd else 12,\n"
        "            8 if compact_fhd else 14,\n"
        "        )",
    ),
    (
        "        header_widget.setMinimumHeight(160)",
        "        header_widget.setMinimumHeight(105 if compact_fhd else 160)",
    ),
    (
        "        controls_group_layout.setContentsMargins(0, 20, 15, 20)",
        "        controls_group_layout.setContentsMargins(\n"
        "            0, 6 if compact_fhd else 20,\n"
        "            8, 6 if compact_fhd else 20\n"
        "        )",
    ),
    (
        "        self.controls_header.setMinimumHeight(50)",
        "        self.controls_header.setMinimumHeight(32 if compact_fhd else 50)",
    ),
    (
        "                font-size: 20px;          /* Schrift im Header vergrößert */",
        "                font-size: {'14px' if compact_fhd else '20px'};",
    ),
    (
        "        CONTROL_HEIGHT = getattr(self, \"B_HEIGHT\", 50)",
        "        CONTROL_HEIGHT = self.UI_BUTTON_H",
    ),
    (
        "            font-size: 18px;\n"
        "            border-radius: {self.BUTTON_RADIUS}px;",
        "            font-size: {'13px' if compact_fhd else '18px'};\n"
        "            border-radius: {self.BUTTON_RADIUS}px;",
    ),
    (
        "                font-size: 18px;\n"
        "                background: transparent;",
        "                font-size: {'13px' if compact_fhd else '18px'};\n"
        "                background: transparent;",
    ),
    (
        "background-color: #444444; color: white; font-weight: bold; font-size: 20px;",
        "background-color: #444444; color: white; font-weight: bold; "
        "font-size: {'14px' if compact_fhd else '20px'};",
    ),
    (
        "            min-height: 45px;\n"
        "            max-height: 45px;",
        "           min-height: {self.UI_BUTTON_H}px;\n"
        "           max-height: {self.UI_BUTTON_H}px;",
    ),
]

# Erst alle Fundstellen prüfen, bevor etwas geschrieben wird.
for old, new in replacements:
    count = patched.count(old)
    if count != 1:
        sys.exit(
            f"ABBRUCH: Erwartete Code-Stelle genau einmal, gefunden: {count}\n"
            f"Beginn der gesuchten Stelle: {old[:100]!r}"
        )
    patched = patched.replace(old, new, 1)

backup = file.with_name("gui.py.bak_fhd_compact")

if backup.exists():
    sys.exit(f"ABBRUCH: Sicherung existiert bereits: {backup}")

shutil.copy2(file, backup)
file.write_text(patched, encoding="utf-8")

print("Full-HD-Kompaktmodus wurde eingefügt.")
print(f"Sicherung: {backup}")
print("Geändert wurde ausschließlich gui.py.")

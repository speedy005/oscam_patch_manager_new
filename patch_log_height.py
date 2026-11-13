from pathlib import Path
import shutil
import sys

changes = {
    "gui.py": [
        (
            "        console_layout.setContentsMargins(10, 12, 10, 10)\n"
            "        console_layout.setSpacing(8)",
            "        console_layout.setContentsMargins(6, 5, 6, 5)\n"
            "        console_layout.setSpacing(3)",
        ),
        (
            "        console_tools.setSpacing(4)",
            "        console_tools.setSpacing(2)",
        ),
        (
            "            tool_button.setIconSize(QSize(20, 20))",
            "            tool_button.setIconSize(QSize(16, 16))",
        ),
        (
            "            tool_font.setPointSizeF(13.0)",
            "            tool_font.setPointSizeF(10.0)",
        ),
        (
            "            tool_button.setMinimumHeight(38)",
            "            tool_button.setMinimumHeight(30)",
        ),
    ],
    "gui_layout_helper.py": [
        (
            "    info_text.setMinimumHeight(min(sh, max(150, int(sh * 0.22))))",
            "    log_min_height = min(sh, max(300, int(sh * 0.32)))\n"
            "    info_text.setMinimumHeight(log_min_height)\n"
            "\n"
            "    console_panel = getattr(window, 'console_panel', None)\n"
            "    if console_panel is not None:\n"
            "        console_panel.setMinimumHeight(log_min_height + 72)",
        ),
    ],
}

prepared = {}

for filename, replacements in changes.items():
    path = Path(filename)
    if not path.is_file():
        sys.exit(f"FEHLER: {filename} nicht gefunden.")

    content = path.read_text(encoding="utf-8")

    for old, new in replacements:
        count = content.count(old)
        if count != 1:
            sys.exit(
                f"ABBRUCH: {filename}: Fundstelle {count}-mal gefunden:\n{old}"
            )
        content = content.replace(old, new, 1)

    backup = path.with_name(path.name + ".bak_log_height")
    if backup.exists():
        sys.exit(f"ABBRUCH: Sicherung existiert bereits: {backup}")

    prepared[filename] = (path, backup, content)

for filename, (path, backup, content) in prepared.items():
    shutil.copy2(path, backup)
    path.write_text(content, encoding="utf-8")
    print(f"Geändert: {filename}")
    print(f"Sicherung: {backup}")

print("Log-Höhen-Patch erfolgreich angewendet.")

from pathlib import Path
import shutil
import sys

path = Path("gui_layout_helper.py")
content = path.read_text(encoding="utf-8")

old = """    log_min_height = min(sh, max(300, int(sh * 0.32)))
    info_text.setMinimumHeight(log_min_height)

    console_panel = getattr(window, 'console_panel', None)
    if console_panel is not None:
        console_panel.setMinimumHeight(log_min_height + 72)"""

new = """    info_text.setMinimumHeight(0)
    console_panel = getattr(window, 'console_panel', None)
    if console_panel is not None:
        console_panel.setMinimumHeight(0)"""

if content.count(old) != 1:
    sys.exit("Abbruch: Die erwartete Stelle wurde nicht genau einmal gefunden.")

backup = Path("gui_layout_helper.py.bak_overlap_fix")
if backup.exists():
    sys.exit(f"Abbruch: Sicherung existiert bereits: {backup}")

shutil.copy2(path, backup)
path.write_text(content.replace(old, new, 1), encoding="utf-8")

print("Log-Mindesthöhe zurückgesetzt.")
print(f"Sicherung erstellt: {backup}")

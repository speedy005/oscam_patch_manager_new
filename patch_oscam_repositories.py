from pathlib import Path
import shutil
import re

p = Path("system_check.py")
s = p.read_text(encoding="utf-8")

# Repository-Liste suchen und vollständig ersetzen
pattern = r'(?m)^(\s*)repo_list\s*=\s*\[.*?^\s*\]'

new_list = '''repo_list = [
    (
        "📡",
        "Streamboard Oscam",
        "https://git.streamboard.tv/common/oscam",
    ),
    (
        "🐙",
        "OSCam Emu Mirror",
        "https://github.com/oscam-mirror/oscam-emu",
    ),
    (
        "⭐",
        "speedy Oscam Emu",
        "https://github.com/speedy005/Oscam-emu",
    ),
    (
        "⭐",
        "speedy Oscam Git",
        "https://github.com/speedy005/oscam-git",
    ),
    (
        "🔗",
        "GitHub API Server",
        "api.github.com",
    ),
]'''

matches = list(re.finditer(pattern, s, re.S))

if len(matches) != 1:
    raise SystemExit(
        f"Abbruch: repo_list {len(matches)}-mal gefunden. "
        "Datei wurde nicht geändert."
    )

# Einrückung der ursprünglichen Liste übernehmen
indent = matches[0].group(1)
new_list = new_list.replace(
    "\n",
    "\n" + indent
)

new_list = new_list.replace(
    indent + "repo_list",
    "repo_list",
    1
)

# Backup
shutil.copy2(p, "system_check.py.bak_oscam_repositories")

s = s[:matches[0].start()] + new_list + s[matches[0].end():]

p.write_text(s, encoding="utf-8")

print("Repository-Liste erfolgreich aktualisiert.")
print("5 Einträge:")
print("- Streamboard Oscam")
print("- OSCam Emu Mirror")
print("- speedy Oscam Emu")
print("- speedy Oscam Git")
print("- GitHub API Server")

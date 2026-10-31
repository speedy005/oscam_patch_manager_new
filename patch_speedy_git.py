from pathlib import Path
import shutil

p = Path("system_check.py")
s = p.read_text(encoding="utf-8")

old_list = '''            repo_list = [
                (
                    "📡",
                    "Streamboard Oscam",
                    "git.streamboard.tv",


                ),
                (
                    "🐙",
                    "OSCam Emu Mirror",
                    "https://github.com/oscam-mirror/oscam-emu.git",
                ),
                (
                    "⭐",
                    "speedy Oscam Emu",
                    "https://github.com/speedy005/Oscam-emu",
                ),
                (
                    "🔗",
                    "GitHub API Server",
                    "api.github.com",
                ),
            ]'''

new_list = '''            repo_list = [
                (
                    "📡",
                    "Streamboard Oscam",
                    "git.streamboard.tv",
                ),
                (
                    "🐙",
                    "OSCam Emu Mirror",
                    "https://github.com/oscam-mirror/oscam-emu.git",
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

old_check = '''                online = False

                try:
                    # TCP-Test statt gethostbyname().
                    # Dadurch haben wir einen echten Timeout.
                    with socket.create_connection(
                        (host, 443),
                        timeout=self.SOCKET_TIMEOUT,
                    ):
                        online = True

                except (
                    OSError,
                    socket.timeout,
                ):
                    online = False
'''

new_check = '''                online = False

                try:
                    if r_name == "speedy Oscam Git":
                        import subprocess

                        result = subprocess.run(
                            [
                                "git",
                                "ls-remote",
                                "https://github.com/speedy005/oscam-git",
                                "HEAD",
                            ],
                            capture_output=True,
                            text=True,
                            timeout=self.SOCKET_TIMEOUT,
                            check=False,
                        )

                        online = (
                            result.returncode == 0
                            and bool(result.stdout.strip())
                        )
                    else:
                        with socket.create_connection(
                            (host, 443),
                            timeout=self.SOCKET_TIMEOUT,
                        ):
                            online = True

                except (
                    OSError,
                    socket.timeout,
                    subprocess.TimeoutExpired,
                ):
                    online = False
'''

if s.count(old_list) != 1:
    raise SystemExit(
        f"Repository-Liste {s.count(old_list)}-mal gefunden. "
        "Keine Änderung vorgenommen."
    )

if s.count(old_check) != 1:
    raise SystemExit(
        f"Prüfblock {s.count(old_check)}-mal gefunden. "
        "Keine Änderung vorgenommen."
    )

shutil.copy2(p, "system_check.py.bak_speedy_git")

s = s.replace(old_list, new_list, 1)
s = s.replace(old_check, new_check, 1)

p.write_text(s, encoding="utf-8")

print("PATCH ERFOLGREICH: speedy Oscam Git hinzugefügt.")

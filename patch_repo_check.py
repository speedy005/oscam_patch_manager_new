from pathlib import Path
import shutil
import subprocess

p = Path("system_check.py")
s = p.read_text(encoding="utf-8")

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
                    if r_name != "GitHub API Server":
                        result = subprocess.run(
                            ["git", "ls-remote", host],
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

if s.count(old_check) != 1:
    raise SystemExit(
        f"Abbruch: Prüfblock {s.count(old_check)}-mal gefunden. "
        "Keine Änderung vorgenommen."
    )

shutil.copy2(p, "system_check.py.bak_repo_check")

s = s.replace(old_check, new_check, 1)
p.write_text(s, encoding="utf-8")

print("PATCH ERFOLGREICH")

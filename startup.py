"""OSCam Patch Manager module fragment: Application entry point."""

# Explicit module imports retained for compatibility with legacy callbacks.
import ctypes
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import traceback

from PyQt6.QtCore import Qt, QTimer, QLibraryInfo
from PyQt6.QtWidgets import QApplication, QMessageBox

from bootstrap import auto_install_emoji_font
from dialogs_splash import CinematicMatrixSplash
from gui import PatchManagerGUI
from paths import CONFIG_FILE


def _is_elevated():
    """Return whether this process already has administrator/root privileges."""
    if platform.system() == "Windows":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    if platform.system() == "Linux":
        return hasattr(os, "geteuid") and os.geteuid() == 0

    return False


def _restart_elevated():
    """
    Restart this application with elevated privileges.

    Uses absolute paths so a sudo/pkexec process cannot accidentally resolve
    main.py relative to /root. On Linux, only the display-session variables
    needed by Qt are forwarded.
    """
    system = platform.system()
    script_path = os.path.abspath(sys.argv[0])
    python_cmd = [sys.executable, script_path, *sys.argv[1:], "--elevated"]

    if system == "Windows":
        if not ctypes.windll.shell32.IsUserAnAdmin():
            params = subprocess.list2cmdline(python_cmd[1:])
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                params,
                os.path.dirname(script_path),
                1,
            )
            if result <= 32:
                raise RuntimeError(
                    f"Windows could not elevate the process (error {result})."
                )
            return True
        return False

    if system == "Linux":
        if os.geteuid() == 0:
            return False

        launcher = shutil.which("pkexec") or shutil.which("sudo")
        if not launcher:
            raise RuntimeError(
                "Neither pkexec nor sudo was found; cannot request root privileges."
            )

        env_values = {}
        for key in (
            "DISPLAY",
            "XAUTHORITY",
            "XDG_RUNTIME_DIR",
            "WAYLAND_DISPLAY",
            "DBUS_SESSION_BUS_ADDRESS",
        ):
            value = os.environ.get(key)
            if value:
                env_values[key] = value

        # Prefer sudo when available: pass argv directly, without shell quoting.
        sudo = shutil.which("sudo")
        if sudo:
            command = [sudo, "env"]
            command.extend(f"{key}={value}" for key, value in env_values.items())
            command.extend(python_cmd)
            os.execv(sudo, command)

        # pkexec accepts an executable and arguments. Use /usr/bin/env to pass
        # environment values without building an unsafe shell command.
        env_exe = shutil.which("env") or "/usr/bin/env"
        command = [launcher, env_exe]
        command.extend(f"{key}={value}" for key, value in env_values.items())
        command.extend(python_cmd)
        os.execv(launcher, command)

    return False




def _ensure_git():
    """Prüft Git und bietet die Installation an, falls es fehlt."""
    git = shutil.which("git")

    if git:
        result = subprocess.run(
            [git, "--version"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("[GIT] Git verfügbar:", result.stdout.strip(), flush=True)
            return True

    answer = QMessageBox.question(
        None,
        "Git fehlt",
        "Git wurde nicht gefunden oder funktioniert nicht.\n\n"
        "Soll Git jetzt automatisch installiert werden?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )

    if answer != QMessageBox.StandardButton.Yes:
        return False

    system = platform.system()

    try:
        if system == "Windows":
            winget = shutil.which("winget")

            if not winget:
                QMessageBox.warning(
                    None,
                    "Git-Installation",
                    "winget wurde nicht gefunden.\n\n"
                    "Bitte Git manuell installieren:\n"
                    "https://git-scm.com/download/win"
                )
                return False

            result = subprocess.run(
                [
                    winget, "install",
                    "--id", "Git.Git",
                    "-e",
                    "--source", "winget",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ],
                check=False
            )

            if result.returncode != 0:
                raise RuntimeError("Git konnte über winget nicht installiert werden.")

            # Git für den aktuellen Prozess verfügbar machen.
            candidates = [
                os.path.join(
                    os.environ.get("ProgramFiles", r"C:\Program Files"),
                    "Git", "cmd"
                ),
                os.path.join(
                    os.environ.get("LOCALAPPDATA", ""),
                    "Programs", "Git", "cmd"
                ),
            ]

            for folder in candidates:
                if os.path.isfile(os.path.join(folder, "git.exe")):
                    os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")
                    break

        elif system == "Linux":
            if shutil.which("apt-get"):
                commands = [
                    ["apt-get", "update"],
                    ["apt-get", "install", "-y", "git"],
                ]
            elif shutil.which("dnf"):
                commands = [["dnf", "install", "-y", "git"]]
            elif shutil.which("pacman"):
                commands = [["pacman", "-S", "--noconfirm", "git"]]
            elif shutil.which("zypper"):
                commands = [["zypper", "--non-interactive", "install", "git"]]
            else:
                raise RuntimeError("Kein unterstützter Linux-Paketmanager gefunden.")

            if hasattr(os, "geteuid") and os.geteuid() == 0:
                launcher = []
            else:
                sudo = shutil.which("sudo")
                if not sudo:
                    raise RuntimeError("sudo wurde nicht gefunden.")
                launcher = [sudo]

            for command in commands:
                result = subprocess.run(
                    launcher + command,
                    check=False
                )
                if result.returncode != 0:
                    raise RuntimeError(
                        "Git-Installation fehlgeschlagen: "
                        + " ".join(command)
                    )
        else:
            raise RuntimeError(
                f"Automatische Git-Installation für {system} nicht eingerichtet."
            )

        # Installation überprüfen.
        git = shutil.which("git")

        if not git:
            raise RuntimeError(
                "Git wurde installiert, ist aber noch nicht erreichbar."
            )

        result = subprocess.run(
            [git, "--version"],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError("Git-Version konnte nicht geprüft werden.")

        QMessageBox.information(
            None,
            "Git installiert",
            "Git wurde erfolgreich installiert:\n\n"
            + result.stdout.strip()
            + "\n\nDer Patch Manager wird neu gestartet."
        )

        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as exc:
        QMessageBox.warning(
            None,
            "Git-Installationsfehler",
            str(exc)
        )
        return False

    return True


def _ensure_qtsvg():
    """Installiert PyQt6.QtSvg passend zum Betriebssystem."""
    system = platform.system()

    try:
        from PyQt6.QtSvg import QSvgRenderer
        return True
    except ImportError:
        pass

    answer = QMessageBox.question(
        None,
        "QtSvg-Komponente fehlt",
        "Die QtSvg-Komponente fehlt.\n\n"
        "Soll sie jetzt automatisch installiert werden?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )

    if answer != QMessageBox.StandardButton.Yes:
        return False

    is_wsl = (
        system == "Linux"
        and (
            "microsoft" in platform.release().lower()
            or bool(os.environ.get("WSL_INTEROP"))
            or bool(os.environ.get("WSL_DISTRO_NAME"))
        )
    )

    try:
        # Windows, macOS und virtuelle Python-Umgebungen:
        # Installation in genau der aktiven Python-Umgebung.
        is_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)

        if system in ("Windows", "Darwin") or is_venv:
            command = [
                sys.executable, "-m", "pip",
                "install", "--upgrade", "PyQt6"
            ]
            result = subprocess.run(command, check=False)

        elif system == "Linux":
            # Linux-System-Python: passenden Paketmanager verwenden.
            if shutil.which("apt-get"):
                package_command = [
                    "apt-get", "install", "-y",
                    "python3-pyqt6.qtsvg"
                ]
                update_command = ["apt-get", "update"]

            elif shutil.which("dnf"):
                package_command = [
                    "dnf", "install", "-y", "python3-pyqt6"
                ]
                update_command = ["dnf", "makecache"]

            elif shutil.which("pacman"):
                package_command = [
                    "pacman", "-S", "--noconfirm", "python-pyqt6"
                ]
                update_command = ["pacman", "-Sy"]

            elif shutil.which("zypper"):
                package_command = [
                    "zypper", "--non-interactive",
                    "install", "python3-qt6"
                ]
                update_command = ["zypper", "refresh"]

            else:
                package_command = None
                update_command = None

            result = None

            if package_command:
                if is_wsl:
                    launcher = shutil.which("sudo")
                elif shutil.which("pkexec"):
                    launcher = shutil.which("pkexec")
                else:
                    launcher = shutil.which("sudo")

                if launcher:
                    update_result = subprocess.run(
                        [launcher] + update_command,
                        check=False
                    )

                    if update_result.returncode == 0:
                        result = subprocess.run(
                            [launcher] + package_command,
                            check=False
                        )

            # Fallback: pip in der aktiven Python-Umgebung.
            if result is None or result.returncode != 0:
                result = subprocess.run(
                    [
                        sys.executable, "-m", "pip",
                        "install", "PyQt6"
                    ],
                    check=False
                )
        else:
            QMessageBox.warning(
                None,
                "Nicht unterstütztes Betriebssystem",
                f"Automatische QtSvg-Installation für {system} "
                "ist nicht eingerichtet."
            )
            return False

        if result.returncode != 0:
            QMessageBox.warning(
                None,
                "Installation fehlgeschlagen",
                "QtSvg konnte nicht automatisch installiert werden.\n\n"
                "Bitte prüfe die Administratorrechte und die "
                "Python-Paketinstallation."
            )
            return False

        # Installation tatsächlich überprüfen.
        from PyQt6.QtSvg import QSvgRenderer

        QMessageBox.information(
            None,
            "Installation erfolgreich",
            "QtSvg wurde installiert.\n"
            "Der OSCam Patch Manager wird neu gestartet."
        )

        os.execv(sys.executable, [sys.executable] + sys.argv)

    except Exception as exc:
        QMessageBox.warning(
            None,
            "QtSvg-Installationsfehler",
            str(exc)
        )
        return False

    return True


def main():
    """Configure Qt and start the OSCam Patch Manager GUI."""
    # Avoid accidental recursive elevation.
    

    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("NO_AT_BRIDGE", "1")

    system = platform.system()
    if system == "Linux" and not os.environ.get("QT_QPA_PLATFORM"):
        if os.environ.get("WAYLAND_DISPLAY"):
            os.environ["QT_QPA_PLATFORM"] = "wayland"
        elif os.environ.get("DISPLAY"):
            os.environ["QT_QPA_PLATFORM"] = "xcb"
    elif system == "Windows":
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                try:
                    stream.reconfigure(encoding="utf-8")
                except (OSError, ValueError):
                    pass

    try:
        policy = getattr(Qt.HighDpiScaleFactorRoundingPolicy, "PassThrough", None)
        if policy is not None:
            QApplication.setHighDpiScaleFactorRoundingPolicy(policy)
    except Exception:
        pass

    plugin_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    if plugin_path:
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", plugin_path)

    app = QApplication.instance() or QApplication(sys.argv)
    if not _ensure_git():
        return 0
    if not _ensure_qtsvg():
        return 0
    app.setStyle("Fusion")

    screen = app.primaryScreen()
    if screen is not None:
        geometry = screen.availableGeometry()
        width, height = geometry.width(), geometry.height()
    else:
        width, height = 0, 0

    try:
        import getpass
        current_user = getpass.getuser()
    except Exception:
        current_user = (
            os.environ.get("USERNAME")
            or os.environ.get("USER")
            or "unknown"
        )

   

    

    main_window = None

    def actually_start():
        nonlocal main_window
        print("[TRACE] actually_start() wurde erreicht", flush=True)
        try:
            main_window = PatchManagerGUI()

            main_window.setWindowTitle("OSCam Emu Patch Manager new - by speedy005")
            main_window.show()
            main_window._debug_timer = QTimer(main_window)
            main_window._debug_timer.setSingleShot(True)
            main_window._debug_timer.timeout.connect(
                lambda: print("[PERSISTENT-TIMER] Qt-Timer funktioniert", flush=True)
            )
            main_window._debug_timer.start(3000)
            QTimer.singleShot(3000, lambda: print("[TIMER-TEST] Qt-Timer funktioniert", flush=True))
            main_window.raise_()

            # Fenstergeometrie nach dem Anzeigen wiederherstellen.

            def restore_main_window():
                print("[TRACE] restore_main_window() wurde erreicht", flush=True)
                try:
                    main_window._restore_window_state_after_show()
                except Exception:
                    traceback.print_exc()

                def debug_layout_sizes():
                    _original_stdout = sys.stdout
                    sys.stdout = sys.__stderr__
                    try:
                        print("\\n========== OSCAM LAYOUT DIAGNOSE ==========", flush=True)
                        print(
                            f"Fenster: {main_window.width()}x{main_window.height()}",
                            flush=True,
                        )
    
                        layout = main_window.layout()
                        if layout is not None:
                            print(
                                f"Hauptlayout: Höhe={layout.geometry().height()}, "
                                f"sizeHint={layout.sizeHint().height()}",
                                flush=True,
                            )
                            for i in range(layout.count()):
                                item = layout.itemAt(i)
                                widget = item.widget()
                                if widget is not None:
                                    print(
                                        f"{i}: {widget.objectName() or widget.__class__.__name__}: "
                                        f"Höhe={widget.height()}, "
                                        f"sizeHint={widget.sizeHint().height()}, "
                                        f"min={widget.minimumHeight()}, "
                                        f"max={widget.maximumHeight()}",
                                        flush=True,
                                    )
    
                        for name in (
                            "console_panel", "info_text", "header_widget",
                            "controls_group", "grid_container",
                        ):
                            widget = getattr(main_window, name, None)
                            if widget is not None:
                                print(
                                    f"{name}: Höhe={widget.height()}, "
                                    f"sizeHint={widget.sizeHint().height()}, "
                                    f"min={widget.minimumHeight()}, "
                                    f"max={widget.maximumHeight()}",
                                    flush=True,
                                )
    
                        print("========== ENDE DIAGNOSE ==========\\n", flush=True)
                    finally:
                        sys.stdout = _original_stdout
                QTimer.singleShot(1500, debug_layout_sizes)

            QTimer.singleShot(1000, restore_main_window)


            if "--perform-update" in sys.argv:
                sys.argv.remove("--perform-update")
                if hasattr(main_window, "plugin_update_action"):
                    QTimer.singleShot(
                        1500,
                        main_window.plugin_update_action,
                    )
                else:
                    print(
                        "[SYSTEM] Update konnte nicht automatisch "
                        "gestartet werden: Methode nicht gefunden."
                    )

            if hasattr(main_window, "update_ui_texts"):
                QTimer.singleShot(100, main_window.update_ui_texts)

            if system == "Windows":
                try:
                    import winsound
                    winsound.Beep(1500, 100)
                except Exception:
                    pass

        except Exception:
            details = traceback.format_exc()
            print(f"FATAL ERROR:\n{details}")
            message = QMessageBox()
            message.setIcon(QMessageBox.Icon.Critical)
            message.setWindowTitle("SYSTEM FAILURE")
            message.setText("Kritischer Fehler beim Laden des Kern-Moduls.")
            message.setDetailedText(details)
            message.setStyleSheet(
                "background-color: #050505; color: #00ff41; "
                "font-family: 'Consolas';"
            )
            message.exec()
            app.exit(1)

    def launch_main_gui():
        QTimer.singleShot(200, actually_start)

    # Splash-Einstellungen aus der zentralen config.json laden.
    splash_config = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
            loaded_config = json.load(handle)
        if isinstance(loaded_config, dict):
            splash_config = loaded_config
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    splash_mode = str(splash_config.get("splash_mode", "bot")).lower()
    if splash_mode not in ("bot", "premium", "dashboard", "reactor360", "nebula", "minimal", "off"):
        splash_mode = "bot"

    if splash_mode == "off":
        print("[SYSTEM] Splash-Screen deaktiviert – starte Hauptfenster direkt.")
        QTimer.singleShot(0, actually_start)
    else:
        try:
            splash_duration = splash_config.get("splash_duration", 22000)
            try:
                splash_duration = max(5000, min(60000, int(splash_duration)))
            except (TypeError, ValueError):
                splash_duration = 22000
            splash_sound_enabled = bool(
                splash_config.get("splash_sound_enabled", True)
            )
            try:
                splash_volume = max(0, min(100, int(
                    splash_config.get("splash_volume", 65)
                )))
            except (TypeError, ValueError):
                splash_volume = 65
            try:
                splash_speed = max(50, min(200, int(
                    splash_config.get("splash_speed", 100)
                )))
            except (TypeError, ValueError):
                splash_speed = 100

            splash_profiles = splash_config.get("splash_sound_profiles", {})
            if not isinstance(splash_profiles, dict):
                splash_profiles = {}
            selected_sound_profile = splash_profiles.get(splash_mode, {})
            if not isinstance(selected_sound_profile, dict):
                selected_sound_profile = {}

            splash = CinematicMatrixSplash(
                duration=splash_duration,
                sound_enabled=splash_sound_enabled,
                sound_volume=splash_volume,
                variant=splash_mode,
                animation_speed=splash_speed,
                sound_profile=selected_sound_profile,
            )
            splash.finished.connect(launch_main_gui)
            splash.show()
        except Exception as exc:
            print(f"[SYSTEM] Splash-Screen übersprungen: {exc}")
            actually_start()

    return app.exec()

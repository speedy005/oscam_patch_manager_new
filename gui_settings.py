"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerSettingsMixin:
    """Patch Manager Settings"""

    def change_language(self, index=None):
        """Wechselt die Sprache, aktualisiert die UI und führt die Abschlussanimation aus."""
        import os
        import platform
        import re

        from PyQt6.QtCore import QTimer, QRect, Qt
        from PyQt6.QtGui import QFont, QColor, QPixmap
        from PyQt6.QtWidgets import QApplication, QGroupBox, QLabel

        # Schutz vor mehrfacher Ausführung
        if not getattr(self, "language_box", None):
            return
        if getattr(self, "_block_language_change", False):
            return
        self._block_language_change = True

        pbar = getattr(self, "progress_bar", None)
        finished = {"value": False}

        def log_error(stage, exc):
            print(f"[change_language] {stage}: {exc}")

        def release_lock():
            self._block_language_change = False

        def update_pbar(value, text):
            if pbar is not None:
                pbar.setValue(value)
                pbar.setFormat(f"{text} %p%")
            QApplication.processEvents()

        def strip_icons(text):
            return re.sub(r"^[^\w\s]+", "", str(text)).strip()

        def blink_widget(widget, times=6, interval=300):
            if widget is None:
                return
            widget.show()
            widget.raise_()
            state = {"count": 0}

            def toggle():
                widget.setVisible(not widget.isVisible())
                state["count"] += 1
                if state["count"] < times * 2:
                    QTimer.singleShot(interval, toggle)
                else:
                    widget.setVisible(True)

            toggle()

        def after_animation():
            """Aktualisiert die verbleibenden Labels und startet den Abschluss."""
            try:
                lang_dict = getattr(self, "TEXT", {}) or {}
                is_de = getattr(self, "LANG", "en") == "de"

                if hasattr(self, "commit_label"):
                    self.commit_label.setText(
                        lang_dict.get(
                            "commit_count_label",
                            "Anzahl Commits:" if is_de else "Commit Count:",
                        )
                    )

                if hasattr(self, "color_label"):
                    self.color_label.setText(
                        lang_dict.get("color_label", "Farbe:" if is_de else "Color:")
                    )

                if hasattr(self, "log_button"):
                    self.log_button.setText(
                        lang_dict.get(
                            "log_button_text",
                            " Log speichern" if is_de else " Save Log",
                        )
                    )

                # Live-Konsole: neue Werkzeugbuttons der gewählten Sprache anpassen.
                if hasattr(self, "copy_log_button"):
                    self.copy_log_button.setText(
                        lang_dict.get("copy_log_button", "LOG KOPIEREN" if is_de else "COPY LOG")
                    )
                    self.copy_log_button.setToolTip(
                        lang_dict.get(
                            "copy_log_tooltip",
                            "Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren"
                            if is_de else "Copy all visible console output to the clipboard",
                        )
                    )
                if hasattr(self, "clear_console_button"):
                    self.clear_console_button.setText(
                        lang_dict.get("clear_console_button", "KONSOLE LEEREN" if is_de else "CLEAR CONSOLE")
                    )
                    self.clear_console_button.setToolTip(
                        lang_dict.get(
                            "clear_console_tooltip",
                            "Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert"
                            if is_de else "Clear only the visible console output; log files remain unchanged",
                        )
                    )
                # BUILD-LOG-Analyse und Systemdiagnose ebenfalls live umschalten.
                if hasattr(self, "analyze_build_logs_button"):
                    self.analyze_build_logs_button.setText(
                        lang_dict.get("analyze_build_logs_button", "BUILD-LOG ANALYSIEREN" if is_de else "ANALYZE BUILD LOG")
                    )
                    self.analyze_build_logs_button.setToolTip(
                        lang_dict.get("analyze_build_logs_tooltip", "Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen" if is_de else "Check the newest build log for common errors and warnings")
                    )
                if hasattr(self, "diagnostics_button"):
                    self.diagnostics_button.setText(
                        lang_dict.get("system_diagnostics_button", "SYSTEM-DIAGNOSE" if is_de else "SYSTEM DIAGNOSTICS")
                    )
                    self.diagnostics_button.setToolTip(
                        lang_dict.get("system_diagnostics_tooltip", "System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build" if is_de else "Check system, tool directories and existing build logs; does not start a build")
                    )

                if hasattr(self, "header_label"):
                    self.header_label.setText(
                        strip_icons(
                            lang_dict.get(
                                "settings_header",
                                "Einstellungen" if is_de else "Settings",
                            )
                        )
                    )

                # OSCam-Status kurz hervorheben
                status_label = getattr(self, "status_label", None)
                if status_label:
                    timestamp = getattr(self, "last_timestamp", "--:--:--")
                    rev = getattr(self, "current_rev", "----")
                    msg = lang_dict.get(
                        "oscam_uptodate",
                        "OSCam ist aktuell." if is_de else "OSCam is up to date.",
                    )
                    state = {"count": 0}

                    def blink_status():
                        color = "#FF0000" if state["count"] % 2 == 0 else "#00FF00"
                        status_label.setText(
                            f"✅ <span style='font-size:24px;color:#FF0000;font-weight:bold;'>"
                            f"[{timestamp}]</span> "
                            f"<span style='font-size:24px;color:#00FF00;font-weight:bold;'>"
                            f"{msg}</span> "
                            f"<span style='font-size:24px;color:{color};font-weight:bold;'>"
                            f"{rev}</span>"
                        )
                        state["count"] += 1
                        if state["count"] < 6:
                            QTimer.singleShot(300, blink_status)

                    blink_status()

                # Gruppentitel an die gewählte Sprache anpassen
                for box in self.findChildren(QGroupBox):
                    title = box.title()
                    if "Settings" in title or "Einstellungen" in title:
                        box.setTitle("Einstellungen" if is_de else "Settings")
                    if any(term in title for term in ("Configuration", "Konfiguration", "GitHub")):
                        box.setTitle(
                            "GitHub Konfiguration" if is_de else "GitHub Configuration"
                        )

                if hasattr(self, "btn_modifier"):
                    self.btn_modifier.setText(
                        f"👤 {strip_icons(lang_dict.get('modifier_button_text', 'Patch Autor' if is_de else 'Patch Author'))}"
                    )

                if hasattr(self, "btn_patch_online"):
                    self.btn_patch_online.setText(
                        f"🌐 {strip_icons(lang_dict.get('patch_online_download', 'Patches aus Git laden' if is_de else 'Load Patches from Git'))}"
                    )

                # Theme und Tooltips nach den Textänderungen erneut anwenden
                try:
                    if hasattr(self, "apply_global_button_style"):
                        self.apply_global_button_style()
                except Exception as exc:
                    log_error("Button-Theme/Tooltips konnten nicht aktualisiert werden", exc)

                # Button-Texte nach der Layout-Neuberechnung anpassen
                try:
                    if hasattr(self, "_fit_all_button_texts"):
                        layout = self.layout()
                        if layout is not None:
                            layout.activate()
                        QTimer.singleShot(0, self._fit_all_button_texts)
                        QTimer.singleShot(250, self._fit_all_button_texts)
                except Exception as exc:
                    log_error("Button-Text-Anpassung fehlgeschlagen", exc)

                # Finales Label vorbereiten und zunächst verstecken
                if hasattr(self, "final_label") and self.final_label:
                    self.final_label.setText(
                        lang_dict.get(
                            "final_label",
                            "🛠️ Was bauen wir heute?" if is_de else "🛠️ What are we building today?",
                        )
                    )
                    self.final_label.hide()

                # Systemcheck nach dem Sprachwechsel starten
                if hasattr(self, "run_full_system_check"):
                    QTimer.singleShot(
                        200,
                        lambda: self.run_full_system_check(clear_log=True),
                    )

                def final_blink():
                    try:
                        final_geom = pbar.geometry() if pbar is not None else QRect(20, 20, 400, 40)
                        final_label = getattr(self, "final_label", None)

                        if final_label is None:
                            final_label = QLabel(
                                lang_dict.get(
                                    "final_label",
                                    "🛠️ Was bauen wir heute?" if is_de else "🛠️ What are we building today?",
                                ),
                                self,
                            )
                            self.final_label = final_label

                        final_label.setAlignment(
                            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                        )
                        final_label.setGeometry(final_geom)
                        final_label.setStyleSheet(
                            "QLabel { border: 2px solid cyan; background-color: black; "
                            "color: cyan; font-weight: bold; font-size: 24px; "
                            "font-family: Arial, Segoe UI, sans-serif; border-radius: 6px; }"
                        )
                        final_label.show()
                        final_label.raise_()

                        blink_colors = ["transparent", "cyan", "transparent", "cyan", "transparent", "cyan"]
                        for delay, color in zip((0, 300, 600, 900, 1200, 1500), blink_colors):
                            QTimer.singleShot(
                                delay,
                                lambda c=color: final_label.setStyleSheet(
                                    "QLabel { border: 2px solid cyan; background-color: black; "
                                    f"color: {c}; font-weight: bold; font-size: 24px; "
                                    "font-family: Arial, Segoe UI, sans-serif; border-radius: 6px; }"
                                ),
                            )

                        if pbar is not None:
                            pbar.setValue(100)
                            pbar.setFormat("✅ OK")
                            QTimer.singleShot(5000, lambda: pbar.setFormat("%p%"))

                        try:
                            if hasattr(self, "hide_language_overlay"):
                                self.hide_language_overlay()
                        except Exception as exc:
                            log_error("Overlay konnte nicht ausgeblendet werden", exc)
                    except Exception as exc:
                        log_error("Abschlussanimation fehlgeschlagen", exc)
                    finally:
                        finished["value"] = True
                        release_lock()

                QTimer.singleShot(500, final_blink)

            except Exception as exc:
                log_error("Fehler beim Abschluss des Sprachwechsels", exc)
                try:
                    if hasattr(self, "hide_language_overlay"):
                        self.hide_language_overlay()
                except Exception as hide_exc:
                    log_error("Overlay konnte nicht ausgeblendet werden", hide_exc)
                finally:
                    finished["value"] = True
                    release_lock()

        try:
            selected = self.language_box.currentText().upper()
            self.LANG = (
                "de"
                if any(token in selected for token in ("DE", "DEU", "DEUTSCH"))
                else "en"
            )
            # Persist language immediately so it survives a normal restart.
            # Keep both config aliases in sync for older code paths.
            try:
                config_obj = getattr(self, "cfg", None)
                if not isinstance(config_obj, dict):
                    config_obj = getattr(self, "current_config", None)
                if not isinstance(config_obj, dict):
                    config_obj = {}
                config_obj["language"] = self.LANG
                if hasattr(self, "cfg"):
                    self.cfg = config_obj
                if hasattr(self, "current_config"):
                    self.current_config = config_obj
                save_config_func = globals().get("save_config")
                if callable(save_config_func) and not getattr(self, "is_loading", False):
                    save_config_func(config_obj, gui_instance=self, silent=True)
            except Exception as save_exc:
                print(f"[change_language] Sprache konnte nicht gespeichert werden: {save_exc}")
            is_de = self.LANG == "de"

            overlay_text = "Sprache wird angepasst..." if is_de else "Switching language..."
            update_pbar(10, f"⏳ {overlay_text}")

            if hasattr(self, "loading_overlay") and hasattr(self, "loading_label"):
                self.loading_overlay.setGeometry(self.rect())
                self.loading_label.setText(overlay_text)
                self.loading_overlay.show()
                self.loading_overlay.raise_()
                QApplication.processEvents()

            safe_play_func = globals().get("safe_play")
            if callable(safe_play_func):
                try:
                    safe_play_func("service-logout.oga")
                except Exception as exc:
                    log_error("Sprachwechsel-Sound fehlgeschlagen", exc)

            # Schreibrechte prüfen/reparieren, falls die Methode vorhanden ist
            perm_text = "Schreibrechte werden geprüft..." if is_de else "Checking write permissions..."
            update_pbar(25, f"🔐 {perm_text}")
            fix_permissions = getattr(self, "fix_all_tool_permissions", None)
            if callable(fix_permissions):
                try:
                    fix_permissions()
                except Exception as exc:
                    log_error("Rechteprüfung fehlgeschlagen", exc)

            load_text = "Texte werden geladen..." if is_de else "Loading texts..."
            update_pbar(30, f"⏳ {load_text}")

            all_texts = globals().get("TEXTS", {})
            if not all_texts:
                try:
                    all_texts = ensure_dependencies()
                except Exception as exc:
                    log_error("Sprachdateien konnten nicht geladen werden", exc)
                    all_texts = {}

            self.TEXT = all_texts.get(self.LANG, {})
            lang_dict = self.TEXT

            
            ui_text = "UI wird aktualisiert..." if is_de else "Updating UI..."
            update_pbar(50, f"⏳ {ui_text}")

            update_language = getattr(self, "update_language", None)
            if callable(update_language):
                update_language()

            # Alle UI-Texte aktualisieren, einschließlich "Rechte fixen"
            update_ui_texts = getattr(self, "update_ui_texts", None)
            if callable(update_ui_texts):
                try:
                    update_ui_texts()
                except Exception as exc:
                    log_error("UI-Texte konnten nicht aktualisiert werden", exc)


            # Status der Installationsbuttons prüfen und Beschriftung aktualisieren
            button_config = (
                ("btn_s3", "S3", "S3_PATH", "/opt/s3", "s3"),
                ("btn_s4", "S4", "S4_PATH", "/opt/simplebuild4", "s4"),
                ("btn_ncam", "NCam", "NCAM_PATH", "/opt/ncam", "ncam"),
            )

            for btn_attr, display_name, path_attr, default_path, executable in button_config:
                btn = getattr(self, btn_attr, None)
                if btn is None:
                    continue

                exe = executable + (".exe" if platform.system() == "Windows" else "")
                path = getattr(self, path_attr, default_path)
                exists = os.path.exists(os.path.join(path, exe))

                label = (
                    f"{display_name} OK"
                    if exists
                    else (
                        f"{display_name} installieren"
                        if is_de
                        else f"Install {display_name}"
                    )
                )

                # Grün = vorhanden, Orange = fehlt
                color = "#2ecc71" if exists else "#f39c12"
                btn.setText(f"🚀 {label}")
                btn._original_text = f"🚀 {label}"
                btn.setStyleSheet(
                    f"""
                    QPushButton {{
                        text-align: left;
                        padding-left: 8px;
                        font-weight: bold;
                        color: {color};
                        background-color: #3d3d3d;
                        border: 1px solid {color};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {color};
                        color: black;
                    }}
                    """
                )

            try:
                if hasattr(self, "apply_global_button_style"):
                    self.apply_global_button_style()
            except Exception as exc:
                log_error("Installationsbutton-Theme fehlgeschlagen", exc)

            try:
                if hasattr(self, "_fit_all_button_texts"):
                    layout = self.layout()
                    if layout is not None:
                        layout.activate()
                    QTimer.singleShot(0, self._fit_all_button_texts)
                    QTimer.singleShot(250, self._fit_all_button_texts)
            except Exception as exc:
                log_error("Button-Text-Anpassung fehlgeschlagen", exc)

            anim_text = "Animation & Systemcheck..." if is_de else "Animation & system check..."
            update_pbar(80, f"⏳ {anim_text}")

            show_animation = getattr(self, "show_language_animation", None)
            if callable(show_animation):
                show_animation(self.LANG, callback=after_animation)
            else:
                after_animation()

            QApplication.processEvents()

        except Exception as exc:
            log_error("Sprachwechsel fehlgeschlagen", exc)
            try:
                if hasattr(self, "hide_language_overlay"):
                    self.hide_language_overlay()
            except Exception as hide_exc:
                log_error("Overlay konnte nicht ausgeblendet werden", hide_exc)
            finally:
                if not finished["value"]:
                    release_lock()

    def get_language_flag(self):
        """Gibt die passende Flagge zur Systemsprache zurück."""
        try:
            import locale

            # Holen der Sprache (z.B. 'de_DE' oder 'en_US')
            loc = locale.getlocale()[0] or locale.getdefaultlocale()[0] or "en"
            lang = loc[:2].lower()
        except:
            lang = "en"

        # Mapping von Sprachcode zu Flaggen-Emoji
        flags = {
            "de": "🇩🇪",
            "en": "🇺🇸",
            "fr": "🇫🇷",
            "it": "🇮🇹",
            "es": "🇪🇸",
            "ru": "🇷🇺",
            "tr": "🇹🇷",
        }
        return flags.get(lang, "🌐")  # Weltkugel als Fallback

    def toggle_leds(self, enable: bool):
        """
        User-LEDs an/aus, Timer starten/stoppen, Config speichern.
        System-LEDs bleiben statisch.
        """
        # 1. Status synchronisieren
        self.current_config["led_enabled"] = enable
        self.led_enabled = enable  # Hilfsvariable für schnellen Zugriff

        # 2. Timer-Logik
        if hasattr(self, "blink_timer") and self.blink_timer:
            if enable:
                speed = (
                    self.slider_speed.value() if hasattr(self, "slider_speed") else 500
                )

                # Blinken nur in der Range 10ms bis 949ms
                if 10 <= speed < 950:
                    if not self.blink_timer.isActive():
                        self.blink_timer.start(speed)
                else:
                    # Falls Speed auf "Statisch" (>=950) steht
                    self.blink_timer.stop()
                    self.force_user_leds_static()
            else:
                # GLOBAL AUS
                self.blink_timer.stop()
                # WICHTIG: Sofort den statischen (dunklen) Zustand erzwingen
                if hasattr(self, "force_user_leds_static"):
                    self.force_user_leds_static()

        # 3. Permanent speichern (Config-Update)
        if "save_config" in globals():
            save_config({"led_enabled": enable}, gui_instance=self, silent=True)

    def show_language_animation(self, lang_code, callback=None):
        from PyQt6.QtWidgets import (
            QLabel,
            QGraphicsOpacityEffect,
            QGraphicsDropShadowEffect,
        )
        from PyQt6.QtCore import (
            QPropertyAnimation,
            QRect,
            QEasingCurve,
            QTimer,
            QVariantAnimation,
        )
        from PyQt6.QtGui import QFont, QFontInfo, QColor
        from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QTimer
        from PyQt6.QtGui import QFont, QColor

        # 1. Cleanup
        if hasattr(self, "text_label") and self.text_label:
            self.text_label.deleteLater()
        if hasattr(self, "flag_label") and self.flag_label:
            self.flag_label.deleteLater()
        if hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()

        is_de = lang_code.lower() == "de"
        text_msg = "Sprache wird umgestellt..." if is_de else "Switching language..."
        flag_char = "🇩🇪" if is_de else "🇺🇸"

        # 2. Text Label Setup (Neon Glow vorbereitet)
        self.text_label = QLabel(text_msg, self)
        self.text_label.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        self.text_label.setStyleSheet(
            "color: rgba(255, 111, 0, 0); background: transparent;"
        )
        self.text_label.adjustSize()
        t_x, t_y = (self.width() - self.text_label.width()) // 2, (
            self.height() - self.text_label.height()
        ) // 2 + 30
        self.text_label.move(t_x, t_y)

        self.shadow = QGraphicsDropShadowEffect(self.text_label)
        self.shadow.setColor(QColor("#FF6F00"))
        self.shadow.setOffset(0, 0)
        self.shadow.setBlurRadius(0)
        self.text_label.setGraphicsEffect(self.shadow)
        self.text_label.show()

        # 3. Flag Label Setup (Slide & Fade)
        from PyQt6.QtGui import QFont

        self.flag_label = QLabel(flag_char, self)

        font = QFont("Noto Color Emoji", 64)
        font.setFamily("NotoColorEmoji")
        font.setPointSize(64)

        self.flag_label.setFont(font)
        self.flag_label.adjustSize()

        self.flag_label.adjustSize()
        f_x, f_y = (
            self.width() - self.flag_label.width()
        ) // 2, t_y - self.flag_label.height() - 20

        flag_opacity = QGraphicsOpacityEffect(self.flag_label)
        flag_opacity.setOpacity(0)
        self.flag_label.setGraphicsEffect(flag_opacity)
        self.flag_label.show()

        # 4. Animationen: Neon-Puls & Fade-Out
        def fade_out():
            # Text und Flagge sanft ausblenden
            self.out_anim = QVariantAnimation(self)
            self.out_anim.setDuration(600)
            self.out_anim.setStartValue(QColor(255, 111, 0, 255))
            self.out_anim.setEndValue(QColor(255, 111, 0, 0))
            self.out_anim.valueChanged.connect(
                lambda c: self.text_label.setStyleSheet(
                    f"color: {c.name(QColor.NameFormat.HexArgb)}; background: transparent;"
                )
            )

            self.f_out = QPropertyAnimation(flag_opacity, b"opacity")
            self.f_out.setDuration(600)
            self.f_out.setStartValue(1)
            self.f_out.setEndValue(0)

            self.f_out.finished.connect(
                lambda: (
                    self.text_label.hide(),
                    self.flag_label.hide(),
                    callback() if callback else None,
                )
            )
            self.out_anim.start()
            self.f_out.start()

        def start_glow_pulse(times=6):
            state = {"i": 0}

            def toggle():
                val = 5 + (state["i"] % 2) * 25
                self.shadow.setBlurRadius(val)
                state["i"] += 1
                if state["i"] < times * 2:
                    QTimer.singleShot(180, toggle)
                else:
                    fade_out()

            toggle()

        # 5. Start: Text-Farbe Animation (Echter Fade-In)
        self.text_fade_in = QVariantAnimation(self)
        self.text_fade_in.setDuration(900)
        self.text_fade_in.setStartValue(QColor(255, 111, 0, 0))
        self.text_fade_in.setEndValue(QColor(255, 111, 0, 255))
        self.text_fade_in.valueChanged.connect(
            lambda c: self.text_label.setStyleSheet(
                f"color: {c.name(QColor.NameFormat.HexArgb)}; background: transparent;"
            )
        )

        # Flagge Fade & Slide
        self.flag_fade_in = QPropertyAnimation(flag_opacity, b"opacity")
        self.flag_fade_in.setDuration(900)
        self.flag_fade_in.setStartValue(0)
        self.flag_fade_in.setEndValue(1)

        self.flag_slide = QPropertyAnimation(self.flag_label, b"geometry")
        self.flag_slide.setDuration(900)
        self.flag_slide.setStartValue(
            QRect(f_x, f_y + 50, self.flag_label.width(), self.flag_label.height())
        )
        self.flag_slide.setEndValue(
            QRect(f_x, f_y, self.flag_label.width(), self.flag_label.height())
        )
        self.flag_slide.setEasingCurve(QEasingCurve.Type.OutBack)

        self.flag_fade_in.finished.connect(
            lambda: QTimer.singleShot(100, start_glow_pulse)
        )

        self.text_fade_in.start()
        self.flag_fade_in.start()
        self.flag_slide.start()

    def show_tool_help(self, tool_id):
        """Zeigt Status-Infos (Grün) oder Hilfe (Rot) für System-Tools an."""
        from PyQt6.QtWidgets import QMessageBox, QApplication
        import platform
        import shutil

        lang = getattr(self, "LANG", "de").lower()

        # 1. LIVE-CHECK: Ist das Tool installiert?
        path = shutil.which(tool_id)
        # Spezialfälle für PY und QT6, die nicht als binärer Pfad gesucht werden
        is_installed = path is not None or tool_id in ["py", "qt6"]

        # Mapping der Installations-Befehle
        commands = {
            "snd": "sudo apt update && sudo apt install pulseaudio-utils",
            "git": "sudo apt update && sudo apt install git",
            "patch": "sudo apt update && sudo apt install patch",
            "zip": "sudo apt update && sudo apt install zip",
            "gcc": "sudo apt update && sudo apt install build-essential",
            "make": "sudo apt update && sudo apt install make",
            "ssl": "sudo apt update && sudo apt install libssl-dev",
            "usb": "sudo apt update && sudo apt install libusb-1.0-0-dev",
        }

        cmd = commands.get(tool_id, "N/A")
        title = "Tool Status" if lang == "de" else "Tool Status"

        # 2. TEXT-ZUSAMMENSTELLUNG (WEICHE)
        if is_installed:
            # FALL: TOOL IST INSTALLIERT (GRÜN)
            tool_path = path if path else "System / Python"
            if lang == "de":
                msg = f"Das Tool <b style='color:#00FF00;'>{tool_id.upper()}</b> ist bereits installiert.<br><br>"
                msg += f"Pfad: <code style='background-color:#222; color:#00ADFF; padding:3px;'>{tool_path}</code>"
            else:
                msg = f"Tool <b style='color:#00FF00;'>{tool_id.upper()}</b> is already installed.<br><br>"
                msg += f"Path: <code style='background-color:#222; color:#00ADFF; padding:3px;'>{tool_path}</code>"
        else:
            # FALL: TOOL FEHLT (ROT)
            if lang == "de":
                msg = f"Das Tool <b style='color:#F37804;'>{tool_id.upper()}</b> wurde nicht im System gefunden.<br><br>"
                if platform.system() == "Linux" and cmd != "N/A":
                    msg += f"Installieren Sie es über das Terminal mit:<br><br><code style='background-color:#222; color:#00FF00; padding:5px;'>{cmd}</code>"
                else:
                    msg += "Bitte installieren Sie das erforderliche Paket manuell."
            else:
                msg = f"Tool <b style='color:#F37804;'>{tool_id.upper()}</b> not found in system.<br><br>"
                if platform.system() == "Linux" and cmd != "N/A":
                    msg += f"Install it via terminal using:<br><br><code style='background-color:#222; color:#00FF00; padding:5px;'>{cmd}</code>"
                else:
                    msg += "Please install the required package manually."

        # 3. MESSAGEBOX KONFIGURIEREN
        box = QMessageBox(self)
        box.setWindowTitle(title)
        # Icon-Weiche: Information bei Grün, Warnung bei Rot
        box.setIcon(
            QMessageBox.Icon.Information if is_installed else QMessageBox.Icon.Warning
        )
        box.setText(msg)

        # Buttons: Kopieren nur anzeigen, wenn das Tool fehlt
        copy_btn = None
        if not is_installed and cmd != "N/A":
            copy_btn = box.addButton(
                "Befehl kopieren" if lang == "de" else "Copy Command",
                QMessageBox.ButtonRole.ActionRole,
            )

        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()

        # 4. LOGIK FÜR DEN KOPIER-BUTTON
        if copy_btn and box.clickedButton() == copy_btn:
            QApplication.clipboard().setText(cmd)
            if hasattr(self, "append_info"):
                log_msg = f"📋 {tool_id.upper()} " + (
                    "Befehl kopiert" if lang == "de" else "Command copied"
                )
                self.append_info(getattr(self, "info_text", None), log_msg, "status")

    def update_label_only(self, value):
        """
        Aktualisiert Text und Farbe des Speed-Labels beim Programmstart.
        Optimiert für das dunkle UI-Design.
        """
        if not hasattr(self, "lbl_speed_val") or not self.lbl_speed_val:
            return

        # Farbcodes passend zum System-Check
        C_GREEN, C_RED, C_GRAY = "#2ecc71", "#FF0000", "#AAAAAA"

        if value >= 950:
            txt = "STATIC"
            style = f"color: {C_GREEN}; font-weight: bold; font-size: 18px; font-family: 'Segoe UI', sans-serif;"
        elif value <= 50:
            txt = "TURBO"
            style = f"color: {C_RED}; font-weight: bold; font-size: 18px; font-family: 'Segoe UI', sans-serif;"
        else:
            # Zeigt die Millisekunden an, falls kein Extremwert vorliegt
            txt = f"{value}ms"
            style = f"color: {C_GRAY}; font-weight: bold; font-size: 18px; font-family: 'Segoe UI', sans-serif;"

        self.lbl_speed_val.setText(txt)
        self.lbl_speed_val.setStyleSheet(style)

    def force_leds_static(self):
        """Kombinierte LED-Steuerung: Setzt Status-Farben und Design-Stile ohne Blinken."""
        # 1. Sicherheitscheck
        if not hasattr(self, "status_leds") or not self.status_leds:
            return

        # 2. Design-Modus ermitteln (Matrix oder Standard)
        is_matrix = False
        try:
            # Prüft erst den Button-Text, falls vorhanden, sonst die Config
            if hasattr(self, "btn_matrix") and self.btn_matrix:
                is_matrix = "EXIT" in self.btn_matrix.text()
            else:
                is_matrix = self.cfg.get("theme_mode") == "matrix"
        except:
            is_matrix = False

        # 3. LEDs aktualisieren
        for led in self.status_leds:
            try:
                led.show()  # Sicherstellen, dass sie sichtbar sind

                # Tool-Status ermitteln (Grün wenn vorhanden, sonst Rot)
                exists = getattr(led, "tool_exists", False)

                if is_matrix:
                    # Im Matrix-Modus: Hellgrün für OK, Dunkelgrün/Grau für Fehlend
                    color = "#00FF41" if exists else "#003311"
                    border = "1px solid #00FF41"
                else:
                    # Im Standard-Modus: Kräftiges Rot/Grün
                    color = "#27ae60" if exists else "#c0392b"
                    border = "2px solid #555"

                led.setStyleSheet(
                    f"""
                    background-color: {color}; 
                    border-radius: 6px; 
                    border: {border};
                """
                )
            except:
                continue

    def load_config_from_file(self):
        """Lädt die Konfiguration robust; beschädigtes JSON darf den Start nicht abbrechen."""
        import shutil
        from datetime import datetime

        if not os.path.exists(CONFIG_FILE):
            return {}

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8-sig") as f:
                config = json.load(f)
            if isinstance(config, dict):
                return config
            print(f"[CONFIG] Ungültiges Format in {CONFIG_FILE}: erwartet wurde ein JSON-Objekt.")
            return {}
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
            print(f"[CONFIG] Konfigurationsdatei kann nicht gelesen werden: {exc}")
            # Originaldatei sichern und niemals automatisch durch {} ersetzen.
            try:
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup = f"{CONFIG_FILE}.invalid_{stamp}.bak"
                shutil.copy2(CONFIG_FILE, backup)
                print(f"[CONFIG] Fehlerhafte Datei gesichert unter: {backup}")
                print("[CONFIG] Originaldatei bleibt unverändert. Bitte Sicherung prüfen.")
            except OSError as backup_exc:
                print(f"[CONFIG] Konnte Konfiguration nicht sichern: {backup_exc}")
            return {}

    def update_blink_speed(self, value):
        """
        Nur User-LEDs blinken lassen, System-LEDs bleiben statisch.
        0=OFF, >=950=STATIC, sonst blinkend (nur wenn led_enabled in Config).
        """
        timer = getattr(self, "blink_timer", None)
        if not timer or getattr(self, "is_loading", False):
            return

        # 1. UI Feedback (Texte & Farben des Labels)
        if hasattr(self, "lbl_speed_val"):
            if value <= 0:
                self.lbl_speed_val.setText("OFF")
                self.lbl_speed_val.setStyleSheet(
                    "color: #777; font-weight: bold; font-size: 12px;"
                )
            elif value >= 950:
                self.lbl_speed_val.setText("STATIC")
                self.lbl_speed_val.setStyleSheet(
                    "color: #2ecc71; font-weight: bold; font-size: 12px;"
                )
            elif value <= 50:
                self.lbl_speed_val.setText("TURBO")
                self.lbl_speed_val.setStyleSheet(
                    "color: #FF0000; font-weight: bold; font-size: 12px;"
                )
            else:
                self.lbl_speed_val.setText(f"{value}ms")
                self.lbl_speed_val.setStyleSheet(
                    "color: #aaa; font-weight: bold; font-size: 12px;"
                )

        # 2. Logik: Soll überhaupt geblinkt werden?
        # Wir prüfen den globalen "An/Aus"-Schalter aus der Config
        is_led_globally_enabled = self.current_config.get("led_enabled", True)
        config_updates = {"blink_speed": value}

        # Bedingung zum STOPPEN:
        # Slider auf 0 ODER Slider auf Max ODER User hat Blinken global deaktiviert
        if value <= 0 or value >= 950 or not is_led_globally_enabled:
            timer.stop()
            if hasattr(self, "force_user_leds_static"):
                self.force_user_leds_static()

            # Nur wenn der Slider selbst auf 0/Max steht, ändern wir led_enabled in der Config
            if value <= 0 or value >= 950:
                config_updates["led_enabled"] = value > 0
        else:
            # Bedingung zum STARTEN/AKTUALISIEREN:
            timer.setInterval(max(10, value))
            if not timer.isActive():
                timer.start()
            config_updates["led_enabled"] = True

        # 3. Speichern & System-Status
        # Falls du die Checkbox in der UI hast, hier ggf. synchronisieren:
        # if hasattr(self, "led_checkbox"): self.led_checkbox.setChecked(config_updates.get("led_enabled", is_led_globally_enabled))

        save_config(config_updates, gui_instance=self, silent=True)

    def set_system_leds_static(self):
        """System-LEDs immer statisch lassen"""
        for led in getattr(self, "status_leds", []):
            led.setStyleSheet("background-color: green; border-radius: 4px;")

    def get_matrix_style(self):
        """Gibt das neon-grüne Matrix-Stylesheet zurück."""
        return """
            QWidget {
                background-color: #0D0D0D;
                color: #00FF41;
                font-family: 'Segoe UI', 'Ubuntu', sans-serif;
            }

            QGroupBox {
                border: 2px solid #008F11;
                border-radius: 8px;
                margin-top: 1ex;
                font-weight: bold;
                color: #00FF41;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }

            QTextEdit {
                background-color: #000000;
                border: 1px solid #00FF41;
                color: #00FF41;
                font-family: 'Consolas', 'Ubuntu Mono', monospace;
                font-size: 20px;
            }

            QPushButton {
                background-color: #1A1A1A;
                color: #00FF41;
                border: 1px solid #008F11;
                border-radius: 5px;
                padding: 6px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #008F11;
                color: #000000;
                border: 1px solid #00FF41;
            }

            QPushButton:pressed {
                background-color: #005F0A;
                color: #FFFFFF;
            }

            QPushButton:disabled {
                background-color: #111111;
                color: #555555;
                border-color: #333333;
            }

            QLabel {
                color: #00FF41;
                background: transparent;
                border: none;
            }

            QLineEdit {
                background-color: #1A1A1A;
                border: 1px solid #008F11;
                color: #00FF41;
                padding: 3px;
                selection-background-color: #008F11;
                selection-color: #FFFFFF;
            }

            QProgressBar {
                background-color: #111111;
                border: 1px solid #008F11;
                border-radius: 5px;
                text-align: center;
                color: #FFFFFF;
            }

            QProgressBar::chunk {
                background-color: #008F11;
                border-radius: 3px;
            }

            QSlider::groove:horizontal {
                border: 1px solid #008F11;
                height: 6px;
                background: #000000;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #00FF41;
                border: 1px solid #008F11;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }

            QCheckBox, QRadioButton {
                color: #00FF41;
                spacing: 6px;
            }

            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #1A1A1A;
                color: #00FF41;
                border: 1px solid #008F11;
                padding: 3px;
            }

            QComboBox QAbstractItemView {
                background-color: #111111;
                color: #00FF41;
                selection-background-color: #008F11;
            }

            QToolTip {
                background-color: #000000;
                color: #00FF41;
                border: 1px solid #008F11;
                border-radius: 4px;
                padding: 5px;
                font-size: 10pt;
                font-weight: bold;
            }
        """

    def toggle_matrix(self, force_state=None):
        """
        Schaltet den Matrix-Modus ein oder aus.

        force_state:
            None       -> Modus anhand des Button-Texts umschalten
            "matrix"   -> Matrix-Modus einschalten
            "standard" -> Standarddesign einschalten
        """
        import traceback

        print(
            "DEBUG: toggle_matrix aufgerufen:",
            "force_state =", repr(force_state),
            flush=True
        )

        # 1. Final-Label ausblenden
        try:
            hide_label = getattr(self, "hide_final_label", None)

            if callable(hide_label):
                hide_label()
            else:
                final_label = getattr(self, "final_label", None)
                if final_label is not None:
                    final_label.hide()

        except Exception as exc:
            print(
                f"DEBUG: Final-Label konnte nicht ausgeblendet werden: {exc}",
                flush=True
            )

        # 2. Button prüfen
        btn = getattr(self, "btn_matrix", None)

        if btn is None:
            print(
                "FEHLER: self.btn_matrix ist nicht vorhanden!",
                flush=True
            )
            return

        # 3. Sprache und Übersetzungen
        lang_code = str(getattr(self, "LANG", "de")).lower()
        translations = globals().get("TEXTS", {})

        if not isinstance(translations, dict):
            translations = {}

        t = translations.get(
            lang_code,
            translations.get("en", {})
        )

        if not isinstance(t, dict):
            t = {}

        # 4. Konfiguration absichern
        cfg = getattr(self, "current_config", None)

        if not isinstance(cfg, dict):
            cfg = {}
            self.current_config = cfg

        # 5. Aktuellen Modus bestimmen
        current_mode = str(
            cfg.get("theme_mode", "standard")
        ).strip().lower()

        button_text = str(btn.text()).strip().lower()

        # Bei normalem Klick entscheidet der sichtbare Button-Text.
        # "EXIT MATRIX" bedeutet: Matrix ist aktiv -> Standard einschalten.
        # Andernfalls: Matrix einschalten.
        if force_state is None:
            if (
                "exit matrix" in button_text
                or "matrix verlassen" in button_text
                or "matrix beenden" in button_text
            ):
                target_mode = "standard"
            else:
                target_mode = "matrix"
        else:
            target_mode = str(force_state).strip().lower()

        if target_mode not in ("matrix", "standard"):
            print(
                f"FEHLER: Ungültiger Matrix-Modus: {target_mode!r}",
                flush=True
            )
            return

        print(
            "DEBUG: Zustand vor Umschaltung:",
            "config =", repr(current_mode),
            "| button =", repr(btn.text()),
            "| ziel =", repr(target_mode),
            flush=True
        )

        # 6. Standard-Styles nur einmal sichern
        # So wird der Matrix-Style nicht versehentlich als Standard gespeichert.
        if not hasattr(self, "_standard_stylesheet"):
            self._standard_stylesheet = self.styleSheet()

        header = getattr(self, "header_widget", None)

        if (
            header is not None
            and not hasattr(self, "_standard_header_stylesheet")
        ):
            self._standard_header_stylesheet = header.styleSheet()

        slider = getattr(
            self,
            "blink_slider",
            getattr(self, "slider_speed", None)
        )

        if (
            slider is not None
            and not hasattr(self, "_standard_slider_stylesheet")
        ):
            self._standard_slider_stylesheet = slider.styleSheet()

        is_loading = bool(getattr(self, "is_loading", False))

        # 7. Gewünschten Modus anwenden
        try:
            if target_mode == "matrix":

                # Matrix-Stylesheet holen
                matrix_style_func = getattr(
                    self,
                    "get_matrix_style",
                    None
                )

                if not callable(matrix_style_func):
                    raise AttributeError(
                        "get_matrix_style() fehlt oder ist keine "
                        "Methode von PatchManagerGUI."
                    )

                matrix_style = matrix_style_func()

                if not isinstance(matrix_style, str):
                    raise TypeError(
                        "get_matrix_style() muss einen String zurückgeben."
                    )

                self.setStyleSheet(matrix_style)

                # Button zeigt ab jetzt die Aktion zum Verlassen an
                btn.setText(
                    t.get("matrix_btn_exit", "🔙 EXIT MATRIX")
                )

                cfg["theme_mode"] = "matrix"
                self.current_config = cfg

                # Header anpassen
                if header is not None:
                    header.setStyleSheet("""
                        QWidget {
                            background-color: #000000;
                            color: #00FF41;
                            border: 1px solid #008F11;
                        }
                    """)

                print(
                    "DEBUG: Matrix-Modus AKTIVIERT",
                    "| config =", repr(cfg.get("theme_mode")),
                    "| button =", repr(btn.text()),
                    flush=True
                )

                # Aktivierungsnachricht
                info = getattr(self, "info_text", None)

                if info is not None and not is_loading:
                    sys_tag = t.get("matrix_sys", "System")
                    message = t.get(
                        "matrix_on",
                        "Matrix-Modus aktiviert."
                    )

                    info.append(
                        '<br><span style="color:#00FF41; '
                        'font-family:monospace;">'
                        f'<b>[{sys_tag}]</b> {message}'
                        '</span>'
                    )

                # Optionaler Sound
                safe_play_func = globals().get("safe_play")

                if callable(safe_play_func) and not is_loading:
                    try:
                        safe_play_func("dialog-information.oga")
                    except Exception as exc:
                        print(
                            f"DEBUG: Sound übersprungen: {exc}",
                            flush=True
                        )

            else:

                # Standard-Styles wiederherstellen
                self.setStyleSheet(
                    self._standard_stylesheet
                )

                # Button zeigt wieder die Aktivierungsaktion an
                btn.setText(
                    t.get("matrix_btn_enter", "📟 MATRIX MODE")
                )

                cfg["theme_mode"] = "standard"
                self.current_config = cfg

                # Header wiederherstellen
                if header is not None:
                    header.setStyleSheet(
                        self._standard_header_stylesheet
                    )

                # Slider wiederherstellen
                if slider is not None:
                    slider.setStyleSheet(
                        self._standard_slider_stylesheet
                    )

                print(
                    "DEBUG: Standard-Modus AKTIVIERT",
                    "| config =", repr(cfg.get("theme_mode")),
                    "| button =", repr(btn.text()),
                    flush=True
                )

                # Deaktivierungsnachricht
                info = getattr(self, "info_text", None)

                if info is not None and not is_loading:
                    sys_tag = t.get("matrix_sys", "System")
                    message = t.get(
                        "matrix_off",
                        "Matrix-Modus deaktiviert."
                    )

                    info.append(
                        '<br><span style="color:orange; '
                        'font-family:monospace;">'
                        f'<b>[{sys_tag}]</b> {message}'
                        '</span>'
                    )

        except Exception as exc:
            print(
                f"FEHLER beim Umschalten des Matrix-Modus: {exc}",
                flush=True
            )
            traceback.print_exc()
            return

        # 8. Uhr aktualisieren
        analog_clock = getattr(self, "analog_clock", None)

        if analog_clock is not None:
            try:
                analog_clock.update()
            except Exception as exc:
                print(
                    f"DEBUG: Uhr-Aktualisierung fehlgeschlagen: {exc}",
                    flush=True
                )

        # 9. LEDs synchronisieren
        force_leds = getattr(
            self,
            "force_leds_static",
            None
        )

        if callable(force_leds):
            try:
                force_leds()
            except Exception as exc:
                print(
                    f"DEBUG: LED-Aktualisierung fehlgeschlagen: {exc}",
                    flush=True
                )

        # 10. Button-Höhen aktualisieren
        for button in getattr(self, "all_buttons", []):
            try:
                button.setFixedHeight(
                    getattr(self, "BUTTON_HEIGHT", 50)
                )
            except (AttributeError, RuntimeError):
                continue

        # 11. Konfiguration speichern
        if not is_loading:
            save_config_func = globals().get("save_config")

            if callable(save_config_func):
                try:
                    save_config_func(
                        cfg,
                        gui_instance=self,
                        silent=True
                    )
                except Exception as exc:
                    print(
                        "WARNUNG: Konfiguration konnte nicht gespeichert "
                        f"werden: {exc}",
                        flush=True
                    )

        # 12. Endzustand protokollieren
        print(
            "DEBUG: toggle_matrix abgeschlossen:",
            "theme_mode =", repr(cfg.get("theme_mode")),
            "| button_text =", repr(btn.text()),
            flush=True
        )

    def animate_everything(self):
        """Steuert das Blinken von Text und LEDs."""
        self._blink_state = not self._blink_state
        # 2. LEDs blinken lassen (Matrix-Check inklusive)
        is_matrix = "EXIT" in self.btn_matrix.text()

        for led in self.status_leds:
            if self._blink_state:
                # AN-Phase
                color = led.base_color if not is_matrix else "#00FF41"
                border = "#FFF" if not is_matrix else "#00FF41"
            else:
                # AUS-Phase (Abgedunkelt)
                color = "#1a532d" if led.tool_exists else "#5a1a14"
                border = "#333"

            led.setStyleSheet(
                f"background-color: {color}; border-radius: 7px; border: 2px solid {border};"
            )

    def get_status_indicator(self, tool_name):
        """Erzeugt ein Widget mit LED-Punkt und Label für den Systemcheck."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(6)

        # Die LED (ein Kreis)
        led = QLabel()
        led.setFixedSize(10, 10)

        # Prüfung ob Tool (git, patch, etc.) im Systempfad ist
        exists = shutil.which(tool_name) is not None
        color = "#27ae60" if exists else "#c0392b"  # Grün wenn da, Rot wenn fehlt

        led.setStyleSheet(
            f"""
            background-color: {color}; 
            border-radius: 5px; 
            border: 1px solid rgba(255,255,255,0.3);
        """
        )

        # Das Text-Label daneben
        label = QLabel(tool_name.lower())
        label.setFont(QFont("Monospace", 9))

        layout.addWidget(led)
        layout.addWidget(label)
        return container

    def get_t(self, key, default=None):
        """Zentrale Methode zur Textübersetzung."""
        lang = str(getattr(self, "LANG", "de")).lower()
        # Dictionary für die aktuelle Sprache holen, Fallback auf Englisch
        lang_dict = TEXTS.get(lang, TEXTS.get("en", {}))

        if key in lang_dict:
            return lang_dict[key]

        # Falls Key fehlt, technischen Namen schön machen
        if default:
            return default

        return str(key).replace("_", " ").title()

    def get_gui_settings(self):
        """Sammelt alle aktuellen Einstellungen aus der UI für die Config."""
        return {
            # Falls du ein Eingabefeld/Spinbox für Commits hast:
            "commit_count": (
                self.commit_spin.value()
                if hasattr(self, "commit_spin")
                else getattr(self, "commit_count", 5)
            ),
            # Falls du eine Color-Box (QComboBox) hast:
            "color": (
                self.color_box.currentText()
                if hasattr(self, "color_box")
                else getattr(self, "current_color", "")
            ),
            # Sprache (Wichtig: "language" muss klein geschrieben sein wie in load_config!)
            "language": str(getattr(self, "LANG", "DE")).upper(),
            # Pfad
            "s3_patch_path": getattr(self, "OLD_PATCH_DIR", OLD_PATCH_DIR),
        }

    def show_update_dialog(self, latest_version, current_version):
        """Öffnet das Pop-up Fenster für das verfügbare Update."""

        # --- Final-Label ausblenden ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()
        elif hasattr(self, "final_label") and self.final_label:
            self.final_label.hide()
        from PyQt6.QtWidgets import QMessageBox

        txt = getattr(self, "TEXT", {})
        lang = getattr(self, "LANG", "de").lower()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(txt.get("update_title", "Update"))

        # Text-Inhalt
        msg_text = (
            f"{txt.get('update_msg', 'Update verfügbar')}\n\n"
            f"{txt.get('new_version_label', 'Neu')}: v{latest_version}\n"
            f"{txt.get('old_version_label', 'Installiert')}: v{current_version}"
        )
        msg_box.setText(msg_text)

        # Buttons übersetzen
        msg_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        btn_yes = msg_box.button(QMessageBox.StandardButton.Yes)
        if btn_yes:
            btn_yes.setText(txt.get("yes", "Ja"))
        btn_no = msg_box.button(QMessageBox.StandardButton.No)
        if btn_no:
            btn_no.setText(txt.get("no", "Nein"))

        # Sound beim Öffnen des Update-Fensters
        sound_manager = getattr(self, "sound_manager", None)
        if sound_manager and sound_manager.enabled:
            sound_manager.success_sound.play()

        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if hasattr(self, "plugin_update_action"):
                self.plugin_update_action(latest_version=latest_version)

    def update_ui_texts(self):
        """Aktualisiert Texte, Icons und Tooltips zentral, ohne unnötig Styles anzuhängen."""
        import json
        import os
        import platform

        from PyQt6.QtCore import QSize, QTimer
        from PyQt6.QtWidgets import QApplication, QStyle

        # --------------------------------------------------
        # 1. Abschlussmeldung ausblenden und Sprache bestimmen
        # --------------------------------------------------
        try:
            hide_final = getattr(self, "hide_final_label", None)
            if callable(hide_final):
                hide_final()
            else:
                final_label = getattr(self, "final_label", None)
                if final_label is not None:
                    final_label.hide()
        except Exception as exc:
            print(f"[update_ui_texts] Abschlusslabel konnte nicht ausgeblendet werden: {exc}")

        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"
        pbar = getattr(self, "progress_bar", None)

        def tr(de_text, en_text):
            return de_text if is_de else en_text

        def apply_button_style(btn, color="#00FFFF", tooltip_color=None):
            """Setzt einen vollständigen, wiederholbar anwendbaren Button-Style."""
            if btn is None:
                return
            tip_color = tooltip_color or color
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    text-align: left;
                    padding-left: 8px;
                    font-weight: bold;
                    color: {color};
                    background-color: #3d3d3d;
                    border: 1px solid {color};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    color: black;
                }}

                QToolTip {{
                    background-color: #202833;
                    color: #EAF6FF;
                    border: 1px solid #00B8D4;
                    border-radius: 5px;
                    padding: 5px;
                    font-size: 10pt;
                }}
                """
            )

        def apply_final_style(btn, text, standard_pixmap):
            if btn is None:
                return
            clean_text = str(text).strip()
            if len(clean_text) > 22 and " " in clean_text:
                clean_text = clean_text.replace(" ", "\n", 1)

            btn.setText(clean_text)
            btn.setIcon(QApplication.style().standardIcon(standard_pixmap))
            btn.setIconSize(QSize(20, 20))
            btn.setMinimumSize(200, 50)
            apply_button_style(btn, "#00FFFF")

        # --------------------------------------------------
        # 2. ProgressBar starten
        # --------------------------------------------------
        if pbar is not None:
            pbar.setValue(20)
            pbar.show()

        # --------------------------------------------------
        # 3. Labels aktualisieren
        # --------------------------------------------------
        labels = [
            ("commit_label", "Anzahl Commits:", "Commit Count:"),
            ("color_label", "Farbe:", "Color:"),
            ("lang_label", "🌐 Sprache:", "🌐 Language:"),
        ]
        for attr, de_text, en_text in labels:
            label = getattr(self, attr, None)
            if label is not None:
                label.setText(tr(de_text, en_text))

        # --------------------------------------------------
        # 4. Konfiguration laden und Pfade übernehmen
        # --------------------------------------------------
        is_win = platform.system() == "Windows"
        config_file = globals().get("CONFIG_FILE", "config.json")
        file_cfg = {}

        if os.path.isfile(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as handle:
                    loaded_cfg = json.load(handle)
                if isinstance(loaded_cfg, dict):
                    file_cfg = loaded_cfg
                else:
                    print("[update_ui_texts] config.json enthält kein JSON-Objekt.")
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[update_ui_texts] Konfiguration konnte nicht geladen werden: {exc}")

        s3_path = file_cfg.get(
            "s3_custom_path",
            getattr(self, "S3_PATH", r"C:\s3" if is_win else "/opt/s3"),
        )
        s4_path = file_cfg.get(
            "s4_custom_path",
            getattr(self, "S4_PATH", r"C:\opt\simplebuild4" if is_win else "/opt/simplebuild4"),
        )
        ncam_path = file_cfg.get(
            "ncam_custom_path",
            getattr(self, "NCAM_PATH", r"C:\opt\ncam" if is_win else "/opt/s3_ncam_bonecrew"),
        )

        self.S3_PATH = os.path.normpath(os.path.expanduser(str(s3_path)))
        self.S4_PATH = os.path.normpath(os.path.expanduser(str(s4_path)))
        self.NCAM_PATH = os.path.normpath(os.path.expanduser(str(ncam_path)))
        self.current_config = file_cfg
        self.cfg = file_cfg

        # --------------------------------------------------
        # 5. S3 / S4 / NCam: Installation erkennen und Tooltips setzen
        # --------------------------------------------------
        def apply_tool_button(btn, current_path, name):
            if btn is None:
                return

            sub_map = {
                "S3": "s3",
                "NCam": "s3_ncam_bonecrew",
                "S4": "simplebuild4",
            }
            sub_folder = sub_map[name]

            if name == "S4":
                possible_names = (
                    "simplebuild", "simplebuild.exe", "s4", "s4.exe",
                    "simplebuild4", "simplebuild4.exe",
                )
            elif name == "NCam":
                possible_names = (
                    "ncam", "ncam.exe", "oscam", "oscam.exe", "s3", "s3.exe",
                )
            else:
                possible_names = ("s3", "s3.exe")

            base = os.path.normpath(os.path.expanduser(str(current_path)))
            exists = False
            for filename in possible_names:
                direct_path = os.path.join(base, filename)
                nested_path = ""
                if os.path.basename(base).lower() != sub_folder.lower():
                    nested_path = os.path.join(base, sub_folder, filename)
                if os.path.isfile(direct_path) or (
                    nested_path and os.path.isfile(nested_path)
                ):
                    exists = True
                    break

            if exists:
                label = f"🚀 {name} OK"
                color = "#2ecc71"
                tip = tr(
                    f"<b>Linksklick:</b> {name}-Menü öffnen<br><b>Rechtsklick:</b> Pfad ändern",
                    f"<b>Left-click:</b> Open {name} menu<br><b>Right-click:</b> Change path",
                )
            else:
                label = f"🚀 {name} {tr('Installieren', 'Install')}"
                color = "#f39c12"
                tip = tr(
                    f"<b>Linksklick:</b> {name}-Installation starten<br><b>Rechtsklick:</b> Ordner wählen",
                    f"<b>Left-click:</b> Start {name} setup<br><b>Right-click:</b> Select folder",
                )

            btn.setText(label)
            btn.setToolTip(tip)
            btn.setToolTipDuration(10000)
            btn.setMinimumSize(320, 50)
            btn._original_text = label
            apply_button_style(btn, color)

        apply_tool_button(getattr(self, "btn_s3", None), self.S3_PATH, "S3")
        apply_tool_button(getattr(self, "btn_s4", None), self.S4_PATH, "S4")
        apply_tool_button(getattr(self, "btn_ncam", None), self.NCAM_PATH, "NCam")

        # --------------------------------------------------
        # 6. Standard-Buttons und Tooltips
        # --------------------------------------------------
        mapping = [
            # 1. Arbeitsordner und lokale Repositories
            (getattr(self, "btn_open_work", None), "Arbeitsordner", "Work Folder",
             QStyle.StandardPixmap.SP_DirIcon,
             "Öffnet den lokalen Patch-Ordner",
             "Opens the local patch folder"),

            (getattr(self, "btn_open_temp", None), "Temp Git Streamboard", "Temp Git Streamboard",
             QStyle.StandardPixmap.SP_DirIcon,
             "Zeigt den lokalen Git-Clone",
             "Shows the local Git clone"),

            (getattr(self, "btn_open_emu", None), "Emu Git Temp", "Emu Git Temp",
             QStyle.StandardPixmap.SP_DirIcon,
             "Öffnet das Repository im Browser",
             "Opens the repository in the browser"),

            # 2. Umgebung prüfen
            (getattr(self, "btn_check_tools", None), "Tools prüfen", "Check Tools",
             QStyle.StandardPixmap.SP_ComputerIcon,
             "Prüft Compiler und Abhängigkeiten",
             "Checks compilers and dependencies"),

            # 3. Repository konfigurieren
            (getattr(self, "btn_repo_url", None), "Oscam Emu URL", "Oscam Emu URL",
             QStyle.StandardPixmap.SP_DriveNetIcon,
             "Ändert die Git-Repository-URL",
             "Changes the Git repository URL"),

            (getattr(self, "btn_modifier", None), "Patch Autor", "Patch Author",
             QStyle.StandardPixmap.SP_FileDialogDetailedView,
             "Ändert den Namen des Patch-Autors",
             "Changes the patch author's name"),

            # 4. Änderungen und Updates prüfen
            (getattr(self, "btn_check_commit", None), "Commit-Prüfung", "Commit Check",
             QStyle.StandardPixmap.SP_BrowserReload,
             "Prüft online auf Updates",
             "Checks online for updates"),

            
            # 5. Dateiberechtigungen reparieren
            (
            getattr(self, "btn_fix_perms", None),
            "Rechte reparieren" if self.LANG == "de"
            else "Fix Permissions",
            "Fix Permissions",
            QStyle.StandardPixmap.SP_DialogNoButton,
            "🔐 <b>Rechte:</b> Setzt Schreibrechte für Tool-Dateien und Ordner neu.",
            "🔐 <b>Permissions:</b> Resets write permissions for tool files and folders.",
        ),
        ]
        for btn, de_text, en_text, icon, de_tip, en_tip in mapping:
            if btn is not None:
                apply_final_style(btn, tr(de_text, en_text), icon)
                btn.setToolTip(tr(de_tip, en_tip))
                btn.setToolTipDuration(10000)


        
        # --------------------------------------------------
        # 7. Grid-Buttons
        # --------------------------------------------------
        if isinstance(getattr(self, "buttons", None), dict):
            # Logische Reihenfolge der Patch-Funktionen
            grid_icons = {
                # 1. Patch erstellen und bearbeiten
                "patch_create": QStyle.StandardPixmap.SP_FileIcon,
                "patch_renew": QStyle.StandardPixmap.SP_BrowserReload,

                # 2. Patch prüfen und anwenden
                "patch_check": QStyle.StandardPixmap.SP_DialogApplyButton,
                "patch_apply": QStyle.StandardPixmap.SP_MediaPlay,

                # 3. Patch exportieren und sichern
                "patch_zip": QStyle.StandardPixmap.SP_DriveFDIcon,
                "backup_old": QStyle.StandardPixmap.SP_DialogSaveButton,

                # 4. Verzeichnisse verwalten
                "change_old_dir": QStyle.StandardPixmap.SP_DirOpenIcon,
                "clean_folder": QStyle.StandardPixmap.SP_TrashIcon,

                # 5. Programm beenden
                "exit": QStyle.StandardPixmap.SP_DialogCloseButton,
            }

            get_t = getattr(self, "get_t", None)

            for key, btn in self.buttons.items():
                if btn is None or key not in grid_icons:
                    continue

                try:
                    text = get_t(key, key) if callable(get_t) else key
                except Exception as exc:
                    print(
                        f"[update_ui_texts] Übersetzung für {key} fehlgeschlagen: {exc}"
                    )
                    text = key

                apply_final_style(btn, text, grid_icons[key])


        # --------------------------------------------------
        # 8. Matrix-Button
        # --------------------------------------------------
        matrix_btn = getattr(self, "btn_matrix", None)
        if matrix_btn is not None:
            matrix_btn.setText(tr("🔙 MATRIX Beenden", "🔙 EXIT MATRIX"))
            matrix_btn.setMinimumSize(220, 50)
            matrix_btn.setToolTip(
                tr("Verlässt den Matrix-Modus.", "Exits Matrix mode.")
            )
            matrix_btn.setToolTipDuration(10000)
            apply_button_style(matrix_btn, "#00FFFF")

        # --------------------------------------------------
        # 9. Theme auswählen und anwenden
        # --------------------------------------------------
        theme_mode = str(file_cfg.get("theme_mode", "standard")).lower()
        theme_color = str(file_cfg.get("color", "Classics")).lower()
        is_matrix = "matrix" in theme_mode or "matrix" in theme_color

        theme_method = getattr(
            self,
            "enable_matrix_theme" if is_matrix else "enable_standard_theme",
            None,
        )
        if callable(theme_method):
            try:
                theme_method()
            except Exception as exc:
                print(f"[update_ui_texts] Theme konnte nicht angewendet werden: {exc}")

        # --------------------------------------------------
        # 10. Info-Button-Tooltip mit Theme-Farben
        # --------------------------------------------------
        info_btn = getattr(self, "info_button", None) or getattr(self, "btn_info", None)
        if info_btn is not None:
            info_btn.setToolTip(
                tr(
                    "Zeigt Informationen über das OSCam Toolkit an.",
                    "Displays information about the OSCam Toolkit.",
                )
            )
            info_btn.setToolTipDuration(10000)

            if is_matrix:
                tooltip_bg, tooltip_fg, tooltip_border = "#101010", "#00FF00", "#00FF00"
            elif "blue" in theme_color or "blau" in theme_color:
                tooltip_bg, tooltip_fg, tooltip_border = "#202A44", "#FFFFFF", "#4488FF"
            elif "red" in theme_color or "rot" in theme_color:
                tooltip_bg, tooltip_fg, tooltip_border = "#351818", "#FFFFFF", "#FF4444"
            elif "purple" in theme_color or "lila" in theme_color:
                tooltip_bg, tooltip_fg, tooltip_border = "#291A35", "#FFFFFF", "#BB77FF"
            elif "green" in theme_color or "grün" in theme_color:
                tooltip_bg, tooltip_fg, tooltip_border = "#18301F", "#FFFFFF", "#44CC66"
            else:
                tooltip_bg, tooltip_fg, tooltip_border = "#303030", "#FFFFFF", "#777777"

            # Nur den Tooltip-Stil ergänzen; nicht bei jedem Aufruf erneut anhängen.
            info_btn.setStyleSheet(
                f"""
                QToolTip {{
                    background-color: {tooltip_bg};
                    color: {tooltip_fg};
                    border: 1px solid {tooltip_border};
                    border-radius: 5px;
                    padding: 6px;
                    font-size: 10pt;
                }}
                """
            )

        # --------------------------------------------------
        # 11. Button-Text-Fit und ProgressBar abschließen
        # --------------------------------------------------
        fit_buttons = getattr(self, "_fit_all_button_texts", None)
        if callable(fit_buttons):
            QTimer.singleShot(0, fit_buttons)
            QTimer.singleShot(200, fit_buttons)

        if pbar is not None:
            pbar.setValue(100)
            idle_callback = getattr(self, "pbar_idle", None)
            if callable(idle_callback):
                QTimer.singleShot(2000, idle_callback)
            else:
                QTimer.singleShot(2000, pbar.hide)

        QApplication.processEvents()

    def update_language(self):
        """
        Übersetzt alle Buttons, Labels und Header zentral.
        Verhindert 'RuntimeError: wrapped C/C++ object has been deleted'.
        """
        from PyQt6.QtWidgets import QApplication

        # 1. Aktuelle Sprache ermitteln
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        lang_dict = TEXTS.get(lang, TEXTS.get("en", {}))
        self.TEXT = lang_dict

        # Helferfunktion für Übersetzungen
        def get_t(key, default=None):
            if key in lang_dict:
                return lang_dict[key]
            return (
                default if default is not None else str(key).replace("_", " ").title()
            )

        # Sicherheits-Check Funktion
        def safe_ui(attr_name, func_name, *args, **kwargs):
            widget = getattr(self, attr_name, None)
            if widget is not None:
                try:
                    # Prüfen ob das Widget noch "lebt"
                    method = getattr(widget, func_name)
                    method(*args, **kwargs)
                except (RuntimeError, AttributeError):
                    pass

        # --- A) GRID & OPTION BUTTONS ---
        if hasattr(self, "buttons") and self.buttons:
            for key, btn in self.buttons.items():
                try:
                    btn.setText(get_t(key))
                except RuntimeError:
                    pass

        if hasattr(self, "option_buttons") and self.option_buttons:
            for key, val in self.option_buttons.items():
                if isinstance(val, (list, tuple)) and len(val) >= 2:
                    try:
                        prefix = "💻 " if "terminal" in str(key).lower() else ""
                        val[0].setText(f"{prefix}{get_t(val[1])}")
                    except RuntimeError:
                        pass
        # Backup-Button übersetzen
        if hasattr(self, "btn_backup_gui"):
            self.btn_backup_gui.setText(
                self.TEXT.get(
                    "backup_button_text",
                    "💾 Backup erstellen" if self.LANG == "de"
                    else "💾 Create Backup"
                )
            )
        # --- B) HEADER (Die Haupt-Fehlerquelle) ---
        safe_ui("controls_header", "setText", get_t("settings_header", "Einstellungen" if lang == "de" else "Settings"))
        safe_ui(
            "github_header",
            "setText",
            get_t("github_config_header", "GitHub-Konfiguration" if lang == "de" else "GitHub Configuration"),
        )

        # --- C) DIE 3 NEUEN ORDNER-BUTTONS & INSTALLATIONS-BUTTONS ---
        safe_ui(
            "btn_open_work",
            "setText",
            "📁 Arbeitsordner" if lang == "de" else "📁 Working Folder",
        )
        safe_ui(
            "btn_open_temp", "setText", "📁 Temp-Repo" if lang == "de" else "📁 Temp Repo"
        )
        safe_ui("btn_open_emu", "setText", "📁 Emu-Git" if lang == "de" else "📁 Emu Git")

        # HIER ERGÄNZT: Die Übersetzungen für S3, S4 und NCam
        safe_ui(
            "btn_s3", 
            "setText", 
            get_t("install_s3", "🚀 S3 Installieren" if lang == "de" else "🚀 Install S3")
        )
        safe_ui(
            "btn_s4", 
            "setText", 
            get_t("install_s4", "🚀 S4 Installieren" if lang == "de" else "🚀 Install S4")
        )
        safe_ui(
            "btn_ncam", 
            "setText", 
            get_t("install_ncam", "🚀 NCam Installieren" if lang == "de" else "🚀 Install NCam-speedy")
        )

        # --- D) FUNKTIONS-BUTTONS ---
        safe_ui(
            "btn_check_tools", "setText",
            get_t("check_tools_button", "🛠️ Tools prüfen" if lang == "de" else "🛠️ Check Tools")
        )
        safe_ui(
            "btn_check_commit", "setText",
            get_t("check_commit_button", "🔄 Commit prüfen" if lang == "de" else "🔄 Check Commit")
        )
        safe_ui(
            "btn_patch_online", "setText",
            "🌐 " + str(get_t(
                "patch_online_download",
                "Patches aus Git laden" if lang == "de" else "Load Patches from Git"
            ))
        )

        # Patch Autor
        if hasattr(self, "btn_modifier"):
            auth_text = "👤 Patch Autor" if lang == "de" else "👤 Patch Author"
            current_name = getattr(self, "patch_modifier", "speedy005")
            tip = (
                f"Autor: {current_name}" if lang == "de" else f"Author: {current_name}"
            )
            safe_ui("btn_modifier", "setText", auth_text)
            safe_ui("btn_modifier", "setToolTip", tip)

        # Repo URL
        if hasattr(self, "btn_repo_url"):
            safe_ui("btn_repo_url", "setText", get_t("repo_url_button", "🌐 Repo URL"))
            repo_tip = "Emu-Repo URL ändern" if lang == "de" else "Change Emu-Repo URL"
            safe_ui("btn_repo_url", "setToolTip", repo_tip)

        # --- PATCH-ORDNER / PATCH-KOPIERBUTTONS ---
        safe_ui("header_btn_s3_ncam", "setText", get_t("patch_folder_s3_ncam", "S3-NCam-Bonecrew-Pfad" if lang == "de" else "S3-NCam-Bonecrew path"))
        safe_ui("header_btn_s4", "setText", get_t("patch_folder_s4", "S4-Pfad" if lang == "de" else "S4 path"))
        safe_ui("header_btn_patch_ncam", "setText", get_t("patch_copy_s3_ncam", "Patch → S3-NCam"))
        safe_ui("header_btn_patch_s4", "setText", get_t("patch_copy_s4", "Patch → S4"))
        safe_ui("header_btn_s3_ncam", "setToolTip", get_t("patch_folder_s3_ncam_tooltip", "S3-NCam-Bonecrew-Pfad wählen" if lang == "de" else "Select the S3-NCam-Bonecrew path"))
        safe_ui("header_btn_s4", "setToolTip", get_t("patch_folder_s4_tooltip", "S4-Pfad wählen" if lang == "de" else "Select the S4 path"))
        safe_ui(
            "header_btn_patch_ncam",
            "setToolTip",
            "Kopiert oscam-emu.patch in den konfigurierten S3-NCam-Bonecrew-Patch-Ordner."
            if lang == "de"
            else "Copies oscam-emu.patch to the configured S3-NCam-Bonecrew patch folder.",
        )
        safe_ui(
            "header_btn_patch_s4",
            "setToolTip",
            "Kopiert oscam-emu.patch in den konfigurierten S4-Patch-Ordner."
            if lang == "de"
            else "Copies oscam-emu.patch to the configured S4 patch folder.",
        )
        safe_ui(
            "log_button",
            "setToolTip",
            "Speichert den aktuellen Log-/Protokollinhalt in einer Datei."
            if lang == "de"
            else "Saves the current log output to a file.",
        )

        # --- E) LABELS & SYSTEM ---
        safe_ui("lang_label", "setText", get_t("language_label", "Sprache:"))
        safe_ui("color_label", "setText", get_t("color_label", "Farbe:"))
        safe_ui("commit_label", "setText", get_t("commit_count_label", "Anzahl Commits:"))

        safe_ui(
            "patch_emu_git_button",
            "setText",
            get_t("patch_emu_git_button", "Patch OSCam Emu"),
        )
        safe_ui(
            "github_upload_patch_button",
            "setText",
            get_t("github_upload_button", "GitHub Upload"),
        )
        safe_ui("clean_emu_button", "setText", get_t("clean_emu_button", "Bereinigen"))
        safe_ui("copy_log_button", "setText", get_t("copy_log_button", "LOG KOPIEREN" if lang == "de" else "COPY LOG"))
        safe_ui("analyze_build_logs_button", "setText", get_t("analyze_build_logs_button", "BUILD-LOG ANALYSIEREN" if lang == "de" else "ANALYZE BUILD LOG"))
        safe_ui("diagnostics_button", "setText", get_t("system_diagnostics_button", "SYSTEM-DIAGNOSE" if lang == "de" else "SYSTEM DIAGNOSTICS"))
        safe_ui("log_history_button", "setText", get_t("build_log_history_button", "BUILD-LOG-VERLAUF" if lang == "de" else "BUILD LOG HISTORY"))
        safe_ui("clear_console_button", "setText", get_t("clear_console_button", "KONSOLE LEEREN" if lang == "de" else "CLEAR CONSOLE"))
        safe_ui("copy_log_button", "setToolTip", get_t("copy_log_tooltip", "Gesamte sichtbare Konsolenausgabe in die Zwischenablage kopieren" if lang == "de" else "Copy all visible console output to the clipboard"))
        safe_ui("clear_console_button", "setToolTip", get_t("clear_console_tooltip", "Nur die sichtbare Konsolenausgabe leeren; Logdateien bleiben unverändert" if lang == "de" else "Clear only the visible console output; log files remain unchanged"))
        safe_ui("analyze_build_logs_button", "setToolTip", get_t("analyze_build_logs_tooltip", "Das neueste Build-Protokoll auf typische Fehler und Warnungen prüfen" if lang == "de" else "Check the newest build log for common errors and warnings"))
        safe_ui("diagnostics_button", "setToolTip", get_t("system_diagnostics_tooltip", "System, Tool-Verzeichnisse und vorhandene Build-Logs prüfen; startet keinen Build" if lang == "de" else "Check system, tool directories and existing build logs; does not start a build"))
        safe_ui("log_history_button", "setToolTip", get_t("build_log_history_tooltip", "Alle Build-Logs nach Status, Zeit und Fehlerhinweisen vergleichen" if lang == "de" else "Compare all build logs by status, time and error indicators"))

        

        # Tooltips und Hover-Farben nach allen Textänderungen synchronisieren.
        try:
            self.apply_global_button_style()
        except Exception as exc:
            print(f"[update_language] Button-Theme/Tooltips konnten nicht aktualisiert werden: {exc}")

        QApplication.processEvents()


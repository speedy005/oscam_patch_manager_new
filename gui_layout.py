"""Extracted GUI methods for the OSCam Patch Manager.

This module contains a focused mixin. Runtime dependencies and shared helpers
are imported from gui_support to keep behavior consistent across modules.
"""
from gui_support import *  # noqa: F401,F403 - legacy GUI methods use shared names via globals()


class PatchManagerLayoutMixin:
    """Patch Manager Layout"""

    def create_buttons(self):
        self.btn_s3 = QPushButton("🚀 Install S3")
        self.btn_s4 = QPushButton("🚀 Install S4")
        self.btn_ncam = QPushButton("🚀 Install NCam-speedy")

    def _responsive_button_height(self):
        """Berechnet eine einheitliche Buttonhöhe (30–50 px) anhand der Bildschirmhöhe."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        screen = self.screen() if hasattr(self, "screen") else None
        if screen is None and app is not None:
            screen = app.primaryScreen()
        screen_height = screen.availableGeometry().height() if screen else 900
        # 720 px -> 30 px, 1080 px -> 40 px, 1440 px -> 50 px.
        return max(30, min(50, int(round(30 + (screen_height - 720) * 20 / 720))))

    def _fit_all_button_texts(self):
        """Zentriert und skaliert alle Buttons nach jeder Größen-/Textänderung."""
        from PyQt6.QtWidgets import QPushButton, QToolButton, QSizePolicy
        from PyQt6.QtGui import QFont, QFontMetrics

        height = self._responsive_button_height()
        buttons = list(self.findChildren(QPushButton)) + list(self.findChildren(QToolButton))
        # Auch eventuell separat verwaltete Buttons berücksichtigen.
        for collection_name in ("all_buttons", "buttons", "option_buttons"):
            collection = getattr(self, collection_name, None)
            values = collection.values() if isinstance(collection, dict) else (collection or [])
            for value in values:
                if isinstance(value, (tuple, list)):
                    value = value[0] if value else None
                if isinstance(value, (QPushButton, QToolButton)):
                    buttons.append(value)

        # Options-Buttons haben eine bewusst gesetzte Mindestbreite. Die bisherige
        # globale setMinimumWidth(0)-Zeile hat diese Vorgabe bei jedem Resize
        # wieder aufgehoben.
        option_button_ids = set()
        option_buttons = getattr(self, "option_buttons", {})
        if isinstance(option_buttons, dict):
            for value in option_buttons.values():
                candidate = value[0] if isinstance(value, (tuple, list)) and value else value
                if isinstance(candidate, (QPushButton, QToolButton)):
                    option_button_ids.add(id(candidate))

        seen = set()
        for btn in buttons:
            try:
                if id(btn) in seen:
                    continue
                seen.add(id(btn))
                text = " ".join(btn.text().replace("\n", " ").split())
                btn.setFixedHeight(height)
                if id(btn) in option_button_ids:
                    btn.setMinimumWidth(220)
                else:
                    btn.setMinimumWidth(0)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

                # Nicht bei jedem Resize dieselbe CSS-Regel erneut anhängen.
                # Das verhinderte zwar keinen sichtbaren Fehler, ließ den
                # Stylesheet-String aber bei jeder Fensteränderung anwachsen.
                style = btn.styleSheet()
                center_rule = "QPushButton, QToolButton { text-align: center; }"
                if "text-align: center;" not in style:
                    btn.setStyleSheet(style + "\n" + center_rule)

                if text:
                    btn.setToolTip(btn.toolTip() or text)
                    font = QFont(btn.font())
                    font.setBold(True)
                    available = max(45, btn.contentsRect().width() - 16)
                    if btn.width() <= 1:
                        available = max(45, btn.sizeHint().width() - 16)
                    # So groß wie möglich, aber so klein wie nötig, damit der
                    # komplette Text einzeilig in die vorhandene Buttonbreite passt.
                    min_point_size = 8 if id(btn) in option_button_ids else 7
                    for point_size in range(min(14, max(min_point_size, font.pointSize())), min_point_size - 1, -1):
                        font.setPointSize(point_size)
                        if QFontMetrics(font).horizontalAdvance(text) <= available:
                            break
                    btn.setFont(font)
                btn.updateGeometry()
            except RuntimeError:
                continue
            except Exception as exc:
                print(f"[_fit_all_button_texts] Button-Anpassung fehlgeschlagen: {exc}")

    def create_action_button(
        self,
        parent,
        text,
        color,
        callback,
        all_buttons_list,
        fg="white",
        factor_hover=1.15,
        factor_pressed=0.85,
        min_height=50,
        radius=8,
        icon_name=None,
    ):
        # --- Final Label verstecken ---
        if hasattr(self, "hide_final_label"):
            self.hide_final_label()

        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import QSize, Qt
        from PyQt6.QtWidgets import QStyle, QSizePolicy, QPushButton

        # Text-Formatierung: Bei mehr als 12 Zeichen Umbruch für Icons
        display_text = text
        btn = QPushButton(display_text, parent)
        btn.setProperty("action_button", True)
        # --- ICON LOGIK (WINDOWS & LINUX SAFE) ---
        if icon_name:
            icon = QIcon()
            if str(icon_name).startswith("SP_"):
                p_enum = getattr(QStyle.StandardPixmap, icon_name, None)
                if p_enum:
                    icon = self.style().standardIcon(p_enum)
            elif os.path.exists(str(icon_name)):
                icon = QIcon(icon_name)

            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(22, 22))

        # Farben für Effekte berechnen
        hover_color = (
            self.adjust_color(color, factor_hover)
            if hasattr(self, "adjust_color")
            else color
        )
        pressed_color = (
            self.adjust_color(color, factor_pressed)
            if hasattr(self, "adjust_color")
            else color
        )

        # --- STYLESHEET MIT GLOW-EFFEKT ---
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {color}; color: {fg}; border-radius: {radius}px;
                border: 1px solid rgba(255,255,255,0.1); padding: 5px;
                font-weight: bold; min-height: {min_height}px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
                border: 1px solid white;
                color: #FFFFFF;
                /* Glow-Effekt Simulation durch Border */
            }} 
            QPushButton:pressed {{
                background-color: {pressed_color};
                border: 2px solid white;
            }} 
        """
        )

        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # --- DER AUTOMATISCHE REGENBOGEN-TRIGGER ---
        def enhanced_callback():
            # 1. Regenbogen-Progress sofort starten
            pbar = getattr(self, "progress_bar", None)
            if pbar:
                rainbow = (
                    "qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    "stop:0.0 #FF0000, stop:0.2 #FF7F00, stop:0.4 #FFFF00, "
                    "stop:0.6 #00FF00, stop:0.8 #0000FF, stop:1.0 #8B00FF);"
                )
                pbar.setStyleSheet(
                    f"QProgressBar {{ text-align: center; font-weight: 700; border: 2px solid #222; "
                    f"border-radius: 6px; background: #111; color: black; font-size: 15pt; }} "
                    f"QProgressBar::chunk {{ background: {rainbow}; }}"
                )
                pbar.setValue(15)
                pbar.show()

            # 2. Original-Funktion ausführen
            if callback:
                callback()

        if callback:
            btn.clicked.connect(enhanced_callback)

        all_buttons_list.append(btn)
        return btn

    def generate_buttons(
        self, parent, button_definitions, all_buttons_list, info_widget=None
    ):
        """Erzeugt Buttons basierend auf Dictionary-Listen (DE/EN tauglich)."""
        buttons = {}
        def_height = getattr(self, "BUTTON_HEIGHT", 50)
        def_radius = getattr(self, "BUTTON_RADIUS", 8)

        for bd in button_definitions:
            # Falls Name "work", "temp" oder "emu" -> Nutze open_custom_folder
            key = bd.get("key", "unknown")
            callback = bd.get("callback", lambda: None)

            # Icons übersetzen (SP_ Pfade)
            icon = bd.get("icon")
            if not icon and "open" in key:
                icon = "SP_DirIcon"

            btn = self.create_action_button(
                parent=parent,
                text=bd.get("text", "Button"),
                color=bd.get("color", "#444444"),
                callback=callback,
                all_buttons_list=all_buttons_list,
                fg=bd.get("fg", "white"),
                icon_name=icon,
                min_height=bd.get("min_height", def_height),
                radius=bd.get("radius", def_radius),
            )
            buttons[key] = btn
        return buttons

    def _fit_header_controls(self):
        """Passt die Kopfzeilen-Buttons an die verfügbare Fensterbreite an."""
        if not hasattr(self, "header_widget"):
            return

        width = max(480, self.width())
        # Schrift wird bei schmalen Fenstern kleiner, aber nicht unlesbar.
        font_size = max(7, min(10, int(width / 150)))
        compact = width < 1450
        gap = 4 if compact else 8

        for layout_name in ("header_layout", "left_header_layout", "right_header_layout"):
            layout = getattr(self, layout_name, None)
            if layout is not None:
                layout.setSpacing(gap)

        names = (
            "info_button", "btn_s3", "btn_s4", "btn_ncam",
            "header_btn_s3_ncam", "header_btn_s4",
            "header_btn_patch_ncam", "header_btn_patch_s4",
            "log_button", "telemetry_cb", "oscam_source_button",
        )
        for name in names:
            button = getattr(self, name, None)
            if button is None:
                continue
            button.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
            if name != "info_button":
                button.setMinimumHeight(50 if compact else 50)
                button.setMaximumWidth(260 if name in ("btn_s3", "btn_s4", "btn_ncam") else 340)
                button.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _fit_header_logo(self):
        """Skaliert das Banner proportional bis zur maximalen Größe."""
        if (
            not hasattr(self, "logo_label")
            or self.original_pixmap is None
        ):
            return

        rect = self.logo_label.contentsRect()
        if rect.width() <= 0 or rect.height() <= 0:
            return

        # Die verfügbare Fläche des Labels bestimmt die Logo-Größe.
        # Keine festen Pixel-Maxima: Das Banner wächst/schrumpft mit der
        # Fenster- und Bildschirmgröße und behält sein Seitenverhältnis.
        self.update_logo(
            width=rect.width(),
            height=rect.height(),
            fill_gap=False,
        )

    def update_logo(self, width=None, height=None, fill_gap=False):
        """Skaliert das Banner auf die vorgegebene Fläche."""
        if (
            not hasattr(self, "logo_label")
            or self.original_pixmap is None
        ):
            return

        if width is None or height is None:
            rect = self.logo_label.contentsRect()
            width = rect.width()
            height = rect.height()

        if width <= 0 or height <= 0:
            return

        aspect_mode = (
            Qt.AspectRatioMode.IgnoreAspectRatio
            if fill_gap
            else Qt.AspectRatioMode.KeepAspectRatio
        )

        scaled_pixmap = self.original_pixmap.scaled(
            width,
            height,
            aspect_mode,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.logo_label.setPixmap(scaled_pixmap)

    def adjust_color(self, hex_color, factor):
        """
        Passt die Helligkeit einer Farbe an.
        factor > 1.0 = heller (Hover), factor < 1.0 = dunkler (Pressed).
        """
        hex_color = hex_color.lstrip("#")

        # Support für 3-stellige Hex-Codes (z.B. #F00 -> #FF0000)
        if len(hex_color) == 3:
            hex_color = "".join([c * 2 for c in hex_color])

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except ValueError:
            # Fallback falls der Hex-Code ungültig ist
            return "#1E90FF"

        # Farbberechnung mit Clamp (0-255)
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))

        return f"#{r:02X}{g:02X}{b:02X}"

    def update_revision_button_labels(self):
        """
        Aktualisiert die beiden Revisions-Buttons mit der Versionsnummer aus
        globals.h des aktuell verwendeten Git-Commits.

        Beispiel:
            Streamboard Revision (11968)
            OSCam-Emu Revision (11968)

        Die ermittelte Revisionsnummer wird zusätzlich im GUI-Objekt
        gespeichert. Dadurch bleibt die Anzeige auch nach einem
        Sprachwechsel erhalten, selbst wenn globals.h kurzfristig nicht
        erneut gelesen werden kann.
        """
        import os
        import re

        def revision_for(repo_dir, selected_commit=None, cache_attr=None):
            repo_dir = os.path.abspath(str(repo_dir or "").strip())
            commit = str(selected_commit or "").strip()

            if not commit and repo_dir and os.path.isdir(os.path.join(repo_dir, ".git")):
                try:
                    result = git_command(["rev-parse", "HEAD"], cwd=repo_dir)
                    commit = (result.stdout or "").strip()
                except Exception:
                    commit = ""

            revision = ""

            # Die Version wird immer aus globals.h des exakt verwendeten
            # Commits gelesen, nicht aus einer eventuell alten Arbeitsdatei.
            if repo_dir and commit and os.path.isdir(os.path.join(repo_dir, ".git")):
                try:
                    version = str(get_oscam_version(repo_dir, commit) or "").strip()
                except Exception:
                    version = ""

                if version:
                    # Üblicher OSCam-Wert: 2.xx.xx-11968
                    match = re.search(r"(?:^|[-_.])([0-9]+)$", version)
                    if match:
                        revision = match.group(1)
                    else:
                        # Falls globals.h nur eine reine Revisionsnummer enthält.
                        match = re.fullmatch(r"[0-9]+", version)
                        if match:
                            revision = version

            # Letzten erfolgreichen Wert behalten, damit ein Sprachwechsel
            # oder ein kurzzeitig nicht lesbares Repository die Anzeige nicht
            # verschwinden lässt.
            if revision:
                if cache_attr:
                    setattr(self, cache_attr, revision)
            elif cache_attr:
                revision = str(getattr(self, cache_attr, "") or "").strip()

            return revision

        stream_revision = revision_for(
            globals().get("STREAMREPO", ""),
            (
                getattr(self, "selected_streamboard_commit", None)
                or getattr(self, "display_streamboard_commit", None)
            ),
            "streamboard_revision_number",
        )

        emu_dir = globals().get("PATCH_EMU_GIT_DIR", "")
        if not emu_dir:
            emu_dir = getattr(self, "PATCH_EMU_GIT_DIR", "")

        emu_revision = revision_for(
            emu_dir,
            (
                getattr(self, "selected_emu_commit", None)
                or getattr(self, "display_emu_commit", None)
            ),
            "emu_revision_number",
        )

        def set_revision(key, base_text, revision):
            entry = getattr(self, "option_buttons", {}).get(key)
            if not entry:
                return

            btn = entry[0] if isinstance(entry, tuple) else entry
            text = base_text
            if revision:
                text = f"{base_text} ({revision})"

            btn.setText(text)
            btn.setProperty("revision_number", revision or "")
            btn.setProperty("base_text", base_text)

        # Die Bezeichnungen sind sprachunabhängig identisch. Wichtig ist,
        # dass nur der Text vor der Klammer übersetzt würde; die Revision
        # selbst bleibt unverändert erhalten.
        set_revision(
            "streamboard_checkout",
            "Streamboard Rev.",
            stream_revision,
        )
        set_revision(
            "oscam_emu_revision",
            "OSCam-Emu Rev.",
            emu_revision,
        )

    def setup_option_buttons(self, parent_layout):
        """Erstellt die mittleren Buttons mit HTML-Tooltips, Regenbogen-Progress und Sound."""
        from PyQt6.QtWidgets import (
            QGridLayout,
            QWidget,
            QSizePolicy,
            QApplication,
            QPushButton,
        )
        from PyQt6.QtGui import QFont
        from PyQt6.QtCore import QTimer

        # Sprache abrufen
        lang = str(getattr(self, "LANG", "de")).lower()[:2]
        is_de = lang == "de"

        button_defs = [
            (
                "git_status",
                "git_status",
                "#1E90FF",
                self.show_commits,
                "white",
                "SP_FileDialogContentsView",
                "🔍 <b>Git Status:</b> Zeigt die neuesten Commits vom Server an.",
                "🔍 <b>Git Status:</b> Shows the latest commits from the server.",
            ),
            (
                "plugin_update",
                "plugin_update",
                "#FF8C00",
                self.plugin_update_button_clicked,
                "white",
                "SP_ArrowDown",
                "🔄 <b>Update:</b> Sucht nach neuen Versionen für Plugins und Tools.",
                "🔄 <b>Update:</b> Checks for new versions of plugins and tools.",
            ),
            (
                "restart_tool",
                "restart_tool",
                "#FF4500",
                self.restart_application_with_info,
                "white",
                "SP_BrowserReload",
                "♻️ <b>Neustart:</b> Startet den Patch Manager komplett neu.",
                "♻️ <b>Restart:</b> Restarts the patch manager completely.",
            ),
                        (
                "restart_tool_admin",
                "restart_tool_admin",
                "#B22222",
                self.restart_application_elevated,
                "white",
                "SP_DialogApplyButton",
                "🔐 <b>Admin-Neustart:</b> Startet das Tool mit Administratorrechten.",
                "🔐 <b>Admin restart:</b> Restarts the tool with elevated privileges.",
            ),
            (
                "edit_patch_header",
                "edit_patch_header",
                "#32CD32",
                self.edit_patch_header,
                "white",
                "SP_FileDialogDetailedView",
                "📝 <b>Header:</b> Bearbeite die Beschreibungs-Daten des Patches.",
                "📝 <b>Header:</b> Edit the patch description metadata.",
            ),
            (
                "github_emu_config",
                "github_emu_config_button",
                "#FFA500",
                self.edit_emu_github_config,
                "black",
                "SP_ComputerIcon",
                "⚙️ <b>Config:</b> GitHub Token und Emu-Einstellungen konfigurieren.",
                "⚙️ <b>Config:</b> Configure GitHub tokens and Emu settings.",
            ),
            (
                "github_upload_patch",
                "github_upload_patch",
                "#1E90FF",
                github_upload_patch_file,
                "white",
                "SP_ArrowUp",
                "⬆️ <b>Upload:</b> Lädt die aktuelle Patch-Datei in dein GitHub Repo.",
                "⬆️ <b>Upload:</b> Uploads the current patch file to your GitHub repo.",
            ),
            (
                "github_upload_emu",
                "github_upload_emu",
                "#1E90FF",
                github_upload_oscam_emu_folder,
                "white",
                "SP_ArrowUp",
                "📂 <b>Upload:</b> Lädt den gesamten Emu-Ordner auf GitHub hoch.",
                "📂 <b>Upload:</b> Uploads the entire Emu folder to GitHub.",
            ),
            (
                "oscam_emu_git_patch",
                "oscam_emu_git_patch",
                "#32CD32",
                patch_oscam_emu_git,
                "white",
                "SP_DialogApplyButton",
                "🛠️ <b>Patch Emu:</b> Wendet Änderungen auf das Emu-Git Repository an.",
                "🛠️ <b>Patch Emu:</b> Applies changes to the Emu-Git repository.",
            ),
            (
                "oscam_emu_git_clear",
                "oscam_emu_git_clear",
                "#FF4500",
                self.oscam_emu_git_clear,
                "white",
                "SP_TrashIcon",
                "🧹 <b>Clear:</b> Bereinigt das lokale Emu-Verzeichnis (Reset).",
                "🧹 <b>Clear:</b> Cleans the local Emu directory (reset).",
            ),
            (
                "s3_menu",
                "s3_simplebuild",
                "#EAFF00",
                self.start_s3_menu,
                "black",
                "SP_FileDialogDetailedView",
                "🚀 <b>S3 Menü:</b> Öffnet das Standard s3_simplebuild Terminal.",
                "🚀 <b>S3 Menu:</b> Opens the standard s3_simplebuild terminal.",
            ),
            (
                "s4_menu",
                "s4_simplebuild",
                "#00E5FF",
                self.start_s4_menu,
                "black",
                "SP_FileDialogDetailedView",
                "🚀 <b>S4 Menü:</b> Öffnet das S4 Simplebuild Terminal.",
                "🚀 <b>S4 Menu:</b> Opens the S4 Simplebuild terminal.",
            ),
            (
                "ncam_menu",
                "NCam Bonecrew",
                "#FF8C00",
                self.start_ncam_menu,
                "black",
                "SP_ComputerIcon",
                "🏴‍☠️ <b>NCam:</b> Startet das spezialisierte NCam Bonecrew Menü.",
                "🏴‍☠️ <b>NCam:</b> Launches the specialized NCam Bonecrew menu.",
            ),
            (
                "fix_perms",
                "Rechte reparieren" if is_de else "Fix Permissions",
                "#D3D3D3",
                self.fix_all_tool_permissions,
                "black",
                "SP_DialogNoButton",
                "🔓 <b>Rechte:</b> Fixiert Schreibrechte für alle Ordner/Dateien.",
                "🔓 <b>Rights:</b> Fixes write permissions for all folders/files.",
            ),
            (
                "streamboard_checkout",
                "Streamboard Revision" if is_de else "Streamboard Revision",
                "#00BFFF",
                self.checkout_streamboard_revision,
                "white",
                "SP_DialogOpenButton",
                "📌 <b>Streamboard Revision:</b> Beliebigen Streamboard-Commit als Patch-Basis auswählen.",
                "📌 <b>Streamboard Revision:</b> Select any Streamboard commit as the patch base.",
            ),
            (
                "oscam_emu_revision",
                "OSCam-Emu Revision",
                "#00BFFF",
                self.checkout_emu_revision,
                "white",
                "SP_DialogOpenButton",
                "📌 <b>OSCam-Emu Revision:</b> Beliebigen OSCam-Emu-Commit als Patch-Basis auswählen.",
                "📌 <b>OSCam-Emu Revision:</b> Select any OSCam-Emu commit as the patch base.",
            ),
        ]

        container = QGroupBox("INSTALLATION & TOOLS")
        container.setObjectName("installationToolsPanel")
        options_grid = QGridLayout(container)
        options_grid.setSpacing(6)
        options_grid.setContentsMargins(10, 12, 10, 10)

        if not hasattr(self, "all_buttons"):
            self.all_buttons = []

        self.option_buttons = getattr(self, "option_buttons", {})

        # Responsive Startaufteilung; wird bei jeder Größenänderung angepasst.
        cols_per_row = 4

        # Einheitliche Höhe
        FLACH_HEIGHT = 50

        # ---------------------------------------------------------
        # BUTTONS ERSTELLEN
        # ---------------------------------------------------------
        for idx, (
            key,
            text_key,
            color,
            callback,
            fg,
            icon,
            tt_de,
            tt_en,
        ) in enumerate(button_defs):

            raw_text = (
                self.get_t(text_key, text_key)
                if hasattr(self, "get_t")
                else text_key
            )

            btn = QPushButton(raw_text)

            if key == "fix_perms":
                self.btn_fix_perms = btn

            # -----------------------------------------------------
            # CALLBACK
            # -----------------------------------------------------
            def create_cb(c, k=key):
                def wrapper():

                    if "safe_play" in globals():
                        safe_play("service-login.oga")

                    pbar = getattr(self, "progress_bar", None)

                    if pbar:
                        rainbow = (
                            "qlineargradient("
                            "x1:0, y1:0, x2:1, y2:0, "
                            "stop:0.0 #FF0000, "
                            "stop:0.2 #FF7F00, "
                            "stop:0.4 #FFFF00, "
                            "stop:0.6 #00FF00, "
                            "stop:0.8 #0000FF, "
                            "stop:1.0 #8B00FF);"
                        )

                        pbar.setStyleSheet(
                            f"""
                            QProgressBar {{
                                text-align: center;
                                font-weight: 700;
                                border: 2px solid #222;
                                border-radius: 6px;
                                background-color: #111;
                                color: black;
                                font-size: 15pt;
                            }}

                            QProgressBar::chunk {{
                                background-color: {rainbow};
                                border-radius: 4px;
                            }}
                            """
                        )

                        msg = (
                            "Verarbeite..."
                            if is_de
                            else "Processing..."
                        )

                        pbar.setFormat(f"⚙️ {msg} %p%")
                        pbar.setValue(15)
                        pbar.show()

                        QApplication.processEvents()

                    try:

                        if hasattr(c, "__self__") or k == "online_patch_dl":
                            c()

                        else:
                            callback_func = getattr(
                                self,
                                "upload_progress_with_speed",
                                pbar.setValue if pbar else None,
                            )

                            c(
                                gui_instance=self,
                                info_widget=self.info_text,
                                progress_callback=callback_func,
                            )

                        if "safe_play" in globals():
                            safe_play("complete.oga")

                        if pbar:
                            pbar.setValue(100)
                            pbar.setFormat(
                                "✅ OK!"
                                if is_de
                                else "✅ Done!"
                            )

                    except Exception as e:

                        if "safe_play" in globals():
                            safe_play("dialog-error.oga")

                        if pbar:
                            pbar.setStyleSheet(
                                """
                                QProgressBar {
                                    color: red;
                                    font-weight: 700;
                                }
                                """
                            )

                        print(f"Fehler bei {k}: {e}")

                    if pbar:
                        QTimer.singleShot(
                            3000,
                            self.pbar_idle
                            if hasattr(self, "pbar_idle")
                            else lambda: pbar.setValue(0),
                        )

                return wrapper

            # -----------------------------------------------------
            # BUTTON ERSTELLEN
            # -----------------------------------------------------
            btn = self.create_action_button(
                parent=self,
                text=raw_text,
                color=color,
                callback=create_cb(callback),
                all_buttons_list=self.all_buttons,
                fg=fg,
                icon_name=icon,
                min_height=FLACH_HEIGHT,
                radius=getattr(self, "BUTTON_RADIUS", 10),
            )

            # -----------------------------------------------------
            # TOOLTIP
            # -----------------------------------------------------
            btn.setToolTip(
                tt_de if is_de else tt_en
            )

            btn.setStyleSheet(
                btn.styleSheet()
                + f"""
                QToolTip {{
                    background-color: #2b2b2b;
                    color: {color};
                    border: 1px solid {color};
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 10pt;
                }}
                """
            )

            # -----------------------------------------------------
            # WICHTIG:
            # TEXT NICHT UMBRECHEN
            # -----------------------------------------------------
            

            # -----------------------------------------------------
            # BUTTON-GRÖSSE
            # -----------------------------------------------------
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )

            btn.setMinimumWidth(220)
            btn.setMinimumHeight(50)
            btn.setMaximumHeight(50)

            # ---------------------------------------------------------
            # EINZEILIGER BUTTON-TEXT
            # Schrift wird bei langen Namen automatisch kleiner
            # ---------------------------------------------------------
            font = QFont("Segoe UI", 9, QFont.Weight.Bold)
            btn.setFont(font)
            btn.setToolTip(btn.toolTip() or raw_text)


            # -----------------------------------------------------
            # GRID
            # -----------------------------------------------------
            row, col = divmod(
                idx,
                cols_per_row,
            )

            options_grid.addWidget(
                btn,
                row,
                col,
            )

            # Button speichern
            self.option_buttons[key] = (
                btn,
                text_key,
            )

        # ---------------------------------------------------------
        # Die konfigurierten Spalten gleichmäßig verteilen.
        # ---------------------------------------------------------
        for i in range(cols_per_row):
            options_grid.setColumnStretch(i, 1)

        # Responsive Reflow: Buttons bleiben verbunden und werden nur neu angeordnet.
        # Die Reflow-Schwelle an die tatsächliche Mindestbreite der Buttons
        # anlehnen. So nutzt das Grid breite Fenster besser aus, ohne die
        # Buttons unter ihre lesbare Mindestbreite zu drücken.
        self._options_grid_reflow = ResponsiveGridReflow(
            # Drei bis vier ausreichend breite Spalten statt vieler schmaler
            # Spalten; lange Beschriftungen bleiben dadurch lesbar.
            container, options_grid, min_item_width=400, parent=self
        )

        # ---------------------------------------------------------
        # CONTAINER
        # ---------------------------------------------------------
        parent_layout.addWidget(container)

        # Revisions direkt im Button anzeigen, z. B. "Streamboard Revision (11968)".
        self.update_revision_button_labels()

    def update_all_texts(self):
        # ---------------------------------------------------------
        # LABELS
        # ---------------------------------------------------------
        self.lang_label.setText(
            TEXTS[self.LANG]["ui.language"]
        )

        self.color_label.setText(
            TEXTS[self.LANG]["color_label"]
        )

        self.commit_label.setText(
            TEXTS[self.LANG]["commit_count_label"]
        )

        self.info_button.setToolTip(
            TEXTS[self.LANG]["ui.info"]
        )

        # ---------------------------------------------------------
        # OPTION BUTTONS
        # ---------------------------------------------------------
        for key, (btn, text_key) in self.option_buttons.items():

            new_text = self.get_t(text_key, text_key)

            btn.setText(new_text)
            btn.setProperty("text_key", text_key)

        # Revisions-Suffix nach dem Sprachwechsel wieder ergänzen.
        self.update_revision_button_labels()

        # ---------------------------------------------------------
        # GRID BUTTONS / PATCH AKTIONEN
        # ---------------------------------------------------------
        for key, btn in getattr(self, "buttons", {}).items():

            new_text = self.get_t(key, key)

            # Vollständigen Text setzen
            btn.setText(new_text)

            # Übersetzungsschlüssel speichern
            btn.setProperty("text_key", key)

            # Vollständigen Text zusätzlich speichern
            btn.setProperty("full_text", new_text)

        # ---------------------------------------------------------
        # INFO TEXT
        # ---------------------------------------------------------
        # Die Live-Konsole enthält laufende Systemprüfungen, Git-Status und
        # Diagnosemeldungen. Ein Sprachwechsel darf diesen Inhalt niemals
        # mit dem statischen Übersetzungstext überschreiben. Nur initialen
        # Hilfetext einsetzen, falls die Konsole tatsächlich noch leer ist.
        if (
            hasattr(self, "info_text")
            and self.info_text is not None
            and not self.info_text.document().toPlainText().strip()
            and "info_text" in TEXTS.get(self.LANG, {})
        ):
            self.info_text.setPlainText(TEXTS[self.LANG]["info_text"])

    def update_buttons_language(self):
        self.github_upload_patch_button.setText(TEXTS[LANG]["github_upload_patch"])
        self.github_upload_emu_button.setText(TEXTS[LANG]["github_upload_emu"])

    def setup_grid_buttons(self):
            """
            Erstellt die Aktions-Buttons für die Patch-Verwaltung.

            Verwendet ausschließlich das bereits in init_ui()
            erzeugte self.grid_container und self.layout_grid_buttons.

            Der Patch-Check besitzt einen direkten Qt-Signal-Handler,
            damit sicher festgestellt werden kann, ob der Button-Klick
            überhaupt ankommt.
            """

            from PyQt6.QtWidgets import (
                QSizePolicy,
                QApplication,
                QStyle,
            )
            from PyQt6.QtGui import QIcon
            from PyQt6.QtCore import QSize, QTimer

            print(
                "[GRID SETUP] setup_grid_buttons() START",
                flush=True
            )

            # =========================================================
            # SPRACHE
            # =========================================================

            is_de = (
                getattr(
                    self,
                    "LANG",
                    "de"
                ).lower() == "de"
            )

            # =========================================================
            # GRID CONTAINER
            # =========================================================

            grid_container = getattr(
                self,
                "grid_container",
                None
            )

            if grid_container is None:
                raise RuntimeError(
                    "self.grid_container wurde vor "
                    "setup_grid_buttons() nicht erstellt."
                )

            grid_layout = getattr(
                self,
                "layout_grid_buttons",
                None
            )

            if grid_layout is None:
                raise RuntimeError(
                    "self.layout_grid_buttons wurde vor "
                    "setup_grid_buttons() nicht erstellt."
                )

            print(
                f"[GRID SETUP] Container vorhanden: "
                f"{grid_container}",
                flush=True
            )

            print(
                f"[GRID SETUP] Layout vorhanden: "
                f"{grid_layout}",
                flush=True
            )

            # =========================================================
            # ALTE BUTTONS ENTFERNEN
            # =========================================================

            print(
                "[GRID SETUP] Entferne alte Buttons...",
                flush=True
            )

            while grid_layout.count():

                item = grid_layout.takeAt(0)

                widget = item.widget()

                if widget is not None:

                    try:
                        widget.deleteLater()
                    except Exception:
                        pass

            grid_layout.setHorizontalSpacing(6)
            grid_layout.setVerticalSpacing(6)
            grid_layout.setContentsMargins(8, 8, 8, 8)

            # =========================================================
            # ICONS
            # =========================================================

            def get_system_icon(
                theme_name: str,
                fallback: QStyle.StandardPixmap
            ):

                icon = QIcon.fromTheme(
                    theme_name
                )

                if not icon.isNull():
                    return icon

                return QApplication.style().standardIcon(
                    fallback
                )

            ICON_MAP = {

                "patch_create": (
                    "document-new",
                    QStyle.StandardPixmap.SP_FileIcon
                ),

                "patch_renew": (
                    "view-refresh",
                    QStyle.StandardPixmap.SP_BrowserReload
                ),

                "patch_check": (
                    "dialog-ok",
                    QStyle.StandardPixmap.SP_DialogApplyButton
                ),

                "patch_apply": (
                    "system-run",
                    QStyle.StandardPixmap.SP_MediaPlay
                ),

                "patch_zip": (
                    "package-x-generic",
                    QStyle.StandardPixmap.SP_DriveFDIcon
                ),

                "backup_old": (
                    "document-save",
                    QStyle.StandardPixmap.SP_DialogSaveButton
                ),

                "clean_folder": (
                    "edit-clear",
                    QStyle.StandardPixmap.SP_TrashIcon
                ),

                "change_old_dir": (
                    "folder-open",
                    QStyle.StandardPixmap.SP_DirOpenIcon
                ),

                "exit": (
                    "application-exit",
                    QStyle.StandardPixmap.SP_DialogCloseButton
                ),
            }

            # =========================================================
            # BUTTON CALLBACKS
            # =========================================================

            def callback_patch_create():

                print(
                    "[GRID CALLBACK] patch_create START",
                    flush=True
                )

                return create_patch(
                    self,
                    self.info_text,
                    self.progress_bar.setValue
                )

            def callback_patch_renew():

                print(
                    "[GRID CALLBACK] patch_renew START",
                    flush=True
                )

                return create_patch(
                    self,
                    self.info_text,
                    self.progress_bar.setValue
                )

            def callback_patch_check():

                print(
                    "",
                    flush=True
                )

                print(
                    "==================================================",
                    flush=True
                )

                print(
                    "[PATCH CHECK BUTTON] CLICK EMPFANGEN",
                    flush=True
                )

                print(
                    "[PATCH CHECK BUTTON] self.check_patch =",
                    getattr(
                        self,
                        "check_patch",
                        None
                    ),
                    flush=True
                )

                print(
                    "[PATCH CHECK BUTTON] info_text =",
                    getattr(
                        self,
                        "info_text",
                        None
                    ),
                    flush=True
                )

                print(
                    "[PATCH CHECK BUTTON] progress_bar =",
                    getattr(
                        self,
                        "progress_bar",
                        None
                    ),
                    flush=True
                )

                try:

                    if hasattr(
                        self,
                        "append_info"
                    ):

                        self.append_info(
                            self.info_text,
                            "🚨 PATCH CHECK BUTTON WURDE GEDRÜCKT!",
                            "info"
                        )

                except Exception as exc:

                    print(
                        "[PATCH CHECK BUTTON] "
                        "append_info Fehler:",
                        repr(exc),
                        flush=True
                    )

                # -----------------------------------------------------
                # check_patch existiert?
                # -----------------------------------------------------

                check_function = getattr(
                    self,
                    "check_patch",
                    None
                )

                if not callable(
                    check_function
                ):

                    print(
                        "[PATCH CHECK BUTTON] "
                        "FEHLER: self.check_patch ist "
                        "nicht aufrufbar!",
                        flush=True
                    )

                    try:

                        self.append_info(
                            self.info_text,
                            "❌ self.check_patch ist nicht aufrufbar!",
                            "error"
                        )

                    except Exception:
                        pass

                    return False

                # -----------------------------------------------------
                # Progress Callback
                # -----------------------------------------------------

                progress_callback = None

                try:

                    if getattr(
                        self,
                        "progress_bar",
                        None
                    ) is not None:

                        progress_callback = (
                            self.progress_bar.setValue
                        )

                except Exception:
                    progress_callback = None

                # -----------------------------------------------------
                # check_patch aufrufen
                # -----------------------------------------------------

                print(
                    "[PATCH CHECK BUTTON] "
                    "Rufe self.check_patch() auf...",
                    flush=True
                )

                try:

                    result = check_function(
                        self.info_text,
                        progress_callback
                    )

                    print(
                        "[PATCH CHECK BUTTON] "
                        f"check_patch() Ergebnis: {result!r}",
                        flush=True
                    )

                    print(
                        "==================================================",
                        flush=True
                    )

                    return result

                except Exception as exc:

                    print(
                        "[PATCH CHECK BUTTON] "
                        "check_patch() EXCEPTION:",
                        repr(exc),
                        flush=True
                    )

                    import traceback

                    traceback.print_exc()

                    try:

                        self.append_info(
                            self.info_text,
                            (
                                "❌ Fehler beim Starten "
                                "des Patch-Checks:\n"
                                f"{exc}"
                            ),
                            "error"
                        )

                    except Exception:
                        pass

                    return False

            def callback_patch_apply():

                print(
                    "[GRID CALLBACK] patch_apply START",
                    flush=True
                )

                is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
                confirm = QMessageBox(self)
                confirm.setIcon(QMessageBox.Icon.Warning)
                confirm.setWindowTitle("Patch anwenden?" if is_de else "Apply patch?")
                confirm.setText(
                    "Der Patch kann Dateien im Zielprojekt verändern.\n\n"
                    "Stelle sicher, dass wichtige Änderungen gesichert sind.\n"
                    "Möchtest du fortfahren?"
                    if is_de else
                    "The patch may modify files in the target project.\n\n"
                    "Make sure important changes are backed up.\n"
                    "Do you want to continue?"
                )
                confirm.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                confirm.setDefaultButton(QMessageBox.StandardButton.No)
                confirm.button(QMessageBox.StandardButton.Yes).setText("Ja" if is_de else "Yes")
                confirm.button(QMessageBox.StandardButton.No).setText("Nein" if is_de else "No")
                answer = confirm.exec()
                if answer != QMessageBox.StandardButton.Yes:
                    try:
                        self.append_info(
                            self.info_text,
                            "Patch-Anwendung vom Benutzer abgebrochen.",
                            "warning",
                        )
                    except Exception:
                        pass
                    return False

                try:
                    if self.progress_bar:
                        self.progress_bar.setValue(0)
                except Exception:
                    pass

                try:
                    return self.apply_patch(
                        self.info_text,
                        self.progress_bar.setValue
                    )
                except Exception as exc:
                    try:
                        self.append_info(
                            self.info_text,
                            f"Patch konnte nicht angewendet werden: {exc}",
                            "error",
                        )
                    except Exception:
                        pass
                    QMessageBox.critical(
                        self,
                        "Patch-Fehler",
                        f"Der Patch konnte nicht angewendet werden.\n\n{exc}",
                    )
                    return False

            def callback_patch_zip():

                print(
                    "[GRID CALLBACK] patch_zip START",
                    flush=True
                )

                return self.zip_patch(
                    self.info_text,
                    self.progress_bar.setValue
                )

            def callback_backup_old():

                print(
                    "[GRID CALLBACK] backup_old START",
                    flush=True
                )

                return backup_old_patch(
                    self,
                    make_backup=True,
                    info_widget=self.info_text,
                    progress_callback=self.progress_bar.setValue
                )

            def callback_clean_folder():

                print(
                    "[GRID CALLBACK] clean_folder START",
                    flush=True
                )

                is_de = str(getattr(self, "LANG", "de")).lower().startswith("de")
                confirm = QMessageBox(self)
                confirm.setIcon(QMessageBox.Icon.Warning)
                confirm.setWindowTitle(
                    "Patch-Ordner leeren?" if is_de else "Clear patch folder?"
                )
                confirm.setText(
                    "Diese Aktion kann Dateien im Patch-Ordner löschen.\n\n"
                    "Bitte prüfe, ob du benötigte Dateien gesichert hast.\n"
                    "Möchtest du wirklich fortfahren?"
                    if is_de else
                    "This action may delete files in the patch folder.\n\n"
                    "Make sure you have backed up any files you need.\n"
                    "Do you really want to continue?"
                )
                confirm.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                confirm.setDefaultButton(QMessageBox.StandardButton.No)
                confirm.button(QMessageBox.StandardButton.Yes).setText("Ja" if is_de else "Yes")
                confirm.button(QMessageBox.StandardButton.No).setText("Nein" if is_de else "No")
                answer = confirm.exec()
                if answer != QMessageBox.StandardButton.Yes:
                    try:
                        self.append_info(
                            self.info_text,
                            "Bereinigung des Patch-Ordners abgebrochen.",
                            "warning",
                        )
                    except Exception:
                        pass
                    return False

                try:
                    return clean_patch_folder(
                        self,
                        self.info_text,
                        self.progress_bar.setValue
                    )
                except Exception as exc:
                    try:
                        self.append_info(
                            self.info_text,
                            f"Patch-Ordner konnte nicht bereinigt werden: {exc}",
                            "error",
                        )
                    except Exception:
                        pass
                    QMessageBox.critical(
                        self,
                        "Bereinigungsfehler",
                        f"Der Patch-Ordner konnte nicht bereinigt werden.\n\n{exc}",
                    )
                    return False

            def callback_change_old_dir():

                print(
                    "[GRID CALLBACK] change_old_dir START",
                    flush=True
                )

                return self.change_old_patch_dir(
                    self.info_text,
                    self.progress_bar.setValue
                )

            def callback_emu_revision():
                print(
                    "[GRID CALLBACK] oscam_emu_revision START",
                    flush=True
                )
                return self.checkout_emu_revision()

            def callback_exit():

                print(
                    "[GRID CALLBACK] exit START",
                    flush=True
                )

                return self.close_with_confirm()

            # =========================================================
            # ACTION-LISTE
            # =========================================================

            grid_actions = [

                (
                    "patch_create",
                    callback_patch_create,
                    "Erstellt einen neuen Patch aus den aktuellen Änderungen",
                    "Creates a new patch from current changes",
                ),

                (
                    "patch_renew",
                    callback_patch_renew,
                    "Erneuert den vorhandenen Patch im Arbeitsverzeichnis",
                    "Renews the existing patch in work directory",
                ),

                (
                    "patch_check",
                    callback_patch_check,
                    "Prüft, ob der Patch sauber auf den Quellcode anwendbar ist",
                    "Checks if the patch can be applied cleanly",
                ),

                (
                    "patch_apply",
                    callback_patch_apply,
                    "Wendet den Patch permanent auf die OSCam-Sourcen an",
                    "Applies the patch permanently to OSCam sources",
                ),

                (
                    "patch_zip",
                    callback_patch_zip,
                    "Packt alle Patch-Dateien in ein ZIP-Archiv",
                    "Compresses all patch files into a ZIP archive",
                ),

                (
                    "backup_old",
                    callback_backup_old,
                    "Sichert den aktuellen Stand in den Backup-Ordner",
                    "Backs up the current state to backup folder",
                ),

                (
                    "clean_folder",
                    callback_clean_folder,
                    "Löscht temporäre Dateien im Patch-Verzeichnis",
                    "Deletes temporary files in patch directory",
                ),

                (
                    "change_old_dir",
                    callback_change_old_dir,
                    "Wählt ein anderes Verzeichnis für alte Patches aus",
                    "Selects a different directory for old patches",
                ),

                (
                    "exit",
                    callback_exit,
                    "Beendet das Programm sicher",
                    "Exit the program safely",
                ),
            ]

            # =========================================================
            # BUTTON-SPEICHER
            # =========================================================

            self.buttons = {}

            if not hasattr(
                self,
                "all_buttons"
            ):
                self.all_buttons = []

            cols = 3

            btn_color = "#1E90FF"

            # =========================================================
            # BUTTONS ERZEUGEN
            # =========================================================

            for idx, (
                key,
                func,
                tt_de,
                tt_en
            ) in enumerate(
                grid_actions
            ):

                button_text = self.get_t(
                    key,
                    key
                )

                # -----------------------------------------------------
                # Sonderfall clean_folder
                # -----------------------------------------------------

                if key == "clean_folder":

                    if (
                        button_text == "clean_folder"
                        or
                        button_text.strip()
                        == "Patch-Ordner"
                    ):

                        button_text = (
                            "Patch-Ordner leeren"
                            if is_de
                            else
                            "Clear Patch Folder"
                        )

                print(
                    f"[GRID] Erzeuge {key}: "
                    f"{button_text!r}",
                    flush=True
                )

                # -----------------------------------------------------
                # CALLBACK-WRAPPER
                #
                # Wichtig:
                # Kein Lambda.
                # Kein verschachteltes [-1].
                # -----------------------------------------------------

                def grid_callback(
                    checked=False,
                    f=func,
                    k=key
                ):

                    print(
                        "",
                        flush=True
                    )

                    print(
                        "--------------------------------------------------",
                        flush=True
                    )

                    print(
                        f"[GRID SIGNAL] clicked: {k}",
                        flush=True
                    )

                    print(
                        f"[GRID SIGNAL] checked: {checked}",
                        flush=True
                    )

                    print(
                        f"[GRID SIGNAL] callback: {f}",
                        flush=True
                    )

                    try:

                        result = self._run_grid_action(
                            k,
                            f
                        )

                        print(
                            f"[GRID SIGNAL] "
                            f"{k} Ergebnis: {result!r}",
                            flush=True
                        )

                        return result

                    except Exception as exc:

                        print(
                            f"[GRID SIGNAL] "
                            f"{k} EXCEPTION:",
                            repr(exc),
                            flush=True
                        )

                        import traceback

                        traceback.print_exc()

                        return False

                # -----------------------------------------------------
                # BUTTON ERZEUGEN
                # -----------------------------------------------------

                print(
                    f"[GRID] create_action_button("
                    f"{key})...",
                    flush=True
                )

                btn = self.create_action_button(
                    parent=grid_container,
                    text=button_text,
                    color=btn_color,
                    fg="white",
                    callback=grid_callback,
                    all_buttons_list=self.all_buttons,
                    min_height=46,
                    radius=self.BUTTON_RADIUS,
                )

                # -----------------------------------------------------
                # BUTTON VALIDIEREN
                # -----------------------------------------------------

                if btn is None:

                    print(
                        f"[GRID ERROR] "
                        f"create_action_button({key}) "
                        f"gab None zurück!",
                        flush=True
                    )

                    continue

                print(
                    f"[GRID] Button Objekt: "
                    f"{btn!r}",
                    flush=True
                )

                print(
                    f"[GRID] enabled={btn.isEnabled()} "
                    f"visible={btn.isVisible()}",
                    flush=True
                )

                # =====================================================
                # SPEZIALBEHANDLUNG PATCH CHECK
                # =====================================================

                if key == "patch_check":

                    print(
                        "[PATCH CHECK] QPushButton wurde erzeugt",
                        flush=True
                    )

                    print(
                        "[PATCH CHECK] objectName:",
                        btn.objectName(),
                        flush=True
                    )

                    print(
                        "[PATCH CHECK] enabled:",
                        btn.isEnabled(),
                        flush=True
                    )

                    print(
                        "[PATCH CHECK] visible:",
                        btn.isVisible(),
                        flush=True
                    )

                    print(
                        "[PATCH CHECK] signalsBlocked:",
                        btn.signalsBlocked(),
                        flush=True
                    )

                    # -------------------------------------------------
                    # DIREKTER SIGNAL-TEST
                    # -------------------------------------------------

                    def patch_check_direct_signal(
                        checked=False
                    ):

                        print(
                            "",
                            flush=True
                        )

                        print(
                            "##################################################",
                            flush=True
                        )

                        print(
                            "[PATCH CHECK DIRECT] "
                            "Qt clicked SIGNAL EMPFANGEN!",
                            flush=True
                        )

                        print(
                            f"[PATCH CHECK DIRECT] checked={checked}",
                            flush=True
                        )

                        print(
                            "##################################################",
                            flush=True
                        )

                    btn.clicked.connect(
                        patch_check_direct_signal
                    )

                    print(
                        "[PATCH CHECK] "
                        "Direktes clicked-Signal verbunden.",
                        flush=True
                    )

                # =====================================================
                # BUTTON-EIGENSCHAFTEN
                # =====================================================

                btn.setProperty(
                    "text_key",
                    key
                )

                btn.setProperty(
                    "full_text",
                    button_text
                )

                btn.setText(
                    button_text
                )

                btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed
                )

                btn.setMinimumWidth(
                    230
                )

                btn.setMinimumHeight(
                    50
                )

                btn.setMaximumHeight(
                    50
                )

                # =====================================================
                # ICON
                # =====================================================

                theme_name, fallback = ICON_MAP.get(
                    key,
                    (
                        "application-x-executable",
                        QStyle.StandardPixmap.SP_FileIcon
                    )
                )

                btn.setIcon(
                    get_system_icon(
                        theme_name,
                        fallback
                    )
                )

                btn.setIconSize(
                    QSize(
                        20,
                        20
                    )
                )

                # =====================================================
                # TOOLTIP
                # =====================================================

                btn.setToolTip(
                    tt_de
                    if is_de
                    else
                    tt_en
                )

                # =====================================================
                # STYLE
                # =====================================================

                btn.setStyleSheet(
                    btn.styleSheet()
                    +
                    f"""
                    QPushButton {{
                        padding: 8px 10px;
                        text-align: center;
                        border: 1px solid #2d7185;
                        border-radius: 9px;
                        font-weight: 700;
                        min-height: 42px;
                    }}
                    QPushButton:hover {{
                        border: 1px solid #35e6ff;
                        color: #ffffff;
                    }}
                    QPushButton:pressed {{
                        padding-top: 10px;
                        background-color: #123b49;
                    }}

                    QToolTip {{
                    background-color: #202833;
                    color: #EAF6FF;
                    border: 1px solid #00B8D4;
                    border-radius: 4px;
                    padding: 5px;
                    font-size: 10pt;
                    font-weight: bold;
                }}
                                    """
                )

                # =====================================================
                # GRID POSITION
                # =====================================================

                row, col = divmod(
                    idx,
                    cols
                )

                grid_layout.addWidget(
                    btn,
                    row,
                    col
                )

                # =====================================================
                # BUTTON SPEICHERN
                # =====================================================

                self.buttons[
                    key
                ] = btn

                print(
                    f"[GRID] Button fertig: "
                    f"{key} -> {btn.text()!r}",
                    flush=True
                )

            # =========================================================
            # SPALTEN-STRETCH
            # =========================================================

            for i in range(cols):

                grid_layout.setColumnStretch(
                    i,
                    1
                )

            # Bei schmalen Fenstern weniger Spalten, bei breiten mehr.
            self._patch_grid_reflow = ResponsiveGridReflow(
                grid_container, grid_layout, min_item_width=320, parent=self
            )

            # =========================================================
            # TEXT ANPASSEN
            # =========================================================

            QTimer.singleShot(
                100,
                self._fit_all_button_texts
            )

            # =========================================================
            # ABSCHLUSS
            # =========================================================

            print(
                "[GRID SETUP] "
                f"{len(self.buttons)} Buttons erstellt.",
                flush=True
            )

            print(
                "[GRID SETUP] "
                "Patch-Check Button:",
                self.buttons.get(
                    "patch_check"
                ),
                flush=True
            )

            print(
                "[GRID SETUP] setup_grid_buttons() ENDE",
                flush=True
            )


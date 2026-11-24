"""OSCam Patch Manager - Achievement System."""

import json
import os
import threading
from datetime import datetime

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar,
    QScrollArea, QWidget, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QSettings


_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "achievements.json")
_LOCK = threading.Lock()

ACHIEVEMENTS = [
    {
        "id": "first_patch",
        "title_de": "Erster Patch",
        "title_en": "First Patch",
        "description_de": "Erstelle deinen ersten Patch.",
        "description_en": "Create your first patch.",
        "title_it": "Prima patch",
        "description_it": "Crea la tua prima patch.",
        "title_gr": "Πρώτο patch",
        "description_gr": "Δημιούργησε το πρώτο σου patch.",
        "title_pl": "Pierwszy patch",
        "description_pl": "Utwórz swój pierwszy patch.",
        "title_tr": "İlk yama",
        "description_tr": "İlk yamanı oluştur.",
        "event": "patch_created",
        "target": 1,
        "icon": "🏆",
    },
    {
        "id": "patches_10",
        "title_de": "Patch-Sammler",
        "title_en": "Patch Collector",
        "description_de": "Erstelle 10 Patches.",
        "description_en": "Create 10 patches.",
        "title_it": "Collezionista di patch",
        "description_it": "Crea 10 patch.",
        "title_gr": "Συλλέκτης patch",
        "description_gr": "Δημιούργησε 10 patch.",
        "title_pl": "Kolekcjoner patchy",
        "description_pl": "Utwórz 10 patchy.",
        "title_tr": "Yama koleksiyoncusu",
        "description_tr": "10 yama oluştur.",
        "event": "patch_created",
        "target": 10,
        "icon": "🧩",
    },
    {
        "id": "patches_50",
        "title_de": "Patch-Profi",
        "title_en": "Patch Expert",
        "description_de": "Erstelle 50 Patches.",
        "description_en": "Create 50 patches.",
        "title_it": "Esperto di patch",
        "description_it": "Crea 50 patch.",
        "title_gr": "Ειδικός στα patch",
        "description_gr": "Δημιούργησε 50 patch.",
        "title_pl": "Ekspert patchy",
        "description_pl": "Utwórz 50 patchy.",
        "title_tr": "Yama uzmanı",
        "description_tr": "50 yama oluştur.",
        "event": "patch_created",
        "target": 50,
        "icon": "💎",
    },
    {
        "id": "first_build",
        "title_de": "Build erfolgreich",
        "title_en": "Successful Build",
        "description_de": "Schließe deinen ersten Build erfolgreich ab.",
        "description_en": "Complete your first successful build.",
        "title_it": "Build riuscita",
        "description_it": "Completa con successo la tua prima build.",
        "title_gr": "Επιτυχής δημιουργία",
        "description_gr": "Ολοκλήρωσε με επιτυχία την πρώτη σου δημιουργία.",
        "title_pl": "Pierwszy udany build",
        "description_pl": "Pomyślnie ukończ swój pierwszy build.",
        "title_tr": "İlk başarılı derleme",
        "description_tr": "İlk derlemeni başarıyla tamamla.",
        "event": "build_success",
        "target": 1,
        "icon": "🔨",
    },
    {
        "id": "builds_10",
        "title_de": "Build-Meister",
        "title_en": "Build Master",
        "description_de": "Schließe 10 Builds erfolgreich ab.",
        "description_en": "Complete 10 successful builds.",
        "title_it": "Maestro delle build",
        "description_it": "Completa con successo 10 build.",
        "title_gr": "Μάστορας δημιουργιών",
        "description_gr": "Ολοκλήρωσε με επιτυχία 10 δημιουργίες.",
        "title_pl": "Mistrz buildów",
        "description_pl": "Pomyślnie ukończ 10 buildów.",
        "title_tr": "Derleme ustası",
        "description_tr": "10 derlemeyi başarıyla tamamla.",
        "event": "build_success",
        "target": 10,
        "icon": "🚀",
    },
]


def _load_data():
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("Invalid achievement data")
    except (OSError, ValueError, json.JSONDecodeError):
        data = {}

    data.setdefault("counts", {})
    data.setdefault("unlocked", {})
    data.setdefault("history", [])
    return data


def _save_data(data):
    temp_file = _DATA_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    os.replace(temp_file, _DATA_FILE)


def record_event(event, details=None):
    """Record an achievement event. Safe to call from a worker thread."""
    unlocked_now = []

    with _LOCK:
        data = _load_data()
        counts = data.setdefault("counts", {})
        counts[event] = int(counts.get(event, 0)) + 1

        data.setdefault("history", []).append({
            "event": event,
            "details": str(details or ""),
            "time": datetime.now().astimezone().isoformat(timespec="seconds"),
        })
        data["history"] = data["history"][-200:]

        unlocked = data.setdefault("unlocked", {})
        for item in ACHIEVEMENTS:
            if item["event"] != event:
                continue
            if counts[event] >= item["target"] and item["id"] not in unlocked:
                unlocked[item["id"]] = datetime.now().astimezone().isoformat(timespec="seconds")
                unlocked_now.append(item["id"])

        _save_data(data)

    return unlocked_now


def get_progress():
    with _LOCK:
        data = _load_data()

    result = []
    counts = data.get("counts", {})
    unlocked = data.get("unlocked", {})

    for item in ACHIEVEMENTS:
        current = int(counts.get(item["event"], 0))
        result.append({
            **item,
            "current": current,
            "unlocked": item["id"] in unlocked,
            "unlocked_at": unlocked.get(item["id"]),
        })

    return result


class AchievementDialog(QDialog):
    def __init__(self, parent=None, language="de"):
        super().__init__(parent)
        self.language = str(language).lower()[:2]
        lang = self.language

        dialog_titles = {
            "de": "OSCam Erfolgssystem",
            "en": "OSCam Achievement System",
            "it": "Sistema obiettivi OSCam",
            "gr": "Σύστημα επιτευγμάτων OSCam",
            "pl": "System osiągnięć OSCam",
            "tr": "OSCam Başarım Sistemi",
        }
        self.setWindowTitle(dialog_titles.get(lang, dialog_titles["en"]))
        self.resize(620, 600)
        self.setMinimumSize(480, 400)

        # Gespeicherte Größe und Position des Erfolgsfensters wiederherstellen.
        self._geometry_settings = QSettings(
            "speedy005", "OSCamPatchManager"
        )
        saved_geometry = self._geometry_settings.value(
            "achievement/geometry"
        )
        if saved_geometry:
            self.restoreGeometry(saved_geometry)

        layout = QVBoxLayout(self)

        header_titles = {
            "de": "🏆 OSCam Erfolgssystem",
            "en": "🏆 OSCam Achievement System",
            "it": "🏆 Obiettivi OSCam",
            "gr": "🏆 Επιτεύγματα OSCam",
            "pl": "🏆 Osiągnięcia OSCam",
            "tr": "🏆 OSCam Başarımları",
        }
        title = QLabel(header_titles.get(lang, header_titles["en"]))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 12px;")
        layout.addWidget(title)

        self.summary = QLabel()
        self.summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.items_layout = QVBoxLayout(content)
        self.items_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close_labels = {
            "de": "Schließen",
            "en": "Close",
            "it": "Chiudi",
            "gr": "Κλείσιμο",
            "pl": "Zamknij",
            "tr": "Kapat",
        }
        close_button = QPushButton(close_labels.get(lang, close_labels["en"]))
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.refresh()

    def _save_dialog_geometry(self):
        """Speichert Größe und Position des Erfolgsfensters."""
        try:
            self._geometry_settings.setValue(
                "achievement/geometry", self.saveGeometry()
            )
            self._geometry_settings.sync()
        except Exception as exc:
            print(f"[ACHIEVEMENT] Geometrie konnte nicht gespeichert werden: {exc}",
                  flush=True)

    def done(self, result):
        # Wird auch beim Klick auf „Schließen“ (accept) aufgerufen.
        self._save_dialog_geometry()
        super().done(result)

    def closeEvent(self, event):
        self._save_dialog_geometry()
        super().closeEvent(event)

    def refresh(self):
        lang = self.language
        progress = get_progress()
        unlocked_count = sum(1 for item in progress if item["unlocked"])

        summaries = {
            "de": f"{unlocked_count} / {len(progress)} Erfolge freigeschaltet",
            "en": f"{unlocked_count} / {len(progress)} achievements unlocked",
            "it": f"{unlocked_count} / {len(progress)} obiettivi sbloccati",
            "gr": f"{unlocked_count} / {len(progress)} επιτεύγματα ξεκλειδωμένα",
            "pl": f"{unlocked_count} / {len(progress)} osiągnięć odblokowanych",
            "tr": f"{unlocked_count} / {len(progress)} başarı açıldı",
        }
        self.summary.setText(summaries.get(lang, summaries["en"]))

        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            widget = child.widget()
            if widget is not None:
                widget.deleteLater()

        for item in progress:
            card = QWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)

            title_text = item.get(f"title_{lang}", item["title_en"])
            description = item.get(f"description_{lang}", item["description_en"])

            status_labels = {
                "de": ("FREIGESCHALTET", "Noch gesperrt"),
                "en": ("UNLOCKED", "Locked"),
                "it": ("SBLOCCATO", "Bloccato"),
                "gr": ("ΞΕΚΛΕΙΔΩΘΗΚΕ", "Κλειδωμένο"),
                "pl": ("ODBLOKOWANO", "Zablokowane"),
                "tr": ("AÇILDI", "Kilitli"),
            }
            status, locked = status_labels.get(lang, status_labels["en"])

            heading = QLabel(f'{item["icon"]}  {title_text}  {"✓" if item["unlocked"] else "🔒"}')
            heading.setStyleSheet("font-weight: bold; font-size: 14px;")
            card_layout.addWidget(heading)

            card_layout.addWidget(QLabel(description))

            target = item["target"]
            current = min(item["current"], target)
            bar = QProgressBar()
            bar.setRange(0, target)
            bar.setValue(current)
            bar.setFormat(f"{current} / {target}")
            card_layout.addWidget(bar)

            state = QLabel(status if item["unlocked"] else locked)
            state.setStyleSheet(
                "color: #2e9d55; font-weight: bold;"
                if item["unlocked"] else "color: gray;"
            )
            card_layout.addWidget(state)

            card.setStyleSheet(
                "QWidget { border: 1px solid palette(mid); border-radius: 8px; }"
            )
            self.items_layout.addWidget(card)

        self.items_layout.addStretch(1)

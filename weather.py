"""Bilingual weather window for NEON BEAST ULTIMATE.
Uses Open-Meteo. No API key or additional Python packages required.
"""

import json
import urllib.parse
import urllib.request

from paths import CONFIG_FILE

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QFrame
)


WEATHER_TEXT = {
    "de": {
        "title": "NEON BEAST | WETTER",
        "subtitle": "Aktuelles Wetter und 5-Tage-Vorhersage",
        "search": "Anzeigen",
        "location": "Ort eingeben ...",
        "loading": "Wetterdaten werden geladen ...",
        "temperature": "Temperatur",
        "feels": "Gefühlt",
        "humidity": "Luftfeuchtigkeit",
        "wind": "Wind",
        "forecast": "VORHERSAGE – NÄCHSTE 5 TAGE",
        "error": "Wetterdaten konnten nicht geladen werden:",
        "not_found": "Ort nicht gefunden. Bitte überprüfe die Eingabe.",
        "close": "Schließen",
    },
    "en": {
        "title": "NEON BEAST | WEATHER",
        "subtitle": "Current weather and 5-day forecast",
        "search": "Search",
        "location": "Enter city ...",
        "loading": "Loading weather data ...",
        "temperature": "Temperature",
        "feels": "Feels like",
        "humidity": "Humidity",
        "wind": "Wind",
        "forecast": "FORECAST – NEXT 5 DAYS",
        "error": "Could not load weather data:",
        "not_found": "Location not found. Please check your search.",
        "close": "Close",
    },
}

WEATHER_CODES = {
    0: ("Sonnig / Klar", "Sunny / Clear", "☀️"),
    1: ("Überwiegend sonnig", "Mainly sunny", "🌤️"),
    2: ("Teilweise bewölkt", "Partly cloudy", "⛅"),
    3: ("Bewölkt", "Overcast", "☁️"),
    45: ("Neblig", "Foggy", "🌫️"),
    48: ("Reifnebel", "Rime fog", "🌫️"),
    51: ("Leichter Nieselregen", "Light drizzle", "🌦️"),
    53: ("Nieselregen", "Drizzle", "🌦️"),
    55: ("Starker Nieselregen", "Dense drizzle", "🌧️"),
    56: ("Gefrierender Nieselregen", "Freezing drizzle", "🌧️"),
    57: ("Starker gefrierender Nieselregen", "Dense freezing drizzle", "🌧️"),
    61: ("Leichter Regen", "Light rain", "🌧️"),
    63: ("Regen", "Rain", "🌧️"),
    65: ("Starker Regen", "Heavy rain", "🌧️"),
    66: ("Gefrierender Regen", "Freezing rain", "🌧️"),
    67: ("Starker gefrierender Regen", "Heavy freezing rain", "🌧️"),
    71: ("Leichter Schneefall", "Light snowfall", "🌨️"),
    73: ("Schneefall", "Snowfall", "🌨️"),
    75: ("Starker Schneefall", "Heavy snowfall", "❄️"),
    77: ("Schneegriesel", "Snow grains", "❄️"),
    80: ("Regenschauer", "Rain showers", "🌦️"),
    81: ("Starke Regenschauer", "Heavy showers", "🌧️"),
    82: ("Heftige Regenschauer", "Violent showers", "⛈️"),
    85: ("Schneeschauer", "Snow showers", "🌨️"),
    86: ("Starke Schneeschauer", "Heavy snow showers", "❄️"),
    95: ("Gewitter", "Thunderstorm", "⛈️"),
    96: ("Gewitter mit Hagel", "Thunderstorm with hail", "⛈️"),
    99: ("Starkes Gewitter mit Hagel", "Heavy thunderstorm with hail", "⛈️"),
}


def _weather_description(code, language):
    german, english, icon = WEATHER_CODES.get(
        int(code), ("Unbekannt", "Unknown", "🌡️")
    )
    return icon, german if language == "de" else english


class WeatherWorker(QThread):
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, location, language, parent=None):
        super().__init__(parent)
        self.location = location
        self.language = language

    @staticmethod
    def _get_json(url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NEON-BEAST-Weather/1.0"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def run(self):
        try:
            query = urllib.parse.urlencode({
                "name": self.location,
                "count": 1,
                "language": self.language,
                "format": "json",
            })
            geo_url = "https://geocoding-api.open-meteo.com/v1/search?" + query
            geo = self._get_json(geo_url)

            results = geo.get("results") or []
            if not results:
                raise ValueError("LOCATION_NOT_FOUND")

            place = results[0]
            latitude = place["latitude"]
            longitude = place["longitude"]

            forecast_query = urllib.parse.urlencode({
                "latitude": latitude,
                "longitude": longitude,
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,precipitation,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,precipitation_probability_max"
                ),
                "timezone": "auto",
                "forecast_days": 5,
            })

            url = "https://api.open-meteo.com/v1/forecast?" + forecast_query
            data = self._get_json(url)

            data["place_name"] = place.get("name", self.location)
            data["country"] = place.get("country", "")
            self.loaded.emit(data)

        except Exception as exc:
            self.failed.emit(str(exc))


class WeatherWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.language = (
            "de" if str(getattr(parent, "LANG", "de")).lower().startswith("de")
            else "en"
        )
        self.t = WEATHER_TEXT[self.language]
        self._worker = None

        self.setWindowTitle(self.t["title"])
        self.setMinimumSize(520, 570)
        self.resize(600, 650)

        self.setStyleSheet("""
            QDialog {
                background-color: #10131d;
                color: #e8f4ff;
            }
            QLabel {
                color: #e8f4ff;
            }
            QLineEdit {
                background-color: #1b2232;
                color: white;
                border: 1px solid #00cfff;
                border-radius: 6px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #142b43;
                color: #00d9ff;
                border: 1px solid #00cfff;
                border-radius: 6px;
                padding: 9px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16466a;
            }
            QPushButton:disabled {
                color: #777;
                border-color: #555;
            }
            QFrame#weatherCard {
                background-color: #171e2d;
                border: 1px solid #24435e;
                border-radius: 10px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("🌤  " + self.t["title"])
        title.setStyleSheet(
            "font-size: 21px; font-weight: bold; color: #00d9ff;"
        )
        root.addWidget(title)

        subtitle = QLabel(self.t["subtitle"])
        subtitle.setStyleSheet("color: #9eafc5; font-size: 12px;")
        root.addWidget(subtitle)

        search_row = QHBoxLayout()
        saved_city = self._load_saved_city()
        self.location_input = QLineEdit(saved_city or "Ratingen")
        self.location_input.setPlaceholderText(self.t["location"])
        self.location_input.returnPressed.connect(self.load_weather)

        self.search_button = QPushButton(self.t["search"])
        self.search_button.clicked.connect(self.load_weather)

        search_row.addWidget(self.location_input, 1)
        search_row.addWidget(self.search_button)
        root.addLayout(search_row)

        self.status_label = QLabel(self.t["loading"])
        self.status_label.setStyleSheet("color: #9eafc5;")
        root.addWidget(self.status_label)

        self.current_card = QFrame()
        self.current_card.setObjectName("weatherCard")
        current_layout = QVBoxLayout(self.current_card)
        current_layout.setContentsMargins(18, 16, 18, 16)

        self.place_label = QLabel("Ratingen")
        self.place_label.setStyleSheet(
            "font-size: 17px; font-weight: bold; color: #00d9ff;"
        )
        current_layout.addWidget(self.place_label)

        self.temperature_label = QLabel("-- °C")
        self.temperature_label.setStyleSheet(
            "font-size: 42px; font-weight: bold; color: white;"
        )
        current_layout.addWidget(self.temperature_label)

        self.condition_label = QLabel("--")
        self.condition_label.setStyleSheet("font-size: 15px;")
        current_layout.addWidget(self.condition_label)

        self.details_label = QLabel("--")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet(
            "font-size: 12px; color: #b7c8dc; line-height: 1.5;"
        )
        current_layout.addWidget(self.details_label)

        root.addWidget(self.current_card)

        forecast_title = QLabel(self.t["forecast"])
        forecast_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #00d9ff;"
        )
        root.addWidget(forecast_title)

        self.forecast_layout = QVBoxLayout()
        self.forecast_layout.setSpacing(7)
        root.addLayout(self.forecast_layout)

        root.addStretch()

        close_button = QPushButton(self.t["close"])
        close_button.clicked.connect(self.close)
        root.addWidget(close_button)

        self.load_weather()

    def _load_saved_city(self):
        """Lädt die zuletzt verwendete Wetterstadt aus config.json."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)
            if isinstance(config, dict):
                return str(config.get("weather_city", "")).strip()
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        return ""

    def _save_city_to_config(self, city):
        """Speichert die Wetterstadt, ohne andere Config-Einträge zu verändern."""
        try:
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                    config = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"[WETTER] Config konnte nicht sicher gelesen werden: {exc}")
                return


            if not isinstance(config, dict):
                print("[WETTER] Config ist kein gültiges JSON-Objekt. Speichern abgebrochen.")
                return

            config["weather_city"] = city

            with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=4, ensure_ascii=False)
                handle.write("\n")
        except (OSError, TypeError, ValueError) as exc:
            print(f"[WETTER] Stadt konnte nicht gespeichert werden: {exc}")

    def load_weather(self):
        location = self.location_input.text().strip()
        if not location:
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self.search_button.setEnabled(False)
        self.status_label.setText(self.t["loading"])

        self._worker = WeatherWorker(location, self.language, self)
        self._worker.loaded.connect(self.show_weather)
        self._worker.failed.connect(self.show_error)
        self._worker.start()

    def show_weather(self, data):
        self.search_button.setEnabled(True)

        current = data["current"]
        daily = data["daily"]

        place = data.get("place_name", "")
        country = data.get("country", "")

        # Nur nach erfolgreicher Wetterabfrage dauerhaft speichern.
        self._save_city_to_config(self.location_input.text().strip())
        self.place_label.setText(
            f"📍 {place}" + (f", {country}" if country else "")
        )

        icon, description = _weather_description(
            current["weather_code"], self.language
        )

        self.temperature_label.setText(
            f"{round(current['temperature_2m'])} °C"
        )
        self.condition_label.setText(f"{icon}  {description}")

        self.details_label.setText(
            f"{self.t['feels']}: "
            f"{round(current['apparent_temperature'])} °C"
            f"     |     {self.t['humidity']}: "
            f"{current['relative_humidity_2m']} %\n"
            f"{self.t['wind']}: "
            f"{round(current['wind_speed_10m'])} km/h"
            f"     |     Niederschlag: "
            f"{current['precipitation']} mm"
            if self.language == "de"
            else
            f"{self.t['feels']}: "
            f"{round(current['apparent_temperature'])} °C"
            f"     |     {self.t['humidity']}: "
            f"{current['relative_humidity_2m']} %\n"
            f"{self.t['wind']}: "
            f"{round(current['wind_speed_10m'])} km/h"
            f"     |     Precipitation: "
            f"{current['precipitation']} mm"
        )

        while self.forecast_layout.count():
            item = self.forecast_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for index, date in enumerate(daily["time"]):
            code = daily["weather_code"][index]
            icon, description = _weather_description(code, self.language)

            if self.language == "de":
                date_text = f"{date[8:10]}.{date[5:7]}."
            else:
                date_text = f"{date[5:7]}/{date[8:10]}"

            line = QLabel(
                f"{date_text}     {icon}  {description}"
                f"     |     ↑ {round(daily['temperature_2m_max'][index])} °C"
                f"     ↓ {round(daily['temperature_2m_min'][index])} °C"
                f"     |     💧 {daily['precipitation_probability_max'][index]} %"
            )
            line.setStyleSheet("""
                background-color: #171e2d;
                border: 1px solid #24435e;
                border-radius: 6px;
                padding: 9px;
                font-size: 11px;
            """)
            self.forecast_layout.addWidget(line)

        self.status_label.setText(
            f"✓ {place}" if self.language == "de"
            else f"✓ Weather updated: {place}"
        )

    def show_error(self, message):
        self.search_button.setEnabled(True)

        if message == "LOCATION_NOT_FOUND":
            detail = self.t["not_found"]
        else:
            detail = f"{self.t['error']} {message}"

        self.status_label.setText(detail)
        self.status_label.setStyleSheet("color: #ff7777;")


def open_weather_window(parent):
    """Open or raise the weather window belonging to the main GUI."""
    window = getattr(parent, "_weather_window", None)

    if window is not None:
        try:
            if window.isVisible():
                window.raise_()
                window.activateWindow()
                return
        except RuntimeError:
            pass

    window = WeatherWindow(parent)
    window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
    parent._weather_window = window
    window.show()
    window.raise_()
    window.activateWindow()

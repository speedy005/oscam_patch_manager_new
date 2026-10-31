"""NEON BEAST ULTIMATE WEATHER
Bilingual PyQt6 weather dashboard powered by Open-Meteo.
No API key or additional Python packages required.
"""

import json
import urllib.parse
import urllib.request
from datetime import datetime

from paths import CONFIG_FILE

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QDialog, QWidget, QLabel, QPushButton, QLineEdit,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QScrollArea, QSizePolicy
)


# ---------------------------------------------------------
# LANGUAGE
# ---------------------------------------------------------

WEATHER_TEXT = {
    "de": {
        "title": "NEON BEAST | WEATHER SYSTEM",
        "subtitle": "LIVE WETTERDATEN  •  OPEN-METEO",
        "search": "SUCHEN",
        "location": "Stadt oder Ort eingeben ...",
        "loading": "WETTERDATEN WERDEN GELADEN ...",
        "updated": "Letzte Aktualisierung",
        "temperature": "TEMPERATUR",
        "feels": "Gefühlt",
        "humidity": "Luftfeuchtigkeit",
        "wind": "Wind",
        "precipitation": "Niederschlag",
        "uv": "UV-INDEX",
        "sunrise": "SONNENAUFGANG",
        "sunset": "SONNENUNTERGANG",
        "wind_direction": "WINDRICHTUNG",
        "forecast": "5-TAGE-PROGNOSE",
        "hourly": "STUNDENPROGNOSE",
        "today": "HEUTE",
        "refresh": "AKTUALISIEREN",
        "close": "SCHLIESSEN",
        "not_found": "Ort nicht gefunden. Bitte Eingabe prüfen.",
        "error": "Wetterdaten konnten nicht geladen werden:",
        "automatic": "Automatische Aktualisierung alle 15 Minuten",
        "day": "Tag",
        "night": "Nacht",
    },
    "en": {
        "title": "NEON BEAST | WEATHER SYSTEM",
        "subtitle": "LIVE WEATHER DATA  •  OPEN-METEO",
        "search": "SEARCH",
        "location": "Enter city or location ...",
        "loading": "LOADING WEATHER DATA ...",
        "updated": "Last update",
        "temperature": "TEMPERATURE",
        "feels": "Feels like",
        "humidity": "Humidity",
        "wind": "Wind",
        "precipitation": "Precipitation",
        "uv": "UV INDEX",
        "sunrise": "SUNRISE",
        "sunset": "SUNSET",
        "wind_direction": "WIND DIRECTION",
        "forecast": "5-DAY FORECAST",
        "hourly": "HOURLY FORECAST",
        "today": "TODAY",
        "refresh": "REFRESH",
        "close": "CLOSE",
        "not_found": "Location not found. Please check your search.",
        "error": "Could not load weather data:",
        "automatic": "Automatic refresh every 15 minutes",
        "day": "Day",
        "night": "Night",
    },
}


WEATHER_CODES = {
    0: ("Klarer Himmel", "Clear sky", "☀️"),
    1: ("Überwiegend sonnig", "Mainly clear", "🌤️"),
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


WEEKDAYS = {
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}


def weather_description(code, language):
    german, english, icon = WEATHER_CODES.get(
        int(code), ("Unbekannt", "Unknown", "🌡️")
    )
    return icon, german if language == "de" else english


def safe_round(value, digits=0):
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return "--"


def wind_direction(degrees, language):
    try:
        directions_de = [
            "N", "NO", "O", "SO", "S", "SW", "W", "NW"
        ]
        directions_en = [
            "N", "NE", "E", "SE", "S", "SW", "W", "NW"
        ]
        index = int((float(degrees) + 22.5) / 45) % 8
        return (directions_de if language == "de" else directions_en)[index]
    except (TypeError, ValueError):
        return "--"


def format_hour(value):
    try:
        return datetime.fromisoformat(value).strftime("%H:%M")
    except (TypeError, ValueError):
        return "--:--"


def format_day(value, language):
    try:
        date = datetime.fromisoformat(value)
        weekday = WEEKDAYS[language][date.weekday()]
        return f"{weekday} {date.strftime('%d.%m.')}"
    except (TypeError, ValueError):
        return value


# ---------------------------------------------------------
# WEATHER WORKER
# ---------------------------------------------------------

class WeatherWorker(QThread):
    loaded = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, location, language, parent=None):
        super().__init__(parent)
        self.location = location
        self.language = language

    @staticmethod
    def get_json(url):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "NEON-BEAST-Weather/2.0"}
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def run(self):
        try:
            geo_query = urllib.parse.urlencode({
                "name": self.location,
                "count": 1,
                "language": self.language,
                "format": "json",
            })

            geo = self.get_json(
                "https://geocoding-api.open-meteo.com/v1/search?"
                + geo_query
            )

            results = geo.get("results") or []
            if not results:
                raise ValueError("LOCATION_NOT_FOUND")

            place = results[0]

            forecast_query = urllib.parse.urlencode({
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": (
                    "temperature_2m,relative_humidity_2m,"
                    "apparent_temperature,precipitation,"
                    "weather_code,wind_speed_10m,"
                    "wind_direction_10m,is_day"
                ),
                "hourly": (
                    "temperature_2m,precipitation_probability,"
                    "weather_code,wind_speed_10m"
                ),
                "daily": (
                    "weather_code,temperature_2m_max,"
                    "temperature_2m_min,"
                    "precipitation_probability_max,"
                    "sunrise,sunset,uv_index_max,"
                    "wind_direction_10m_dominant"
                ),
                "timezone": "auto",
                "forecast_days": 5,
                "forecast_hours": 24,
            })

            data = self.get_json(
                "https://api.open-meteo.com/v1/forecast?"
                + forecast_query
            )

            data["place_name"] = place.get("name", self.location)
            data["country"] = place.get("country", "")
            self.loaded.emit(data)

        except Exception as exc:
            self.failed.emit(str(exc))


# ---------------------------------------------------------
# MAIN WEATHER WINDOW
# ---------------------------------------------------------

class WeatherWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.language = (
            "de" if str(getattr(parent, "LANG", "de"))
            .lower().startswith("de") else "en"
        )
        self.t = WEATHER_TEXT[self.language]
        self._worker = None

        self.setWindowTitle(self.t["title"])
        self.setMinimumSize(650, 700)

        saved_size = self._load_saved_size()
        if saved_size:
            self.resize(saved_size)
        else:
            self.resize(900, 850)

        self.setStyleSheet("""
            QDialog {
                background-color: #080d18;
                color: #eafaff;
            }

            QWidget#weatherContent {
                background-color: #080d18;
            }

            QLabel {
                color: #eafaff;
                background: transparent;
            }

            QLineEdit {
                background-color: #101c30;
                color: #ffffff;
                border: 1px solid #00d9ff;
                border-radius: 9px;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #007caa;
            }

            QPushButton {
                background-color: #102d45;
                color: #00e5ff;
                border: 1px solid #00cfff;
                border-radius: 9px;
                padding: 11px 17px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #16486b;
                border: 1px solid #66f2ff;
            }

            QPushButton:disabled {
                color: #64758a;
                border-color: #34475c;
            }

            QFrame#heroCard {
                background-color: #101e33;
                border: 1px solid #00bfe8;
                border-radius: 18px;
            }

            QFrame#infoCard {
                background-color: #101a2b;
                border: 1px solid #244663;
                border-radius: 12px;
            }

            QFrame#forecastCard {
                background-color: #111f33;
                border: 1px solid #28516d;
                border-radius: 12px;
            }

            QScrollArea {
                border: none;
                background: transparent;
            }

            QScrollBar:vertical {
                background: #101a2b;
                width: 9px;
                margin: 0;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #007fa5;
                border-radius: 4px;
                min-height: 25px;
            }

            QScrollBar:horizontal {
                background: #101a2b;
                height: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:horizontal {
                background: #007fa5;
                border-radius: 4px;
                min-width: 25px;
            }
        """)

        # Main scrolling area
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer_layout.addWidget(scroll)

        content = QWidget()
        content.setObjectName("weatherContent")
        scroll.setWidget(content)

        root = QVBoxLayout(content)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(15)

        # Header
        header = QHBoxLayout()

        title = QLabel("◈  " + self.t["title"])
        title.setStyleSheet(
            "font-size: 23px; font-weight: 900; color: #00e5ff;"
        )
        header.addWidget(title)
        header.addStretch()

        live = QLabel("● LIVE")
        live.setStyleSheet(
            "color: #35ff9b; font-size: 12px; font-weight: bold;"
        )
        header.addWidget(live)
        root.addLayout(header)

        subtitle = QLabel(self.t["subtitle"])
        subtitle.setStyleSheet(
            "color: #7796b5; font-size: 11px; letter-spacing: 2px;"
        )
        root.addWidget(subtitle)

        # Search
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

        # Status
        self.status_label = QLabel(self.t["loading"])
        self.status_label.setStyleSheet(
            "color: #8daac5; font-size: 11px;"
        )
        root.addWidget(self.status_label)

        # Main hero card
        self.hero_card = QFrame()
        self.hero_card.setObjectName("heroCard")

        hero = QVBoxLayout(self.hero_card)
        hero.setContentsMargins(24, 22, 24, 22)
        hero.setSpacing(8)

        self.place_label = QLabel("📍 Ratingen")
        self.place_label.setStyleSheet(
            "color: #00e5ff; font-size: 19px; font-weight: bold;"
        )
        hero.addWidget(self.place_label)

        self.temperature_label = QLabel("--°")
        self.temperature_label.setStyleSheet(
            "color: #ffffff; font-size: 68px; font-weight: 900;"
        )
        hero.addWidget(self.temperature_label)

        self.condition_label = QLabel("--")
        self.condition_label.setStyleSheet(
            "color: #8eeeff; font-size: 19px; font-weight: bold;"
        )
        hero.addWidget(self.condition_label)

        self.feels_label = QLabel("--")
        self.feels_label.setStyleSheet(
            "color: #91a9c1; font-size: 12px;"
        )
        hero.addWidget(self.feels_label)

        root.addWidget(self.hero_card)

        # Details grid
        self.details_grid = QGridLayout()
        self.details_grid.setSpacing(10)

        self.detail_values = {}

        detail_items = [
            ("humidity", "💧", self.t["humidity"]),
            ("wind", "💨", self.t["wind"]),
            ("precipitation", "🌧️", self.t["precipitation"]),
            ("uv", "☀️", self.t["uv"]),
            ("wind_direction", "🧭", self.t["wind_direction"]),
            ("sunrise", "🌅", self.t["sunrise"]),
            ("sunset", "🌇", self.t["sunset"]),
        ]

        for index, (key, icon, label) in enumerate(detail_items):
            card = self.create_info_card(icon, label)
            self.detail_values[key] = card[1]
            self.details_grid.addWidget(
                card[0], index // 4, index % 4
            )

        root.addLayout(self.details_grid)

        # Hourly forecast
        root.addWidget(self.section_title(self.t["hourly"]))

        self.hourly_container = QWidget()
        self.hourly_layout = QHBoxLayout(self.hourly_container)
        self.hourly_layout.setContentsMargins(0, 0, 0, 0)
        self.hourly_layout.setSpacing(9)
        self.hourly_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        hourly_scroll = QScrollArea()
        hourly_scroll.setWidgetResizable(True)
        hourly_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        hourly_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        hourly_scroll.setFixedHeight(145)
        hourly_scroll.setWidget(self.hourly_container)

        root.addWidget(hourly_scroll)

        # Daily forecast
        root.addWidget(self.section_title(self.t["forecast"]))

        self.forecast_grid = QGridLayout()
        self.forecast_grid.setSpacing(10)
        root.addLayout(self.forecast_grid)

        # Footer
        footer = QHBoxLayout()

        self.updated_label = QLabel(self.t["automatic"])
        self.updated_label.setStyleSheet(
            "color: #718ba5; font-size: 10px;"
        )
        footer.addWidget(self.updated_label, 1)

        self.refresh_button = QPushButton("↻  " + self.t["refresh"])
        self.refresh_button.clicked.connect(self.load_weather)
        footer.addWidget(self.refresh_button)

        close_button = QPushButton(self.t["close"])
        close_button.clicked.connect(self.close)
        footer.addWidget(close_button)

        root.addLayout(footer)

        # Automatic refresh every 15 minutes
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(15 * 60 * 1000)
        self.refresh_timer.timeout.connect(self.load_weather)
        self.refresh_timer.start()

        self.load_weather()

    # -----------------------------------------------------
    # UI HELPERS
    # -----------------------------------------------------

    def section_title(self, text):
        label = QLabel("◈  " + text)
        label.setStyleSheet(
            "color: #00dfff; font-size: 14px; "
            "font-weight: 900; padding-top: 7px;"
        )
        return label

    def create_info_card(self, icon, title):
        card = QFrame()
        card.setObjectName("infoCard")
        card.setMinimumHeight(85)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        heading = QLabel(f"{icon}  {title}")
        heading.setStyleSheet(
            "color: #829eb9; font-size: 10px; font-weight: bold;"
        )
        layout.addWidget(heading)

        value = QLabel("--")
        value.setStyleSheet(
            "color: #00e5ff; font-size: 17px; font-weight: bold;"
        )
        value.setWordWrap(True)
        layout.addWidget(value)

        return card, value

    def create_forecast_card(self, date, icon, description,
                             maximum, minimum, rain):
        card = QFrame()
        card.setObjectName("forecastCard")
        card.setMinimumHeight(150)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(7)

        date_label = QLabel(date)
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet(
            "color: #00dfff; font-size: 12px; font-weight: bold;"
        )
        layout.addWidget(date_label)

        icon_label = QLabel(icon)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 27px;")
        layout.addWidget(icon_label)

        description_label = QLabel(description)
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet(
            "color: #b7c9dd; font-size: 10px;"
        )
        layout.addWidget(description_label)

        temp_label = QLabel(f"↑ {maximum}°  ↓ {minimum}°")
        temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        temp_label.setStyleSheet(
            "color: #ffffff; font-size: 12px; font-weight: bold;"
        )
        layout.addWidget(temp_label)

        rain_label = QLabel(f"💧 {rain}%")
        rain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rain_label.setStyleSheet(
            "color: #69cfff; font-size: 10px;"
        )
        layout.addWidget(rain_label)

        return card

    # -----------------------------------------------------
    # CONFIG
    # -----------------------------------------------------

    def _load_saved_city(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)

            if isinstance(config, dict):
                return str(config.get("weather_city", "")).strip()

        except (OSError, json.JSONDecodeError, TypeError):
            pass

        return ""

    def _load_saved_size(self):
        """Lädt die zuletzt gespeicherte Fenstergröße."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)

            if isinstance(config, dict):
                width = int(config.get("weather_window_width", 0))
                height = int(config.get("weather_window_height", 0))

                if width >= 650 and height >= 700:
                    return QSize(width, height)

        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

        return None

    def closeEvent(self, event):
        self._save_window_size()
        super().closeEvent(event)

    def _save_window_size(self):
        """Speichert nur die Wetterfenstergröße in der Config."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)

            if not isinstance(config, dict):
                return

            config["weather_window_width"] = self.width()
            config["weather_window_height"] = self.height()

            with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
                json.dump(config, handle, indent=4, ensure_ascii=False)
                handle.write("\n")

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"[WETTER] Fenstergröße konnte nicht gespeichert werden: {exc}")

    def _save_city_to_config(self, city):
        """Update only weather_city and preserve all other settings."""
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as handle:
                config = json.load(handle)

            if not isinstance(config, dict):
                print("[WETTER] Ungültige Config. Speichern abgebrochen.")
                return

            config["weather_city"] = city

            with open(CONFIG_FILE, "w", encoding="utf-8") as handle:
                json.dump(
                    config, handle, indent=4, ensure_ascii=False
                )
                handle.write("\n")

        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            print(f"[WETTER] Stadt konnte nicht gespeichert werden: {exc}")

    # -----------------------------------------------------
    # LOAD WEATHER
    # -----------------------------------------------------

    def load_weather(self):
        location = self.location_input.text().strip()

        if not location:
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self.search_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

        self.status_label.setStyleSheet("color: #8daac5;")
        self.status_label.setText(self.t["loading"])

        self._worker = WeatherWorker(
            location, self.language, self
        )
        self._worker.loaded.connect(self.show_weather)
        self._worker.failed.connect(self.show_error)
        self._worker.finished.connect(self.worker_finished)
        self._worker.start()

    def worker_finished(self):
        self.search_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self._worker = None

    # -----------------------------------------------------
    # DISPLAY CURRENT WEATHER
    # -----------------------------------------------------

    def show_weather(self, data):
        current = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        place = data.get("place_name", "")
        country = data.get("country", "")

        self._save_city_to_config(
            self.location_input.text().strip()
        )

        self.place_label.setText(
            f"📍 {place}" + (f", {country}" if country else "")
        )

        icon, description = weather_description(
            current.get("weather_code", 0), self.language
        )

        temperature = safe_round(current.get("temperature_2m"))
        feels = safe_round(current.get("apparent_temperature"))

        self.temperature_label.setText(f"{temperature}°C")
        self.condition_label.setText(f"{icon}  {description}")

        self.feels_label.setText(
            f"{self.t['feels']}: {feels} °C"
        )

        # Detail cards
        self.detail_values["humidity"].setText(
            f"{current.get('relative_humidity_2m', '--')} %"
        )

        self.detail_values["wind"].setText(
            f"{safe_round(current.get('wind_speed_10m'))} km/h"
        )

        self.detail_values["precipitation"].setText(
            f"{safe_round(current.get('precipitation'), 1)} mm"
        )

        uv_values = daily.get("uv_index_max", [])
        uv = safe_round(uv_values[0]) if uv_values else "--"
        self.detail_values["uv"].setText(str(uv))

        direction = wind_direction(
            current.get("wind_direction_10m"), self.language
        )
        self.detail_values["wind_direction"].setText(direction)

        sunrise_values = daily.get("sunrise", [])
        sunset_values = daily.get("sunset", [])

        sunrise = (
            format_hour(sunrise_values[0])
            if sunrise_values else "--:--"
        )
        sunset = (
            format_hour(sunset_values[0])
            if sunset_values else "--:--"
        )

        self.detail_values["sunrise"].setText(sunrise)
        self.detail_values["sunset"].setText(sunset)

        # Update hourly forecast
        self.update_hourly(hourly)

        # Update 5-day forecast
        self.update_daily(daily)

        now = datetime.now().strftime("%H:%M")
        self.status_label.setText(
            f"● LIVE  |  {place}  |  {self.t['updated']}: {now}"
        )
        self.status_label.setStyleSheet(
            "color: #35ff9b; font-size: 11px; font-weight: bold;"
        )

        self.updated_label.setText(
            f"↻ {self.t['automatic']}  •  {now}"
        )

    # -----------------------------------------------------
    # HOURLY FORECAST
    # -----------------------------------------------------

    def update_hourly(self, hourly):
        while self.hourly_layout.count():
            item = self.hourly_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        codes = hourly.get("weather_code", [])
        rain_values = hourly.get("precipitation_probability", [])

        try:
            current_time = datetime.fromisoformat(
                datetime.now().strftime("%Y-%m-%dT%H:00")
            )
            start_index = next(
                (
                    i for i, value in enumerate(times)
                    if datetime.fromisoformat(value) >= current_time
                ),
                0
            )
        except (ValueError, TypeError):
            start_index = 0

        end_index = min(start_index + 12, len(times))

        for index in range(start_index, end_index):
            icon, _ = weather_description(
                codes[index], self.language
            )

            card = QFrame()
            card.setObjectName("forecastCard")
            card.setFixedWidth(82)

            layout = QVBoxLayout(card)
            layout.setContentsMargins(5, 8, 5, 8)
            layout.setSpacing(7)

            hour = QLabel(format_hour(times[index]))
            hour.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hour.setStyleSheet(
                "color: #8faac4; font-size: 10px;"
            )
            layout.addWidget(hour)

            weather_icon = QLabel(icon)
            weather_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            weather_icon.setStyleSheet("font-size: 23px;")
            layout.addWidget(weather_icon)

            temperature = QLabel(
                f"{safe_round(temperatures[index])}°"
            )
            temperature.setAlignment(Qt.AlignmentFlag.AlignCenter)
            temperature.setStyleSheet(
                "color: #ffffff; font-size: 15px; font-weight: bold;"
            )
            layout.addWidget(temperature)

            rain = (
                rain_values[index]
                if index < len(rain_values) else "--"
            )
            rain_label = QLabel(f"💧 {rain}%")
            rain_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rain_label.setStyleSheet(
                "color: #69cfff; font-size: 9px;"
            )
            layout.addWidget(rain_label)

            self.hourly_layout.addWidget(card)

        self.hourly_layout.addStretch()

    # -----------------------------------------------------
    # DAILY FORECAST
    # -----------------------------------------------------

    def update_daily(self, daily):
        while self.forecast_grid.count():
            item = self.forecast_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        dates = daily.get("time", [])
        codes = daily.get("weather_code", [])
        maximums = daily.get("temperature_2m_max", [])
        minimums = daily.get("temperature_2m_min", [])
        rain_values = daily.get(
            "precipitation_probability_max", []
        )

        for index, date in enumerate(dates):
            icon, description = weather_description(
                codes[index], self.language
            )

            maximum = safe_round(maximums[index])
            minimum = safe_round(minimums[index])

            rain = (
                rain_values[index]
                if index < len(rain_values) else "--"
            )

            date_text = (
                self.t["today"] if index == 0
                else format_day(date, self.language)
            )

            card = self.create_forecast_card(
                date_text, icon, description,
                maximum, minimum, rain
            )

            self.forecast_grid.addWidget(
                card, 0, index
            )

    # -----------------------------------------------------
    # ERRORS
    # -----------------------------------------------------

    def show_error(self, message):
        if message == "LOCATION_NOT_FOUND":
            detail = self.t["not_found"]
        else:
            detail = f"{self.t['error']} {message}"

        self.status_label.setText(detail)
        self.status_label.setStyleSheet(
            "color: #ff657a; font-size: 11px; font-weight: bold;"
        )


# ---------------------------------------------------------
# OPEN WINDOW FROM MAIN GUI
# ---------------------------------------------------------

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
    window.setAttribute(
        Qt.WidgetAttribute.WA_DeleteOnClose, True
    )

    parent._weather_window = window

    window.show()
    window.raise_()
    window.activateWindow()
# -*- coding: utf-8 -*-
"""OSCam Patch Manager - AI Assistant."""

import json
from pathlib import Path
import urllib.request
import urllib.error


CONFIG_FILE = Path(__file__).resolve().parent / "config.json"


API_KEY_CONFIG = {
    "Google Gemini": "gemini_api_key",
    "OpenRouter (Free)": "openrouter_api_key",
    "Groq": "groq_api_key",
}


def _load_saved_api_key(provider="Google Gemini"):
    config_key = API_KEY_CONFIG.get(provider)
    if not config_key:
        return ""
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if isinstance(config, dict):
            return str(config.get(config_key, ""))
    except (OSError, ValueError, TypeError):
        pass
    return ""


def _save_api_key(api_key, provider="Google Gemini", language="de"):
    t = AI_TRANSLATIONS.get(str(language).lower()[:2], AI_TRANSLATIONS["en"])
    config_key = API_KEY_CONFIG.get(provider)
    if not config_key:
        raise ValueError(t["unknown_provider"] + " " + str(provider))

    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(
                t["config_read_error"] + " " + str(exc)
            )
        if not isinstance(config, dict):
            raise ValueError(t["config_invalid_json"])

    key = api_key.strip()
    if key:
        config[config_key] = key
    else:
        config.pop(config_key, None)

    temporary = CONFIG_FILE.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(config, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    temporary.replace(CONFIG_FILE)



from PyQt6.QtCore import QThread, pyqtSignal, QSettings
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QTextEdit, QMessageBox, QGroupBox
)


AI_TRANSLATIONS = {
    "de": {
        "title": "OSCam AI Assistant", "provider": "KI-Anbieter",
        "model": "Modell", "api_key": "API-Schlüssel",
        "settings": "KI-Anbieter und API",
        "privacy": "Hinweis: Eingaben werden an den gewählten KI-Anbieter übertragen. Keine Passwörter oder vertraulichen Zugangsdaten senden.",
        "key_placeholder": "API-Schlüssel für den ausgewählten Anbieter",
        "output_placeholder": "Dein KI-Chat erscheint hier ...",
        "prompt_placeholder": "Frage zur Patch-Analyse oder Fehlersuche ...",
        "send": "➤ Senden", "test": "🔑 API testen",
        "clear": "Chat leeren", "close": "Schließen",
        "testing": "Teste ...", "responding": "KI antwortet ...",
        "api_required": "Bitte API-Schlüssel und Modell eingeben.",
        "checking": "Verbindung wird geprüft ...",
        "config": "Konfiguration",
        "test_prompt": "Hallo! Antworte kurz auf Deutsch.",
        "test_success": "HTTP 200 – Verbindung erfolgreich!",
        "error_details_missing": "Keine Fehlerdetails verfügbar.",
        "api_error": "API-Fehler HTTP",
        "connection_error": "Verbindungs- oder Antwortfehler:",
        "connection_failed": "Verbindungsfehler:",
    },
    "en": {
        "title": "OSCam AI Assistant", "provider": "Provider",
        "model": "Model", "api_key": "API Key",
        "settings": "AI provider and API",
        "privacy": "Notice: Your prompts are sent to the selected AI provider. Do not send passwords or confidential credentials.",
        "key_placeholder": "API key for the selected provider",
        "output_placeholder": "Your AI conversation appears here ...",
        "prompt_placeholder": "Ask about patch analysis or troubleshooting ...",
        "send": "➤ Send", "test": "🔑 Test API",
        "clear": "Clear chat", "close": "Close",
        "testing": "Testing ...", "responding": "AI is responding ...",
        "api_required": "Please enter an API key and model.",
        "checking": "Checking connection ...",
        "config": "Configuration",
    },
    "it": {
        "title": "Assistente IA OSCam", "provider": "Fornitore",
        "model": "Modello", "api_key": "Chiave API",
        "settings": "Fornitore IA e API",
        "privacy": "Nota: i messaggi vengono inviati al fornitore IA selezionato. Non inviare password o credenziali riservate.",
        "key_placeholder": "Chiave API del fornitore selezionato",
        "output_placeholder": "La conversazione IA apparirà qui ...",
        "prompt_placeholder": "Domanda sull'analisi della patch o sulla risoluzione dei problemi ...",
        "send": "➤ Invia", "test": "🔑 Testa API",
        "clear": "Svuota chat", "close": "Chiudi",
        "testing": "Test in corso ...", "responding": "L'IA sta rispondendo ...",
        "api_required": "Inserisci la chiave API e il modello.",
        "checking": "Verifica della connessione ...",
        "config": "Configurazione",
    },
    "gr": {
        "title": "Βοηθός AI OSCam", "provider": "Πάροχος",
        "model": "Μοντέλο", "api_key": "Κλειδί API",
        "settings": "Πάροχος AI και API",
        "privacy": "Σημείωση: Τα μηνύματα αποστέλλονται στον επιλεγμένο πάροχο AI. Μην στέλνετε κωδικούς πρόσβασης ή εμπιστευτικά στοιχεία.",
        "key_placeholder": "Κλειδί API για τον επιλεγμένο πάροχο",
        "output_placeholder": "Η συνομιλία AI θα εμφανιστεί εδώ ...",
        "prompt_placeholder": "Ερώτηση σχετικά με την ανάλυση patch ή την αντιμετώπιση προβλημάτων ...",
        "send": "➤ Αποστολή", "test": "🔑 Έλεγχος API",
        "clear": "Εκκαθάριση συνομιλίας", "close": "Κλείσιμο",
        "testing": "Έλεγχος ...", "responding": "Το AI απαντά ...",
        "api_required": "Εισαγάγετε κλειδί API και μοντέλο.",
        "checking": "Έλεγχος σύνδεσης ...",
        "config": "Ρυθμίσεις",
    },
    "pl": {
        "title": "Asystent AI OSCam", "provider": "Dostawca",
        "model": "Model", "api_key": "Klucz API",
        "settings": "Dostawca AI i API",
        "privacy": "Uwaga: wiadomości są wysyłane do wybranego dostawcy AI. Nie wysyłaj haseł ani poufnych danych logowania.",
        "key_placeholder": "Klucz API wybranego dostawcy",
        "output_placeholder": "Tutaj pojawi się rozmowa z AI ...",
        "prompt_placeholder": "Pytanie dotyczące analizy patcha lub rozwiązywania problemów ...",
        "send": "➤ Wyślij", "test": "🔑 Testuj API",
        "clear": "Wyczyść czat", "close": "Zamknij",
        "testing": "Testowanie ...", "responding": "AI odpowiada ...",
        "api_required": "Wprowadź klucz API i model.",
        "checking": "Sprawdzanie połączenia ...",
        "config": "Konfiguracja",
    },
    "tr": {
        "title": "OSCam Yap zekâ Asistanı", "provider": "Sağlayıcı",
        "model": "Model", "api_key": "API Anahtarı",
        "settings": "Yapay zekâ sağlayıcısı ve API",
        "privacy": "Not: Mesajlarınız seçilen yapay zekâ sağlayıcısına gönderilir. Parola veya gizli erişim bilgileri göndermeyin.",
        "key_placeholder": "Seçilen sağlayıcının API anahtarı",
        "output_placeholder": "Yapay zekâ sohbetiniz burada görünecek ...",
        "prompt_placeholder": "Patch analizi veya sorun giderme hakkında soru sorun ...",
        "send": "➤ Gönder", "test": "🔑 API'yi test et",
        "clear": "Sohbeti temizle", "close": "Kapat",
        "testing": "Test ediliyor ...", "responding": "Yapay zekâ yanıtlıyor ...",
        "api_required": "Lütfen API anahtarını ve modeli girin.",
        "checking": "Bağlantı kontrol ediliyor ...",
        "config": "Yapılandırma",
    },
}

for _language, _values in {'de': {'unknown_provider': 'Unbekannter KI-Anbieter:', 'config_read_error': 'config.json konnte nicht gelesen werden:', 'config_invalid_json': 'config.json enthält kein JSON-Objekt.'}, 'en': {'unknown_provider': 'Unknown AI provider:', 'config_read_error': 'Could not read config.json:', 'config_invalid_json': 'config.json does not contain a JSON object.'}, 'it': {'unknown_provider': 'Fornitore IA sconosciuto:', 'config_read_error': 'Impossibile leggere config.json:', 'config_invalid_json': 'config.json non contiene un oggetto JSON.'}, 'gr': {'unknown_provider': 'Άγνωστος πάροχος AI:', 'config_read_error': 'Δεν ήταν δυνατή η ανάγνωση του config.json:', 'config_invalid_json': 'Το config.json δεν περιέχει αντικείμενο JSON.'}, 'pl': {'unknown_provider': 'Nieznany dostawca AI:', 'config_read_error': 'Nie można odczytać pliku config.json:', 'config_invalid_json': 'Plik config.json nie zawiera obiektu JSON.'}, 'tr': {'unknown_provider': 'Bilinmeyen yapay zekâ sağlayıcısı:', 'config_read_error': 'config.json okunamadı:', 'config_invalid_json': 'config.json bir JSON nesnesi içermiyor.'}}.items():
    AI_TRANSLATIONS[_language].update(_values)


for _language, _values in {'en': {'test_prompt': 'Hello! Reply briefly in English.', 'test_success': 'HTTP 200 – Connection successful!', 'api_error': 'API error HTTP', 'connection_error': 'Connection or response error:', 'connection_failed': 'Connection error:', 'error_details_missing': 'No error details available.'}, 'it': {'test_prompt': 'Ciao! Rispondi brevemente in italiano.', 'test_success': 'HTTP 200 – Connessione riuscita!', 'api_error': 'Errore API HTTP', 'connection_error': 'Errore di connessione o risposta:', 'connection_failed': 'Errore di connessione:', 'error_details_missing': "Nessun dettaglio dell'errore disponibile."}, 'gr': {'test_prompt': 'Γεια! Απάντησε σύντομα στα ελληνικά.', 'test_success': 'HTTP 200 – Η σύνδεση ήταν επιτυχής!', 'api_error': 'Σφάλμα API HTTP', 'connection_error': 'Σφάλμα σύνδεσης ή απάντησης:', 'connection_failed': 'Σφάλμα σύνδεσης:', 'error_details_missing': 'Δεν υπάρχουν διαθέσιμες λεπτομέρειες σφάλματος.'}, 'pl': {'test_prompt': 'Cześć! Odpowiedz krótko po polsku.', 'test_success': 'HTTP 200 – Połączenie zakończone sukcesem!', 'api_error': 'Błąd API HTTP', 'connection_error': 'Błąd połączenia lub odpowiedzi:', 'connection_failed': 'Błąd połączenia:', 'error_details_missing': 'Brak szczegółów błędu.'}, 'tr': {'test_prompt': 'Merhaba! Kısaca Türkçe yanıt ver.', 'test_success': 'HTTP 200 – Bağlantı başarılı!', 'api_error': 'API hatası HTTP', 'connection_error': 'Bağlantı veya yanıt hatası:', 'connection_failed': 'Bağlantı hatası:', 'error_details_missing': 'Hata ayrıntısı bulunamadı.'}}.items():
    AI_TRANSLATIONS[_language].update(_values)



PROVIDERS = {
    "OpenRouter (Free)": {
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "model": "openrouter/free",
    },
    "Groq": {
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "model": "llama-3.3-70b-versatile",
    },
    "Google Gemini": {
        "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/",
        "model": "gemini-3.8-flash",
    },
}


class AIWorker(QThread):
    result_ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, provider, model, api_key, messages, language='en'):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.messages = messages
        self.t = AI_TRANSLATIONS.get(str(language).lower()[:2], AI_TRANSLATIONS['en'])

    def run(self):
        try:
            if self.provider == "Google Gemini":
                url = (
                    PROVIDERS[self.provider]["endpoint"]
                    + self.model
                    + ":generateContent?key="
                    + self.api_key
                )
                contents = []
                for item in self.messages:
                    role = "model" if item["role"] == "assistant" else "user"
                    contents.append({
                        "role": role,
                        "parts": [{"text": item["content"]}],
                    })
                payload = {"contents": contents}
                headers = {"Content-Type": "application/json"}
            else:
                url = PROVIDERS[self.provider]["endpoint"]
                payload = {
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": 0.3,
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.api_key,
                }
                if self.provider == "OpenRouter (Free)":
                    headers["HTTP-Referer"] = "https://localhost"
                    headers["X-Title"] = "OSCam Patch Manager"

            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))

            if self.provider == "Google Gemini":
                answer = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                answer = data["choices"][0]["message"]["content"]

            self.result_ready.emit(str(answer).strip())

        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            self.failed.emit(f"{self.t['api_error']} {exc.code}:\n{detail[:1800]}")
        except Exception as exc:
            self.failed.emit(f"{self.t['connection_error']}\n{exc}")



class APITestWorker(QThread):
    result_ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, provider, model, api_key, language='en'):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.t = AI_TRANSLATIONS.get(str(language).lower()[:2], AI_TRANSLATIONS['en'])

    def run(self):
        try:
            if self.provider == "Google Gemini":
                import urllib.parse
                url = (
                    PROVIDERS[self.provider]["endpoint"]
                    + self.model
                    + ":generateContent?"
                    + urllib.parse.urlencode({"key": self.api_key})
                )
                payload = {
                    "contents": [{
                        "parts": [{"text": self.t["test_prompt"]}]
                    }],
                    "generationConfig": {"maxOutputTokens": 128},
                }
                headers = {"Content-Type": "application/json"}
            else:
                url = PROVIDERS[self.provider]["endpoint"]
                payload = {
                    "model": self.model,
                    "messages": [{
                        "role": "user",
                        "content": self.t["test_prompt"]
                    }],
                    "temperature": 0.2,
                    "max_tokens": 128,
                }
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + self.api_key,
                }
                if self.provider == "OpenRouter (Free)":
                    headers["HTTP-Referer"] = "https://localhost"
                    headers["X-Title"] = "OSCam Patch Manager"

            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=45) as response:
                data = json.loads(response.read().decode("utf-8"))

            if self.provider == "Google Gemini":
                answer = data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                answer = data["choices"][0]["message"]["content"]

            self.result_ready.emit(
                self.t["test_success"] + "\\n\\n" + str(answer).strip()
            )
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = self.t["error_details_missing"]
            self.failed.emit(f"{self.t['api_error']} {exc.code}\\n\\n{detail[:2000]}")
        except Exception as exc:
            self.failed.emit(f"{self.t['connection_failed']}\\n{exc}")


class AIAssistantDialog(QDialog):
    def __init__(self, parent=None, language="de"):
        super().__init__(parent)
        self.lang = str(language).lower()[:2]
        self.t = AI_TRANSLATIONS.get(self.lang, AI_TRANSLATIONS["en"])
        self.settings = QSettings("speedy005", "OSCamPatchManager")
        self.messages = []
        self.worker = None

        self.setWindowTitle(self.t["title"])
        self.resize(850, 680)
        self.setMinimumSize(650, 500)

        layout = QVBoxLayout(self)

        heading = QLabel("🤖 " + self.t["title"])
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(heading)

        privacy = QLabel(self.t["privacy"])
        privacy.setWordWrap(True)
        privacy.setStyleSheet(
            "padding: 9px; background: #59451d; color: white; border-radius: 5px;"
        )
        layout.addWidget(privacy)

        settings_box = QGroupBox(self.t["settings"])
        settings_layout = QVBoxLayout(settings_box)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel(self.t["provider"] + ":"))
        self.provider = QComboBox()
        self.provider.addItems(list(PROVIDERS.keys()))
        saved_provider = self.settings.value("ai/provider", "OpenRouter (Free)")
        index = self.provider.findText(saved_provider)
        self.provider.setCurrentIndex(max(0, index))
        provider_row.addWidget(self.provider, 2)

        provider_row.addWidget(QLabel(self.t["model"] + ":"))
        self.model = QComboBox()
        self.model.setEditable(True)
        self.model.addItems([
            "openrouter/free",
            "llama-3.3-70b-versatile",
            "gemini-3.8-flash",
        ])
        settings_layout.addLayout(provider_row)

        model_row = QHBoxLayout()
        model_row.addWidget(self.model, 1)
        settings_layout.addLayout(model_row)

        key_row = QHBoxLayout()
        key_row.addWidget(QLabel(self.t["api_key"] + ":"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText(self.t["key_placeholder"])
        self.api_key.setText(
            _load_saved_api_key(self.provider.currentText())
        )
        self.api_key.editingFinished.connect(
            lambda: _save_api_key(
                self.api_key.text(), self.provider.currentText(), self.lang
            )
        )
        key_row.addWidget(self.api_key, 1)
        settings_layout.addLayout(key_row)

        layout.addWidget(settings_box)

        self.provider.currentTextChanged.connect(self._provider_changed)
        self._provider_changed(self.provider.currentText(), initial=True)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(self.t["output_placeholder"])
        layout.addWidget(self.output, 1)

        self.prompt = QTextEdit()
        self.prompt.setMaximumHeight(100)
        self.prompt.setPlaceholderText(self.t["prompt_placeholder"])
        layout.addWidget(self.prompt)

        buttons = QHBoxLayout()
        self.send_button = QPushButton(self.t["send"])
        self.test_api_button = QPushButton(self.t["test"])
        self.clear_button = QPushButton(self.t["clear"])
        close_button = QPushButton(self.t["close"])
        buttons.addWidget(self.send_button)
        buttons.addWidget(self.test_api_button)
        buttons.addWidget(self.clear_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

        self.send_button.clicked.connect(self.send_message)
        self.test_api_button.clicked.connect(self.test_current_api)
        self.clear_button.clicked.connect(self.clear_chat)
        close_button.clicked.connect(self.close)

    def _provider_changed(self, provider, initial=False):
        if provider not in PROVIDERS:
            return

        previous = getattr(self, "_active_provider", None)
        if not initial and previous in PROVIDERS:
            try:
                _save_api_key(self.api_key.text(), previous, self.lang)
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, self.t["config"], str(exc))

        self.api_key.setText(_load_saved_api_key(provider))
        self._active_provider = provider

        default_model = PROVIDERS[provider]["model"]
        if initial:
            saved_model = self.settings.value("ai/model", "")
            if saved_model and self.settings.value("ai/provider") == provider:
                default_model = saved_model
            if provider == "Google Gemini" and default_model == "gemini-3.8-flash":
                default_model = "gemini-3.8-flash"
                self.settings.setValue("ai/model", default_model)

        self.model.setCurrentText(default_model)
        self.settings.setValue("ai/provider", provider)

    def test_current_api(self):
        provider = self.provider.currentText()
        key = self.api_key.text().strip()
        model = self.model.currentText().strip()

        if not key or not model:
            QMessageBox.warning(
                self, "API",
                self.t["api_required"]
            )
            return

        try:
            _save_api_key(key, provider, self.lang)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self.t["config"], str(exc))
            return

        self.test_api_button.setEnabled(False)
        self.test_api_button.setText(
            self.t["testing"]
        )
        self.output.append(
            f"<b>API-Test: {provider} – {model}</b><br>{self.t['checking']}"
        )

        self.test_worker = APITestWorker(provider, model, key, self.lang)
        self.test_worker.result_ready.connect(self._on_test_result)
        self.test_worker.failed.connect(self._on_test_error)
        self.test_worker.finished.connect(self._on_test_finished)
        self.test_worker.start()

    def _on_test_result(self, result):
        self.output.append(result.replace("\\n", "<br>"))
        self.output.append("")

    def _on_test_error(self, error):
        self.output.append(error.replace("\\n", "<br>"))
        self.output.append("")

    def _on_test_finished(self):
        self.test_api_button.setEnabled(True)
        self.test_api_button.setText(
            self.t["test"]
        )
        self.test_worker = None

    def send_message(self):
        prompt = self.prompt.toPlainText().strip()
        key = self.api_key.text().strip()
        provider = self.provider.currentText()
        model = self.model.currentText().strip()

        if not prompt:
            return
        if not key or not model:
            QMessageBox.warning(
                self,
                "API",
                self.t["api_required"]
            )
            return
        if provider not in PROVIDERS:
            return

        self.settings.setValue("ai/provider", provider)
        self.settings.setValue("ai/model", model)
        try:
            _save_api_key(key, provider, self.lang)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, self.t["config"], str(exc))
            return

        self.messages.append({"role": "user", "content": prompt})
        self.output.append(f"<b>{self.t['send'].replace('➤ ', '')}:</b> {prompt}")
        self.prompt.clear()
        self.send_button.setEnabled(False)
        self.send_button.setText(
            self.t["responding"]
        )

        self.worker = AIWorker(provider, model, key, list(self.messages), self.lang)
        self.worker.result_ready.connect(self._on_result)
        self.worker.failed.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_result(self, answer):
        self.messages.append({"role": "assistant", "content": answer})
        self.output.append(f"<b>🤖 {self.t['title']}:</b><br>{answer}")
        self.output.append("")

    def _on_error(self, error):
        self.output.append(f"<b>API:</b><br>{error}")
        self.output.append("")

    def _on_finished(self):
        self.send_button.setEnabled(True)
        self.send_button.setText(
            self.t["send"]
        )
        self.worker = None

    def clear_chat(self):
        self.messages.clear()
        self.output.clear()

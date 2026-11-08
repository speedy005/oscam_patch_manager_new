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


def _save_api_key(api_key, provider="Google Gemini"):
    config_key = API_KEY_CONFIG.get(provider)
    if not config_key:
        raise ValueError("Unbekannter KI-Anbieter: " + str(provider))

    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(
                "config.json konnte nicht gelesen werden: " + str(exc)
            )
        if not isinstance(config, dict):
            raise ValueError("config.json enthält kein JSON-Objekt.")

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

    def __init__(self, provider, model, api_key, messages):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.messages = messages

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
            self.failed.emit(f"API-Fehler HTTP {exc.code}:\n{detail[:1800]}")
        except Exception as exc:
            self.failed.emit(f"Verbindungs- oder Antwortfehler:\n{exc}")



class APITestWorker(QThread):
    result_ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, provider, model, api_key):
        super().__init__()
        self.provider = provider
        self.model = model
        self.api_key = api_key

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
                        "parts": [{"text": "Hallo! Antworte kurz auf Deutsch."}]
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
                        "content": "Hallo! Antworte kurz auf Deutsch."
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
                "HTTP 200 – Verbindung erfolgreich!\\n\\n" + str(answer).strip()
            )
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = "Keine Fehlerdetails verfügbar."
            self.failed.emit(f"HTTP {exc.code}\\n\\n{detail[:2000]}")
        except Exception as exc:
            self.failed.emit(f"Verbindungsfehler:\\n{exc}")


class AIAssistantDialog(QDialog):
    def __init__(self, parent=None, language="de"):
        super().__init__(parent)
        self.is_de = str(language).lower().startswith("de")
        self.settings = QSettings("speedy005", "OSCamPatchManager")
        self.messages = []
        self.worker = None

        self.setWindowTitle("OSCam AI Assistant")
        self.resize(850, 680)
        self.setMinimumSize(650, 500)

        layout = QVBoxLayout(self)

        heading = QLabel("🤖 OSCam AI Assistant")
        heading.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(heading)

        privacy = QLabel(
            "Hinweis: Eingaben werden an den gewählten KI-Anbieter übertragen. "
            "Keine Passwörter oder vertraulichen Zugangsdaten senden."
            if self.is_de else
            "Notice: Your prompts are sent to the selected AI provider. "
            "Do not send passwords or confidential credentials."
        )
        privacy.setWordWrap(True)
        privacy.setStyleSheet(
            "padding: 9px; background: #59451d; color: white; border-radius: 5px;"
        )
        layout.addWidget(privacy)

        settings_box = QGroupBox(
            "KI-Anbieter und API" if self.is_de else "AI provider and API"
        )
        settings_layout = QVBoxLayout(settings_box)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("Provider:"))
        self.provider = QComboBox()
        self.provider.addItems(list(PROVIDERS.keys()))
        saved_provider = self.settings.value("ai/provider", "OpenRouter (Free)")
        index = self.provider.findText(saved_provider)
        self.provider.setCurrentIndex(max(0, index))
        provider_row.addWidget(self.provider, 2)

        provider_row.addWidget(QLabel("Model:"))
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
        key_row.addWidget(QLabel("API Key:"))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText(
            "API-Key für den ausgewählten Anbieter"
        )
        self.api_key.setText(
            _load_saved_api_key(self.provider.currentText())
        )
        self.api_key.editingFinished.connect(
            lambda: _save_api_key(
                self.api_key.text(), self.provider.currentText()
            )
        )
        key_row.addWidget(self.api_key, 1)
        settings_layout.addLayout(key_row)

        layout.addWidget(settings_box)

        self.provider.currentTextChanged.connect(self._provider_changed)
        self._provider_changed(self.provider.currentText(), initial=True)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Dein KI-Chat erscheint hier ..." if self.is_de
            else "Your AI conversation appears here ..."
        )
        layout.addWidget(self.output, 1)

        self.prompt = QTextEdit()
        self.prompt.setMaximumHeight(100)
        self.prompt.setPlaceholderText(
            "Frage zur Patch-Analyse oder Fehlersuche ..."
            if self.is_de else
            "Ask about patch analysis or troubleshooting ..."
        )
        layout.addWidget(self.prompt)

        buttons = QHBoxLayout()
        self.send_button = QPushButton(
            "➤ Senden" if self.is_de else "➤ Send"
        )
        self.test_api_button = QPushButton(
            "🔑 API testen" if self.is_de else "🔑 Test API"
        )
        self.clear_button = QPushButton(
            "Chat leeren" if self.is_de else "Clear chat"
        )
        close_button = QPushButton(
            "Schließen" if self.is_de else "Close"
        )
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
                _save_api_key(self.api_key.text(), previous)
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "Config", str(exc))

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
                "Bitte API-Key und Modell eingeben."
                if self.is_de else
                "Please enter an API key and model."
            )
            return

        try:
            _save_api_key(key, provider)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Config", str(exc))
            return

        self.test_api_button.setEnabled(False)
        self.test_api_button.setText(
            "Teste ..." if self.is_de else "Testing ..."
        )
        self.output.append(
            f"<b>API-Test: {provider} – {model}</b><br>Verbindung wird geprüft ..."
        )

        self.test_worker = APITestWorker(provider, model, key)
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
            "🔑 API testen" if self.is_de else "🔑 Test API"
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
                "Bitte API-Key und Modell eingeben."
                if self.is_de else
                "Please enter an API key and model."
            )
            return
        if provider not in PROVIDERS:
            return

        self.settings.setValue("ai/provider", provider)
        self.settings.setValue("ai/model", model)
        try:
            _save_api_key(key, provider)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Config", str(exc))
            return

        self.messages.append({"role": "user", "content": prompt})
        self.output.append(f"<b>You:</b> {prompt}")
        self.prompt.clear()
        self.send_button.setEnabled(False)
        self.send_button.setText(
            "KI antwortet ..." if self.is_de else "AI is responding ..."
        )

        self.worker = AIWorker(provider, model, key, list(self.messages))
        self.worker.result_ready.connect(self._on_result)
        self.worker.failed.connect(self._on_error)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_result(self, answer):
        self.messages.append({"role": "assistant", "content": answer})
        self.output.append(f"<b>🤖 AI:</b><br>{answer}")
        self.output.append("")

    def _on_error(self, error):
        self.output.append(f"<b>API error:</b><br>{error}")
        self.output.append("")

    def _on_finished(self):
        self.send_button.setEnabled(True)
        self.send_button.setText(
            "➤ Senden" if self.is_de else "➤ Send"
        )
        self.worker = None

    def clear_chat(self):
        self.messages.clear()
        self.output.clear()

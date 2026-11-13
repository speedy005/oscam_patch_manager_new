from PyQt6.QtWidgets import QApplication, QSizePolicy, QAbstractButton
from PyQt6.QtGui import QFont


def configure_window_layout(window, info_text, toolbar_buttons):
    """Bildschirmabhängige Fenster- und Konsoleneinstellungen."""

    screen = window.screen() or QApplication.primaryScreen()
    if screen is None:
        return

    available = screen.availableGeometry()
    sw = available.width()
    sh = available.height()

    if sw < 1 or sh < 1:
        return

    # Alle Buttons im Hauptfenster auf maximal 45 px begrenzen.
    for button in window.findChildren(QAbstractButton):
        button.setMinimumHeight(min(button.minimumHeight(), 45))
        button.setMaximumHeight(45)

    # Benötigte Breite der ersten Toolbar-Reihe.
    widths = [
        max(button.minimumWidth(), button.sizeHint().width())
        for button in toolbar_buttons[:8]
    ]
    toolbar_width = sum(widths) + max(0, len(widths) - 1) * 8 + 50

    min_width = min(sw, max(1000, min(toolbar_width, int(sw * 0.94))))
    min_height = min(sh, max(560, int(sh * 0.68)))

    window.setMinimumSize(min_width, min_height)

    # Logbereich flexibel und ausreichend hoch halten.
    info_text.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Expanding
    )
    info_text.setMinimumHeight(0)
    console_panel = getattr(window, 'console_panel', None)
    if console_panel is not None:
        console_panel.setMinimumHeight(0)

    # DPI-abhängige Grundschrift.
    dpi = screen.logicalDotsPerInchY()
    scale = dpi / 96.0 if dpi > 0 else 1.0

    font = QFont("Courier")
    font.setPointSize(max(10, min(14, round(10.5 * scale))))
    info_text.setFont(font)

    # Fenster passend zur verfügbaren Bildschirmfläche.
    width = min(sw, max(min_width, int(sw * 0.92)))
    height = min(sh, max(min_height, int(sh * 0.90)))

    x = available.x() + (sw - width) // 2
    y = available.y() + (sh - height) // 2

    window.setGeometry(x, y, width, height)

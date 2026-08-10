"""Sistema de temas de la interfaz.

El cambio de tema solo afecta a los colores. Un tema se define por un
modo (claro u oscuro) y dos colores de acento (primary y secondary).
El resto de la paleta (fondos, paneles, textos, bordes, barra de título,
rejilla del calendario...) se deriva automáticamente de esos valores.

El contraste del texto siempre es automático: sobre un fondo oscuro el
texto se aclara y sobre un fondo claro se oscurece, de modo que cualquier
combinación de colores elegida mantiene la legibilidad.

El QSS evita a propósito el selector global ``QWidget { background-color:
transparent }``: ese fondo transparente en todos los widgets es lo que
causaba que las ventanas parecieran translúcidas y parpadearan al repintar.
Los fondos se asignan de forma explícita a cada tipo de contenedor.
"""

from PySide6.QtGui import QColor

# Claves de los modos de tema.
THEME_MODE_LIGHT = "light"
THEME_MODE_DARK = "dark"

# Colores por defecto si la configuración no tiene ninguno.
DEFAULT_PRIMARY = "#4A90D9"
DEFAULT_SECONDARY = "#7A8694"


def _hex(color: QColor) -> str:
    return color.name()


def _darken(color: QColor, by: int) -> QColor:
    """Oscurece un color hacia el negro.

    "by" se interpreta como un porcentaje (100 no cambia nada; 110 lo
    oscurece un 10% de la distancia al negro). Esto da un oscurecido
    sutil sin perder el matiz.
    """
    factor = by / 100.0

    return QColor(
        min(255, round(color.red() * factor)),
        min(255, round(color.green() * factor)),
        min(255, round(color.blue() * factor)),
        color.alpha(),
    )


def _lighten(color: QColor, by: int) -> QColor:
    """Aclara un color hacia el blanco (porcentaje de distancia)."""
    factor = by / 100.0

    return QColor(
        round(color.red() + (255 - color.red()) * factor),
        round(color.green() + (255 - color.green()) * factor),
        round(color.blue() + (255 - color.blue()) * factor),
        color.alpha(),
    )


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    """Mezcla dos colores: t=0 devuelve a, t=1 devuelve b."""
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _luminance(color: QColor) -> float:
    """Luminancia relativa aproximada (0=negro, 1=blanco).

    Se usa para decidir el color de texto legible sobre un fondo: a
    partir de 0.5 el fondo se considera claro y el texto debe ser
    oscuro; por debajo se considera oscuro y el texto debe ser claro.
    """
    def channel(value: int) -> float:
        normalized = value / 255.0

        if normalized <= 0.03928:
            return normalized / 12.92

        return ((normalized + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * channel(color.red())
        + 0.7152 * channel(color.green())
        + 0.0722 * channel(color.blue())
    )


def _on_background(background: QColor) -> QColor:
    """Devuelve el color de texto legible sobre el fondo dado.

    Fondo claro -> texto oscuro; fondo oscuro -> texto claro.
    """
    light = QColor("#F9FAFB")
    dark = QColor("#111827")

    return dark if _luminance(background) >= 0.5 else light


def _active_theme() -> dict[str, str]:
    """Devuelve {mode, primary, secondary} del tema activo."""
    from tutor_heaven.data.settings_storage import get_settings

    settings = get_settings()

    return {
        "mode": settings.theme_mode,
        "primary": settings.theme_primary,
        "secondary": settings.theme_secondary,
    }


def _derive_palette(theme: dict[str, str]) -> dict[str, str]:
    """Construye la paleta completa a partir del tema activo.

    A partir del modo (claro/oscuro) y de los dos colores de acento se
    derivan las superficies, el texto (con contraste automático) y los
    contenedores teñidos con el acento, estilo Material You.
    """
    mode = theme.get("mode", THEME_MODE_LIGHT)
    primary = QColor(theme.get("primary", DEFAULT_PRIMARY))
    secondary = QColor(theme.get("secondary", DEFAULT_SECONDARY))

    dark = mode == THEME_MODE_DARK

    # Superficies base según el modo. En ambos modos las superficies se
    # tiñen con el color primario (mezcla hacia el blanco en claro y hacia
    # el negro en oscuro), de modo que el fondo "es del color del tema".
    window_bg = (
        _mix(primary, QColor("#0B0E11"), 0.86)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.93)
    )
    panel_bg = (
        _mix(primary, QColor("#14181D"), 0.80)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.97)
    )
    panel_alt = (
        _mix(primary, QColor("#1E242B"), 0.72)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.89)
    )
    border = (
        _mix(primary, QColor("#2A3138"), 0.60)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.82)
    )
    text = (
        QColor("#F3F4F6")
        if dark
        else QColor("#1A2230")
    )
    muted_text = (
        QColor("#A9B4C0")
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.55)
    )

    # Texto sobre los acentos: siempre con contraste automático.
    accent_text = _on_background(primary)
    on_secondary = _on_background(secondary)

    # Contenedores teñidos: sobre fondo claro se tiñe hacia el blanco;
    # sobre fondo oscuro se tiñe hacia el negro/acento.
    container = (
        _mix(primary, window_bg, 0.72)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.88)
    )
    hover_bg = (
        _lighten(window_bg, 8)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.93)
    )
    focus_bg = (
        _lighten(window_bg, 12)
        if dark
        else _mix(primary, QColor("#FFFFFF"), 0.95)
    )

    # El texto "sobre contenedor" debe leerse sobre container.
    on_container = _on_background(container)

    return {
        # Superficies.
        "window_bg": _hex(window_bg),
        "panel_bg": _hex(panel_bg),
        "panel_alt": _hex(panel_alt),
        # Texto.
        "text": _hex(text),
        "muted_text": _hex(muted_text),
        "border": _hex(border),
        # Acentos (lo que usa el código como theme_color).
        "accent": _hex(primary),
        "accent_2": _hex(secondary),
        "accent_text": _hex(accent_text),
        "on_secondary": _hex(on_secondary),
        # Contenedores teñidos: selección, chips, hover, focus.
        "container": _hex(container),
        "on_container": _hex(on_container),
        "hover_bg": _hex(hover_bg),
        "focus_bg": _hex(focus_bg),
        # Barra de título.
        "title_bg": _hex(primary),
        "title_fg": _hex(accent_text),
        # Rejilla del calendario.
        "canvas_bg": _hex(panel_bg),
        "grid_line": _hex(border),
        "grid_text": _hex(muted_text),
        # Semánticos (con contraste sobre sus propios fondos claros).
        "danger": "#B91C1C" if not dark else "#F87171",
        "success": "#15803D" if not dark else "#4ADE80",
        "warning": "#B45309" if not dark else "#FBBF24",
    }


def theme_color(key: str, fallback: str = "") -> str:
    """Devuelve el color de la paleta del tema activo."""
    palette = _derive_palette(_active_theme())

    if key in palette:
        return palette[key]

    return fallback or palette["text"]


def theme_palette() -> dict[str, str]:
    """Devuelve la paleta completa del tema activo (para los widgets que
    necesiten más de un color)."""
    return _derive_palette(_active_theme())


def _build_qss(palette: dict[str, str]) -> str:
    """Construye el QSS global a partir de la paleta del tema."""
    return f"""
    /* ---------- Fondos base ---------- */
    QMainWindow, QDialog, QMessageBox {{
        background-color: {palette["window_bg"]};
    }}
    QWidget {{
        color: {palette["text"]};
        font-size: 13px;
    }}
    QLabel {{
        background: transparent;
        color: {palette["text"]};
    }}

    /* ---------- Tarjetas (GroupBox) ---------- */
    QGroupBox {{
        background-color: {palette["panel_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 16px;
        margin-top: 14px;
        padding-top: 10px;
        padding-bottom: 6px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 16px;
        padding: 0 8px;
        color: {palette["muted_text"]};
        font-weight: 600;
        font-size: 11px;
    }}

    /* ---------- Botones (tipo pill) ---------- */
    QPushButton {{
        background-color: {palette["panel_bg"]};
        color: {palette["text"]};
        border: 1px solid {palette["border"]};
        border-radius: 999px;
        padding: 7px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        background-color: {palette["hover_bg"]};
        border-color: {palette["accent_2"]};
    }}
    QPushButton:pressed {{
        background-color: {palette["container"]};
        border-color: {palette["accent"]};
    }}
    QPushButton:disabled {{
        background-color: {palette["panel_alt"]};
        color: {palette["muted_text"]};
        border-color: {palette["border"]};
    }}
    QPushButton#primary {{
        background-color: {palette["accent"]};
        border-color: {palette["accent"]};
        color: {palette["accent_text"]};
    }}
    QPushButton#primary:hover {{
        background-color: {palette["accent_2"]};
        border-color: {palette["accent_2"]};
        color: {palette["on_secondary"]};
    }}
    QPushButton#primary:pressed {{
        background-color: {palette["container"]};
        border-color: {palette["container"]};
        color: {palette["on_container"]};
    }}
    QPushButton#danger {{
        color: {palette["danger"]};
        border-color: {_hex(_mix(QColor(palette["danger"]), QColor(palette["panel_bg"]), 0.7))};
    }}
    QPushButton#danger:hover {{
        background-color: {_hex(_mix(QColor(palette["danger"]), QColor(palette["panel_bg"]), 0.92))};
        border-color: {palette["danger"]};
    }}
    QDialogButtonBox QPushButton:default {{
        background-color: {palette["accent"]};
        border-color: {palette["accent"]};
        color: {palette["accent_text"]};
    }}
    QDialogButtonBox QPushButton:default:hover {{
        background-color: {palette["accent_2"]};
        border-color: {palette["accent_2"]};
        color: {palette["on_secondary"]};
    }}

    /* ---------- Campos de entrada ---------- */
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit,
    QComboBox, QPlainTextEdit, QTextEdit {{
        background-color: {palette["panel_bg"]};
        color: {palette["text"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 7px 11px;
        selection-background-color: {palette["accent"]};
        selection-color: {palette["accent_text"]};
    }}
    QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover,
    QTimeEdit:hover, QComboBox:hover, QPlainTextEdit:hover, QTextEdit:hover {{
        border-color: {palette["accent_2"]};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus,
    QTimeEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
        border: 2px solid {palette["accent"]};
        background-color: {palette["focus_bg"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {palette["panel_bg"]};
        color: {palette["text"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 4px;
        selection-background-color: {palette["container"]};
        selection-color: {palette["on_container"]};
    }}
    QAbstractItemView QScrollBar::handle:vertical {{
        background: {palette["border"]};
        min-height: 28px;
        border-radius: 5px;
    }}

    /* Flechas de los campos numéricos y de fecha redondeadas. */
    QSpinBox::up-button, QDoubleSpinBox::up-button,
    QDateEdit::up-button, QTimeEdit::up-button {{
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 16px;
        height: 50%;
        border: none;
        border-top-right-radius: 8px;
        background: transparent;
    }}
    QSpinBox::down-button, QDoubleSpinBox::down-button,
    QDateEdit::down-button, QTimeEdit::down-button {{
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 16px;
        height: 50%;
        border: none;
        border-bottom-right-radius: 8px;
        background: transparent;
    }}
    QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
    QDateEdit::up-button:hover, QTimeEdit::up-button:hover,
    QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover,
    QDateEdit::down-button:hover, QTimeEdit::down-button:hover {{
        background-color: {palette["panel_alt"]};
    }}
    QSpinBox::up-arrow, QDoubleSpinBox::up-arrow,
    QDateEdit::up-arrow, QTimeEdit::up-arrow,
    QSpinBox::down-arrow, QDoubleSpinBox::down-arrow,
    QDateEdit::down-arrow, QTimeEdit::down-arrow {{
        border: none;
        width: 8px;
        height: 8px;
    }}

    /* ---------- Listas y tablas ---------- */
    QListWidget, QTableWidget, QTableView {{
        background-color: {palette["panel_bg"]};
        color: {palette["text"]};
        border: 1px solid {palette["border"]};
        border-radius: 12px;
        gridline-color: {palette["border"]};
        alternate-background-color: {palette["panel_alt"]};
    }}
    QListWidget::item {{
        padding: 8px 12px;
        border-radius: 8px;
        margin: 2px 3px;
    }}
    QListWidget::item:hover {{
        background-color: {palette["hover_bg"]};
    }}
    QListWidget::item:selected {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
        border-radius: 8px;
    }}
    QHeaderView::section {{
        background-color: {palette["panel_alt"]};
        color: {palette["muted_text"]};
        border: none;
        border-bottom: 1px solid {palette["border"]};
        padding: 8px;
        font-weight: 600;
    }}
    QHeaderView::section:first {{
        border-top-left-radius: 10px;
        border-bottom-left-radius: 10px;
    }}
    QHeaderView::section:last {{
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }}
    QTableWidget::item:selected, QTableView::item:selected {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
    }}
    QTableWidget::item {{
        padding: 4px 8px;
    }}

    /* ---------- Pestañas (tipo chips) ---------- */
    QTabWidget::pane {{
        border: none;
        background: transparent;
    }}
    QTabBar {{
        background: transparent;
    }}
    QTabBar::tab {{
        background: transparent;
        color: {palette["muted_text"]};
        padding: 7px 16px;
        margin-right: 6px;
        border: none;
        border-radius: 999px;
        font-weight: 600;
    }}
    QTabBar::tab:hover {{
        background-color: {palette["hover_bg"]};
        color: {palette["text"]};
    }}
    QTabBar::tab:selected {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
    }}
    QTabBar::tab:selected:focus {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
    }}

    /* ---------- Barra de herramientas ---------- */
    QToolBar {{
        background-color: {palette["panel_bg"]};
        border: none;
        border-bottom: 1px solid {palette["border"]};
        spacing: 8px;
        padding: 4px 10px;
    }}
    QToolButton {{
        color: {palette["text"]};
        padding: 6px 14px;
        border-radius: 999px;
        font-weight: 600;
    }}
    QToolButton:hover {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
    }}

    /* ---------- Divisor ---------- */
    QSplitter::handle {{
        background-color: transparent;
        width: 6px;
    }}
    QSplitter::handle:hover {{
        background-color: {palette["border"]};
    }}

    /* ---------- Barras de desplazamiento ---------- */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea > QWidget {{
        background-color: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {palette["border"]};
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {palette["muted_text"]};
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: {palette["border"]};
        min-width: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {palette["muted_text"]};
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{
        height: 0;
        width: 0;
    }}
    QScrollBar::add-page, QScrollBar::sub-page {{
        background: none;
    }}

    /* ---------- Menús y tooltips ---------- */
    QToolTip {{
        background-color: {palette["title_bg"]};
        color: {palette["title_fg"]};
        border: none;
        padding: 6px 10px;
        border-radius: 8px;
    }}
    QMenu {{
        background-color: {palette["panel_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 10px;
        padding: 5px;
    }}
    QMenu::item {{
        padding: 6px 22px;
        border-radius: 6px;
    }}
    QMenu::item:selected {{
        background-color: {palette["container"]};
        color: {palette["on_container"]};
    }}
    QMenu::separator {{
        height: 1px;
        background: {palette["border"]};
        margin: 4px 10px;
    }}

    QMessageBox {{
        background-color: {palette["panel_bg"]};
        border: 1px solid {palette["border"]};
        border-radius: 16px;
    }}

    QMessageBox QLabel {{
        background: transparent;
    }}
    QMessageBox QPushButton {{
        min-width: 80px;
    }}

    /* ---------- Casillas ---------- */
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {palette["accent"]};
        border-radius: 5px;
        background: transparent;
    }}
    QCheckBox::indicator:hover {{
        border-color: {palette["accent_2"]};
    }}
    QCheckBox::indicator:checked {{
        background-color: {palette["accent"]};
        border-color: {palette["accent"]};
    }}
    """


def theme_qss() -> str:
    """Devuelve el QSS del tema activo."""
    return _build_qss(_derive_palette(_active_theme()))


def apply_theme(app) -> None:
    """Aplica el QSS del tema activo a toda la aplicación."""
    app.setStyleSheet(theme_qss())

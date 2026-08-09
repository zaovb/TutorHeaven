"""Sistema de temas de la interfaz.

Cada tema se define por dos colores principales (primary y secondary).
El resto de la paleta (fondos, paneles, textos, bordes, barra de título,
rejilla del calendario...) se deriva automáticamente de esos dos colores,
de modo que crear un tema nuevo es tan fácil como añadir una entrada
con sus dos colores a _THEMES.

Por ahora todos los temas se resuelven en una paleta en escala de grises
(estética Material You: superficies neutras, contenedores teñidos, esquinas
muy redondeadas, botones tipo "pill" y pestañas como chips). Los colores
de acento por tema se irán añadiendo más adelante.

El QSS evita a propósito el selector global ``QWidget { background-color:
transparent }``: ese fondo transparente en todos los widgets es lo que
causaba que las ventanas parecieran translúcidas y parpadearan al repintar.
Los fondos se asignan de forma explícita a cada tipo de contenedor.
"""

from PySide6.QtGui import QColor

# Claves de los temas disponibles.
THEME_CLASSIC = "classic"
THEME_BLACK_WHITE = "black_white"
THEME_COFFEE = "coffee_royal"
THEME_FOREST = "forest"

# Orden de aparición en el selector de Configuración.
THEME_KEYS = [
    THEME_CLASSIC,
    THEME_BLACK_WHITE,
    THEME_COFFEE,
    THEME_FOREST,
]

# Nombres visibles (se traducen con tr()).
THEME_NAMES = {
    THEME_CLASSIC: "Ocean",
    THEME_BLACK_WHITE: "Black & White",
    THEME_COFFEE: "Coffee & Royal",
    THEME_FOREST: "Forest",
}

THEME_NAMES_ES = {
    THEME_CLASSIC: "Océano",
    THEME_BLACK_WHITE: "Blanco y negro",
    THEME_COFFEE: "Café y azul rey",
    THEME_FOREST: "Bosque",
}

# Cada tema define sus dos colores principales: primary (acento, acciones
# principales) y secondary (segundo acento, detalles y resaltados).
# Actualmente se usan tonos neutros/grises; los colores de marca de cada
# tema se añadirán en una iteración posterior.
_THEMES: dict[str, dict[str, str]] = {
    THEME_CLASSIC: {
        "primary": "#374151",
        "secondary": "#9CA3AF",
    },
    THEME_BLACK_WHITE: {
        "primary": "#111827",
        "secondary": "#6B7280",
    },
    THEME_COFFEE: {
        "primary": "#1F2937",
        "secondary": "#8B8B8B",
    },
    THEME_FOREST: {
        "primary": "#2B3440",
        "secondary": "#7A8694",
    },
}

# Paleta derivada: claves usadas por los widgets (week_grid, title_bar...).
# "accent" es el color primario del tema y "accent_2" el secundario.
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


def _mix(a: QColor, b: QColor, t: float) -> QColor:
    """Mezcla dos colores: t=0 devuelve a, t=1 devuelve b."""
    return QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


def _derive_palette(theme: dict[str, str]) -> dict[str, str]:
    """Construye la paleta completa a partir de los dos colores del tema.

    Sigue el esquema de color de Material You en modo claro: un fondo
    neutro muy claro, superficies blancas y contenedores teñidos del
    acento (container / on_container) que dan el toque "dinámico".
    """
    primary = QColor(theme["primary"])
    secondary = QColor(theme["secondary"])

    white = QColor("#FFFFFF")
    black = QColor("#111827")

    return {
        # Superficies.
        "window_bg": "#F3F4F6",
        "panel_bg": "#FFFFFF",
        "panel_alt": "#E9EBEF",
        # Texto.
        "text": _hex(black),
        "muted_text": "#6B7280",
        "border": "#D8DCE3",
        # Acentos (lo que usa el código como theme_color).
        "accent": _hex(primary),
        "accent_2": _hex(secondary),
        "accent_text": "#FFFFFF",
        # Contenedores teñidos: selección, chips, hover, focus.
        "container": _hex(_mix(primary, white, 0.90)),
        "on_container": _hex(_mix(primary, white, 0.22)),
        "hover_bg": _hex(_mix(primary, white, 0.93)),
        "focus_bg": _hex(_mix(primary, white, 0.95)),
        # Barra de título.
        "title_bg": _hex(_darken(primary, 100)),
        "title_fg": "#FFFFFF",
        # Rejilla del calendario.
        "canvas_bg": "#FFFFFF",
        "grid_line": "#E5E7EB",
        "grid_text": "#9CA3AF",
        # Semánticos.
        "danger": "#B91C1C",
        "success": "#15803D",
        "warning": "#B45309",
    }


def current_theme_key() -> str:
    """Devuelve la clave del tema activo desde la configuración."""
    from tutor_heaven.data.settings_storage import get_settings

    theme = get_settings().theme

    if theme in _THEMES:
        return theme

    return THEME_CLASSIC


def theme_color(key: str, fallback: str = "") -> str:
    """Devuelve el color de la paleta del tema activo."""
    palette = _derive_palette(_THEMES[current_theme_key()])

    if key in palette:
        return palette[key]

    return fallback or palette["text"]


def theme_palette() -> dict[str, str]:
    """Devuelve la paleta completa del tema activo (para los widgets que
    necesiten más de un color)."""
    return _derive_palette(_THEMES[current_theme_key()])


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
    }}
    QPushButton#primary:pressed {{
        background-color: {palette["text"]};
        border-color: {palette["text"]};
    }}
    QPushButton#danger {{
        color: {palette["danger"]};
        border-color: {_hex(_mix(QColor(palette["danger"]), QColor("#FFFFFF"), 0.7))};
    }}
    QPushButton#danger:hover {{
        background-color: {_hex(_mix(QColor(palette["danger"]), QColor("#FFFFFF"), 0.92))};
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
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #B9C0CA;
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: #A3ABB7;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal {{
        background: #B9C0CA;
        min-width: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: #A3ABB7;
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
        background-color: #111827;
        color: #FFFFFF;
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

    QMessageBox QLabel {{
        background: transparent;
    }}
    """


def theme_qss() -> str:
    """Devuelve el QSS del tema activo."""
    return _build_qss(_derive_palette(_THEMES[current_theme_key()]))


def apply_theme(app) -> None:
    """Aplica el QSS del tema activo a toda la aplicación."""
    app.setStyleSheet(theme_qss())

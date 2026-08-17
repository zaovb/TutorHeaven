import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.i18n import LANGUAGE_SPANISH, set_language
from tutor_heaven.ui.main_window import MainWindow
from tutor_heaven.ui.themes import apply_theme


def _install_qt_translations(app: QApplication) -> None:
    """Traduce los textos estándar de Qt (OK, Cancelar, Sí, No...).

    Solo aplica cuando el idioma activo es español. Carga el catálogo
    ``qtbase_es`` de las traducciones de Qt; si no está disponible en
    el sistema, los botones estándar se mantienen en inglés (sin
    errores).
    """
    if get_settings().language != LANGUAGE_SPANISH:
        return

    candidates = [
        Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
        / "qtbase_es.qm",
        Path("/usr/share/qt5/translations") / "qtbase_es.qm",
        Path("/usr/share/qt6/translations") / "qtbase_es.qm",
    ]

    translator = QTranslator()

    for candidate in candidates:
        if candidate.exists() and translator.load(
            QLocale(QLocale.Language.Spanish, QLocale.Country.Spain),
            str(candidate.stem),
            "_",
            str(candidate.parent),
        ):
            app.installTranslator(translator)
            return


def main() -> None:
    # Crea la aplicación Qt, construye la ventana principal
    # y entra en el bucle de eventos (app.exec()).
    # El programa termina cuando se cierra la ventana.
    app = QApplication(sys.argv)

    # Aplica el idioma guardado antes de crear cualquier ventana.
    set_language(get_settings().language)

    _install_qt_translations(app)

    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
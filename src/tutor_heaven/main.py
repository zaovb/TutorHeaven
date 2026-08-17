import sys
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from tutor_heaven.data.settings_storage import (
    SETTINGS_FILE,
    get_settings,
    reload_settings,
    save_settings,
)
from tutor_heaven.i18n import LANGUAGE_SPANISH, set_language, tr
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


def _setup_backup_on_first_run(window: "MainWindow") -> None:
    """Pide elegir dónde guardar la copia de seguridad en el primer inicio.

    Solo se muestra la primera vez que se ejecuta el programa (cuando
    todavía no existe data/settings.json). La carpeta debe quedar FUERA
    de la carpeta del programa para que la copia sobreviva a una
    desinstalación.
    """
    if SETTINGS_FILE.exists():
        return

    from PySide6.QtWidgets import (
        QFileDialog,
        QMessageBox,
    )

    from tutor_heaven.data.backup import (
        is_path_inside_program,
        update_backup,
    )

    ask = QMessageBox.question(
        window,
        tr("Welcome to Tutor Heaven"),
        tr(
            "Do you want to enable automatic backups?\n\n"
            "You will choose a folder OUTSIDE the app so your data "
            "survives an uninstall."
        ),
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )

    if ask != QMessageBox.StandardButton.Yes:
        return

    folder = QFileDialog.getExistingDirectory(
        window,
        tr("Choose Backup Folder"),
        str(Path.home()),
    )

    if not folder:
        return

    if is_path_inside_program(folder):
        QMessageBox.warning(
            window,
            tr("Backup"),
            tr(
                "The backup folder cannot be inside the app folder.\n\n"
                "Choose an external location (for example Documents) "
                "so the backup survives an uninstall."
            ),
        )

        return

    settings = get_settings()

    settings.backup_enabled = True
    settings.backup_path = str(
        Path(folder) / "tutor_heaven_backup.zip"
    )

    save_settings(settings)
    reload_settings()

    update_backup()


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

    # En el primer arranque, si el usuario quiere backup, debe elegir
    # dónde guardarlo (fuera del programa).
    _setup_backup_on_first_run(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
import sys

from PySide6.QtWidgets import QApplication

from tutor_heaven.ui.main_window import MainWindow
from tutor_heaven.ui.themes import apply_theme


def main() -> None:
    # Crea la aplicación Qt, construye la ventana principal
    # y entra en el bucle de eventos (app.exec()).
    # El programa termina cuando se cierra la ventana.
    app = QApplication(sys.argv)

    apply_theme(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
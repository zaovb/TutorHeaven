from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from tutor_heaven.ui.themes import theme_color


class Placeholder(QWidget):
    """Temporary page while the module is under development.

    Widget simple que muestra un texto centrado, usado como marcador
    de posición mientras un módulo no está implementado. En este
    proyecto se usa en el panel de perfil antes de seleccionar a un
    estudiante.
    """

    def __init__(self, title: str) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        label = QLabel(title)

        font = QFont()
        font.setPointSize(20)
        font.setBold(True)

        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"color: {theme_color('muted_text')}; background: transparent;"
        )

        # "Stretches" verticales para centrar la etiqueta.
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        self.setLayout(layout)
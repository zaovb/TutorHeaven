"""Diálogo 'Acerca de' con información de la aplicación."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

from tutor_heaven.app_info import APP_AUTHOR, APP_NAME, APP_VERSION
from tutor_heaven.i18n import tr
from tutor_heaven.ui.dialog_utils import FitDialog


class AboutDialog(FitDialog):
    """Muestra información sobre Tutor Heaven."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(tr("About"))
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Nombre y versión.
        title = QLabel(f"<b>{APP_NAME}</b>  v{APP_VERSION}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Descripción.
        desc = QLabel(tr("Private tutor management application"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(12)

        # Autor.
        author = QLabel(tr("Developer: {0}").format(APP_AUTHOR))
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author)

        # Hecha con OpenCode.
        made = QLabel(tr("Built with: OpenCode"))
        made.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(made)

        layout.addSpacing(12)

        # Licencia.
        license_label = QLabel(tr("License: GPL-3.0"))
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)

        # URL del repositorio.
        url = QLabel(
            '<a href="https://github.com/zaovb/TutorHeaven">'
            "github.com/zaovb/TutorHeaven</a>"
        )
        url.setAlignment(Qt.AlignmentFlag.AlignCenter)
        url.setOpenExternalLinks(True)
        layout.addWidget(url)

        layout.addStretch()

        # Botón OK.
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
        )
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

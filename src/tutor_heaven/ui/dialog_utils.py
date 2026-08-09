"""Utilidades para los diálogos de la aplicación.

Los diálogos heredan de ``FitDialog`` (un QDialog que se limita al área
disponible de la pantalla y se centra al mostrarse). Esto evita que una
ventana de diálogo sobrepase las dimensiones del monitor y que aparezca
fuera de la vista en pantallas pequeñas.
"""

from PySide6.QtWidgets import QApplication, QDialog


class FitDialog(QDialog):
    """QDialog que siempre cabe en el área de la pantalla.

    Al mostrarse (showEvent) limita el tamaño máximo al área disponible
    del monitor donde está la ventana y la centra en ese monitor. Si el
    contenido pidiese más espacio del que cabe, aparecen scrollbars
    (los layouts de los diálogos ya usan QScrollArea donde es necesario).
    """

    def showEvent(self, event) -> None:
        super().showEvent(event)

        # Usa el monitor donde está la ventana (o el primario si aún no
        # tiene uno asignado) para que el diálogo quepa en cualquier
        # pantalla, no solo en la principal.
        screen = self.screen() or QApplication.primaryScreen()

        if screen is None:
            return

        available = screen.availableGeometry()

        # Margen respecto al borde de la pantalla.
        margin = 24
        max_width = max(320, available.width() - margin * 2)
        max_height = max(320, available.height() - margin * 2)

        self.setMaximumWidth(max_width)
        self.setMaximumHeight(max_height)

        # Tamaño natural del diálogo (sin superar el máximo).
        hint = self.sizeHint()
        width = min(hint.width(), max_width)
        height = min(hint.height(), max_height)

        self.resize(width, height)

        # Centra el diálogo en la pantalla disponible.
        x = available.x() + (available.width() - self.width()) // 2
        y = available.y() + (available.height() - self.height()) // 2

        self.move(x, y)

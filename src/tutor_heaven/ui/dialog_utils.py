"""Utilidades para los diálogos de la aplicación.

Los diálogos heredan de ``FitDialog`` (un QDialog que se limita al área
de la ventana principal y se centra sobre ella al mostrarse). Esto evita
que una ventana de diálogo sobrepase las dimensiones del monitor y que
aparezca fuera de la vista en pantallas pequeñas. El diálogo nunca es
más grande que la ventana principal y nunca toca los bordes de la
pantalla.
"""

from PySide6.QtWidgets import QApplication, QDialog


class FitDialog(QDialog):
    """QDialog que siempre cabe dentro de la ventana principal.

    Al mostrarse (showEvent) limita el tamaño máximo al área de la
    ventana principal (o de la pantalla si no hay una) y lo centra
    sobre ella, manteniendo un margen para que nunca toque ni el borde
    superior ni el inferior de la pantalla. Si el contenido pidiese más
    espacio del que cabe, aparecen scrollbars (los layouts de los
    diálogos ya usan QScrollArea donde es necesario).
    """

    # Margen que separa el diálogo de los bordes de la pantalla.
    _MARGIN = 24

    def _reference_window(self) -> object:
        """Devuelve la ventana principal visible que sirve de referencia.

        Se elige la ventana de nivel superior visible más grande (en
        área) distinta del propio diálogo; típicamente es la ventana
        principal de la aplicación. Si no hay ninguna, devuelve None y
        se usa la pantalla como referencia.
        """
        active = QApplication.activeWindow()

        candidates = []

        if (
            active is not None
            and active is not self
            and active.isWindow()
            and active.isVisible()
        ):
            candidates.append(active)

        for window in QApplication.topLevelWidgets():
            if (
                window is self
                or not window.isWindow()
                or not window.isVisible()
            ):
                continue

            candidates.append(window)

        if not candidates:
            return None

        return max(
            candidates,
            key=lambda window: window.width() * window.height(),
        )

    def showEvent(self, event) -> None:
        super().showEvent(event)

        # Usa el monitor donde está la ventana (o el primario si aún no
        # tiene uno asignado) para que el diálogo quepa en cualquier
        # pantalla, no solo en la principal.
        screen = self.screen() or QApplication.primaryScreen()

        if screen is None:
            return

        available = screen.availableGeometry()

        reference = self._reference_window()

        if reference is not None:
            # El diálogo nunca es más grande que la ventana principal:
            # se limita a su geometría, sin superar el área disponible
            # de la pantalla.
            ref = reference.geometry()

            max_width = min(
                available.width(),
                ref.width(),
            ) - self._MARGIN * 2
            max_height = min(
                available.height(),
                ref.height(),
            ) - self._MARGIN * 2

            center_geometry = ref
        else:
            max_width = available.width() - self._MARGIN * 2
            max_height = available.height() - self._MARGIN * 2

            center_geometry = available

        max_width = max(320, max_width)
        max_height = max(320, max_height)

        self.setMaximumWidth(max_width)
        self.setMaximumHeight(max_height)

        # Tamaño natural del diálogo (sin superar el máximo).
        hint = self.sizeHint()
        width = min(hint.width(), max_width)
        height = min(hint.height(), max_height)

        self.resize(width, height)

        # Centra el diálogo sobre la ventana principal, recortando al
        # área disponible para que nunca toque los bordes de la pantalla.
        x = center_geometry.x() + (center_geometry.width() - self.width()) // 2
        y = center_geometry.y() + (center_geometry.height() - self.height()) // 2

        x = max(
            available.x() + self._MARGIN,
            min(
                x,
                available.x() + available.width() - self.width() - self._MARGIN,
            ),
        )
        y = max(
            available.y() + self._MARGIN,
            min(
                y,
                available.y() + available.height() - self.height() - self._MARGIN,
            ),
        )

        self.move(x, y)

"""Indicador de sincronización animado.

Muestra un círculo girando cuando la aplicación está sincronizando
datos con Google Drive.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QLabel


class SyncSpinner(QLabel):
    """Widget que dibuja un arco rotatorio indicando sync activo."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(20, 20)

        self._angle = 0
        self._spinning = False

        self._timer = QTimer()
        self._timer.setInterval(50)  # 20 FPS
        self._timer.timeout.connect(self._rotate)

    def start(self) -> None:
        """Inicia la animación de rotación."""
        if self._spinning:
            return

        self._spinning = True
        self._timer.start()
        self.update()

    def stop(self) -> None:
        """Detiene la animación y oculta el spinner."""
        self._spinning = False
        self._timer.stop()
        self._angle = 0
        self.update()

    def _rotate(self) -> None:
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, event) -> None:
        if not self._spinning:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Centro y radio.
        cx = self.width() / 2
        cy = self.height() / 2
        radius = min(cx, cy) - 2

        # Color accent del tema.
        from tutor_heaven.ui.themes import theme_color

        color = QColor(theme_color("accent"))

        # Dibujar arco de 270 grados.
        pen = QPen(color, 2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        rect = self.rect()
        # Ajustar para que el arco quepa dentro del rectángulo.
        margin = int((self.width() - radius * 2) / 2)
        rect.adjust(margin, margin, -margin, -margin)

        painter.drawArc(
            rect,
            int(self._angle * 16),
            int(270 * 16),
        )

        painter.end()

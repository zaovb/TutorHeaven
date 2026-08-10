from PySide6.QtCore import Qt
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from tutor_heaven.i18n import tr
from tutor_heaven.ui.themes import theme_color


class _WindowButton(QPushButton):
    """Botón de control de la ventana con icono dibujado.

    En lugar de usar caracteres unicode (que dependen de la fuente y
    pueden salir mal con algunos temas), el icono se pinta con QPainter
    usando el color del texto de la barra de título.
    """

    def __init__(
        self,
        kind: str,
        tooltip: str,
    ) -> None:
        super().__init__(tooltip)

        self.kind = kind

        self.setFixedSize(32, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Fondo destacado al pasar el ratón.
        self._hover = False

    def _ink(self) -> QColor:
        return QColor(theme_color("title_fg"))

    def _hover_bg(self) -> QColor:
        # El botón de cerrar se resalta en rojo, como en la mayoría de
        # los controles de ventana de los sistemas operativos.
        if self.kind == "close":
            return QColor("#E81123")

        return QColor(theme_color("title_fg")).darker(140)

    def paintEvent(self, event: QPaintEvent) -> None:
        del event

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if self._hover:
            painter.fillRect(
                self.rect(),
                self._hover_bg(),
            )

        pen = painter.pen()
        pen.setColor(self._ink())
        pen.setWidthF(1.5)

        painter.setPen(pen)
        painter.setBrush(
            Qt.BrushStyle.NoBrush
        )

        x = 8.0
        y = 8.0
        w = 16.0
        h = 10.0

        if self.kind == "minimize":
            painter.drawLine(
                10,
                self.height() / 2,
                self.width() - 10,
                self.height() / 2,
            )
        elif self.kind == "maximize":
            painter.drawRect(x, y, w, h)
        elif self.kind == "restore":
            # Dos rectángulos superpuestos: delante y detrás.
            painter.drawRect(x + 3, y - 3, w - 3, h - 3)
            painter.drawRect(x, y, w - 3, h - 3)
        elif self.kind == "fullscreen":
            painter.drawRect(x + 2, y + 2, w - 4, h - 4)
            painter.drawLine(
                x + 2,
                y + 2,
                x + 2 + 5,
                y + 2 + 5,
            )
            painter.drawLine(
                x + w - 2,
                y + 2,
                x + w - 2 - 5,
                y + 2 + 5,
            )
        elif self.kind == "close":
            painter.drawLine(
                x + 3,
                y + 3,
                x + w - 3,
                y + h - 3,
            )
            painter.drawLine(
                x + 3,
                y + h - 3,
                x + w - 3,
                y + 3,
            )

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()

        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()

        super().leaveEvent(event)


class TitleBar(QWidget):
    """Custom title bar for the frameless window.

    Barra de título personalizada que permite arrastrar la ventana,
    maximizarla con doble clic y ofrece botones de minimizar,
    maximizar/restaurar, pantalla completa y cerrar. Como la ventana
    no tiene marco nativo (FramelessWindowHint), esta barra reemplaza
    los controles de sistema.

    Los colores provienen del tema activo (title_bg / title_fg), así
    que la barra se adapta al tema elegido por el usuario.
    """

    def __init__(
        self,
        title: str,
        window,
    ) -> None:
        super().__init__()

        self.window = window

        self.setFixedHeight(40)
        self.setStyleSheet(
            f"background-color: {theme_color('title_bg')}; "
            f"color: {theme_color('title_fg')};"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 4, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-weight: bold; background: transparent;"
        )

        layout.addWidget(self.title_label)
        layout.addStretch()

        # Botones de control de la ventana con icono dibujado.
        self.minimize_button = _WindowButton(
            "minimize",
            tr("Minimize"),
        )
        self.maximize_button = _WindowButton(
            "maximize",
            tr("Maximize"),
        )
        self.fullscreen_button = _WindowButton(
            "fullscreen",
            tr("Fullscreen"),
        )
        self.close_button = _WindowButton(
            "close",
            tr("Close"),
        )

        self.minimize_button.clicked.connect(
            self.window.showMinimized
        )
        self.maximize_button.clicked.connect(
            self.toggle_maximize
        )
        self.fullscreen_button.clicked.connect(
            self.toggle_fullscreen
        )
        self.close_button.clicked.connect(
            self.window.close
        )

        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.fullscreen_button)
        layout.addWidget(self.close_button)

    def update_window_buttons(self) -> None:
        """Actualiza el icono de maximizar según el estado de la ventana.

        Cuando la ventana está maximizada el botón cambia a "restore"
        (dos rectángulos), como hacen los controles nativos.
        """
        self.maximize_button.kind = (
            "restore"
            if self.window.isMaximized()
            else "maximize"
        )

        self.maximize_button.update()

    def toggle_maximize(self) -> None:
        """Alterna entre maximizar y restaurar."""
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

        self.update_window_buttons()

    def toggle_fullscreen(self) -> None:
        """Alterna pantalla completa y oculta/muestra los controles."""
        if self.window.isFullScreen():
            self.window.showNormal()
            self.setVisible(True)
        else:
            self.window.showFullScreen()
            self.setVisible(False)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Guarda la posición para arrastrar la ventana.
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        # Arrastrar la barra mueve la ventana (delegado al gestor de
        # ventanas del sistema, fiable también con ventana sin marco).
        if (
            getattr(self, "_dragging", False)
            and not self.window.isMaximized()
            and not self.window.isFullScreen()
        ):
            self.window.windowHandle().startSystemMove()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False

        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        # Doble clic en la barra maximiza o restaura.
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_maximize()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

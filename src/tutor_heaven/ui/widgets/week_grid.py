from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QPainter,
    QPaintEvent,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.themes import theme_color

# Horario visible del calendario: de las 6:00 a las 23:00.
HOUR_START = 6
HOUR_END = 23
HOUR_COUNT = HOUR_END - HOUR_START

# Alto de cada fila de una hora en píxeles (1 minuto = 1 píxel).
PX_PER_HOUR = 60
MINUTES_PER_DAY = HOUR_COUNT * 60
TOTAL_HEIGHT = HOUR_COUNT * PX_PER_HOUR

# Cabecera de días y columna de horas.
HEADER_HEIGHT = 46
TIME_COL_WIDTH = 54
MIN_DAY_WIDTH = 110

# Abreviaturas de los días de la semana (traducidas con tr()).
DAY_SHORT = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
]


def snap15(minutes: int) -> int:
    """Redondea unos minutos a un múltiplo de 15 dentro del horario."""
    minutes = max(
        HOUR_START * 60,
        min(minutes, HOUR_END * 60),
    )

    return max(
        HOUR_START * 60,
        round(minutes / 15) * 15,
    )


class _MarkButton(QPushButton):
    """Botón de marca de clase (vista o pagada).

    Muestra el estado como un punto de color (estilo "dots") o como un
    texto con fondo de color (estilo "text"), según la configuración.
    Al hacer clic el bloque reenvía el cambio al lienzo (señal).
    """

    # Colores por tipo y estado.
    COLORS = {
        "viewed": {
            "off": "#FBC02D",  # amarillo: aún no vista
            "on": "#1565C0",   # azul: vista
        },
        "paid": {
            "off": "#E53935",  # rojo: sin pagar
            "on": "#2E7D32",   # verde: pagada
        },
    }

    TEXT_ON = {
        "viewed": "Viewed",
        "paid": "Paid",
    }

    TEXT_OFF = {
        "viewed": "Not viewed",
        "paid": "Not paid",
    }

    def __init__(
        self,
        kind: str,
        state: bool,
        style: str,
    ) -> None:
        super().__init__()

        self.kind = kind
        self.state = state
        self.style = style

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFlat(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        if style == "text":
            self.setFixedHeight(20)
            self.setStyleSheet(self._text_qss())
            self.setText(
                tr(
                    self.TEXT_ON[kind]
                    if state
                    else self.TEXT_OFF[kind]
                )
            )
            self._resize_to_text()
        else:
            self.setFixedSize(16, 16)

    def color(self) -> str:
        return self.COLORS[self.kind][
            "on" if self.state else "off"
        ]

    def _text_qss(self) -> str:
        return (
            "QPushButton { "
            f"background-color: {self.color()}; color: white; "
            "border: none; border-radius: 9px; padding: 0 8px; "
            "font-size: 11px; font-weight: bold; }"
        )

    def _resize_to_text(self) -> None:
        width = (
            self.fontMetrics().horizontalAdvance(self.text()) + 20
        )

        self.setFixedWidth(width)

    def set_state(self, state: bool) -> None:
        self.state = state

        if self.style == "text":
            self.setText(
                tr(
                    self.TEXT_ON[self.kind]
                    if state
                    else self.TEXT_OFF[self.kind]
                )
            )
            self.setStyleSheet(self._text_qss())
            self._resize_to_text()

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.style != "dots":
            super().paintEvent(event)

            return

        painter = QPainter(self)
        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.color()))

        radius = min(
            self.width(),
            self.height(),
        ) / 2 - 1

        painter.drawEllipse(
            self.rect().center(),
            radius,
            radius,
        )


class SessionBlock(QFrame):
    """Bloque visual de una clase dentro del calendario.

    Se posiciona sobre la rejilla según su fecha y horas. El usuario
    puede redimensionarlo arrastrando el borde inferior (a pasos de
    15 minutos), editarlo con doble clic, marcarlo como pagado o
    eliminarlo desde el menú contextual.

    Si las marcas de clase están activadas (Configuración), el bloque
    muestra en la esquina superior derecha dos indicadores clicables:
    - vista (punto amarillo -> azul al marcarla como vista), y
    - pago (punto rojo -> verde al marcarla como pagada).
    El estilo puede ser puntos o texto.
    """

    def __init__(
        self,
        student: Student,
        session,
        canvas: "_GridCanvas",
    ) -> None:
        super().__init__(canvas)

        self.student = student
        self.session = session
        self.canvas = canvas

        # Guarda el día de la semana (0=Lunes) y las horas en minutos.
        self.day_index = 0
        self.start_minutes = 0
        self.end_minutes = 60

        self._resizing = False
        self._resize_start_y = 0.0

        self.setStyleSheet(
            f"background-color: {student.color}; "
            "border: none; border-radius: 6px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        # Marcas de clase (vista / pagada), según la configuración.
        settings = get_settings()

        if settings.calendar_show_marks:
            marks_row = QHBoxLayout()
            marks_row.setSpacing(4)
            marks_row.addStretch()

            self.viewed_mark = _MarkButton(
                "viewed",
                self.session.status == "Completed",
                settings.calendar_marks_style,
            )
            self.viewed_mark.setToolTip(
                tr("Viewed")
                if self.session.status == "Completed"
                else tr("Not viewed")
            )

            self.paid_mark = _MarkButton(
                "paid",
                self.student.session_is_paid(self.session),
                settings.calendar_marks_style,
            )
            self.paid_mark.setToolTip(
                tr("Paid")
                if self.student.session_is_paid(self.session)
                else tr("Not paid")
            )

            self.viewed_mark.clicked.connect(
                self.toggle_viewed
            )
            self.paid_mark.clicked.connect(
                self.toggle_paid
            )

            marks_row.addWidget(self.viewed_mark)
            marks_row.addWidget(self.paid_mark)

            layout.addLayout(marks_row)

        self.label = QLabel()
        self.label.setStyleSheet(
            "color: white; background: transparent;"
        )
        self.label.setWordWrap(True)

        layout.addWidget(self.label)

        self.update_label()

    def toggle_viewed(self) -> None:
        """Reenvía la petición de marcar/desmarcar como vista."""
        self.canvas.blockToggleViewedRequested.emit(
            self.student,
            self.session,
        )

    def toggle_paid(self) -> None:
        """Reenvía la petición de marcar/desmarcar como pagada."""
        self.canvas.blockTogglePaidRequested.emit(
            self.student,
            self.session,
        )

    def update_label(self) -> None:
        """Rellena el texto del bloque con la info de la clase."""
        self.label.setText(
            f"{self.session.start_time} – {self.session.end_time}\n"
            f"{self.student.name}\n"
            f"{self.session.topic or '-'}"
        )

    def minutes_to_y(self, minutes: int) -> int:
        return self.canvas.minutes_to_y(minutes)

    def apply_geometry(self) -> None:
        """Coloca el bloque en la posición que le corresponde."""
        day_width = self.canvas.day_width()

        x = (
            TIME_COL_WIDTH
            + self.day_index * day_width
            + 2
        )
        y = self.minutes_to_y(self.start_minutes)

        width = max(day_width - 4, 40)
        height = max(
            self.end_minutes - self.start_minutes,
            15,
        )

        self.setGeometry(x, y, width, height)

    def mouseDoubleClickEvent(self, event) -> None:
        self.canvas.blockEditRequested.emit(
            self.student,
            self.session,
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        # Arrastrar desde el borde inferior redimensiona la clase.
        if (
            event.button() == Qt.MouseButton.LeftButton
            and event.position().y() >= self.height() - 10
        ):
            self._resizing = True
            self._resize_start_y = event.position().y()

            event.accept()

            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._resizing:
            delta = int(event.position().y() - self._resize_start_y)

            new_end = snap15(
                self.end_minutes + delta
            )

            new_end = max(
                self.start_minutes + 15,
                new_end,
            )

            new_end = min(new_end, HOUR_END * 60)

            self.end_minutes = new_end
            self.apply_geometry()

            event.accept()

            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._resizing:
            self._resizing = False

            self.canvas.blockResizeRequested.emit(
                self.student,
                self.session,
                self.start_minutes,
                self.end_minutes,
            )

            event.accept()

            return

        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)

        add = menu.addAction(tr("➕ +15 minutes"))
        subtract = menu.addAction(tr("➖ -15 minutes"))
        edit = menu.addAction(tr("✏️ Edit..."))
        mark = menu.addAction(
            tr("💵 Mark as Not Paid")
            if self.student.session_is_paid(self.session)
            else tr("💵 Mark as Paid")
        )
        delete = menu.addAction(tr("🗑 Delete"))

        action = menu.exec(event.globalPos())

        if action == add:
            new_end = min(
                self.end_minutes + 15,
                HOUR_END * 60,
            )

            self.canvas.blockResizeRequested.emit(
                self.student,
                self.session,
                self.start_minutes,
                new_end,
            )
        elif action == subtract:
            new_end = max(
                self.start_minutes + 15,
                self.end_minutes - 15,
            )

            self.canvas.blockResizeRequested.emit(
                self.student,
                self.session,
                self.start_minutes,
                new_end,
            )
        elif action == edit:
            self.canvas.blockEditRequested.emit(
                self.student,
                self.session,
            )
        elif action == mark:
            self.canvas.blockTogglePaidRequested.emit(
                self.student,
                self.session,
            )
        elif action == delete:
            self.canvas.blockDeleteRequested.emit(
                self.student,
                self.session,
            )


class _GridCanvas(QWidget):
    """Lienzo donde se pintan la rejilla horaria y los bloques.

    Gestiona la selección por arrastre para crear una clase nueva en
    un hueco vacío y reenvía las acciones de los bloques.
    """

    createRequested = Signal(str, int, int)
    blockEditRequested = Signal(object, object)
    blockDeleteRequested = Signal(object, object)
    blockResizeRequested = Signal(object, object, int, int)
    blockTogglePaidRequested = Signal(object, object)
    blockToggleViewedRequested = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()

        self.monday = QDate.currentDate()

        self._blocks: list[SessionBlock] = []

        # Selección de creación por arrastre: (día, inicio, fin) en
        # minutos desde la medianoche, o None.
        self._selection = None

        self.setMinimumHeight(TOTAL_HEIGHT)

        # Para que el lienzo se pueda hacer tan ancho como sea
        # necesario, aunque la ventana sea estrecha.
        self.setMinimumWidth(
            TIME_COL_WIDTH + 7 * MIN_DAY_WIDTH
        )

    def day_width(self) -> int:
        return max(
            MIN_DAY_WIDTH,
            (self.width() - TIME_COL_WIDTH) // 7,
        )

    def minutes_to_y(self, minutes: int) -> int:
        # El lienzo empieza en la fila de las 6:00, así que el píxel 0
        # es el borde superior de esa hora.
        return minutes - HOUR_START * 60

    def clear_blocks(self) -> None:
        """Elimina todos los bloques de clases del lienzo."""
        for block in self._blocks:
            block.deleteLater()

        self._blocks.clear()

    def add_block(
        self,
        student: Student,
        session,
    ) -> None:
        block = SessionBlock(student, session, self)

        block.start_minutes = (
            int(session.start_datetime.hour) * 60
            + session.start_datetime.minute
        )
        block.end_minutes = (
            int(session.end_datetime.hour) * 60
            + session.end_datetime.minute
        )

        day_date = QDate.fromString(
            session.date,
            "yyyy-MM-dd",
        )

        if not day_date.isValid():
            day_index = 0
        else:
            day_index = self.monday.daysTo(day_date)
            day_index = max(0, min(day_index, 6))

        block.day_index = day_index

        self._blocks.append(block)

        block.apply_geometry()
        block.show()

    def position_blocks(self) -> None:
        """Reposiciona los bloques tras un cambio de tamaño del lienzo."""
        for block in self._blocks:
            block.apply_geometry()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)

        self.position_blocks()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)

            return

        day_index, minutes = self.point_to_slot(
            event.position().x(),
            event.position().y(),
        )

        start = snap15(minutes)

        self._selection = [
            day_index,
            start,
            start,
        ]

        self.update()

        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._selection is None:
            super().mouseMoveEvent(event)

            return

        _, minutes = self.point_to_slot(
            event.position().x(),
            event.position().y(),
        )

        end = max(
            self._selection[1] + 15,
            snap15(minutes),
        )

        self._selection[2] = min(end, HOUR_END * 60)

        self.update()

        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._selection is None:
            super().mouseReleaseEvent(event)

            return

        day_index, start, end = self._selection

        self._selection = None
        self.update()

        # Un clic sin arrastre crea una clase de una hora por defecto.
        if end - start < 15:
            end = min(start + 60, HOUR_END * 60)

        date = self.monday.addDays(day_index).toString(
            "yyyy-MM-dd"
        )

        self.createRequested.emit(
            date,
            start,
            end,
        )

        event.accept()

    def point_to_slot(
        self,
        x: float,
        y: float,
    ) -> tuple[int, int]:
        """Convierte una posición del lienzo en (día, minutos)."""
        day_width = self.day_width()

        day_index = int(
            (x - TIME_COL_WIDTH) // day_width
        )

        day_index = max(0, min(day_index, 6))

        minutes = HOUR_START * 60 + int(y)

        minutes = max(
            HOUR_START * 60,
            min(minutes, HOUR_END * 60),
        )

        return day_index, minutes

    def paintEvent(self, event: QPaintEvent) -> None:
        del event

        painter = QPainter(self)

        painter.fillRect(
            self.rect(),
            QColor(theme_color("canvas_bg")),
        )

        grid_line = QColor(theme_color("grid_line"))
        grid_text = QColor(theme_color("grid_text"))

        day_width = self.day_width()

        # Líneas horizontales de cada hora y etiquetas de hora.
        for hour in range(HOUR_START, HOUR_END + 1):
            y = (hour - HOUR_START) * PX_PER_HOUR

            painter.setPen(grid_line)

            painter.drawLine(
                TIME_COL_WIDTH,
                y,
                self.width(),
                y,
            )

            painter.setPen(grid_text)

            painter.drawText(
                4,
                y - 4,
                TIME_COL_WIDTH - 8,
                20,
                Qt.AlignmentFlag.AlignRight,
                f"{hour}:00",
            )

        # Separadores verticales entre días.
        for day in range(8):
            x = TIME_COL_WIDTH + day * day_width

            painter.setPen(grid_line)

            painter.drawLine(
                x,
                0,
                x,
                TOTAL_HEIGHT,
            )

        # Selección de arrastre para crear una clase.
        if self._selection is not None:
            day_index, start, end = self._selection

            x = TIME_COL_WIDTH + day_index * day_width + 2
            y = (start - HOUR_START * 60)
            height = end - start

            accent = QColor(theme_color("accent"))
            accent.setAlpha(90)

            painter.fillRect(
                x,
                y,
                day_width - 4,
                height,
                accent,
            )


class WeekGrid(QWidget):
    """Rejilla semanal interactiva de clases.

    Muestra las sesiones de una semana ordenadas por hora (6:00-23:00)
    con las horas a la izquierda. Permite crear una clase haciendo clic
    o arrastrando sobre un hueco vacío, redimensionarla a pasos de 15
    minutos, editarla, marcarla como pagada o eliminarla.

    El widget solo pinta y emite señales; la lógica de guardado la
    decide el padre (pestaña Calendar o perfil del estudiante).
    """

    createRequested = Signal(str, int, int)
    editRequested = Signal(object, object)
    deleteRequested = Signal(object, object)
    resizeRequested = Signal(object, object, int, int)
    togglePaidRequested = Signal(object, object)
    toggleViewedRequested = Signal(object, object)

    # Emitida al cambiar de semana con las flechas o "Today".
    weekChanged = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.week_offset = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ---------- Cabecera fija de días ----------

        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        day_row = QHBoxLayout()
        day_row.setSpacing(0)

        time_spacer = QLabel()
        time_spacer.setFixedWidth(TIME_COL_WIDTH)

        day_row.addWidget(time_spacer)

        self.day_headers: list[QLabel] = []

        for name in DAY_SHORT:
            header = QLabel(name)

            header.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            header.setStyleSheet(
                f"font-weight: bold; color: {theme_color('muted_text')}; "
                f"background-color: {theme_color('panel_alt')}; "
                "border-bottom: 1px solid "
                f"{theme_color('grid_line')}; padding: 4px 0;"
            )

            self.day_headers.append(header)

            day_row.addWidget(header, stretch=1)

        # Espaciador para compensar la barra de scroll vertical del
        # lienzo y que las columnas de la cabecera queden alineadas.
        scroll_spacer = QLabel()
        scroll_spacer.setFixedWidth(16)

        day_row.addWidget(scroll_spacer)

        header_layout.addLayout(day_row)

        layout.addLayout(header_layout)

        # ---------- Lienzo con scroll ----------

        self.canvas = _GridCanvas()

        scroll = QScrollArea()

        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        layout.addWidget(scroll)

        # Reenvía las señales del lienzo hacia fuera del widget.
        self.canvas.createRequested.connect(
            self.createRequested
        )
        self.canvas.blockEditRequested.connect(
            self.editRequested
        )
        self.canvas.blockDeleteRequested.connect(
            self.deleteRequested
        )
        self.canvas.blockResizeRequested.connect(
            self.resizeRequested
        )
        self.canvas.blockTogglePaidRequested.connect(
            self.togglePaidRequested
        )
        self.canvas.blockToggleViewedRequested.connect(
            self.toggleViewedRequested
        )

    def current_monday(self) -> QDate:
        today = QDate.currentDate()

        monday = today.addDays(
            -(today.dayOfWeek() - 1)
        )

        return monday.addDays(
            self.week_offset * 7
        )

    def go_previous_week(self) -> None:
        self.week_offset -= 1

        self.refresh()
        self.weekChanged.emit()

    def go_next_week(self) -> None:
        self.week_offset += 1

        self.refresh()
        self.weekChanged.emit()

    def go_today(self) -> None:
        self.week_offset = 0

        self.refresh()
        self.weekChanged.emit()

    def refresh(
        self,
        items: list[tuple[Student, object]] | None = None,
    ) -> None:
        """Reconstruye el calendario con la semana actual.

        items es una lista de (estudiante, sesión). Si es None se
        recarga desde disco con load_students().
        """
        monday = self.current_monday()

        self.canvas.monday = monday
        self.canvas.clear_blocks()

        for index, header in enumerate(self.day_headers):
            day_date = monday.addDays(index)

            header.setText(
                f"{tr(DAY_SHORT[index])}\n"
                f"{day_date.toString('MMM d')}"
            )

        if items is None:
            from tutor_heaven.data.student_storage import load_students

            items = [
                (student, session)
                for student in load_students()
                for session in student.sessions
            ]

        sunday = monday.addDays(6)

        for student, session in items:
            session_date = QDate.fromString(
                session.date,
                "yyyy-MM-dd",
            )

            if not session_date.isValid():
                continue

            # Solo se pinta lo que cae dentro de la semana mostrada.
            if session_date < monday or session_date > sunday:
                continue

            self.canvas.add_block(student, session)

        self.canvas.update()

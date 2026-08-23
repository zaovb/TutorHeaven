from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import (
    load_deleted_students,
    load_students,
    permanently_delete_student,
    restore_student,
    save_students,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.formatting import format_hours
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.themes import theme_color
from tutor_heaven.ui.widgets.student_dialog import StudentDialog


class NameChipDelegate(QStyledItemDelegate):
    """Delegate que pinta cada nombre con un pequeño rectángulo
    redondeado alrededor del texto (tipo chip), en lugar de resaltar
    toda la fila de la lista.

    La selección y el hover colorean solo ese rectángulo; el resto de
    la fila queda transparente.
    """

    # Márgenes internos del chip.
    _PAD_X = 14
    _PAD_Y = 5
    _MARGIN_LEFT = 4

    def paint(
        self,
        painter: QPainter,
        option,
        index,
    ) -> None:
        text = index.data(
            Qt.ItemDataRole.DisplayRole
        )

        if not text:
            return

        painter.save()

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        font_metrics = option.fontMetrics

        chip_w = (
            font_metrics.horizontalAdvance(text)
            + self._PAD_X * 2
        )
        chip_h = (
            font_metrics.height()
            + self._PAD_Y * 2
        )

        chip_rect = QRect(
            option.rect.left() + self._MARGIN_LEFT,
            option.rect.top()
            + (option.rect.height() - chip_h) // 2,
            chip_w,
            chip_h,
        )

        selected = bool(
            option.state
            & QStyle.StateFlag.State_Selected
        )

        hovered = bool(
            option.state
            & QStyle.StateFlag.State_MouseOver
        )

        # El chip solo se colorea cuando está seleccionado o bajo el
        # ratón; el resto del tiempo la fila es transparente.
        if selected:
            painter.setBrush(
                QColor(theme_color("container"))
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                chip_rect,
                chip_h / 2,
                chip_h / 2,
            )

            text_color = QColor(
                theme_color("on_container")
            )
        else:
            text_color = QColor(
                theme_color("text")
            )

            if hovered:
                painter.setBrush(
                    QColor(theme_color("hover_bg"))
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(
                    chip_rect,
                    chip_h / 2,
                    chip_h / 2,
                )

        painter.setPen(text_color)
        painter.drawText(
            chip_rect,
            Qt.AlignmentFlag.AlignCenter,
            text,
        )

        painter.restore()

    def sizeHint(
        self,
        option,
        index,
    ) -> QSize:
        text = index.data(
            Qt.ItemDataRole.DisplayRole
        )

        font_metrics = option.fontMetrics

        return QSize(
            font_metrics.horizontalAdvance(text or "")
            + self._PAD_X * 2
            + self._MARGIN_LEFT,
            font_metrics.height() + self._PAD_Y * 2 + 6,
        )


class Students(QWidget):
    """Students module.

    Panel lateral con la lista de estudiantes matriculados. Permite
    dar de alta a un estudiante nuevo (abriendo StudentDialog) y
    muestra un resumen del estudiante seleccionado. Al hacer doble
    clic emite studentSelected para abrir el perfil completo.
    """

    # Señal propia: se emite con el Student cuando se quiere abrir
    # su perfil (la consume StudentBrowser).
    studentSelected = Signal(object)

    def __init__(self) -> None:
        super().__init__()

        # Carga la lista persistida una sola vez al crear el widget.
        # Todas las modificaciones (altas, sesiones) operan sobre esta
        # misma lista para que los widgets compartan los cambios.
        self.students: list[Student] = load_students()

        layout = QVBoxLayout(self)

        # ---------- Barra superior ----------

        # Dos botones: dar de alta y entrar al portal de eliminados.
        self.showing_deleted = False

        new_student_button = QPushButton(
            tr("➕ New Enrollment")
        )

        new_student_button.setObjectName("primary")

        new_student_button.clicked.connect(
            self.new_student
        )

        self.deleted_button = QPushButton(
            tr("🗑 Deleted")
        )

        self.deleted_button.clicked.connect(
            self.toggle_deleted
        )

        top_bar = QHBoxLayout()

        top_bar.addWidget(new_student_button)
        top_bar.addWidget(self.deleted_button)

        layout.addLayout(top_bar)

        # Lista con los nombres de los estudiantes.
        self.list = QListWidget()

        # El nombre se muestra como un pequeño rectángulo redondeado
        # alrededor del texto (en lugar de resaltar toda la fila).
        self.list.setItemDelegate(
            NameChipDelegate(self.list)
        )

        # Un solo clic actualiza el resumen y abre el perfil del
        # estudiante seleccionado (solo en la lista activa).
        self.list.itemClicked.connect(
            self.show_enrollment
        )
        self.list.itemClicked.connect(
            self.open_student
        )

        # Panel con el resumen del estudiante seleccionado, como tarjeta.
        self.details = QGroupBox(
            tr("Student Summary")
        )

        details_layout = QFormLayout(
            self.details
        )

        self.total = QLabel("-")
        self.classes_left = QLabel("-")
        self.next_class = QLabel("-")
        self.notes = QLabel("-")
        self.status = QLabel("-")

        details_layout.addRow(
            tr("Total"),
            self.total,
        )

        details_layout.addRow(
            tr("Hours Left"),
            self.classes_left,
        )

        details_layout.addRow(
            tr("Next Class"),
            self.next_class,
        )

        details_layout.addRow(
            tr("Notes"),
            self.notes,
        )

        details_layout.addRow(
            tr("Status"),
            self.status,
        )

        # Acciones del portal de eliminados (solo visibles ahí).
        self.restore_button = QPushButton(
            tr("↩ Restore Student")
        )
        self.restore_button.clicked.connect(
            self.restore_selected
        )

        self.purge_button = QPushButton(
            tr("🗑 Delete Forever")
        )
        self.purge_button.setObjectName("danger")
        self.purge_button.clicked.connect(
            self.purge_selected
        )

        self.restore_button.setVisible(False)
        self.purge_button.setVisible(False)

        layout.addWidget(
            self.list
        )

        layout.addWidget(
            self.details
        )

        layout.addWidget(
            self.restore_button
        )

        layout.addWidget(
            self.purge_button
        )

        self.refresh_students()

        # La lista se mantiene sincronizada con los cambios hechos desde
        # otras vistas (dashboard, perfiles).
        get_bus().studentsChanged.connect(
            self.refresh_students
        )

    def showEvent(self, event) -> None:
        """Al mostrarse recarga desde disco por si los datos cambiaron."""
        super().showEvent(event)

        self.refresh_students()

    def toggle_deleted(self) -> None:
        """Alterna la lista entre estudiantes activos y eliminados."""
        self.showing_deleted = not self.showing_deleted

        self.deleted_button.setText(
            tr("↩ Active Students")
            if self.showing_deleted
            else tr("🗑 Deleted")
        )

        # En el portal de eliminados se muestran las acciones de
        # restaurar / borrar definitivamente.
        self.restore_button.setVisible(
            self.showing_deleted
        )
        self.purge_button.setVisible(
            self.showing_deleted
        )

        self.list.clearSelection()

        self.refresh_students()

    def refresh_students(self) -> None:
        """Recarga la lista desde disco y vuelve a pintar los nombres."""
        if self.showing_deleted:
            self.students = load_deleted_students()
        else:
            self.students = load_students()

        self.list.clear()

        for student in self.students:
            self.list.addItem(
                student.name
            )

    def restore_selected(self) -> None:
        """Devuelve a la lista activa al estudiante eliminado."""
        row = self.list.currentRow()

        if row < 0:
            return

        restore_student(
            self.students[row]
        )

        self.refresh_students()

    def purge_selected(self) -> None:
        """Borra definitivamente al estudiante eliminado seleccionado."""
        row = self.list.currentRow()

        if row < 0:
            return

        student = self.students[row]

        confirm = QMessageBox.warning(
            self,
            tr("Delete student forever"),
            tr(
                "Permanently delete {0}?\n\n"
                "All their packages, sessions, payments and notes will "
                "be permanently removed, including their observer base "
                "note. This action cannot be undone."
            ).format(
                student.name
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        permanently_delete_student(
            student
        )

        self.refresh_students()

    def new_student(self) -> None:
        """Abre el diálogo de alta; si se acepta, agrega y guarda."""
        if self.showing_deleted:
            return

        dialog = StudentDialog()

        if not dialog.exec():
            return

        student = dialog.student

        if student is None:
            return

        self.students.append(
            student
        )

        save_students(
            self.students
        )

        self.refresh_students()

    def show_enrollment(self) -> None:
        """Muestra el resumen del estudiante seleccionado en la lista."""
        row = self.list.currentRow()

        if row < 0:
            return

        student = self.students[row]

        self.total.setText(
            f"$ {student.total:.2f}"
        )

        if student.hours_left >= 0:
            hours_text = format_hours(student.hours_left)
        else:
            hours_text = tr("0 ({0} h owed)").format(
                format_hours(-student.hours_left)
            )

        self.classes_left.setText(
            hours_text
        )

        next_session = student.next_session

        self.next_class.setText(
            (
                f"{next_session.date} "
                f"{next_session.start_time}"
            )
            if next_session is not None
            else "-"
        )

        self.notes.setText(
            student.notes
        )

        # En modo "Pay later" no tiene sentido mostrar un estado de
        # pago; se muestra la etiqueta del modo de pago.
        status = (
            tr("Pay later")
            if student.payment_mode == "Pay later"
            else tr(student.payment_status)
        )

        self.status.setText(
            status
        )

    def open_student(self) -> None:
        """Emite la señal para abrir el perfil del estudiante.

        En el portal de eliminados no se abre un perfil: allí las
        acciones son restaurar o borrar definitivamente.
        """
        if self.showing_deleted:
            return

        row = self.list.currentRow()

        if row < 0:
            return

        self.studentSelected.emit(
            self.students[row]
        )
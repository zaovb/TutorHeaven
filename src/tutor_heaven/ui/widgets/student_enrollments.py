from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import (
    load_students,
    save_students,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.student_dialog import StudentDialog


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

        new_student_button = QPushButton(
            tr("➕ New Enrollment")
        )

        new_student_button.setObjectName("primary")

        new_student_button.clicked.connect(
            self.new_student
        )

        # Lista con los nombres de los estudiantes.
        self.list = QListWidget()

        # Un clic muestra el resumen; doble clic abre el perfil.
        self.list.itemClicked.connect(
            self.show_enrollment
        )

        self.list.itemDoubleClicked.connect(
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
            tr("Classes Left"),
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

        layout.addWidget(
            new_student_button
        )

        layout.addWidget(
            self.list
        )

        layout.addWidget(
            self.details
        )

        self.refresh_students()

        # La lista se mantiene sincronizada con los cambios hechos desde
        # otras vistas (dashboard, calendario, perfiles).
        get_bus().studentsChanged.connect(
            self.refresh_students
        )

    def showEvent(self, event) -> None:
        """Al mostrarse recarga desde disco por si los datos cambiaron."""
        super().showEvent(event)

        self.refresh_students()

    def refresh_students(self) -> None:
        """Recarga la lista desde disco y vuelve a pintar los nombres."""
        self.students = load_students()

        self.list.clear()

        for student in self.students:
            self.list.addItem(
                student.name
            )

    def new_student(self) -> None:
        """Abre el diálogo de alta; si se acepta, agrega y guarda."""
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

        if student.classes_left >= 0:
            classes_text = str(student.classes_left)
        else:
            classes_text = tr("0 ({0} owed)").format(
                -student.classes_left
            )

        self.classes_left.setText(
            classes_text
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
            else student.payment_status
        )

        self.status.setText(
            status
        )

    def open_student(self) -> None:
        """Emite la señal para abrir el perfil del estudiante."""
        row = self.list.currentRow()

        if row < 0:
            return

        self.studentSelected.emit(
            self.students[row]
        )
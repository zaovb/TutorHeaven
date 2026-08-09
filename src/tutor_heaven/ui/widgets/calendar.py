from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import load_students, save_students
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.models.session_model import Session
from tutor_heaven.ui.widgets.session_dialog import SessionDialog
from tutor_heaven.ui.widgets.week_grid import WeekGrid


class Calendar(QWidget):
    """Calendar.

    Calendario de clases sobre una rejilla horaria (6:00-23:00) con las
    horas a la izquierda. Permite navegar entre semanas, crear una clase
    haciendo clic o arrastrando sobre un hueco (para cualquier estudiante
    matriculado; si se elige "New student..." se abre la matrícula),
    redimensionarla a pasos de 15 minutos, editarla, marcarla como pagada
    o eliminarla. Debajo aparece la lista de estudiantes que tuvieron
    clase esa semana.
    """

    # Se emite cuando el usuario elige "New student...": el MainWindow
    # cambia a la pestaña de matrículas para dar de alta al estudiante.
    openEnrollment = Signal()

    def __init__(self) -> None:
        super().__init__()

        self.students: list[Student] = load_students()

        # ---------- Rejilla semanal ----------

        self.week_grid = WeekGrid()

        self.week_grid.createRequested.connect(
            self.create_session
        )
        self.week_grid.editRequested.connect(
            self.edit_session
        )
        self.week_grid.deleteRequested.connect(
            self.delete_session
        )
        self.week_grid.resizeRequested.connect(
            self.resize_session
        )
        self.week_grid.togglePaidRequested.connect(
            self.toggle_paid
        )
        self.week_grid.toggleViewedRequested.connect(
            self.toggle_viewed
        )

        # Al cambiar de semana con las flechas se actualiza el título.
        self.week_grid.weekChanged.connect(
            self.refresh
        )

        layout = QVBoxLayout(self)

        # ---------- Barra superior ----------

        top_layout = QHBoxLayout()

        self.prev_button = QPushButton("◀")
        self.next_button = QPushButton("▶")
        self.today_button = QPushButton(tr("Today"))

        self.prev_button.setFixedWidth(40)
        self.next_button.setFixedWidth(40)

        self.prev_button.clicked.connect(
            self.week_grid.go_previous_week
        )
        self.next_button.clicked.connect(
            self.week_grid.go_next_week
        )
        self.today_button.clicked.connect(
            self.week_grid.go_today
        )

        self.week_title = QLabel()
        self.week_title.setStyleSheet(
            "font-size: 16px; font-weight: bold;"
        )

        top_layout.addWidget(self.prev_button)
        top_layout.addWidget(self.week_title)
        top_layout.addWidget(self.next_button)
        top_layout.addStretch()

        # Selector de estudiante: al crear una clase en un hueco se
        # asigna al estudiante elegido. "New student..." lleva a la
        # matrícula.
        self.student_combo = QComboBox()
        self.student_combo.setMinimumWidth(180)

        top_layout.addWidget(self.student_combo)

        top_layout.addWidget(self.today_button)

        layout.addLayout(top_layout)

        layout.addWidget(self.week_grid, stretch=1)

        # ---------- Estudiantes que estudiaron esa semana ----------

        students_group = QGroupBox(
            tr("Students who studied this week")
        )

        students_layout = QVBoxLayout(students_group)

        self.students_week_list = QListWidget()

        students_layout.addWidget(self.students_week_list)

        layout.addWidget(students_group)

        # Se recarga cuando los datos cambian desde cualquier otra vista.
        get_bus().studentsChanged.connect(
            self.refresh
        )

        self.refresh()

    def showEvent(self, event) -> None:
        """Al mostrar el calendario se vuelve a la semana actual y se
        refresca para reflejar los datos más recientes (nuevas sesiones,
        colores, etc.)."""
        super().showEvent(event)

        # Vuelve siempre a la semana actual para que la pestaña no se
        # quede anclada en una semana vieja de una visita anterior.
        self.week_grid.week_offset = 0

        self.refresh()

    def refresh(self) -> None:
        """Recarga estudiantes, selector, título y rejilla."""
        self.students = load_students()

        monday = self.week_grid.current_monday()
        sunday = monday.addDays(6)

        self.week_title.setText(
            f"{monday.toString('MMM d')} – "
            f"{sunday.toString('MMM d, yyyy')}"
        )

        # Reconstruye el selector de estudiantes.
        current = self.student_combo.currentText()

        self.student_combo.clear()

        self.student_combo.addItem(tr("➕ New student..."))

        for student in self.students:
            self.student_combo.addItem(student.name)

        if current in [
            student.name for student in self.students
        ]:
            self.student_combo.setCurrentText(current)
        else:
            self.student_combo.setCurrentIndex(0)

        self.week_grid.refresh(
            [
                (student, session)
                for student in self.students
                for session in student.sessions
            ]
        )

        self.fill_students_week_list(monday, sunday)

    def selected_student(self) -> Student | None:
        """Devuelve el estudiante elegido o None si se eligió crear uno."""
        name = self.student_combo.currentText()

        for student in self.students:
            if student.name == name:
                return student

        return None

    def minutes_to_hhmm(self, minutes: int) -> str:
        return f"{minutes // 60:02d}:{minutes % 60:02d}"

    def create_session(
        self,
        date: str,
        start_minutes: int,
        end_minutes: int,
    ) -> None:
        """Crea una clase nueva en la fecha/hora del hueco pulsado."""
        student = self.selected_student()

        # Si no hay estudiante elegido (o se eligió crear uno nuevo),
        # se lleva al usuario a la matrícula.
        if student is None:
            self.openEnrollment.emit()

            return

        dialog = SessionDialog(
            student=student,
            date_str=date,
            start_time=self.minutes_to_hhmm(start_minutes),
            end_time=self.minutes_to_hhmm(end_minutes),
        )

        if not dialog.exec():
            return

        data = dialog.session_data

        if data is None:
            return

        session = Session(
            date=data["date"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            topic=data["topic"],
            status=data["status"],
            notes=data["notes"],
            paid=data["paid"],
        )

        student.sessions.append(session)

        # Si la clase se registra como completada consume una clase
        # del paquete del estudiante.
        if session.status == "Completed":
            student.consume_class()

        save_students(self.students)

        self.refresh()

    def edit_session(
        self,
        student: Student,
        session: Session,
    ) -> None:
        """Abre el diálogo para editar la clase de la rejilla."""
        dialog = SessionDialog(
            student=student,
            session=session,
        )

        if not dialog.exec():
            return

        data = dialog.session_data

        if data is None:
            return

        session.date = data["date"]
        session.start_time = data["start_time"]
        session.end_time = data["end_time"]
        session.topic = data["topic"]
        session.status = data["status"]
        session.notes = data["notes"]

        if data.get("conversation_topic") is not None:
            session.conversation_topic = data["conversation_topic"]

        if data.get("grammar_learned") is not None:
            session.grammar_learned = data["grammar_learned"]

        if data.get("homework") is not None:
            session.homework = data["homework"]

        if data.get("next_topics") is not None:
            session.next_topics = data["next_topics"]

        if data.get("homework_done") is not None:
            session.homework_done = data["homework_done"]

        save_students(self.students)

        self.refresh()

    def delete_session(
        self,
        student: Student,
        session: Session,
    ) -> None:
        """Elimina una clase tras confirmar el aviso."""
        confirm = QMessageBox.question(
            self,
            tr("Delete session"),
            tr("Delete the session of {0} on {1} at {2}?").format(
                student.name,
                session.date,
                session.start_time,
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        if session in student.sessions:
            student.sessions.remove(session)

        save_students(self.students)

        self.refresh()

    def resize_session(
        self,
        student: Student,
        session: Session,
        start_minutes: int,
        end_minutes: int,
    ) -> None:
        """Ajusta el horario de una clase a la nueva duración."""
        old_start = session.start_time
        old_end = session.end_time

        session.start_time = self.minutes_to_hhmm(start_minutes)
        session.end_time = self.minutes_to_hhmm(end_minutes)

        if student.overlaps_other_sessions(session):
            session.start_time = old_start
            session.end_time = old_end

            QMessageBox.warning(
                self,
                tr("Overlapping Classes"),
                tr(
                    "This class overlaps another class of {0}. "
                    "Choose a different time."
                ).format(student.name),
            )

            return

        save_students(self.students)

        self.refresh()

    def toggle_paid(
        self,
        student: Student,
        session: Session,
    ) -> None:
        """Cambia el estado de pago de una clase."""
        del student

        session.paid = not session.paid

        save_students(self.students)

        self.refresh()

    def toggle_viewed(
        self,
        student: Student,
        session: Session,
    ) -> None:
        """Marca o desmarca una clase como vista en el calendario.

        Al marcar como vista la sesión pasa a "Completed" y consume una
        clase del paquete; al desmarcar vuelve a "Pending" y la clase
        se libera. Así los cálculos del paquete siempre reflejan lo
        marcado en el calendario.
        """
        if session.status == "Completed":
            session.status = "Pending"

            student.release_class()
        else:
            session.status = "Completed"

            student.consume_class()

        save_students(self.students)

        self.refresh()

    def fill_students_week_list(
        self,
        monday,
        sunday,
    ) -> None:
        """Rellena la lista con los estudiantes que completaron una
        clase dentro de la semana mostrada."""
        self.students_week_list.clear()

        studied = []

        for student in self.students:
            has_class = any(
                session.status == "Completed"
                and monday
                <= QDate.fromString(
                    session.date,
                    "yyyy-MM-dd",
                )
                <= sunday
                for session in student.sessions
            )

            if has_class:
                studied.append(student)

        for student in studied:
            self.students_week_list.addItem(
                f"{student.name} — "
                f"{student.classes_left} {tr('classes left')}"
            )

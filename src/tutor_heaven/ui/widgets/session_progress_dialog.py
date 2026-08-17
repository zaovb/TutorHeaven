from PySide6.QtCore import QDate, QTime, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.teacher_tasks_storage import load_teacher_tasks
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.models.teacher_task import TeacherTask
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next
from tutor_heaven.ui.widgets.teacher_tasks_view import build_task_row


class SessionProgressDialog(FitDialog):
    """Dialog to record the progress of a class just taught.

    Se abre al marcar una clase como vista ("Añadir clase vista").
    Permite registrar la clase de hoy: la fecha (hoy o un día pasado,
    nunca futuro), cuántas clases quedan (o cuántas se deben), la
    tarea de la clase anterior para revisarla, el progreso del día
    (tema de conversación, gramática, próxima tarea, temas por ver) y
    añadir tareas del profesor para el estudiante.

    Al aceptar expone en self.session_data un dict con los campos de
    progreso, en self.new_interests las nuevas etiquetas de interés y
    en self.new_teacher_tasks las nuevas tareas del profesor.
    """

    def __init__(
        self,
        student: Student,
    ) -> None:
        super().__init__()

        self.student = student

        self.session_data = None
        self.new_interests: list[str] = []
        self.new_teacher_tasks: list[TeacherTask] = []

        self.setWindowTitle(tr("New Viewed Class"))
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)

        # ---------- Info de la clase ----------

        info_group = QGroupBox(tr("Class Information"))
        info_layout = QFormLayout()

        # Fecha de la clase vista. Por defecto hoy; se puede elegir una
        # fecha pasada (clase dada sin registrar), pero no una futura:
        # una clase futura no es una "clase vista" sino una por agendar.
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat("yyyy-MM-dd")
        self.date.setDate(QDate.currentDate())
        self.date.setMaximumDate(QDate.currentDate())

        info_layout.addRow(tr("Date"), self.date)

        # Clases disponibles (o por pagar si debe).
        self.classes_left = QLabel()

        info_layout.addRow(
            self.classes_left_label_text(),
            self.classes_left,
        )

        # Tarea de la clase anterior para revisarla en esta. Si no hay
        # tarea previa, se muestra "No tenía tarea" sin casilla.
        self.last_homework = QLabel()

        self.last_homework.setWordWrap(True)
        self.last_homework.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        self.homework_done = QCheckBox(
            tr("Completed the homework")
        )

        task_row = QHBoxLayout()
        task_row.setSpacing(10)
        task_row.addWidget(self.last_homework, stretch=1)
        task_row.addWidget(self.homework_done)

        task_container = QWidget()
        task_container.setLayout(task_row)

        info_layout.addRow(tr("Task:"), task_container)

        info_group.setLayout(info_layout)

        layout.addWidget(info_group)

        # ---------- Progreso del día ----------

        progress_group = QGroupBox(tr("Progress"))
        progress_layout = QFormLayout()

        # Todos los campos del progreso tienen el mismo tamaño.
        FIELD_HEIGHT = 72

        self.conversation_topic = QPlainTextEdit()
        self.conversation_topic.setFixedHeight(FIELD_HEIGHT)
        self.conversation_topic.setTabChangesFocus(True)

        self.grammar_learned = QPlainTextEdit()
        self.grammar_learned.setFixedHeight(FIELD_HEIGHT)
        self.grammar_learned.setTabChangesFocus(True)

        self.homework = QPlainTextEdit()
        self.homework.setFixedHeight(FIELD_HEIGHT)
        self.homework.setTabChangesFocus(True)

        self.next_topics = QPlainTextEdit()
        self.next_topics.setFixedHeight(FIELD_HEIGHT)
        self.next_topics.setTabChangesFocus(True)

        progress_layout.addRow(
            tr("Conversation Topic:"),
            self.conversation_topic,
        )
        progress_layout.addRow(
            tr("Grammar Learned:"),
            self.grammar_learned,
        )
        progress_layout.addRow(
            tr("Next Task:"),
            self.homework,
        )
        progress_layout.addRow(
            tr("To Learn Next:"),
            self.next_topics,
        )

        progress_group.setLayout(progress_layout)

        layout.addWidget(progress_group)

        # ---------- Intereses del estudiante ----------

        interests_group = QGroupBox(tr("Student Interests"))
        interests_layout = QVBoxLayout()

        self.interests_list = QListWidget()

        self.refresh_interests()

        self.new_interest = QLineEdit()
        self.new_interest.setPlaceholderText(
            tr("Add an interest (hobby, topic...)")
        )

        # Al pulsar Enter se añade el interés sin cerrar el diálogo.
        self.new_interest._enter_action = self.add_interest

        add_button = QPushButton(tr("➕ Add Interest"))
        add_button.clicked.connect(
            self.add_interest
        )

        remove_button = QPushButton(tr("Remove Selected"))
        remove_button.clicked.connect(
            self.remove_interest
        )

        add_row = QHBoxLayout()

        add_row.addWidget(self.new_interest)
        add_row.addWidget(add_button)

        interests_layout.addWidget(self.interests_list)
        interests_layout.addLayout(add_row)
        interests_layout.addWidget(remove_button)

        interests_group.setLayout(interests_layout)

        layout.addWidget(interests_group)

        # ---------- Tareas del profesor ----------

        # Aquí se revisan las tareas pendientes del estudiante (marcar
        # como hecha/no hecha o escribir la nota) y se añaden nuevas.
        # Las que se añadan en este diálogo se guardan al confirmar.
        tasks_group = QGroupBox(tr("Teacher Tasks"))
        tasks_layout = QVBoxLayout()

        self.teacher_tasks_scroll = QScrollArea()
        self.teacher_tasks_scroll.setWidgetResizable(True)
        self.teacher_tasks_scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )
        self.teacher_tasks_scroll.setFixedHeight(180)

        tasks_items = QWidget()
        self.teacher_tasks_container = QVBoxLayout(tasks_items)
        self.teacher_tasks_scroll.setWidget(tasks_items)

        self.new_teacher_task = QLineEdit()
        self.new_teacher_task.setPlaceholderText(
            tr("New task for this student...")
        )

        # Al pulsar Enter se añade la tarea sin cerrar el diálogo.
        self.new_teacher_task._enter_action = self.add_teacher_task

        add_task_button = QPushButton(tr("➕ Add Task"))
        add_task_button.clicked.connect(
            self.add_teacher_task
        )

        task_add_row = QHBoxLayout()

        task_add_row.addWidget(self.new_teacher_task)
        task_add_row.addWidget(add_task_button)

        tasks_layout.addWidget(self.teacher_tasks_scroll)
        tasks_layout.addLayout(task_add_row)

        tasks_group.setLayout(tasks_layout)

        layout.addWidget(tasks_group)

        self.refresh_teacher_tasks()

        # ---------- Botones ----------

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # Enter = siguiente campo (sin cerrar el diálogo); Tab cambia
        # al siguiente campo y Shift+Tab al anterior, también dentro de
        # los cuadros de texto multilínea.
        enable_enter_to_next(self)

        self.update_info()

    def classes_left_label_text(self) -> str:
        """Etiqueta de la fila de clases: disponibles o por pagar."""
        if self.student.classes_left >= 0:
            return tr("Classes Available:")

        return tr("Classes Owed:")

    def update_info(self) -> None:
        """Rellena las etiquetas de clases y de la tarea previa."""
        if self.student.classes_left >= 0:
            self.classes_left.setText(
                str(self.student.classes_left)
            )
        else:
            self.classes_left.setText(
                str(-self.student.classes_left)
            )

        # Muestra la tarea de la última sesión registrada (si hay)
        # para poder revisarla en esta clase. Sin tarea previa, el
        # texto cambia a "No tenía tarea" y se oculta la casilla.
        last_homework = self.last_session_homework()

        if last_homework:
            self.last_homework.setText(last_homework)
            self.homework_done.show()
        else:
            self.last_homework.setText(
                tr("Had no task")
            )
            self.homework_done.hide()

    def last_session_homework(self) -> str:
        """Devuelve la tarea de la sesión más reciente, o "" si no hay."""
        if not self.student.sessions:
            return ""

        latest = max(
            self.student.sessions,
            key=lambda session: session.start_datetime,
        )

        return latest.homework

    def refresh_interests(self) -> None:
        """Muestra los intereses actuales del estudiante."""
        self.interests_list.clear()

        # Intereses ya guardados en el estudiante más los nuevos que
        # se vayan añadiendo en este diálogo.
        all_interests = [
            *self.student.interests,
            *self.new_interests,
        ]

        # Elimina duplicados conservando el orden.
        seen = set()
        unique = []

        for interest in all_interests:
            if interest not in seen:
                seen.add(interest)
                unique.append(interest)

        self.interests_list.addItems(unique)

    def add_interest(self) -> None:
        """Añade el interés escrito al cuadro de intereses."""
        text = self.new_interest.text().strip()

        if not text:
            return

        if (
            text in self.student.interests
            or text in self.new_interests
        ):
            QMessageBox.information(
                self,
                tr("Interest"),
                tr("That interest is already added."),
            )

            return

        self.new_interests.append(text)

        self.new_interest.clear()

        self.refresh_interests()

    def remove_interest(self) -> None:
        """Elimina el interés seleccionado (si es nuevo en el diálogo)."""
        row = self.interests_list.currentRow()

        if row < 0:
            return

        text = self.interests_list.currentItem().text()

        # Solo se pueden quitar los intereses añadidos en este diálogo;
        # los ya guardados del estudiante se mantienen.
        if text in self.new_interests:
            self.new_interests.remove(text)

            self.refresh_interests()

    def refresh_teacher_tasks(self) -> None:
        """Muestra las tareas del profesor de este estudiante.

        Cada tarea se muestra con su casilla de completada y su nota.
        Las ya guardadas persisten cualquier cambio al instante; las
        nuevas de este diálogo se guardan solo al confirmar.
        """
        container = self.teacher_tasks_container

        # Vacía el contenedor (se conserva el "stretch" del final).
        removed = []

        while container.count() > 0:
            item = container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                removed.append(widget)

        for widget in removed:
            widget.deleteLater()

        existing = [
            task
            for task in load_teacher_tasks()
            if task.student == self.student.name
        ]

        # Tareas ya guardadas: los cambios se persisten en disco.
        for task in existing:
            container.addWidget(
                build_task_row(task)
            )

        # Tareas nuevas de este diálogo: los cambios quedan en memoria
        # y se guardan al confirmar la clase.
        for task in self.new_teacher_tasks:
            container.addWidget(
                build_task_row(
                    task,
                    on_done=lambda task, checked: setattr(
                        task,
                        "done",
                        checked,
                    ),
                    on_notes=lambda task, text: setattr(
                        task,
                        "notes",
                        text.strip(),
                    ),
                    on_delete=self.remove_new_teacher_task,
                )
            )

        container.addStretch()

    def add_teacher_task(self) -> None:
        """Añade la tarea del profesor escrita al cuadro."""
        text = self.new_teacher_task.text().strip()

        if not text:
            return

        self.new_teacher_tasks.append(
            TeacherTask(
                text=text,
                student=self.student.name,
            )
        )

        self.new_teacher_task.clear()

        self.refresh_teacher_tasks()

    def remove_new_teacher_task(self, task: TeacherTask) -> None:
        """Quita una tarea aún no confirmada del diálogo."""
        if task in self.new_teacher_tasks:
            self.new_teacher_tasks.remove(task)

            self.refresh_teacher_tasks()

    def accept_dialog(self) -> None:
        self.session_data = {
            "date": self.date.date().toString(
                "yyyy-MM-dd"
            ),
            "start_time": QTime.currentTime().toString(
                "HH:mm"
            ),
            "end_time": QTime.currentTime().addSecs(
                3600
            ).toString(
                "HH:mm"
            ),
            "topic": self.conversation_topic.toPlainText(),
            "status": "Completed",
            "notes": "",
            "paid": self.student.session_paid_default(),
            "conversation_topic": self.conversation_topic.toPlainText(),
            "grammar_learned": self.grammar_learned.toPlainText(),
            "homework": self.homework.toPlainText(),
            "next_topics": self.next_topics.toPlainText(),
            "homework_done": self.homework_done.isChecked(),
        }

        self.accept()

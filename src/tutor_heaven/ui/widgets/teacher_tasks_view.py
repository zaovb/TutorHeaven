from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import load_students
from tutor_heaven.data.teacher_tasks_storage import (
    load_teacher_tasks,
    save_teacher_tasks,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.teacher_task import TeacherTask


class TeacherTasksView(QWidget):
    """Tab del menú principal con las tareas del profesor.

    Muestra primero las tareas generales (sin estudiante asignado) y
    después las de cada estudiante agrupadas bajo su nombre. Cada tarea
    se puede marcar como completada, lleva una nota editable por
    separado y se puede eliminar. Desde esta pestaña también se añaden
    tareas nuevas (generales o a un estudiante concreto).
    """

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        # Filas de añadir (general arriba y una por grupo de estudiante)
        # y bloques de tareas, dentro de un área desplazable.
        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)

        self.scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        container = QWidget()

        self.container = QVBoxLayout(container)

        self.scroll.setWidget(container)

        layout.addWidget(self.scroll)

        # Mantiene la vista sincronizada: las tareas cambian al
        # guardarlas y los estudiantes al crearlos/suprimirlos.
        get_bus().teacherTasksChanged.connect(
            self.refresh
        )

        get_bus().studentsChanged.connect(
            self.refresh
        )

        self.refresh()

    def refresh(self) -> None:
        """Reconstruye toda la vista: generales + grupos por estudiante."""
        tasks = load_teacher_tasks()
        students = load_students()

        container = self.container

        # Vacía el contenedor (se conserva el "stretch" del final).
        removed = []

        while container.count() > 0:
            item = container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                removed.append(widget)

        for widget in removed:
            widget.deleteLater()

        general = [
            task for task in tasks if not task.student
        ]

        student_tasks: dict[str, list[TeacherTask]] = {}

        for task in tasks:
            if task.student:
                student_tasks.setdefault(
                    task.student,
                    [],
                ).append(task)

        # ---------- Tareas generales ----------
        container.addWidget(
            self._build_group(
                tr("General Tasks"),
                general,
                student_name="",
            )
        )

        # ---------- Tareas agrupadas por estudiante ----------
        for student in students:
            pending = student_tasks.get(
                student.name,
                [],
            )

            if not pending:
                continue

            container.addWidget(
                self._build_group(
                    student.name,
                    pending,
                    student_name=student.name,
                )
            )

        container.addStretch()

    def _build_group(
        self,
        title: str,
        tasks: list[TeacherTask],
        student_name: str,
    ) -> QWidget:
        """Construye un grupo (general o de un estudiante) de tareas."""
        group = QGroupBox(title)

        column = QVBoxLayout(group)

        # Campo para añadir una tarea nueva a este grupo.
        input_edit = QLineEdit()
        input_edit.setPlaceholderText(
            tr("New task...")
        )

        input_edit.returnPressed.connect(
            lambda edit=input_edit, name=student_name:
            self.add_task(edit, name)
        )

        add_button = QPushButton(tr("➕ Add Task"))
        add_button.clicked.connect(
            lambda _, edit=input_edit, name=student_name:
            self.add_task(edit, name)
        )

        add_row = QHBoxLayout()

        add_row.addWidget(input_edit, stretch=1)
        add_row.addWidget(add_button)

        column.addLayout(add_row)

        if not tasks:
            empty = QLabel(
                tr("No teacher tasks yet")
            )

            empty.setStyleSheet(
                "color: gray;"
            )

            column.addWidget(empty)
        else:
            for task in tasks:
                column.addWidget(
                    self._build_task_row(task)
                )

        return group

    def _build_task_row(self, task: TeacherTask) -> QWidget:
        """Construye el bloque de una tarea.

        Una fila con la casilla de completada, el texto de la tarea (que
        se tacha al completarse) y un botón de eliminar, y debajo un
        campo para la nota de esa tarea.
        """
        group = QGroupBox()

        column = QVBoxLayout(group)

        header = QHBoxLayout()

        check = QCheckBox()
        check.setChecked(task.done)

        label = QLabel(task.text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        self._style_label(label, task)

        check.toggled.connect(
            lambda checked, task=task, label=label:
            self.set_task_done(task, checked, label)
        )

        delete_button = QPushButton(tr("🗑 Delete"))
        delete_button.clicked.connect(
            lambda _, task=task: self.delete_task(task)
        )

        header.addWidget(check)
        header.addWidget(label, stretch=1)
        header.addWidget(delete_button)

        column.addLayout(header)

        notes = QLineEdit(task.notes)
        notes.setPlaceholderText(tr("Notes..."))

        notes.editingFinished.connect(
            lambda task=task, edit=notes:
            self.set_task_notes(task, edit.text())
        )

        column.addWidget(notes)

        return group

    @staticmethod
    def _style_label(
        label: QLabel,
        task: TeacherTask,
    ) -> None:
        """Tacha y atenúa la tarea (rich text) cuando está completada."""
        if task.done:
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(
                f"<s>{task.text}</s>"
            )
            label.setStyleSheet("color: gray;")
        else:
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setText(task.text)
            label.setStyleSheet("")

    def add_task(
        self,
        input_edit: QLineEdit,
        student_name: str,
    ) -> None:
        """Añade la tarea escrita al grupo indicado ("" = general)."""
        text = input_edit.text().strip()

        if not text:
            return

        tasks = load_teacher_tasks()

        tasks.append(
            TeacherTask(
                text=text,
                student=student_name,
            )
        )

        input_edit.clear()

        save_teacher_tasks(tasks)

    def set_task_done(
        self,
        task: TeacherTask,
        checked: bool,
        label: QLabel,
    ) -> None:
        """Marca la tarea como completada y la guarda."""
        if checked:
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setText(
                f"<s>{task.text}</s>"
            )
            label.setStyleSheet("color: gray;")
        else:
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setText(task.text)
            label.setStyleSheet("")

        self._update_task(
            task,
            done=checked,
        )

    def set_task_notes(
        self,
        task: TeacherTask,
        notes: str,
    ) -> None:
        """Guarda la nota de una tarea cuando el campo pierde el foco."""
        self._update_task(
            task,
            notes=notes.strip(),
        )

    def delete_task(self, task: TeacherTask) -> None:
        """Elimina la tarea del profesor seleccionada."""
        tasks = load_teacher_tasks()

        for candidate in tasks:
            if self._is_same_task(candidate, task):
                tasks.remove(candidate)
                break
        else:
            return

        save_teacher_tasks(tasks)

    def _update_task(self, task: TeacherTask, **changes) -> None:
        """Aplica cambios a la tarea coincidente y la guarda.

        La tarea recibida puede pertenecer a una recarga anterior
        (objeto ya sustituido), así que se localiza la equivalente
        dentro de la lista recién cargada antes de modificar.
        """
        tasks = load_teacher_tasks()

        for candidate in tasks:
            if self._is_same_task(candidate, task):
                for key, value in changes.items():
                    setattr(candidate, key, value)

                save_teacher_tasks(tasks)

                return

    @staticmethod
    def _is_same_task(a: TeacherTask, b: TeacherTask) -> bool:
        """True si ambas referencias describen la misma tarea."""
        return (
            a.student == b.student
            and a.text == b.text
            and a.created_at == b.created_at
        )
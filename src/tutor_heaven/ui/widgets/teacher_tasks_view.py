from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import load_students
from tutor_heaven.data.teacher_tasks_storage import (
    delete_teacher_task,
    load_deleted_teacher_tasks,
    load_teacher_tasks,
    purge_teacher_task,
    restore_teacher_task,
    same_task,
    save_teacher_tasks,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.teacher_task import TeacherTask


def update_task_in_store(task: TeacherTask, **changes) -> None:
    """Aplica cambios a la tarea coincidente y la guarda.

    La tarea recibida puede pertenecer a una recarga anterior (objeto
    ya sustituido), así que se localiza la equivalente dentro de la
    lista recién cargada antes de modificar. Si la tarea no existe en
    disco (p.ej. aún no confirmada), no hace nada.
    """
    tasks = load_teacher_tasks()

    for candidate in tasks:
        if same_task(candidate, task):
            for key, value in changes.items():
                setattr(candidate, key, value)

            save_teacher_tasks(tasks)

            return


def delete_task_from_store(task: TeacherTask) -> None:
    """Mueve la tarea del profesor a la papelera (no definitivo).

    Queda disponible en el portal de "Tareas eliminadas" hasta que se
    restaure o se borre definitivamente.
    """
    delete_teacher_task(task)


def restore_task_from_store(task: TeacherTask) -> None:
    """Devuelve una tarea eliminada a la lista activa."""
    restore_teacher_task(task)


def purge_task_from_store(task: TeacherTask) -> None:
    """Elimina para siempre una tarea de la papelera del profesor."""
    purge_teacher_task(task)


def style_task_label(
    label: QLabel,
    text: str,
    done: bool,
) -> None:
    """Tacha y atenúa el texto de la tarea cuando está completada."""
    if done:
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(
            f"<s>{text}</s>"
        )
        label.setStyleSheet("color: gray;")
    else:
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setText(text)
        label.setStyleSheet("")


def build_task_row(
    task: TeacherTask,
    on_done=None,
    on_notes=None,
    on_delete=None,
    on_restore=None,
    on_purge=None,
    deleted: bool = False,
) -> QWidget:
    """Construye el bloque de una tarea del profesor.

    Una fila con la casilla de completada, el texto de la tarea (que se
    tacha al completarse) y un botón de eliminar, y debajo un campo
    para la nota de esa tarea. Los callbacks opcionales permiten
    personalizar qué ocurre al marcar, escribir nota o eliminar.

    - on_done(task, checked): por defecto persiste el estado del
      registro global (update_task_in_store).
    - on_notes(task, text): por defecto persiste la nota igualmente.
    - on_delete(task): por defecto mueve la tarea a la papelera.
    - deleted=True: fila de la papelera. Se muestra el texto tachado y
      botones de restaurar/borrar definitivamente en lugar de la casilla
      de completada, la nota editable y el botón de eliminar.
    - on_restore(task) / on_purge(task): acciones de la papelera (por
      defecto restauran o borran definitivamente del registro global).
    """
    if on_done is None:
        on_done = lambda task, checked: update_task_in_store(
            task,
            done=checked,
        )

    if on_notes is None:
        on_notes = lambda task, text: update_task_in_store(
            task,
            notes=text.strip(),
        )

    if on_delete is None:
        on_delete = delete_task_from_store

    if on_restore is None:
        on_restore = restore_task_from_store

    if on_purge is None:
        on_purge = purge_task_from_store

    group = QGroupBox()

    column = QVBoxLayout(group)

    header = QHBoxLayout()

    label = QLabel(task.text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
        | Qt.TextInteractionFlag.TextSelectableByKeyboard
    )

    if deleted:
        # Fila de la papelera: texto tachado, sin casilla ni nota
        # editable, y acciones de restaurar / borrar definitivamente.
        label.setStyleSheet("color: gray;")

        restore_button = QPushButton(tr("↩ Restore Task"))
        restore_button.clicked.connect(
            lambda _, task=task: on_restore(task)
        )

        purge_button = QPushButton(tr("🗑 Delete Forever"))
        purge_button.setObjectName("danger")
        purge_button.clicked.connect(
            lambda _, task=task: on_purge(task)
        )

        header.addWidget(label, stretch=1)
        header.addWidget(restore_button)
        header.addWidget(purge_button)

        column.addLayout(header)

        return group

    check = QCheckBox()
    check.setChecked(task.done)

    style_task_label(label, task.text, task.done)

    def apply_done(checked: bool) -> None:
        style_task_label(label, task.text, checked)
        on_done(task, checked)

    check.toggled.connect(apply_done)

    delete_button = QPushButton(tr("🗑 Delete"))
    delete_button.clicked.connect(
        lambda _, task=task: on_delete(task)
    )

    header.addWidget(check)
    header.addWidget(label, stretch=1)
    header.addWidget(delete_button)

    column.addLayout(header)

    notes = QLineEdit(task.notes)
    notes.setPlaceholderText(tr("Notes..."))

    notes.editingFinished.connect(
        lambda task=task, edit=notes: on_notes(task, edit.text())
    )

    column.addWidget(notes)

    return group


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

        # Botón que alterna entre tareas activas y eliminadas (papelera).
        # En la papelera las tareas solo se restauran o se borran
        # definitivamente.
        self.showing_deleted = False

        self.deleted_toggle = QPushButton(
            tr("🗑 Deleted Tasks")
        )

        self.deleted_toggle.clicked.connect(
            self.toggle_deleted
        )

        layout.addWidget(
            self.deleted_toggle,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        # Bloques de tareas, dentro de un área desplazable.
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

    def toggle_deleted(self) -> None:
        """Alterna la vista entre tareas activas y eliminadas."""
        self.showing_deleted = not self.showing_deleted

        self.deleted_toggle.setText(
            tr("↩ Active Tasks")
            if self.showing_deleted
            else tr("🗑 Deleted Tasks")
        )

        self.refresh()

    def refresh(self) -> None:
        """Reconstruye toda la vista: generales + grupos por estudiante."""
        # En la papelera se muestran las tareas eliminadas (con acciones
        # de restaurar / borrar definitivamente) en lugar de las activas.
        if self.showing_deleted:
            tasks = load_deleted_teacher_tasks()
        else:
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

        # En la papelera no se pueden añadir tareas nuevas: solo se
        # restauran o se borran definitivamente.
        if not self.showing_deleted:
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
                    build_task_row(
                        task,
                        deleted=self.showing_deleted,
                    )
                )

        return group

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
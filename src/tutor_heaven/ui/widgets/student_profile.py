from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import (
    delete_student,
    load_students,
    save_students,
)
from tutor_heaven.data.teacher_tasks_storage import (
    load_teacher_tasks,
    save_teacher_tasks,
)
from tutor_heaven.i18n import tr
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student
from tutor_heaven.models.teacher_task import TeacherTask
from tutor_heaven.ui.widgets.teacher_tasks_view import (
    build_task_row,
    delete_task_from_store,
)
from tutor_heaven.ui.widgets.package_dialog import PackageDialog
from tutor_heaven.ui.widgets.resume_dialog import ResumeDialog
from tutor_heaven.ui.widgets.session_edit_dialog import SessionEditDialog
from tutor_heaven.ui.widgets.session_progress_dialog import (
    SessionProgressDialog,
)
from tutor_heaven.ui.widgets.student_edit_dialog import StudentEditDialog


class StudentProfile(QWidget):
    """Student profile.

    Vista detallada de un estudiante organizada en pestañas:
    - "Enrollment": información de la matrícula y del pago.
    - "Sessions": registro de sesiones (consumen clases del paquete
      y cada clase puede marcarse como pagada).
    - "Packages": añadir más clases al paquete (devuelve al estudiante
      a activos automáticamente).
    - "Tasks": tareas del profesor de este estudiante (marcables como
      completadas, con nota editable por tarea). Las tareas se añaden
      desde el diálogo de "Nueva clase vista" o desde aquí mismo.
    Las pestañas restantes son marcadores de posición.
    """

    # Emitida cuando el estudiante se elimina, para que el navegador
    # vuelva al panel por defecto.
    studentDeleted = Signal()

    def __init__(
        self,
        student: Student,
        students: list[Student],
    ) -> None:
        super().__init__()

        # Referencias al estudiante y a la lista compartida de todos los
        # estudiantes. Al guardar se guarda la lista completa para que
        # el archivo JSON no pierda los demás registros.
        self.student = student
        self.students = students

        # Referencia a la tabla de sesiones, rellenada tras crearla.
        self.sessions_table: QTableWidget | None = None

        layout = QVBoxLayout(self)

        # Botones superiores: hoja de vida, editar y eliminar estudiante.
        top_buttons = QHBoxLayout()

        self.resume_button = QPushButton(
            tr("📋 Resume")
        )

        self.resume_button.clicked.connect(
            self.open_resume
        )

        # Botón para editar la información del estudiante (nombre,
        # email, teléfono, nivel, temas gramaticales, notas...).
        self.edit_button = QPushButton(tr("✏️ Edit"))

        self.edit_button.clicked.connect(
            self.edit_student
        )

        # Botón para eliminar al estudiante de la aplicación.
        self.delete_button = QPushButton(tr("🗑 Delete"))

        self.delete_button.setObjectName("danger")

        self.delete_button.clicked.connect(
            self.delete_student
        )

        # Botón para marcar/desmarcar al estudiante como antiguo.
        # Permite forzar manualmente la categoría del dashboard aunque
        # los datos aún no la deduzcan (ej. antiguo con clases por ver).
        self.toggle_former_button = QPushButton()

        self.toggle_former_button.clicked.connect(
            self.toggle_former
        )

        top_buttons.addWidget(self.resume_button)
        top_buttons.addWidget(self.edit_button)
        top_buttons.addWidget(self.toggle_former_button)
        top_buttons.addStretch()
        top_buttons.addWidget(self.delete_button)

        layout.addLayout(top_buttons)

        tabs = QTabWidget()

        tabs.addTab(
            self.create_enrollment_tab(),
            tr("Enrollment"),
        )

        tabs.addTab(
            self.create_sessions_tab(),
            tr("Sessions"),
        )

        tabs.addTab(
            self.create_packages_tab(),
            tr("Packages"),
        )

        # Tareas del profesor de este estudiante. Ahí llegan las que se
        # añaden desde el diálogo de "Nueva clase vista" y las añadidas
        # directamente aquí.
        tabs.addTab(
            self.create_tasks_tab(),
            tr("Tasks"),
        )

        tabs.addTab(
            self.create_placeholder_tab(tr("Files")),
            tr("Files"),
        )

        tabs.addTab(
            self.create_placeholder_tab(tr("Statistics")),
            tr("Statistics"),
        )

        self.tabs = tabs

        # Al entrar en la pestaña de sesiones se refresca la tabla para
        # reflejar los últimos datos.
        self.tabs.currentChanged.connect(
            self.on_tab_changed
        )

        layout.addWidget(tabs)

        # Mantiene el perfil sincronizado con los datos guardados desde
        # cualquier otra vista (dashboard, otro perfil...).
        get_bus().studentsChanged.connect(
            self._on_students_changed
        )

        # Las tareas del profesor cambian en el diálogo de clase, la
        # pestaña del menú principal o en otros perfiles; se refrescan.
        get_bus().teacherTasksChanged.connect(
            self.refresh_tasks_tab
        )

        self.refresh_former_button()

    def set_student(
        self,
        student: Student,
        students: list[Student],
    ) -> None:
        """Cambia el estudiante mostrado conservando la pestaña actual.

        Reutiliza el mismo widget (y por tanto la misma pestaña
        seleccionada del QTabWidget) cuando el usuario hace clic en otro
        estudiante de la lista.
        """
        self.student = student
        self.students = students

        self._on_students_changed()

    def showEvent(self, event) -> None:
        """Al mostrarse recarga al estudiante por si cambió en disco."""
        super().showEvent(event)

        self._on_students_changed()

    def reload_from_disk(self) -> bool:
        """Sustituye el estudiante mostrado por el guardado en disco.

        Devuelve True si el estudiante sigue existiendo (y se actualizó
        la referencia). Si ya no existe (fue eliminado) devuelve False.
        """
        if self.student is None:
            return False

        fresh = load_students()

        for candidate in fresh:
            if candidate.name == self.student.name:
                self.student = candidate
                self.students = fresh

                return True

        return False

    def _on_students_changed(self) -> None:
        """Recarga los datos del estudiante y refresca todas las pestañas."""
        if not self.reload_from_disk():
            return

        if hasattr(self, "sessions_table"):
            self.refresh_sessions_table()
            self.refresh_packages_tab()
            self.refresh_enrollment_tab()
            self.refresh_tasks_tab()
            self.refresh_former_button()

    def create_label(
        self,
        text: str,
    ) -> QLabel:
        """Crea una etiqueta cuyo texto se puede copiar con el ratón."""
        label = QLabel(text)

        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        return label

    def create_placeholder_tab(
        self,
        title: str,
    ) -> QWidget:
        """Crea una pestaña provisional hasta implementar el módulo."""
        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            self.create_label(
                f"{title} module"
            )
        )

        layout.addStretch()

        return widget

    def open_resume(self) -> None:
        """Abre la hoja de vida del estudiante (editable)."""
        dialog = ResumeDialog(
            self.student,
            self.students,
        )
        dialog.exec()

    def edit_student(self) -> None:
        """Abre el diálogo para editar la información del estudiante.

        Tras editar, el diálogo pide confirmación antes de aplicar los
        cambios. Al guardar se refrescan la pestaña de matrícula y el
        botón de antiguo (por si cambió el estado).
        """
        dialog = StudentEditDialog(
            self.student,
            self.students,
        )

        if not dialog.exec():
            return

        self.refresh_enrollment_tab()
        self.refresh_former_button()

    def delete_student(self) -> None:
        """Mueve al estudiante a la papelera (eliminación no definitiva).

        La advertencia explica que el estudiante pasa a la lista de
        "Eliminados" y que se puede restaurar. Solo se elimina si el
        usuario confirma. Para borrarlo sin vuelta atrás hay que usar el
        portal de "Eliminados".
        """
        confirm = QMessageBox.question(
            self,
            tr("Delete student"),
            tr(
                "Move {0} to deleted students?\n\n"
                "You can restore them later from the Deleted list."
            ).format(
                self.student.name
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        delete_student(
            self.student
        )

        self.studentDeleted.emit()

    def toggle_former(self) -> None:
        """Marca/desmarca manualmente al estudiante como antiguo.

        La marca queda siempre en oposición a la categoría real: si el
        estudiante es antiguo (por marca manual o por deducción
        automática) se desmarca (force_active); si es activo se marca
        (marked_former). Así el botón siempre ofrece la acción contraria
        a su estado actual y las dos marcas son excluyentes. El
        dashboard reparte al estudiante según su categoría usando estas
        marcas junto con la deducción automática de los datos.
        """
        if self.student.is_former:
            self.student.force_active = True
            self.student.marked_former = False
        else:
            self.student.force_active = False
            self.student.marked_former = True

        save_students(
            self.students
        )

        self.refresh_former_button()
        self.refresh_packages_tab()

    def refresh_former_button(self) -> None:
        """Actualiza el texto del botón según la categoría real.

        Si el estudiante ya es antiguo (por marca manual o por deducción
        automática de los datos) el botón ofrece desmarcarlo; solo tiene
        sentido "Mark as former" cuando el estudiante es activo.
        """
        if self.student.is_former:
            self.toggle_former_button.setText(
                tr("↩ Unmark as former")
            )
        else:
            self.toggle_former_button.setText(
                tr("📦 Mark as former")
            )

    def sort_sessions(self) -> None:
        """Ordena las sesiones del estudiante por fecha de inicio."""
        self.student.sessions.sort(
            key=lambda session: session.start_datetime
        )

    def give_class(self) -> None:
        """Marca una clase como vista: abre el diálogo de progreso.

        Al confirmar se crea una sesión "Completed" y se consume una
        clase del paquete (classes_taken += 1). Si no quedan clases
        disponibles, la clase se registra igualmente y queda como
        "clase por pagar" (el estudiante debe esa clase).
        """
        dialog = SessionProgressDialog(
            self.student
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
            conversation_topic=data["conversation_topic"],
            grammar_learned=data["grammar_learned"],
            homework=data["homework"],
            next_topics=data["next_topics"],
            homework_done=data["homework_done"],
        )

        self.student.sessions.append(
            session
        )

        # Al completar una clase se consume una del paquete.
        self.student.consume_class()

        # Acumula los intereses nuevos en el estudiante.
        for interest in dialog.new_interests:
            if interest not in self.student.interests:
                self.student.interests.append(
                    interest
                )

        # Acumula las nuevas tareas del profesor en el registro global.
        new_tasks = load_teacher_tasks()

        new_tasks.extend(
            dialog.new_teacher_tasks
        )

        save_teacher_tasks(
            new_tasks
        )

        self.sort_sessions()

        save_students(
            self.students
        )

        self.refresh_sessions_table()
        self.refresh_packages_tab()
        self.refresh_enrollment_tab()

    def _classes_left_text(self) -> str:
        """Texto de clases restantes: disponibles o por pagar."""
        if self.student.classes_left >= 0:
            return (
                f"{self.student.classes_left} "
                f"{tr('classes available')}"
            )

        return (
            f"{-self.student.classes_left} "
            f"{tr('classes owed')}"
        )

    @staticmethod
    def package_event_date(package) -> datetime | None:
        """Fecha en que se compró el paquete, o None si no se sabe.

        Usa la fecha de pago y, si no está, la de inicio del paquete.
        Con ella se coloca la división temporal en la tabla de sesiones.
        """
        for value in (
            package.date_of_payment,
            package.date_of_start,
        ):
            if not value:
                continue

            try:
                return datetime.strptime(
                    value[:10],
                    "%Y-%m-%d",
                )
            except ValueError:
                continue

        return None

    def refresh_sessions_table(self) -> None:
        """Vuelve a pintar la tabla de sesiones con los datos actuales."""
        # Actualiza el panel de clases disponibles.
        self.classes_left_label.setText(
            self._classes_left_text()
        )

        # En deuda, el texto se resalta en rojo.
        self.classes_left_label.setStyleSheet(
            "font-weight: bold; color: #C62828;"
            if self.student.classes_left < 0
            else "font-weight: bold;"
        )

        next_session = self.student.next_session

        self.next_class_label.setText(
            tr("Next class: {0} {1}").format(
                next_session.date,
                next_session.start_time,
            )
            if next_session is not None
            else tr("No upcoming scheduled class")
        )

        if self.sessions_table is None:
            return

        self.sort_sessions()

        table = self.sessions_table

        # Se limpian los "spans" de filas divisoria anteriores antes de
        # repintar (la tabla cambia de número de filas en cada refresco).
        table.clearSpans()
        table.setRowCount(0)

        self.divider_rows: set[int] = set()
        self.session_row_map: dict[int, Session] = {}

        # Vista de papelera: se muestran solo las sesiones eliminadas,
        # ordenadas de más reciente a más antigua, sin divisiones.
        if self.showing_deleted_sessions:
            deleted = sorted(
                self.student.deleted_sessions,
                key=lambda session: session.start_datetime,
                reverse=True,
            )

            table.setRowCount(
                len(deleted)
            )

            for row, session in enumerate(deleted):
                self.session_row_map[row] = session

                values = [
                    session.date,
                    session.start_time,
                    session.end_time,
                    session.topic,
                    tr(session.status),
                    tr("Paid")
                    if session.paid
                    else tr("Not paid"),
                    session.notes,
                ]

                for column, column_value in enumerate(values):
                    table.setItem(
                        row,
                        column,
                        QTableWidgetItem(column_value),
                    )

            table.resizeColumnsToContents()

            return

        # La tabla intercala las sesiones con "divisiones temporales":
        # una fila "Paquete comprado" por cada paquete comprado, en la
        # posición cronológica que le corresponde. Se rehace a cada
        # refresco, así que refleja lo que se añade en la pestaña de
        # paquetes automáticamente.
        dividers = []

        for package in self.student.packages:
            date = self.package_event_date(package)

            if date is not None:
                dividers.append(date)

        dividers.sort()

        # Filas resultantes: ("session", sesión) o ("divider", fecha).
        rows = []
        session_index = 0
        seen_dates = []

        for date in dividers:
            while (
                session_index < len(self.student.sessions)
                and self.student.sessions[session_index].start_datetime < date
            ):
                session = self.student.sessions[session_index]
                rows.append(("session", session))
                session_index += 1

            # Varios paquetes en la misma fecha se colapsan en una sola
            # fila divisoria.
            if date not in seen_dates:
                seen_dates.append(date)
                rows.append(("divider", date))

        while session_index < len(self.student.sessions):
            session = self.student.sessions[session_index]
            rows.append(("session", session))
            session_index += 1

        table.setRowCount(
            len(rows)
        )

        for row, (kind, value) in enumerate(rows):
            if kind == "divider":
                self.divider_rows.add(row)

                item = QTableWidgetItem(
                    f"{tr('📦 Package Purchased')} — "
                    f"{value.strftime('%Y-%m-%d')}"
                )

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                item.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                )

                table.setSpan(row, 0, 1, table.columnCount())
                table.setItem(row, 0, item)

                continue

            session = value

            self.session_row_map[row] = session

            values = [
                session.date,
                session.start_time,
                session.end_time,
                session.topic,
                tr(session.status),
                tr("Paid") if self.student.session_is_paid(session) else tr("Not paid"),
                session.notes,
            ]

            for column, column_value in enumerate(values):
                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(column_value),
                )

        table.resizeColumnsToContents()

    def show_session_detail(
        self,
        row: int,
        column: int,
    ) -> None:
        """Muestra el detalle de progreso de la sesión al hacer doble clic."""
        del column

        # Las filas divisorias ("Paquete comprado") no abren detalle.
        if (
            hasattr(self, "divider_rows")
            and row in self.divider_rows
        ):
            return

        if not hasattr(self, "session_row_map"):
            return

        session = self.session_row_map.get(row)

        if session is None:
            return

        QMessageBox.information(
            self,
            tr("Session Detail"),
            (
                f"{tr('Date')}: {session.date}\n"
                f"{tr('Time')}: {session.start_time} - {session.end_time}\n"
                f"{tr('Status')}: {tr(session.status)}\n"
                f"{tr('Paid')}: "
                f"{tr('Yes') if self.student.session_is_paid(session) else tr('No')}\n"
                f"{tr('Homework Done')}: "
                f"{tr('Yes') if session.homework_done else tr('No')}\n\n"
                f"{tr('Conversation Topic')}:\n"
                f"{session.conversation_topic or '-'}\n\n"
                f"{tr('Grammar Learned')}:\n"
                f"{session.grammar_learned or '-'}\n\n"
                f"{tr('Homework')}:\n"
                f"{session.homework or '-'}\n\n"
                f"{tr('To Learn Next')}:\n"
                f"{session.next_topics or '-'}\n\n"
                f"{tr('Notes')}:\n"
                f"{session.notes or '-'}"
            ),
        )

    def add_classes(self) -> None:
        """Abre el diálogo de paquete para añadir más clases.

        Al añadir un nuevo paquete el estudiante vuelve a quedar activo
        automáticamente (is_active = True). El descuento se calcula
        automáticamente según las reglas de la configuración.
        """
        dialog = PackageDialog(
            current_price=self.student.hourly_price,
            student_type=self.student.student_type,
        )

        if not dialog.exec():
            return

        data = dialog.package_data

        if data is None:
            return

        # El tipo elegido en el bloque pasa a ser el tipo vigente del
        # estudiante (privado/grupo/custom).
        self.student.student_type = data["student_type"]

        # Registra el nuevo paquete en el historial y actualiza el
        # precio por hora y el modo de pago vigentes.
        self.student.add_package(
            classes=data["classes"],
            hourly_price=data["hourly_price"],
            discount_percent=data["discount"],
            payment_mode=data["payment_mode"],
            payment_status=data["payment_status"],
            date_of_payment=data["date_of_payment"],
            date_of_start=data["date_of_start"],
        )

        # Las sesiones se pagan automáticamente cuando se añade un
        # paquete pagado por adelantado.
        if (
            data["payment_mode"] == "Pay in advance"
            and data["payment_status"] == "Paid"
        ):
            self.student.mark_sessions_paid(data["classes"])

        save_students(
            self.students
        )

        # Refresca las etiquetas que dependen del paquete: clases
        # disponibles, total y estado (activo/antiguo).
        self.refresh_sessions_table()
        self.refresh_packages_tab()
        self.refresh_enrollment_tab()

    def edit_package(self, package) -> None:
        """Edita un paquete del historial para corregir datos.

        Abre el diálogo de paquete en modo edición con los valores
        actuales. Al confirmar actualiza el bloque (clases compradas,
        precio, descuento, pago y fechas). Si se edita el paquete más
        reciente, se sincronizan también el precio y el modo de pago
        vigentes del estudiante.
        """
        dialog = PackageDialog(
            current_price=package.hourly_price,
            student_type=self.student.student_type,
            package=package,
        )

        if not dialog.exec():
            return

        data = dialog.package_data

        if data is None:
            return

        self.student.student_type = data["student_type"]

        package.classes_purchased = data["classes"]
        package.hourly_price = data["hourly_price"]
        package.discount_percent = data["discount"]
        package.payment_mode = data["payment_mode"]
        package.payment_status = data["payment_status"]
        package.date_of_payment = data["date_of_payment"]
        package.date_of_start = data["date_of_start"]

        # Si el paquete se marca como pagado, las clases vistas sin
        # pagar que cubre pasan a pagarse automáticamente.
        if (
            data["payment_mode"] == "Pay in advance"
            and data["payment_status"] == "Paid"
        ):
            self.student.mark_sessions_paid(package.classes_purchased)

        # Si es el paquete vigente, el estudiante hereda sus valores.
        if package is self.student.packages[-1]:
            self.student.hourly_price = package.hourly_price
            self.student.payment_mode = package.payment_mode
            self.student.payment_status = package.payment_status

        save_students(
            self.students
        )

        self.refresh_sessions_table()
        self.refresh_packages_tab()
        self.refresh_enrollment_tab()

    def on_tab_changed(self, index: int) -> None:
        """Refresca la tabla al entrar en Sessions."""
        if (
            hasattr(self, "sessions_tab")
            and self.tabs.widget(index) is self.sessions_tab
        ):
            self.refresh_sessions_table()

        if (
            hasattr(self, "tasks_tab")
            and self.tabs.widget(index) is self.tasks_tab
        ):
            self.refresh_tasks_tab()

    def create_sessions_tab(self) -> QWidget:
        """Construye la pestaña de sesiones.

        Contiene un panel con las clases disponibles y la próxima clase,
        el botón para dar una clase como vista y la tabla del histórico
        de sesiones.
        """
        sessions = QWidget()

        self.sessions_tab = sessions

        layout = QVBoxLayout(sessions)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        # ---------- Barra compacta de clases ----------

        # Una sola fila con la información esencial (clases disponibles
        # y próxima clase) a la izquierda y las acciones a la derecha.
        info_row = QHBoxLayout()
        info_row.setSpacing(12)

        self.classes_left_label = QLabel()
        self.classes_left_label.setStyleSheet(
            "font-weight: bold;"
        )

        self.next_class_label = QLabel()

        info_row.addWidget(self.classes_left_label)
        info_row.addWidget(self.next_class_label)
        info_row.addStretch()

        # Botón principal del tutor: marcar la clase como vista.
        give_button = QPushButton(
            tr("✅ Mark Class as Viewed")
        )

        give_button.setObjectName("primary")

        give_button.setToolTip(
            tr(
                "Mark a class as done: records progress and "
                "consumes one class from the package."
            )
        )

        give_button.clicked.connect(
            self.give_class
        )

        info_row.addWidget(give_button)

        layout.addLayout(info_row)

        # ---------- Acciones de sesión ----------

        # Fila con acciones sobre la sesión seleccionada: editar,
        # eliminar (a la papelera) y alternar la vista de sesiones
        # eliminadas (restaurar / borrar definitivamente).
        self.showing_deleted_sessions = False

        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        self.edit_session_button = QPushButton(
            tr("✏️ Edit Session")
        )
        self.edit_session_button.clicked.connect(
            self.edit_selected_session
        )

        self.delete_session_button = QPushButton(
            tr("🗑 Delete Session")
        )
        self.delete_session_button.clicked.connect(
            self.delete_selected_session
        )

        # Botón que alterna entre sesiones activas y eliminadas.
        self.deleted_sessions_toggle = QPushButton(
            tr("🗑 Deleted Sessions")
        )
        self.deleted_sessions_toggle.clicked.connect(
            self.toggle_deleted_sessions
        )

        # Acciones de la papelera de sesiones (solo visibles ahí).
        self.restore_session_button = QPushButton(
            tr("↩ Restore Session")
        )
        self.restore_session_button.clicked.connect(
            self.restore_selected_session
        )

        self.purge_session_button = QPushButton(
            tr("🗑 Delete Forever")
        )
        self.purge_session_button.setObjectName("danger")
        self.purge_session_button.clicked.connect(
            self.purge_selected_session
        )

        actions_row.addWidget(self.edit_session_button)
        actions_row.addWidget(self.delete_session_button)
        actions_row.addWidget(self.restore_session_button)
        actions_row.addWidget(self.purge_session_button)
        actions_row.addStretch()
        actions_row.addWidget(self.deleted_sessions_toggle)

        # Vista inicial: sesiones activas (oculta las acciones de papelera).
        self.restore_session_button.setVisible(False)
        self.purge_session_button.setVisible(False)

        layout.addLayout(actions_row)

        # ---------- Tabla de sesiones ----------

        table = QTableWidget()

        # Se guarda como atributo para poder refrescarla después.
        self.sessions_table = table

        table.setColumnCount(7)

        table.setHorizontalHeaderLabels(
            [
                tr("Date"),
                tr("Start"),
                tr("End"),
                tr("Topic"),
                tr("Status"),
                tr("Paid"),
                tr("Notes"),
            ]
        )

        # Solo lectura: las sesiones se crean o editan con diálogos.
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # Las sesiones ya llegan ordenadas (sort_sessions), así que no
        # se habilita el ordenado por columnas para no romper el orden.
        table.setSortingEnabled(False)

        table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        table.horizontalHeader().setStretchLastSection(
            True
        )

        # Doble clic en una sesión muestra su detalle de progreso.
        table.cellDoubleClicked.connect(
            self.show_session_detail
        )

        self.refresh_sessions_table()

        layout.addWidget(
            table,
            stretch=1,
        )

        return sessions

    def toggle_deleted_sessions(self) -> None:
        """Alterna la tabla entre sesiones activas y eliminadas."""
        self.showing_deleted_sessions = (
            not self.showing_deleted_sessions
        )

        # En la vista de papelera se ocultan las acciones de activas y
        # se muestran las de restaurar / borrar definitivamente.
        self.edit_session_button.setVisible(
            not self.showing_deleted_sessions
        )
        self.delete_session_button.setVisible(
            not self.showing_deleted_sessions
        )
        self.restore_session_button.setVisible(
            self.showing_deleted_sessions
        )
        self.purge_session_button.setVisible(
            self.showing_deleted_sessions
        )

        self.deleted_sessions_toggle.setText(
            tr("↩ Active Sessions")
            if self.showing_deleted_sessions
            else tr("🗑 Deleted Sessions")
        )

        self.sessions_table.clearSelection()

        self.refresh_sessions_table()

    def selected_session(self) -> Session | None:
        """Devuelve la sesión de la fila seleccionada, o None."""
        row = self.sessions_table.currentRow()

        if row < 0:
            return None

        return self.session_row_map.get(row)

    def edit_selected_session(self) -> None:
        """Abre el diálogo de edición de la sesión seleccionada."""
        session = self.selected_session()

        if session is None:
            QMessageBox.information(
                self,
                tr("Edit Session"),
                tr("Select a session to edit first."),
            )

            return

        dialog = SessionEditDialog(
            self.student,
            session,
        )

        if not dialog.exec():
            return

        # Si el estado cambió entre "Completed" y otro, se ajusta la
        # clase consumida del paquete para mantener los conteos.
        now_completed = session.status == "Completed"

        if dialog.was_completed and not now_completed:
            self.student.release_class()
        elif not dialog.was_completed and now_completed:
            self.student.consume_class()

        self._save_and_refresh_sessions()

    def delete_selected_session(self) -> None:
        """Mueve la sesión seleccionada a la papelera (no definitivo)."""
        session = self.selected_session()

        if session is None:
            QMessageBox.information(
                self,
                tr("Delete session"),
                tr("Select a session to delete first."),
            )

            return

        self.student.delete_session(session)

        self._save_and_refresh_sessions()

    def restore_selected_session(self) -> None:
        """Devuelve la sesión seleccionada de la papelera a la lista."""
        session = self.selected_session()

        if session is None:
            QMessageBox.information(
                self,
                tr("Restore session"),
                tr("Select a session to restore first."),
            )

            return

        self.student.restore_session(session)

        self._save_and_refresh_sessions()

    def purge_selected_session(self) -> None:
        """Borra definitivamente la sesión seleccionada de la papelera."""
        session = self.selected_session()

        if session is None:
            QMessageBox.information(
                self,
                tr("Delete session"),
                tr("Select a session to delete first."),
            )

            return

        confirm = QMessageBox.warning(
            self,
            tr("Delete session forever"),
            tr(
                "Delete session {0} {1} forever?\n\n"
                "This session and its progress will be permanently "
                "removed. This action cannot be undone."
            ).format(
                session.date,
                session.start_time,
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.student.purge_session(session)

        self._save_and_refresh_sessions()

    def _save_and_refresh_sessions(self) -> None:
        """Guarda los cambios y repinta todo lo que depende de sesiones."""
        save_students(
            self.students
        )

        self.refresh_sessions_table()
        self.refresh_packages_tab()
        self.refresh_enrollment_tab()

    def create_packages_tab(self) -> QWidget:
        """Construye la pestaña de paquetes con historial de compras.

        Muestra un resumen del paquete acumulado y debajo la lista de
        paquetes comprados (el más reciente arriba), con el detalle de
        cada uno: clases, fechas, descuento, precio y estado.
        """
        packages = QWidget()

        layout = QVBoxLayout(packages)

        # Botón para añadir más clases al paquete actual.
        add_button = QPushButton(
            tr("➕ Add Classes to Package")
        )

        add_button.setObjectName("primary")

        add_button.clicked.connect(
            self.add_classes
        )

        # ---------- Resumen acumulado ----------

        summary_group = QGroupBox(
            tr("Package Summary")
        )

        summary_form = QFormLayout()

        # Guarda el formulario para ocultar/mostrar la deuda dinámicamente.
        self.package_summary_form = summary_form

        self.package_classes_purchased = self.create_label("")
        self.package_classes_taken = self.create_label("")
        self.package_classes_left = self.create_label("")
        self.package_total_paid = self.create_label("")
        self.package_total = self.create_label("")
        self.package_status = self.create_label("")

        summary_form.addRow(
            tr("Classes Purchased"),
            self.package_classes_purchased,
        )

        summary_form.addRow(
            tr("Classes Taken"),
            self.package_classes_taken,
        )

        summary_form.addRow(
            tr("Classes Left"),
            self.package_classes_left,
        )

        summary_form.addRow(
            tr("Total Paid"),
            self.package_total_paid,
        )

        summary_form.addRow(
            tr("Debt"),
            self.package_total,
        )

        summary_form.addRow(
            tr("Status"),
            self.package_status,
        )

        summary_group.setLayout(summary_form)

        # ---------- Historial de paquetes ----------

        history_label = QLabel(
            tr("Package History")
        )

        history_label.setStyleSheet(
            "font-size: 14px; font-weight: bold;"
        )

        # El historial va dentro de un área desplazable para que añadir
        # muchos paquetes no agrande la ventana (aparece un scroll).
        self.package_history_scroll = QScrollArea()

        self.package_history_scroll.setWidgetResizable(True)

        self.package_history_scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        history_widget = QWidget()

        # Contenedor donde se insertan los bloques de cada paquete.
        # Se vacía y reconstruye en cada refresco.
        self.package_history_container = QVBoxLayout(history_widget)

        self.package_history_container.addStretch()

        self.package_history_scroll.setWidget(
            history_widget
        )

        layout.addWidget(
            add_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        layout.addWidget(
            summary_group,
        )

        layout.addWidget(
            history_label,
        )

        layout.addWidget(
            self.package_history_scroll,
            stretch=1,
        )

        self.refresh_packages_tab()

        return packages

    def refresh_packages_tab(self) -> None:
        """Actualiza el resumen acumulado y reconstruye el historial."""
        self.package_classes_purchased.setText(
            str(self.student.classes_purchased)
        )

        self.package_classes_taken.setText(
            str(self.student.classes_taken)
        )

        self.package_classes_left.setText(
            self._classes_left_text()
        )

        self.package_classes_left.setStyleSheet(
            "color: #C62828; font-weight: bold;"
            if self.student.classes_left < 0
            else ""
        )

        self.package_total_paid.setText(
            f"$ {self.student.total_paid:.2f}"
        )

        owed = self.student.amount_owed

        self.package_total.setText(
            f"$ {owed:.2f}"
        )

        self.package_total.setStyleSheet(
            "color: #C62828; font-weight: bold;"
            if owed > 0
            else ""
        )

        # La deuda solo se muestra cuando el estudiante debe algo.
        debt_row, _ = self.package_summary_form.getWidgetPosition(
            self.package_total
        )

        self.package_summary_form.setRowVisible(
            debt_row,
            owed > 0,
        )

        self.package_status.setText(
            tr("Active")
            if self.student.is_active
            else tr("Former")
        )

        self.rebuild_package_history()

    def rebuild_package_history(self) -> None:
        """Reconstruye la lista de paquetes comprados.

        El paquete más reciente se muestra como "Current Package" y el
        resto como "Previous Package 1", "Previous Package 2", etc.
        (numerados de más reciente a más antiguo). Cada paquete
        terminado muestra un distintivo "TERMINADO" y, si se consumieron
        más clases de las compradas, la deuda ("clases por pagar").
        """
        container = self.package_history_container

        # Vacía el contenedor quitando los widgets (se conserva el
        # "stretch" del final para apilar los bloques desde arriba).
        removed = []

        while container.count() > 0:
            item = container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                removed.append(widget)

        for widget in removed:
            widget.deleteLater()

        packages = list(
            reversed(self.student.packages)
        )

        for index, package in enumerate(packages):
            title = (
                tr("Current Package")
                if index == 0
                else tr("Previous Package {0}").format(index)
            )

            group = QGroupBox(title)

            group_layout = QVBoxLayout(group)

            # Cabecera: distintivo "TERMINADO" (cuando aplica) y botón
            # para editar el paquete en caso de equivocaciones.
            header = QHBoxLayout()

            edit_button = QPushButton(
                tr("✏️ Edit Package")
            )

            edit_button.clicked.connect(
                lambda _, package=package: self.edit_package(package)
            )

            header.addWidget(edit_button)
            header.addStretch()

            if package.classes_left <= 0:
                badge = QLabel(tr("Finished"))
                badge.setStyleSheet(
                    "color: white; background-color: #C62828; "
                    "font-weight: bold; padding: 3px 8px; "
                    "border-radius: 8px;"
                )

                header.addWidget(badge)

            # Etiqueta con el estado de pago del paquete: pagado (verde)
            # o por pagar (rojo).
            if package.payment_status == "Paid":
                payment_badge = QLabel(tr("Paid Package"))
                payment_badge.setStyleSheet(
                    "color: white; background-color: #2E7D32; "
                    "font-weight: bold; padding: 3px 8px; "
                    "border-radius: 8px;"
                )
            else:
                payment_badge = QLabel(tr("Unpaid Package"))
                payment_badge.setStyleSheet(
                    "color: white; background-color: #C62828; "
                    "font-weight: bold; padding: 3px 8px; "
                    "border-radius: 8px;"
                )

            header.addWidget(payment_badge)

            group_layout.addLayout(header)

            form = QFormLayout()

            form.addRow(
                tr("Classes Purchased"),
                self.create_label(
                    str(package.classes_purchased)
                ),
            )

            form.addRow(
                tr("Classes Taken"),
                self.create_label(
                    str(package.classes_taken)
                ),
            )

            classes_left_label = self.create_label(
                str(max(package.classes_left, 0))
            )

            # Si el paquete se pasó de lo comprado, se resalta la deuda.
            if package.classes_left < 0:
                classes_left_label.setStyleSheet(
                    "color: #C62828; font-weight: bold;"
                )

                form.addRow(
                    tr("Classes Owed"),
                    self.create_label(
                        str(-package.classes_left)
                    ),
                )

            form.addRow(
                tr("Classes Left"),
                classes_left_label,
            )

            form.addRow(
                tr("Date of Payment"),
                self.create_label(
                    package.date_of_payment or "-"
                ),
            )

            form.addRow(
                tr("Date of Start"),
                self.create_label(
                    package.date_of_start or "-"
                ),
            )

            form.addRow(
                tr("Discount"),
                self.create_label(
                    f"{package.discount_percent}%"
                ),
            )

            form.addRow(
                tr("Hourly Price"),
                self.create_label(
                    f"$ {package.hourly_price:.2f}"
                ),
            )

            form.addRow(
                tr("Total"),
                self.create_label(
                    f"$ {package.total:.2f}"
                ),
            )

            form.addRow(
                tr("Status"),
                self.create_label(tr(package.status)),
            )

            group_layout.addLayout(form)

            container.addWidget(group)

        container.addStretch()

    def create_tasks_tab(self) -> QWidget:
        """Construye la pestaña de tareas del profesor del estudiante.

        Muestra las tareas de ESTE estudiante (las que se añaden desde
        el diálogo "Nueva clase vista" o desde aquí). Cada una se puede
        marcar como hecha/no hecha y lleva una nota editable por
        separado.
        """
        tasks = QWidget()

        self.tasks_tab = tasks

        layout = QVBoxLayout(tasks)

        # Fila superior para añadir una tarea nueva a este estudiante.
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText(
            tr("New task for this student...")
        )

        self.task_input.returnPressed.connect(
            self.add_task_for_student
        )

        add_button = QPushButton(tr("➕ Add Task"))
        add_button.setObjectName("primary")

        add_button.clicked.connect(
            self.add_task_for_student
        )

        add_row = QHBoxLayout()

        add_row.addWidget(self.task_input, stretch=1)
        add_row.addWidget(add_button)

        layout.addLayout(add_row)

        # Las tareas van dentro de un área desplazable.
        self.tasks_scroll = QScrollArea()

        self.tasks_scroll.setWidgetResizable(True)

        self.tasks_scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        tasks_widget = QWidget()

        self.tasks_container = QVBoxLayout(tasks_widget)

        self.tasks_container.addStretch()

        self.tasks_scroll.setWidget(tasks_widget)

        layout.addWidget(self.tasks_scroll, stretch=1)

        self.refresh_tasks_tab()

        return tasks

    def refresh_tasks_tab(self) -> None:
        """Reconstruye la lista de tareas de este estudiante."""
        if not hasattr(self, "tasks_container"):
            return

        container = self.tasks_container

        # Vacía el contenedor (se conserva el "stretch" del final).
        removed = []

        while container.count() > 0:
            item = container.takeAt(0)
            widget = item.widget()

            if widget is not None:
                removed.append(widget)

        for widget in removed:
            widget.deleteLater()

        tasks = [
            task
            for task in load_teacher_tasks()
            if task.student == self.student.name
        ]

        if not tasks:
            empty = QLabel(tr("No teacher tasks yet"))
            empty.setStyleSheet("color: gray;")
            container.addWidget(empty)
        else:
            for task in tasks:
                container.addWidget(build_task_row(task))

        container.addStretch()

    def add_task_for_student(self) -> None:
        """Añade la tarea escrita a este estudiante."""
        text = self.task_input.text().strip()

        if not text:
            return

        tasks = load_teacher_tasks()

        tasks.append(
            TeacherTask(
                text=text,
                student=self.student.name,
            )
        )

        self.task_input.clear()

        save_teacher_tasks(tasks)

    def create_enrollment_tab(self) -> QWidget:
        """Construye la pestaña con la información de la matrícula."""
        enrollment = QWidget()

        layout = QVBoxLayout(enrollment)

        group = QGroupBox(
            tr("Enrollment Information")
        )

        form = QFormLayout()

        # Labels guardados como atributos para poder refrescarlos
        # (refresh_enrollment_tab) cuando cambia el estudiante, el
        # paquete o el pago.
        self.enr_name = self.create_label("")
        self.enr_enrolled_on = self.create_label("")
        self.enr_level = self.create_label("")
        self.enr_email = self.create_label("")
        self.enr_phone = self.create_label("")
        self.enr_hourly_price = self.create_label("")
        self.enr_classes_purchased = self.create_label("")
        self.enr_classes_taken = self.create_label("")
        self.enr_classes_left = self.create_label("")
        self.enr_discount = self.create_label("")
        self.enr_total = self.create_label("")
        self.enr_amount_paid = self.create_label("")
        self.enr_amount_owed = self.create_label("")
        self.enr_payment_mode = self.create_label("")
        self.enr_payment_status = self.create_label("")
        self.enr_notes = self.create_label("")
        self.enr_topics = self.create_label("")

        # Pares (etiqueta, valor) mostrados en la pestaña.
        fields = [
            (
                tr("Name"),
                self.enr_name,
            ),
            (
                tr("Enrolled On"),
                self.enr_enrolled_on,
            ),
            (
                tr("Level"),
                self.enr_level,
            ),
            (
                tr("Email"),
                self.enr_email,
            ),
            (
                tr("Phone"),
                self.enr_phone,
            ),
            (
                tr("Hourly Price"),
                self.enr_hourly_price,
            ),
            (
                tr("Classes Purchased"),
                self.enr_classes_purchased,
            ),
            (
                tr("Classes Taken"),
                self.enr_classes_taken,
            ),
            (
                tr("Classes Left"),
                self.enr_classes_left,
            ),
            (
                tr("Discount"),
                self.enr_discount,
            ),
            (
                tr("Package Total"),
                self.enr_total,
            ),
            (
                tr("Amount Paid"),
                self.enr_amount_paid,
            ),
            (
                tr("Amount Owed"),
                self.enr_amount_owed,
            ),
            (
                tr("Payment Mode"),
                self.enr_payment_mode,
            ),
            (
                tr("Payment Status"),
                self.enr_payment_status,
            ),
            (
                tr("Notes"),
                self.enr_notes,
            ),
            (
                tr("Grammar Topics"),
                self.enr_topics,
            ),
        ]

        for title, value in fields:
            form.addRow(
                title,
                value,
            )

        group.setLayout(
            form
        )

        layout.addWidget(
            group
        )

        layout.addStretch()

        self.refresh_enrollment_tab()

        return enrollment

    def refresh_enrollment_tab(self) -> None:
        """Actualiza los labels del tab Enrollment con el estado actual
        del estudiante, el paquete y el pago."""
        self.enr_name.setText(
            self.student.name
        )

        self.enr_enrolled_on.setText(
            self.student.enrolled_at
        )

        self.enr_level.setText(
            self.student.level or "—"
        )

        self.enr_email.setText(
            self.student.email
        )

        self.enr_phone.setText(
            self.student.phone
        )

        self.enr_hourly_price.setText(
            f"$ {self.student.hourly_price:.2f}"
        )

        self.enr_classes_purchased.setText(
            str(self.student.classes_purchased)
        )

        self.enr_classes_taken.setText(
            str(self.student.classes_taken)
        )

        self.enr_classes_left.setText(
            self._classes_left_text()
        )

        self.enr_classes_left.setStyleSheet(
            "color: #C62828; font-weight: bold;"
            if self.student.classes_left < 0
            else ""
        )

        self.enr_discount.setText(
            f"{self.student.discount_percent}%"
        )

        self.enr_total.setText(
            f"$ {self.student.total:.2f}"
        )

        self.enr_amount_paid.setText(
            f"$ {self.student.amount_paid:.2f}"
        )

        self.enr_amount_owed.setText(
            f"$ {self.student.amount_owed:.2f}"
        )

        self.enr_payment_mode.setText(
            tr(self.student.payment_mode)
        )

        self.enr_payment_status.setText(
            tr(self.student.payment_status)
        )

        self.enr_notes.setText(
            self.student.notes
        )

        self.enr_topics.setText(
            ", ".join(self.student.topics)
            if self.student.topics
            else "—"
        )
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
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
from tutor_heaven.data.student_storage import load_students, save_students
from tutor_heaven.i18n import tr
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.package_dialog import PackageDialog
from tutor_heaven.ui.widgets.resume_dialog import ResumeDialog
from tutor_heaven.ui.widgets.session_progress_dialog import (
    SessionProgressDialog,
)


class StudentProfile(QWidget):
    """Student profile.

    Vista detallada de un estudiante organizada en pestañas:
    - "Enrollment": información de la matrícula y del pago.
    - "Sessions": registro de sesiones (consumen clases del paquete
      y cada clase puede marcarse como pagada).
    - "Packages": añadir más clases al paquete (devuelve al estudiante
      a activos automáticamente).
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

        # Botones superiores: hoja de vida, color del calendario y
        # eliminar estudiante.
        top_buttons = QHBoxLayout()

        self.resume_button = QPushButton(
            tr("📋 Resume")
        )

        self.resume_button.clicked.connect(
            self.open_resume
        )

        # Botón para cambiar el color con el que el estudiante se
        # muestra en el calendario.
        self.color_button = QPushButton(tr("🎨 Color"))

        self.color_button.clicked.connect(
            self.choose_color
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
        top_buttons.addWidget(self.color_button)
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

        tabs.addTab(
            self.create_placeholder_tab(tr("Files")),
            tr("Files"),
        )

        tabs.addTab(
            self.create_placeholder_tab(tr("Statistics")),
            tr("Statistics"),
        )

        self.tabs = tabs

        # Al entrar en la pestaña de sesiones se refresca la tabla y el
        # calendario para reflejar los últimos datos.
        self.tabs.currentChanged.connect(
            self.on_tab_changed
        )

        layout.addWidget(tabs)

        # Mantiene el perfil sincronizado con los datos guardados desde
        # cualquier otra vista (dashboard, calendario, otro perfil...).
        get_bus().studentsChanged.connect(
            self._on_students_changed
        )

        self.refresh_former_button()

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

    def choose_color(self) -> None:
        """Abre el selector de color del estudiante para el calendario."""
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QColorDialog

        current = QColor(self.student.color)

        color = QColorDialog.getColor(
            current,
            self,
            "Choose calendar color",
        )

        if not color.isValid():
            return

        self.student.color = color.name()

        save_students(
            self.students
        )

    def delete_student(self) -> None:
        """Elimina al estudiante tras confirmar con un mensaje de advertencia.

        La advertencia explica que se borran todos sus datos (paquetes y
        sesiones) y que la acción no se puede deshacer. Solo se elimina si
        el usuario confirma.
        """
        confirm = QMessageBox.warning(
            self,
            tr("Delete student"),
            tr(
                "Are you sure you want to delete {0}?\n\n"
                "All their packages, sessions and payment data will be "
                "permanently removed. This action cannot be undone."
            ).format(
                self.student.name
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        self.students.remove(
            self.student
        )

        save_students(
            self.students
        )

        self.studentDeleted.emit()

    def toggle_former(self) -> None:
        """Marca/desmarca manualmente al estudiante como antiguo.

        La marca queda siempre en oposición a la categoría real: si el
        estudiante es antiguo (por marca manual o por deducción
        automática) se desmarca; si es activo se marca. Así el botón
        siempre ofrece la acción contraria a su estado actual. El
        dashboard reparte al estudiante según su categoría usando esta
        marca junto con la deducción automática de los datos.
        """
        self.student.marked_former = not self.student.is_former

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

        table.setRowCount(
            len(self.student.sessions)
        )

        for row, session in enumerate(
            self.student.sessions,
            start=0,
        ):
            values = [
                session.date,
                session.start_time,
                session.end_time,
                session.topic,
                tr(session.status),
                tr("Paid") if self.student.session_is_paid(session) else tr("Not paid"),
                session.notes,
            ]

            for column, value in enumerate(values):
                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

        table.resizeColumnsToContents()

    def show_session_detail(
        self,
        row: int,
        column: int,
    ) -> None:
        """Muestra el detalle de progreso de la sesión al hacer doble clic."""
        del column

        if row < 0 or row >= len(self.student.sessions):
            return

        session = self.student.sessions[row]

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
        )

        if not dialog.exec():
            return

        data = dialog.package_data

        if data is None:
            return

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
            package=package,
        )

        if not dialog.exec():
            return

        data = dialog.package_data

        if data is None:
            return

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
        """Refresca la tabla y el calendario al entrar en Sessions."""
        if (
            hasattr(self, "sessions_tab")
            and self.tabs.widget(index) is self.sessions_tab
        ):
            self.refresh_sessions_table()

    def create_sessions_tab(self) -> QWidget:
        """Construye la pestaña de sesiones.

        Contiene un panel con las clases disponibles y la próxima clase,
        el botón para dar una clase como vista y la tabla del histórico
        de sesiones. La planificación de clases se hace desde la pestaña
        de Calendario.
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
            tr("✅ Clase vista")
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

        # Solo lectura: las sesiones se crean con el diálogo.
        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # Las sesiones ya llegan ordenadas (sort_sessions), así que no
        # se habilita el ordenado por columnas para no romper el orden.
        table.setSortingEnabled(False)

        table.horizontalHeader().setStretchLastSection(
            True
        )

        # Doble clic en una sesión muestra su detalle de progreso.
        table.cellDoubleClicked.connect(
            self.show_session_detail
        )

        self.refresh_sessions_table()

        layout.addWidget(
            table
        )

        return sessions

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

    def create_enrollment_tab(self) -> QWidget:
        """Construye la pestaña con la información de la matrícula."""
        enrollment = QWidget()

        layout = QVBoxLayout(enrollment)

        group = QGroupBox(
            tr("Enrollment Information")
        )

        form = QFormLayout()

        # Labels guardados como atributos para poder refrescarlos
        # (refresh_enrollment_tab) cuando cambia el paquete o el pago.
        self.enr_hourly_price = self.create_label("")
        self.enr_classes_purchased = self.create_label("")
        self.enr_classes_taken = self.create_label("")
        self.enr_classes_left = self.create_label("")
        self.enr_discount = self.create_label("")
        self.enr_total = self.create_label("")
        self.enr_amount_paid = self.create_label("")
        self.enr_amount_owed = self.create_label("")

        # Pares (etiqueta, valor) mostrados en la pestaña.
        fields = [
            (
                tr("Name"),
                self.create_label(self.student.name),
            ),
            (
                tr("Enrolled On"),
                self.create_label(self.student.enrolled_at),
            ),
            (
                tr("Type"),
                self.create_label(self.student.student_type),
            ),
            (
                tr("Email"),
                self.create_label(self.student.email),
            ),
            (
                tr("Phone"),
                self.create_label(self.student.phone),
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
                self.create_label(tr(self.student.payment_mode)),
            ),
            (
                tr("Payment Status"),
                self.create_label(tr(self.student.payment_status)),
            ),
            (
                tr("Notes"),
                self.create_label(self.student.notes),
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
        del paquete y del pago."""
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
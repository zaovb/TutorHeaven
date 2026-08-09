from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.data_bus import get_bus
from tutor_heaven.data.student_storage import load_students, save_students
from tutor_heaven.i18n import tr
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.themes import theme_color
from tutor_heaven.ui.widgets.add_session_dialog import AddSessionDialog


class Dashboard(QWidget):
    """Dashboard screen.

    Pantalla de inicio con acceso directo a los estudiantes. Muestra
    dos secciones:

    - Matriculados (activos): estudiantes que aún tienen clases por
      consumir o sesiones futuras pendientes.
    - Antiguos: estudiantes que agotaron sus clases y no tienen
      sesiones a futuro.

    Al hacer doble clic en un estudiante se emite studentSelected para
    que la ventana principal abra su perfil completo.
    """

    # Señal propia: se emite con el Student al hacer doble clic.
    # La consume MainWindow para navegar a la pestaña de estudiantes.
    studentSelected = Signal(object)

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # ---------- Encabezado ----------

        title = QLabel("Tutor Heaven")
        title_font = QFont()
        title_font.setPointSize(26)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet(
            f"color: {theme_color('accent')}; background: transparent;"
        )

        subtitle = QLabel(
            tr("Double-click a student to open their profile")
        )
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)
        subtitle.setStyleSheet(
            f"color: {theme_color('muted_text')}; background: transparent;"
        )

        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignLeft)

        # Botón de acceso rápido para agendar una clase para cualquier
        # estudiante sin abrir su perfil.
        self.add_class_button = QPushButton(tr("➕ Add Class"))
        self.add_class_button.setObjectName("primary")
        self.add_class_button.setFixedWidth(180)
        self.add_class_button.clicked.connect(self.add_class)

        layout.addWidget(
            self.add_class_button,
            alignment=Qt.AlignmentFlag.AlignLeft,
        )

        # ---------- Secciones de estudiantes ----------

        # Dos columnas: activos a la izquierda y antiguos a la derecha.
        # Cada columna se divide en dos listas: con deuda y sin deuda.
        # Las listas vacías (con su etiqueta) se ocultan al refrescar.
        # groups[key] guarda los widgets de cada columna para refrescarlos.
        self.groups: dict[str, dict] = {}

        lists_layout = QHBoxLayout()

        self.active_group = QGroupBox()
        self.active_group.setLayout(
            self.create_group_layout("active")
        )

        self.former_group = QGroupBox()
        self.former_group.setLayout(
            self.create_group_layout("former")
        )

        lists_layout.addWidget(self.active_group)
        lists_layout.addWidget(self.former_group)

        layout.addLayout(lists_layout)

        # Se recarga cuando los datos cambian desde cualquier otra vista.
        get_bus().studentsChanged.connect(
            self.refresh
        )

        # El dashboard se refresca cada vez que se muestra, para reflejar
        # altas de estudiantes o clases añadidas en otras pestañas.
        self.refresh()

    def showEvent(self, event) -> None:
        """Se ejecuta al mostrar el widget (p.ej. al cambiar de pestaña).

        Refresca las listas para reflejar los datos más recientes.
        """
        super().showEvent(event)

        self.refresh()

    def create_student_list(self) -> QListWidget:
        """Crea una lista de estudiantes ya configurada.

        El doble clic sobre un ítem emite studentSelected con el
        Student guardado en el UserRole del ítem.
        """
        list_widget = QListWidget()

        list_widget.itemDoubleClicked.connect(
            self.open_student
        )

        return list_widget

    def create_group_layout(self, key: str) -> QVBoxLayout:
        """Layout interno de una columna del dashboard.

        La columna tiene un encabezado (QLabel en lugar del título del
        QGroupBox, que se salía del cuadro con el estilo actual) y dos
        sub-secciones "Con deuda" / "Sin deuda", cada una con su
        etiqueta y su lista. Los widgets se guardan en self.groups[key]
        para poder rellenarlos y ocultarlos al refrescar.
        """
        inner = QVBoxLayout()

        group_title = QLabel("")
        group_title.setStyleSheet(
            f"color: {theme_color('accent')}; "
            f"font-weight: bold; font-size: 15px;"
        )

        inner.addWidget(group_title)

        # Sub-sección "con deuda": etiqueta + lista.
        debt_label = QLabel("")
        debt_label.setStyleSheet(
            "color: #C62828; font-weight: bold; font-size: 12px;"
        )

        debt_list = self.create_student_list()

        inner.addWidget(debt_label)
        inner.addWidget(debt_list)

        # Sub-sección "sin deuda": etiqueta + lista.
        clean_label = QLabel("")
        clean_label.setStyleSheet(
            f"color: {theme_color('muted_text')}; "
            f"font-weight: bold; font-size: 12px;"
        )

        clean_list = self.create_student_list()

        inner.addWidget(clean_label)
        inner.addWidget(clean_list)

        self.groups[key] = {
            "title": group_title,
            "debt_label": debt_label,
            "debt_list": debt_list,
            "clean_label": clean_label,
            "clean_list": clean_list,
        }

        return inner

    def _refresh_group(
        self,
        key: str,
        title_text: str,
        students: list[Student],
    ) -> None:
        """Rellena una columna del dashboard.

        El título de la columna muestra el total de estudiantes y cada
        sub-sección (con/sin deuda) su etiqueta y su lista. Las partes
        vacías se ocultan para no dejar huecos.
        """
        widgets = self.groups[key]

        with_debt = [
            student
            for student in students
            if student.has_debt
        ]

        without_debt = [
            student
            for student in students
            if not student.has_debt
        ]

        widgets["title"].setText(
            f"{title_text} ({len(students)})"
        )

        self._set_section(
            widgets["debt_label"],
            widgets["debt_list"],
            tr("With debt"),
            with_debt,
        )

        self._set_section(
            widgets["clean_label"],
            widgets["clean_list"],
            tr("Without debt"),
            without_debt,
        )

    def _set_section(
        self,
        label: QLabel,
        list_widget: QListWidget,
        name: str,
        students: list[Student],
    ) -> None:
        """Muestra una sub-sección con su contador y rellena la lista.

        Si no hay estudiantes en la sub-sección, se ocultan la etiqueta
        y la lista para no dejar un hueco vacío en la columna.
        """
        label.setText(
            f"{name} ({len(students)})"
        )
        label.setVisible(bool(students))

        self.fill_list(list_widget, students)

        list_widget.setVisible(bool(students))

    def refresh(self) -> None:
        """Recarga la lista de estudiantes y los reparte entre activos
        y antiguos, actualizando los títulos de cada grupo."""
        students = load_students()

        active = [
            student
            for student in students
            if student.is_active
        ]

        former = [
            student
            for student in students
            if student.is_former
        ]

        self._refresh_group(
            "active",
            tr("Active Students"),
            active,
        )

        self._refresh_group(
            "former",
            tr("Former Students"),
            former,
        )

    def fill_list(
        self,
        list_widget: QListWidget,
        students: list[Student],
    ) -> None:
        """Rellena una lista con los estudiantes dados.

        Cada ítem muestra nombre, clases restantes y próxima clase.
        El Student original se guarda en UserRole para recuperarlo
        al hacer doble clic.
        """
        list_widget.clear()

        for student in students:
            item = QListWidgetItem(
                self.describe(student)
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                student,
            )

            list_widget.addItem(item)

    @staticmethod
    def describe(student: Student) -> str:
        """Texto resumido de un estudiante para la lista."""
        next_session = student.next_session

        if next_session is not None:
            next_text = tr(
                "Next: {0} {1}"
            ).format(
                next_session.date,
                next_session.start_time,
            )
        else:
            next_text = tr("No upcoming class")

        if student.classes_left >= 0:
            classes_text = (
                f"{student.classes_left} {tr('classes left')}"
            )
        else:
            classes_text = (
                f"{-student.classes_left} {tr('classes owed')}"
            )

        return (
            f"{student.name} — "
            f"{classes_text} — "
            f"{next_text}"
        )

    def add_class(self) -> None:
        """Abre el diálogo para agendar una clase para cualquier
        estudiante y, si se acepta, la guarda y consume clase si es
        completada."""
        students = load_students()

        if not students:
            return

        dialog = AddSessionDialog(students)

        if not dialog.exec():
            return

        student = dialog.created_for_student
        session = dialog.created_session

        if student is None or session is None:
            return

        student.sessions.append(session)

        if session.status == "Completed":
            student.consume_class()

        save_students(students)

        self.refresh()

    def open_student(
        self,
        item: QListWidgetItem,
    ) -> None:
        """Emite la señal con el estudiante del ítem hecho doble clic."""
        student = item.data(
            Qt.ItemDataRole.UserRole
        )

        if student is None:
            return

        self.studentSelected.emit(student)

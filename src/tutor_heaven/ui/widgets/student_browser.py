from PySide6.QtWidgets import (
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.i18n import tr
from tutor_heaven.ui.widgets.placeholder import Placeholder
from tutor_heaven.ui.widgets.student_enrollments import Students
from tutor_heaven.ui.widgets.student_profile import StudentProfile


class StudentBrowser(QWidget):
    """Main student browser.

    Compone la vista principal de estudiantes: un panel izquierdo con
    la lista de matrículas (Students) y un panel derecho con el perfil
    del estudiante seleccionado (StudentProfile). Al principio el panel
    derecho muestra un Placeholder pidiendo que se seleccione a alguien.
    """

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        self.splitter = QSplitter()

        # Panel izquierdo: lista de estudiantes matriculados.
        self.enrollments = Students()

        # Cuando el usuario hace doble clic en un estudiante, se abre
        # su perfil en el panel derecho.
        self.enrollments.studentSelected.connect(
            self.open_student_profile
        )

        self.placeholder = Placeholder(
            tr("Select a student\n\nto open the profile.")
        )

        # self.profile guarda el widget actual del panel derecho
        # (primero el placeholder, luego el perfil real) para poder
        # liberarlo al reemplazarlo.
        self.profile = self.placeholder

        self.splitter.addWidget(
            self.enrollments
        )

        self.splitter.addWidget(
            self.profile
        )

        self.splitter.setSizes(
            [
                400,
                900,
            ]
        )

        layout.addWidget(
            self.splitter
        )

    def open_student_profile(
        self,
        student,
    ) -> None:
        """Muestra el perfil del estudiante en el panel derecho.

        La primera vez se crea un StudentProfile; si ya existe se
        reutiliza (llamando a set_student) para que al cambiar de
        estudiante se conserve la pestaña seleccionada.
        """
        if self.profile is self.placeholder:
            new_profile = StudentProfile(
                student,
                self.enrollments.students,
            )

            # Si el estudiante se elimina desde el perfil, se vuelve al
            # panel por defecto y se refresca la lista de matrículas.
            new_profile.studentDeleted.connect(
                self.back_to_placeholder
            )

            self.splitter.replaceWidget(
                1,
                new_profile,
            )

            self.profile.deleteLater()

            self.profile = new_profile
        else:
            self.profile.set_student(
                student,
                self.enrollments.students,
            )

    def back_to_placeholder(self) -> None:
        """Vuelve el panel derecho al Placeholder tras eliminar a un
        estudiante y refresca la lista de matrículas."""
        self.enrollments.refresh_students()

        # Se crea un Placeholder nuevo: el anterior se eliminó al
        # abrir el perfil que acabamos de cerrar.
        placeholder = Placeholder(
            tr("Select a student\n\nto open the profile.")
        )

        self.splitter.replaceWidget(
            1,
            placeholder,
        )

        self.profile.deleteLater()

        self.profile = placeholder

    def open_student_by_name(
        self,
        name: str,
    ) -> None:
        """Abre el perfil del estudiante que coincida con el nombre.

        Usado cuando se llega desde el Dashboard: el estudiante se
        busca en la lista compartida del navegador para operar sobre
        la misma instancia y no sobre una copia distinta.
        """
        for index, student in enumerate(
            self.enrollments.students
        ):
            if student.name == name:
                self.enrollments.list.setCurrentRow(index)
                self.open_student_profile(student)

                return
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.student_storage import save_students
from tutor_heaven.models.session_model import Session
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.session_dialog import SessionDialog


class StudentProfile(QWidget):
    """Student profile."""

    def __init__(
        self,
        student: Student,
        students: list[Student],
    ) -> None:
        super().__init__()

        self.student = student
        self.students = students

        self.sessions_table: QTableWidget | None = None

        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        tabs.addTab(
            self.create_enrollment_tab(),
            "Enrollment",
        )

        tabs.addTab(
            self.create_sessions_tab(),
            "Sessions",
        )

        tabs.addTab(
            self.create_placeholder_tab("Payments"),
            "Payments",
        )

        tabs.addTab(
            self.create_placeholder_tab("Packages"),
            "Packages",
        )

        tabs.addTab(
            self.create_placeholder_tab("Notes"),
            "Notes",
        )

        tabs.addTab(
            self.create_placeholder_tab("Files"),
            "Files",
        )

        tabs.addTab(
            self.create_placeholder_tab("Statistics"),
            "Statistics",
        )

        layout.addWidget(tabs)

    def create_label(
        self,
        text: str,
    ) -> QLabel:

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

        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(
            self.create_label(
                f"{title} module"
            )
        )

        layout.addStretch()

        return widget

    def sort_sessions(self) -> None:
        self.student.sessions.sort(
            key=lambda session: session.start_datetime
        )

    def add_session(self) -> None:
        dialog = SessionDialog()

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
        )

        self.student.sessions.append(
            session
        )

        self.sort_sessions()

        save_students(
            self.students
        )

        self.refresh_sessions_table()
    def refresh_sessions_table(self) -> None:
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
                str(row + 1),
                session.date,
                session.start_time,
                session.end_time,
                session.topic,
                session.status,
                session.notes,
            ]

            for column, value in enumerate(values):
                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

        table.resizeColumnsToContents()

    def create_sessions_tab(self) -> QWidget:
        sessions = QWidget()

        layout = QVBoxLayout(sessions)

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        add_button = QPushButton(
            "➕ Add Session"
        )

        add_button.clicked.connect(
            self.add_session
        )

        table = QTableWidget()

        self.sessions_table = table

        table.setColumnCount(7)

        table.setHorizontalHeaderLabels(
            [
                "#",
                "Date",
                "Start",
                "End",
                "Topic",
                "Status",
                "Notes",
            ]
        )

        table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        table.setSortingEnabled(True)

        table.horizontalHeader().setStretchLastSection(
            True
        )

        self.refresh_sessions_table()

        layout.addWidget(
            add_button
        )

        layout.addWidget(
            table
        )

        return sessions

    def create_enrollment_tab(self) -> QWidget:
        enrollment = QWidget()

        layout = QVBoxLayout(enrollment)

        group = QGroupBox(
            "Enrollment Information"
        )

        form = QFormLayout()

        fields = [
            (
                "Name",
                self.student.name,
            ),
            (
                "Type",
                self.student.student_type,
            ),
            (
                "Email",
                self.student.email,
            ),
            (
                "Phone",
                self.student.phone,
            ),
            (
                "Hourly Price",
                f"$ {self.student.hourly_price:.2f}",
            ),
            (
                "Classes Purchased",
                str(self.student.classes_purchased),
            ),
            (
                "Classes Taken",
                str(self.student.classes_taken),
            ),
            (
                "Classes Left",
                str(self.student.classes_left),
            ),
            (
                "Total",
                f"$ {self.student.total:.2f}",
            ),
            (
                "Payment Mode",
                self.student.payment_mode,
            ),
            (
                "Payment Status",
                self.student.payment_status,
            ),
            (
                "Notes",
                self.student.notes,
            ),
        ]

        for title, value in fields:
            form.addRow(
                title,
                self.create_label(value),
            )

        group.setLayout(
            form
        )

        layout.addWidget(
            group
        )

        layout.addStretch()

        return enrollment
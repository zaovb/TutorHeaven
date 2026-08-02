from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.widgets.student_dialog import StudentDialog


class Students(QWidget):
    """Students module."""

    studentSelected = Signal(object)

    def __init__(self) -> None:
        super().__init__()

        self.students: list[Student] = []

        layout = QVBoxLayout(self)

        new_student_button = QPushButton("➕ New Enrollment")
        new_student_button.clicked.connect(self.new_student)

        self.table = QTableWidget()

        self.table.setColumnCount(7)

        self.table.setHorizontalHeaderLabels(
            [
                "Name",
                "Type",
                "Total",
                "Classes Left",
                "Next Class",
                "Notes",
                "Status",
            ]
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        header.setStretchLastSection(True)

        self.table.cellDoubleClicked.connect(self.open_student)

        layout.addWidget(new_student_button)
        layout.addWidget(self.table)

    def new_student(self) -> None:
        dialog = StudentDialog()

        if not dialog.exec():
            return

        student = dialog.student

        if student is None:
            return

        self.students.append(student)

        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(
            row,
            0,
            QTableWidgetItem(student.name),
        )

        self.table.setItem(
            row,
            1,
            QTableWidgetItem(student.student_type),
        )

        self.table.setItem(
            row,
            2,
            QTableWidgetItem(f"$ {student.total:.2f}"),
        )

        self.table.setItem(
            row,
            3,
            QTableWidgetItem(str(student.classes_left)),
        )

        self.table.setItem(
            row,
            4,
            QTableWidgetItem("-"),
        )

        notes = QTableWidgetItem(student.notes)
        notes.setToolTip(student.notes)

        self.table.setItem(
            row,
            5,
            notes,
        )

        status = (
            "Pay later"
            if student.payment_mode == "Pay later"
            else student.payment_status
        )

        self.table.setItem(
            row,
            6,
            QTableWidgetItem(status),
        )

    def open_student(self, row: int, column: int) -> None:
        del column

        self.studentSelected.emit(self.students[row])
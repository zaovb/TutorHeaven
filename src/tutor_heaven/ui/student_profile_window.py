from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.models.student_model import Student


class StudentProfileWindow(QMainWindow):
    """Main window for a student's profile."""

    def __init__(self, student: Student) -> None:
        super().__init__()

        self.student = student

        self.setWindowTitle(student.name)
        self.resize(1000, 700)

        tabs = QTabWidget()

        tabs.addTab(self._placeholder("Overview"), "Overview")
        tabs.addTab(self._placeholder("Enrollment"), "Enrollment")
        tabs.addTab(self._placeholder("Sessions"), "Sessions")
        tabs.addTab(self._placeholder("Payments"), "Payments")
        tabs.addTab(self._placeholder("Packages"), "Packages")
        tabs.addTab(self._placeholder("Notes"), "Notes")
        tabs.addTab(self._placeholder("Files"), "Files")
        tabs.addTab(self._placeholder("Statistics"), "Statistics")

        self.setCentralWidget(tabs)

    def _placeholder(self, title: str) -> QWidget:
        widget = QWidget()

        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel(title))
        layout.addStretch()

        return widget
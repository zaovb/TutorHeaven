from PySide6.QtWidgets import QMainWindow

from tutor_heaven.app_info import APP_NAME
from tutor_heaven.ui.widgets.student_browser import StudentBrowser


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)

        self.setCentralWidget(StudentBrowser())
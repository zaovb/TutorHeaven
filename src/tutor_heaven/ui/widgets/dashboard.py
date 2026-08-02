from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Dashboard(QWidget):
    """Dashboard screen."""

    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("Tutor Heaven")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Welcome to Tutor Heaven")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle.setFont(subtitle_font)

        layout.addStretch()
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.setLayout(layout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class Placeholder(QWidget):
    """Temporary page while the module is under development."""

    def __init__(self, title: str) -> None:
        super().__init__()

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)

        label = QLabel(title)

        font = QFont()
        font.setPointSize(22)
        font.setBold(True)

        label.setFont(font)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        self.setLayout(layout)
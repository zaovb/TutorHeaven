from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTimeEdit,
    QVBoxLayout,
)


class SessionDialog(QDialog):
    """Dialog to create a session."""

    def __init__(self) -> None:
        super().__init__()

        self.session_data = None

        self.setWindowTitle("Add Session")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        self.date.setDisplayFormat("yyyy-MM-dd")

        self.start_time = QTimeEdit()
        self.start_time.setTime(
            QTime.currentTime()
        )
        self.start_time.setDisplayFormat("HH:mm")

        self.end_time = QTimeEdit()
        self.end_time.setTime(
            QTime.currentTime().addSecs(3600)
        )
        self.end_time.setDisplayFormat("HH:mm")

        self.topic = QLineEdit()

        self.status = QComboBox()
        self.status.addItems(
            [
                "Pending",
                "Completed",
                "Cancelled",
            ]
        )

        self.notes = QLineEdit()

        form.addRow("Date", self.date)
        form.addRow("Start Time", self.start_time)
        form.addRow("End Time", self.end_time)
        form.addRow("Topic", self.topic)
        form.addRow("Status", self.status)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_session)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def accept_session(self) -> None:
        self.session_data = {
            "date": self.date.date().toString(
                "yyyy-MM-dd"
            ),
            "start_time": self.start_time.time().toString(
                "HH:mm"
            ),
            "end_time": self.end_time.time().toString(
                "HH:mm"
            ),
            "topic": self.topic.text(),
            "status": self.status.currentText(),
            "notes": self.notes.text(),
        }

        self.accept()
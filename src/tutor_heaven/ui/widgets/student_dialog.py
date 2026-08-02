from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from tutor_heaven.models.student_model import Student


class StudentDialog(QDialog):
    """Dialog to create a new student."""

    INDIVIDUAL_PRICE = 20.0
    GROUP_PRICE = 15.0

    def __init__(self) -> None:
        super().__init__()

        self.student: Student | None = None

        self.setWindowTitle("New Student")
        self.setMinimumWidth(500)

        main_layout = QVBoxLayout(self)

        # ---------- Basic Information ----------

        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()

        self.name = QLineEdit()

        self.student_type = QComboBox()
        self.student_type.addItems(
            [
                "Individual",
                "Group",
                "Custom",
            ]
        )

        self.email = QLineEdit()
        self.phone = QLineEdit()

        basic_layout.addRow("Name", self.name)
        basic_layout.addRow("Type", self.student_type)
        basic_layout.addRow("Email", self.email)
        basic_layout.addRow("Phone", self.phone)

        basic_group.setLayout(basic_layout)

        # ---------- Course Package ----------

        package_group = QGroupBox("Course Package")
        package_layout = QFormLayout()

        self.classes_purchased = QSpinBox()
        self.classes_purchased.setRange(1, 100)
        self.classes_purchased.setValue(1)

        self.classes_taken = QSpinBox()
        self.classes_taken.setRange(0, 100)
        self.classes_taken.setValue(0)
        self.classes_taken.setEnabled(False)

        self.hourly_price = QDoubleSpinBox()
        self.hourly_price.setPrefix("$ ")
        self.hourly_price.setDecimals(2)
        self.hourly_price.setMaximum(1000)

        self.payment_mode = QComboBox()
        self.payment_mode.addItems(
            [
                "Pay in advance",
                "Pay later",
            ]
        )

        self.payment_status = QComboBox()
        self.payment_status.addItems(
            [
                "Pending",
                "Paid",
            ]
        )

        self.notes = QLineEdit()

        package_layout.addRow("Classes Purchased", self.classes_purchased)
        package_layout.addRow("Classes Taken", self.classes_taken)
        package_layout.addRow("Hourly Price", self.hourly_price)
        package_layout.addRow("Payment Mode", self.payment_mode)
        package_layout.addRow("Payment Status", self.payment_status)
        package_layout.addRow("Notes", self.notes)

        package_group.setLayout(package_layout)

        # ---------- Summary ----------

        summary_group = QGroupBox("Summary")
        summary_layout = QFormLayout()

        self.summary_hourly_price = QLabel()
        self.package_price = QLabel()
        self.discount = QLabel()
        self.classes_left = QLabel()
        self.total = QLabel()

        summary_layout.addRow("Hourly Price", self.summary_hourly_price)
        summary_layout.addRow("Package Price", self.package_price)
        summary_layout.addRow("Discount", self.discount)
        summary_layout.addRow("Classes Left", self.classes_left)
        summary_layout.addRow("Total", self.total)

        summary_group.setLayout(summary_layout)

        main_layout.addWidget(basic_group)
        main_layout.addWidget(package_group)
        main_layout.addWidget(summary_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        main_layout.addWidget(buttons)

        self.student_type.currentTextChanged.connect(self.update_summary)
        self.classes_purchased.valueChanged.connect(self.update_summary)
        self.classes_taken.valueChanged.connect(self.update_summary)
        self.hourly_price.valueChanged.connect(self.update_summary)
        self.payment_mode.currentTextChanged.connect(self.update_summary)

        self.update_summary()

    def accept_dialog(self) -> None:
        self.student = Student(
            name=self.name.text(),
            student_type=self.student_type.currentText(),
            email=self.email.text(),
            phone=self.phone.text(),
            classes_purchased=self.classes_purchased.value(),
            classes_taken=self.classes_taken.value(),
            hourly_price=self.hourly_price.value(),
            payment_mode=self.payment_mode.currentText(),
            payment_status=self.payment_status.currentText(),
            notes=self.notes.text(),
        )

        self.accept()

    def update_summary(self) -> None:
        student_type = self.student_type.currentText()

        if student_type == "Individual":
            hourly_price = self.INDIVIDUAL_PRICE
            self.hourly_price.setEnabled(False)
            self.hourly_price.setValue(hourly_price)

        elif student_type == "Group":
            hourly_price = self.GROUP_PRICE
            self.hourly_price.setEnabled(False)
            self.hourly_price.setValue(hourly_price)

        else:
            self.hourly_price.setEnabled(True)

            if self.hourly_price.value() == 0:
                self.hourly_price.setValue(self.INDIVIDUAL_PRICE)

            hourly_price = self.hourly_price.value()

        purchased = self.classes_purchased.value()
        taken = self.classes_taken.value()

        classes_left = purchased - taken

        package_price = purchased * hourly_price

        if purchased >= 10:
            discount = 10
        elif purchased >= 5:
            discount = 5
        else:
            discount = 0

        total = package_price * (1 - discount / 100)

        if self.payment_mode.currentText() == "Pay later":
            self.payment_status.setEnabled(False)
            self.payment_status.setCurrentIndex(-1)
        else:
            self.payment_status.setEnabled(True)

            if self.payment_status.currentIndex() == -1:
                self.payment_status.setCurrentText("Pending")

        self.summary_hourly_price.setText(f"$ {hourly_price:.2f}")
        self.package_price.setText(f"$ {package_price:.2f}")
        self.discount.setText(f"{discount}%")
        self.classes_left.setText(str(classes_left))
        self.total.setText(f"$ {total:.2f}")
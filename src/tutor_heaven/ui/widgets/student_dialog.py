from datetime import datetime

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.i18n import tr
from tutor_heaven.models.package_model import Package
from tutor_heaven.models.student_model import Student
from tutor_heaven.ui.dialog_utils import (
    FitDialog,
    make_value_field_manual,
)
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class StudentDialog(FitDialog):
    """Dialog to create a new student.

    Formulario de alta de un estudiante. Recoge datos básicos, el
    paquete inicial de clases y el modo de pago, y muestra en vivo un
    resumen de precios con el descuento automático por reglas. Al
    aceptar, expone el Student construido en self.student.
    """

    def __init__(self) -> None:
        super().__init__()

        self.student: Student | None = None

        self.setWindowTitle(tr("New Student"))
        self.setMinimumWidth(500)

        # Precios por defecto para Individual y Group desde la
        # configuración (editables en Settings).
        settings = get_settings()

        self.INDIVIDUAL_PRICE = settings.individual_price
        self.GROUP_PRICE = settings.group_price

        main_layout = QVBoxLayout(self)

        # ---------- Basic Information ----------

        basic_group = QGroupBox(tr("Basic Information"))
        basic_layout = QFormLayout()

        self.name = QLineEdit()

        self.student_type = QComboBox()
        self.student_type.addItem(tr("Individual"), "Individual")
        self.student_type.addItem(tr("Group"), "Group")
        self.student_type.addItem(tr("Custom"), "Custom")

        self.level = QComboBox()
        self.level.addItems(
            [
                "",
                "A1",
                "A2",
                "B1",
                "B2",
                "C1",
                "C2",
            ]
        )

        self.email = QLineEdit()
        self.phone = QLineEdit()

        basic_layout.addRow(tr("Name"), self.name)
        basic_layout.addRow(tr("Type"), self.student_type)
        basic_layout.addRow(tr("Level"), self.level)
        basic_layout.addRow(tr("Email"), self.email)
        basic_layout.addRow(tr("Phone"), self.phone)

        basic_group.setLayout(basic_layout)

        # ---------- Initial Package ----------

        package_group = QGroupBox(tr("Initial Package"))
        package_layout = QFormLayout()

        self.classes_purchased = QSpinBox()
        self.classes_purchased.setRange(0, 100)
        self.classes_purchased.setValue(1)

        self.hourly_price = QDoubleSpinBox()
        self.hourly_price.setPrefix("$ ")
        self.hourly_price.setDecimals(2)
        self.hourly_price.setMaximum(1000)

        self.payment_mode = QComboBox()
        self.payment_mode.addItem(tr("Pay in advance"), "Pay in advance")
        self.payment_mode.addItem(tr("Pay later"), "Pay later")

        self.payment_status = QComboBox()
        self.payment_status.addItem(tr("Pending"), "Pending")
        self.payment_status.addItem(tr("Paid"), "Paid")

        self.notes = QLineEdit()

        # Botón para decidir si el paquete inicial lleva descuento o no.
        self.apply_discount = QCheckBox(tr("Apply Discount"))
        self.apply_discount.setChecked(True)

        package_layout.addRow(tr("Classes Purchased"), self.classes_purchased)
        package_layout.addRow(tr("Hourly Price"), self.hourly_price)
        package_layout.addRow(tr("Payment Mode"), self.payment_mode)
        package_layout.addRow(tr("Payment Status"), self.payment_status)
        package_layout.addRow(tr("Discount"), self.apply_discount)
        package_layout.addRow(tr("Notes"), self.notes)

        package_group.setLayout(package_layout)

        # ---------- Summary ----------

        summary_group = QGroupBox(tr("Summary"))
        summary_layout = QFormLayout()

        self.summary_hourly_price = QLabel()
        self.package_price = QLabel()
        self.discount = QLabel()
        self.classes_left = QLabel()
        self.total = QLabel()

        summary_layout.addRow(tr("Hourly Price"), self.summary_hourly_price)
        summary_layout.addRow(tr("Package Price"), self.package_price)
        summary_layout.addRow(tr("Discount"), self.discount)
        summary_layout.addRow(tr("Classes Left"), self.classes_left)
        summary_layout.addRow(tr("Total"), self.total)

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

        # Recalcula el resumen cuando cambia cualquiera de estos valores.
        self.student_type.currentTextChanged.connect(self.update_summary)
        self.classes_purchased.valueChanged.connect(self.update_summary)
        self.hourly_price.valueChanged.connect(self.update_summary)
        self.payment_mode.currentTextChanged.connect(self.update_summary)
        self.apply_discount.toggled.connect(self.update_summary)

        # Enter = siguiente campo (sin cerrar el diálogo).
        enable_enter_to_next(self)

        # Los valores solo se editan con el teclado: sin scroll ni flechas.
        for field in (
            self.student_type,
            self.level,
            self.classes_purchased,
            self.hourly_price,
            self.payment_mode,
            self.payment_status,
        ):
            make_value_field_manual(field)

        self.update_summary()

    def accept_dialog(self) -> None:
        """Construye el Student con el paquete inicial y acepta."""
        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        if self.apply_discount.isChecked():
            discount = get_settings().discount_for_classes(
                self.classes_purchased.value()
            )
        else:
            discount = 0

        self.student = Student(
            name=self.name.text(),
            student_type=self.student_type.currentData(),
            email=self.email.text(),
            phone=self.phone.text(),
            level=self.level.currentText(),
            hourly_price=self.hourly_price.value(),
            payment_mode=self.payment_mode.currentData(),
            payment_status=self.payment_status.currentData(),
            notes=self.notes.text(),
            packages=[
                Package(
                    classes_purchased=self.classes_purchased.value(),
                    classes_taken=0,
                    hourly_price=self.hourly_price.value(),
                    discount_percent=discount,
                    payment_mode=self.payment_mode.currentData(),
                    payment_status=self.payment_status.currentData(),
                    date_of_payment=today,
                    date_of_start=today,
                )
            ],
        )

        self.accept()

    def update_summary(self) -> None:
        """Actualiza en vivo el resumen de precios y descuentos."""
        student_type = self.student_type.currentData()

        # El precio por hora depende del tipo: fijo para Individual y
        # Group, editable solo en "Custom".
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
            hourly_price = self.hourly_price.value()

        purchased = self.classes_purchased.value()

        # El descuento es automático según las reglas de la configuración
        # solo si el botón "Apply Discount" está marcado.
        if self.apply_discount.isChecked():
            discount = get_settings().discount_for_classes(
                purchased
            )
        else:
            discount = 0

        package_price = purchased * hourly_price
        total = package_price * (1 - discount / 100)

        # En modo "Pay later" no se puede elegir estado de pago:
        # el botón de estado se deshabilita y queda como "Pending".
        if self.payment_mode.currentData() == "Pay later":
            self.payment_status.setEnabled(False)
            self.payment_status.setCurrentIndex(
                self.payment_status.findData("Pending")
            )
        else:
            self.payment_status.setEnabled(True)

            if self.payment_status.currentIndex() < 0:
                self.payment_status.setCurrentIndex(
                    self.payment_status.findData("Pending")
                )

        self.summary_hourly_price.setText(
            f"$ {hourly_price:.2f}"
        )
        self.package_price.setText(
            f"$ {package_price:.2f}"
        )
        if discount:
            self.discount.setText(
                f"{discount}%"
            )
        else:
            self.discount.setText(
                tr("No discount")
            )

        self.classes_left.setText(
            str(purchased)
        )
        self.total.setText(
            f"$ {total:.2f}"
        )

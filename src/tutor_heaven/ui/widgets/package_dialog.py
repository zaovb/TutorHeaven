from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.i18n import tr
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.ui.enter_navigation import enable_enter_to_next


class PackageDialog(FitDialog):
    """Dialog to add more classes to a student's package.

    Permite negociar el nuevo bloque de clases: número de clases,
    precio por hora, modo de pago y fechas de pago e inicio. El
    descuento se calcula automáticamente según las reglas de la
    configuración. Al aceptar expone el resultado en self.package_data.

    Si se pasa un Package existente (package=...), el diálogo se abre
    en modo edición: los campos vienen rellenos y el título cambia a
    "Edit Package". Las clases ya tomadas no se modifican aquí.
    """

    def __init__(
        self,
        current_price: float,
        package=None,
    ) -> None:
        super().__init__()

        self.package_data = None

        self.package = package

        self.setWindowTitle(
            tr("Edit Package")
            if package is not None
            else tr("Add Classes to Package")
        )
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)

        # ---------- Negociación del paquete ----------

        package_group = QGroupBox(tr("New Block"))
        package_form = QFormLayout()

        self.classes = QSpinBox()
        self.classes.setRange(1, 100)
        self.classes.setValue(
            package.classes_purchased
            if package is not None
            else 5
        )

        self.hourly_price = QDoubleSpinBox()
        self.hourly_price.setPrefix("$ ")
        self.hourly_price.setDecimals(2)
        self.hourly_price.setMaximum(1000)
        self.hourly_price.setValue(
            package.hourly_price
            if package is not None
            else current_price
        )

        package_form.addRow(
            tr("Classes Purchased")
            if package is not None
            else tr("Classes to Add"),
            self.classes,
        )
        package_form.addRow(tr("Hourly Price"), self.hourly_price)

        package_group.setLayout(package_form)

        # ---------- Fechas ----------

        dates_group = QGroupBox(tr("Dates"))
        dates_form = QFormLayout()

        today = QDate.currentDate()

        payment_date = QDate.fromString(
            package.date_of_payment,
            "yyyy-MM-dd",
        ) if package is not None else QDate()
        start_date = QDate.fromString(
            package.date_of_start,
            "yyyy-MM-dd",
        ) if package is not None else QDate()

        self.date_of_payment = QDateEdit(
            payment_date
            if payment_date.isValid()
            else today
        )
        self.date_of_payment.setCalendarPopup(True)
        self.date_of_payment.setDisplayFormat("yyyy-MM-dd")

        self.date_of_start = QDateEdit(
            start_date
            if start_date.isValid()
            else today
        )
        self.date_of_start.setCalendarPopup(True)
        self.date_of_start.setDisplayFormat("yyyy-MM-dd")

        dates_form.addRow(tr("Date of Payment"), self.date_of_payment)
        dates_form.addRow(tr("Date of Start"), self.date_of_start)

        dates_group.setLayout(dates_form)

        # ---------- Pago ----------

        payment_group = QGroupBox(tr("Payment"))
        payment_form = QFormLayout()

        self.payment_mode = QComboBox()
        self.payment_mode.addItems(
            [
                "Pay in advance",
                "Pay later",
            ]
        )

        if package is not None:
            index = self.payment_mode.findText(
                package.payment_mode
            )

            if index >= 0:
                self.payment_mode.setCurrentIndex(index)

        self.payment_status = QComboBox()
        self.payment_status.addItems(
            [
                "Pending",
                "Paid",
            ]
        )

        if package is not None:
            index = self.payment_status.findText(
                package.payment_status
            )

            if index >= 0:
                self.payment_status.setCurrentIndex(index)

        payment_form.addRow(tr("Mode"), self.payment_mode)
        payment_form.addRow(tr("Status"), self.payment_status)

        payment_group.setLayout(payment_form)

        # ---------- Resumen en vivo ----------

        summary_group = QGroupBox(tr("Summary"))
        summary_form = QFormLayout()

        self.block_price_label = QLabel()
        self.discount_label = QLabel()
        self.total_label = QLabel()

        summary_form.addRow(tr("Block Price"), self.block_price_label)
        summary_form.addRow(tr("Discount"), self.discount_label)
        summary_form.addRow(tr("Total"), self.total_label)

        summary_group.setLayout(summary_form)

        layout.addWidget(package_group)
        layout.addWidget(dates_group)
        layout.addWidget(payment_group)
        layout.addWidget(summary_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.accept_dialog)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # Recalcula el resumen al cambiar cualquier valor.
        self.classes.valueChanged.connect(self.update_summary)
        self.hourly_price.valueChanged.connect(self.update_summary)

        # El estado de pago solo tiene sentido al pagar por adelantado.
        self.payment_mode.currentTextChanged.connect(
            self.on_payment_mode_changed
        )

        # Enter = siguiente campo (sin cerrar el diálogo).
        enable_enter_to_next(self)

        self.on_payment_mode_changed(
            self.payment_mode.currentText()
        )

        self.update_summary()

    def on_payment_mode_changed(
        self,
        mode: str,
    ) -> None:
        """Habilita/deshabilita el estado de pago según el modo."""
        if mode == "Pay later":
            self.payment_status.setEnabled(False)
            self.payment_status.setCurrentText("Pending")
        else:
            self.payment_status.setEnabled(True)

    def update_summary(self) -> None:
        """Muestra en vivo el precio, descuento y total del bloque.

        El descuento es automático según las reglas configuradas:
        depende del número de clases de este bloque.
        """
        classes = self.classes.value()

        discount_percent = get_settings().discount_for_classes(
            classes
        )

        block_price = classes * self.hourly_price.value()
        total = block_price * (1 - discount_percent / 100)

        self.block_price_label.setText(
            f"$ {block_price:.2f}"
        )
        self.discount_label.setText(
            f"-{discount_percent}%"
        )
        self.total_label.setText(
            f"$ {total:.2f}"
        )

    def accept_dialog(self) -> None:
        self.package_data = {
            "classes": self.classes.value(),
            "hourly_price": self.hourly_price.value(),
            "discount": get_settings().discount_for_classes(
                self.classes.value()
            ),
            "payment_mode": self.payment_mode.currentText(),
            "payment_status": self.payment_status.currentText(),
            "date_of_payment": self.date_of_payment.date().toString(
                "yyyy-MM-dd"
            ),
            "date_of_start": self.date_of_start.date().toString(
                "yyyy-MM-dd"
            ),
        }

        self.accept()

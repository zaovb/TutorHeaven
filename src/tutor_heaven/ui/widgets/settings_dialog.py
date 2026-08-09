from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from tutor_heaven.data.settings_storage import (
    reload_settings,
    save_settings,
)
from tutor_heaven.ui.dialog_utils import FitDialog
from tutor_heaven.i18n import (
    LANGUAGE_ENGLISH,
    LANGUAGE_SPANISH,
    set_language,
    tr,
)
from tutor_heaven.models.settings_model import Settings
from tutor_heaven.ui.enter_navigation import enable_enter_to_next
from tutor_heaven.ui.themes import THEME_KEYS, THEME_NAMES, THEME_NAMES_ES


class SettingsDialog(FitDialog):
    """Dialog to edit the application settings.

    Configuración de la app: perfil del profesor, precios por defecto,
    descuentos por volumen, idioma de la interfaz y un bloc de notas.
    Al aceptar guarda en data/settings.json y recarga la cache global.
    """

    def __init__(
        self,
        settings: Settings,
    ) -> None:
        super().__init__()

        self.settings = settings

        self.setWindowTitle(tr("Settings"))
        self.setMinimumWidth(480)
        self.resize(520, 560)

        layout = QVBoxLayout(self)

        # El contenido de configuración va dentro de un área desplazable
        # para que, si no cabe en la ventana principal, aparezca una barra
        # de scroll en lugar de recortar o aplastar los campos.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        # ---------- Perfil del profesor ----------

        teacher_group = QGroupBox(tr("Teacher Profile"))
        teacher_form = QFormLayout()

        self.teacher_name = QLineEdit(settings.teacher_name)
        self.teacher_email = QLineEdit(settings.teacher_email)
        self.teacher_phone = QLineEdit(settings.teacher_phone)

        teacher_form.addRow(tr("Teacher Name"), self.teacher_name)
        teacher_form.addRow(tr("Teacher Email"), self.teacher_email)
        teacher_form.addRow(tr("Teacher Phone"), self.teacher_phone)

        teacher_group.setLayout(teacher_form)

        # ---------- Precios y descuentos ----------

        pricing_group = QGroupBox(tr("Prices"))
        pricing_form = QFormLayout()

        self.individual_price = QDoubleSpinBox()
        self.individual_price.setPrefix("$ ")
        self.individual_price.setDecimals(2)
        self.individual_price.setMaximum(1000)
        self.individual_price.setValue(settings.individual_price)

        self.group_price = QDoubleSpinBox()
        self.group_price.setPrefix("$ ")
        self.group_price.setDecimals(2)
        self.group_price.setMaximum(1000)
        self.group_price.setValue(settings.group_price)

        self.discount_5_threshold = QSpinBox()
        self.discount_5_threshold.setRange(1, 100)
        self.discount_5_threshold.setSuffix(" classes")
        self.discount_5_threshold.setValue(settings.discount_5_threshold)

        self.discount_5_percent = QSpinBox()
        self.discount_5_percent.setRange(0, 100)
        self.discount_5_percent.setSuffix(" %")
        self.discount_5_percent.setValue(settings.discount_5_percent)

        self.discount_10_threshold = QSpinBox()
        self.discount_10_threshold.setRange(1, 100)
        self.discount_10_threshold.setSuffix(" classes")
        self.discount_10_threshold.setValue(settings.discount_10_threshold)

        self.discount_10_percent = QSpinBox()
        self.discount_10_percent.setRange(0, 100)
        self.discount_10_percent.setSuffix(" %")
        self.discount_10_percent.setValue(settings.discount_10_percent)

        pricing_form.addRow(tr("Individual price"), self.individual_price)
        pricing_form.addRow(tr("Group price"), self.group_price)
        pricing_form.addRow(
            tr("Discount threshold 1"),
            self.discount_5_threshold,
        )
        pricing_form.addRow(tr("Discount 1"), self.discount_5_percent)
        pricing_form.addRow(
            tr("Discount threshold 2"),
            self.discount_10_threshold,
        )
        pricing_form.addRow(tr("Discount 2"), self.discount_10_percent)

        pricing_group.setLayout(pricing_form)

        # ---------- Idioma ----------

        language_group = QGroupBox(tr("Language"))
        language_form = QFormLayout()

        self.language_combo = QComboBox()
        self.language_combo.addItem(
            tr("English"),
            LANGUAGE_ENGLISH,
        )
        self.language_combo.addItem(
            tr("Spanish"),
            LANGUAGE_SPANISH,
        )

        index = self.language_combo.findData(
            settings.language
        )

        if index >= 0:
            self.language_combo.setCurrentIndex(index)

        language_form.addRow(
            tr("Language"),
            self.language_combo,
        )

        language_group.setLayout(language_form)

        # ---------- Tema ----------

        theme_group = QGroupBox(tr("Theme"))
        theme_form = QFormLayout()

        self.theme_combo = QComboBox()

        for key in THEME_KEYS:
            name = (
                THEME_NAMES_ES[key]
                if settings.language == LANGUAGE_SPANISH
                else THEME_NAMES[key]
            )

            self.theme_combo.addItem(name, key)

        index = self.theme_combo.findData(
            settings.theme
        )

        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        theme_form.addRow(
            tr("Theme"),
            self.theme_combo,
        )

        theme_group.setLayout(theme_form)

        # ---------- Marcas del calendario ----------

        marks_group = QGroupBox(tr("Calendar Marks"))
        marks_form = QFormLayout()

        self.marks_enabled = QCheckBox(
            tr("Show class marks in calendar")
        )
        self.marks_enabled.setChecked(
            settings.calendar_show_marks
        )

        self.marks_style = QComboBox()
        self.marks_style.addItem(tr("Dots"), "dots")
        self.marks_style.addItem(tr("Text"), "text")

        index = self.marks_style.findData(
            settings.calendar_marks_style
        )

        if index >= 0:
            self.marks_style.setCurrentIndex(index)

        # Sin marcas el estilo no aplica.
        self.marks_style.setEnabled(
            settings.calendar_show_marks
        )

        self.marks_enabled.toggled.connect(
            self.marks_style.setEnabled
        )

        marks_form.addRow(
            tr("Marks"),
            self.marks_enabled,
        )
        marks_form.addRow(
            tr("Marks Style"),
            self.marks_style,
        )

        marks_group.setLayout(marks_form)

        # ---------- Notas / ideas ----------

        notes_group = QGroupBox(tr("Notes"))
        notes_layout = QVBoxLayout()

        self.notes = QPlainTextEdit(settings.notes)
        self.notes.setPlaceholderText(
            tr(
                "Ideas, reminders, anything...\n"
                "(here Enter inserts a new line)"
            )
        )
        self.notes.setMinimumHeight(120)

        notes_layout.addWidget(self.notes)

        notes_group.setLayout(notes_layout)

        content_layout.addWidget(teacher_group)
        content_layout.addWidget(pricing_group)
        content_layout.addWidget(language_group)
        content_layout.addWidget(theme_group)
        content_layout.addWidget(marks_group)
        content_layout.addWidget(notes_group)

        content_layout.addStretch()

        scroll.setWidget(content)

        layout.addWidget(scroll, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )

        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        # Enter = siguiente campo (sin cerrar el diálogo). Las notas
        # son un QPlainTextEdit, así que conservan Enter = nueva línea.
        enable_enter_to_next(self)

    def save_settings(self) -> None:
        """Guarda la configuración editada en disco y la recarga."""
        self.settings.teacher_name = self.teacher_name.text()
        self.settings.teacher_email = self.teacher_email.text()
        self.settings.teacher_phone = self.teacher_phone.text()
        self.settings.individual_price = self.individual_price.value()
        self.settings.group_price = self.group_price.value()
        self.settings.discount_5_threshold = (
            self.discount_5_threshold.value()
        )
        self.settings.discount_5_percent = (
            self.discount_5_percent.value()
        )
        self.settings.discount_10_threshold = (
            self.discount_10_threshold.value()
        )
        self.settings.discount_10_percent = (
            self.discount_10_percent.value()
        )
        self.settings.notes = self.notes.toPlainText()

        # Aplica el idioma elegido de inmediato.
        self.settings.language = self.language_combo.currentData()

        set_language(
            self.settings.language
        )

        # Guarda el tema elegido.
        self.settings.theme = self.theme_combo.currentData()

        # Guarda las marcas del calendario.
        self.settings.calendar_show_marks = (
            self.marks_enabled.isChecked()
        )
        self.settings.calendar_marks_style = (
            self.marks_style.currentData()
        )

        save_settings(
            self.settings
        )

        # Recarga la cache global para que el resto de la app use
        # los nuevos valores de inmediato.
        reload_settings()

        self.accept()

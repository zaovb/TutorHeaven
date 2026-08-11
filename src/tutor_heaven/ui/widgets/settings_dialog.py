from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
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

        # Modo del tema: claro u oscuro.
        self.theme_mode = QComboBox()
        self.theme_mode.addItem(tr("Light"), "light")
        self.theme_mode.addItem(tr("Dark"), "dark")

        index = self.theme_mode.findData(
            settings.theme_mode
        )

        if index >= 0:
            self.theme_mode.setCurrentIndex(index)

        theme_form.addRow(
            tr("Mode"),
            self.theme_mode,
        )

        # Los dos colores de acento del tema. Se eligen con un selector
        # de color; el texto siempre se ajusta automáticamente al fondo.
        self.theme_primary = self._color_picker(
            settings.theme_primary,
            tr("Primary Color"),
            "primary",
        )

        self.theme_secondary = self._color_picker(
            settings.theme_secondary,
            tr("Secondary Color"),
            "secondary",
        )

        theme_form.addRow(
            tr("Primary Color"),
            self.theme_primary,
        )

        theme_form.addRow(
            tr("Secondary Color"),
            self.theme_secondary,
        )

        theme_group.setLayout(theme_form)

        # ---------- Bóveda de Obsidian ----------

        vault_group = QGroupBox(tr("Obsidian Vault"))
        vault_form = QFormLayout()

        # Genera una nota Markdown por estudiante, actualizada sola.
        self.vault_enabled = QCheckBox(
            tr("Enable Obsidian vault")
        )
        self.vault_enabled.setChecked(
            settings.vault_enabled
        )

        self.vault_path = QLineEdit(settings.vault_path)
        self.vault_path.setPlaceholderText("data/vault")
        self.vault_path.setToolTip(
            tr("Folder Obsidian will open as a vault.")
        )

        # Sin bóveda activa la carpeta no aplica.
        self.vault_path.setEnabled(
            settings.vault_enabled
        )

        self.vault_enabled.toggled.connect(
            self.vault_path.setEnabled
        )

        vault_hint = QLabel(
            tr(
                "One note per student, updated automatically "
                "as data changes."
            )
        )
        vault_hint.setWordWrap(True)

        vault_form.addRow(self.vault_enabled)
        vault_form.addRow(
            tr("Vault Folder"),
            self.vault_path,
        )
        vault_form.addRow(vault_hint)

        vault_group.setLayout(vault_form)

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
        content_layout.addWidget(vault_group)
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

    def _color_picker(
        self,
        initial: str,
        label: str,
        object_name: str,
    ) -> QPushButton:
        """Crea un botón que abre un selector de color.

        Muestra un cuadradito con el color actual y su código
        hexadecimal. Al pulsarlo se abre QColorDialog y, si se elige un
        color válido, se actualiza el botón.
        """
        button = QPushButton()

        button.setObjectName(object_name)
        button.setMinimumHeight(34)

        def choose() -> None:
            from PySide6.QtGui import QColor

            current = QColor(
                button.property("color") or initial
            )

            color = QColorDialog.getColor(
                current,
                self,
                label,
            )

            if not color.isValid():
                return

            button.setProperty(
                "color",
                color.name(),
            )
            button.setText(color.name())

            from tutor_heaven.ui.themes import _on_background

            text_color = _on_background(color)

            button.setStyleSheet(
                f"background-color: {color.name()}; "
                f"color: {text_color.name()}; "
                "border: 1px solid palette(mid); "
                "font-weight: 600; border-radius: 10px;"
            )

        button.clicked.connect(choose)

        button.setProperty(
            "color",
            initial,
        )
        button.setText(initial)

        from tutor_heaven.ui.themes import _on_background
        from PySide6.QtGui import QColor

        text_color = _on_background(QColor(initial))

        button.setStyleSheet(
            f"background-color: {initial}; "
            f"color: {text_color.name()}; "
            "border: 1px solid palette(mid); "
            "font-weight: 600; border-radius: 10px;"
        )

        return button

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

        # Guarda el tema elegido: modo y los dos colores de acento.
        self.settings.theme_mode = self.theme_mode.currentData()
        self.settings.theme_primary = (
            self.theme_primary.property("color")
            or self.theme_primary.text()
            or "#4A90D9"
        )
        self.settings.theme_secondary = (
            self.theme_secondary.property("color")
            or self.theme_secondary.text()
            or "#7A8694"
        )

        # Guarda la bóveda de Obsidian (activación y carpeta).
        self.settings.vault_enabled = (
            self.vault_enabled.isChecked()
        )
        self.settings.vault_path = (
            self.vault_path.text().strip()
        )

        save_settings(
            self.settings
        )

        # Recarga la cache global para que el resto de la app use
        # los nuevos valores de inmediato.
        reload_settings()

        self.accept()

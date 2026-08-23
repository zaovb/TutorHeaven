from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
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
from tutor_heaven.ui.dialog_utils import (
    FitDialog,
    make_value_field_manual,
)
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

        # Se pone en True si el usuario restauró el estado de fábrica;
        # la ventana principal lo usa para reconstruir toda la interfaz.
        self.factory_reset_done = False

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
        self.discount_5_threshold.setSuffix(tr(" hours"))
        self.discount_5_threshold.setValue(settings.discount_5_threshold)

        self.discount_5_percent = QSpinBox()
        self.discount_5_percent.setRange(0, 100)
        self.discount_5_percent.setSuffix(" %")
        self.discount_5_percent.setValue(settings.discount_5_percent)

        self.discount_10_threshold = QSpinBox()
        self.discount_10_threshold.setRange(1, 100)
        self.discount_10_threshold.setSuffix(tr(" hours"))
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

        # ---------- Backup en un .zip ----------

        backup_group = QGroupBox(tr("Backup"))
        backup_form = QFormLayout()

        # Exporta/actualiza un .zip con todos los datos (estudiantes,
        # sesiones, paquetes, configuración y notas Markdown). Se puede
        # descomprimir y abrir en cualquier editor, o restaurar desde
        # el programa sin descomprimir.
        self.backup_enabled = QCheckBox(
            tr("Enable automatic backup")
        )
        self.backup_enabled.setChecked(
            settings.backup_enabled
        )

        # La carpeta del backup debe estar FUERA del programa: si la app
        # se desinstala, la copia sobrevive. Se elige con un selector y
        # no se puede escribir a mano.
        self.backup_path = QLineEdit(settings.backup_path)
        self.backup_path.setPlaceholderText(
            tr("Choose a folder outside the app...")
        )
        self.backup_path.setReadOnly(True)
        self.backup_path.setToolTip(
            tr("The backup is stored outside the app so it survives an uninstall.")
        )

        browse_button = QPushButton(
            tr("📁 Choose Folder")
        )
        browse_button.clicked.connect(
            self.choose_backup_folder
        )

        backup_path_row = QWidget()
        backup_path_row_layout = QHBoxLayout(backup_path_row)
        backup_path_row_layout.setContentsMargins(0, 0, 0, 0)
        backup_path_row_layout.addWidget(
            self.backup_path,
            stretch=1,
        )
        backup_path_row_layout.addWidget(browse_button)

        # Sin backup activo la ruta no aplica.
        self.backup_path.setEnabled(
            settings.backup_enabled
        )
        browse_button.setEnabled(
            settings.backup_enabled
        )

        self.backup_enabled.toggled.connect(
            self.backup_path.setEnabled
        )
        self.backup_enabled.toggled.connect(
            browse_button.setEnabled
        )
        self.backup_enabled.toggled.connect(
            self.on_backup_enabled_changed
        )

        backup_hint = QLabel(
            tr(
                "A portable .zip with all data and readable notes. "
                "You can open it with any editor."
            )
        )
        backup_hint.setWordWrap(True)

        export_button = QPushButton(
            tr("📦 Export Backup Now")
        )
        export_button.clicked.connect(
            self.export_backup
        )

        restore_button = QPushButton(
            tr("♻ Restore from Backup")
        )
        restore_button.clicked.connect(
            self.restore_backup
        )

        backup_form.addRow(self.backup_enabled)
        backup_form.addRow(
            tr("Backup Folder"),
            backup_path_row,
        )
        backup_form.addRow(backup_hint)
        backup_form.addRow(export_button)
        backup_form.addRow(restore_button)

        backup_group.setLayout(backup_form)

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

        # ---------- Restablecer a estado de fábrica ----------

        reset_group = QGroupBox(tr("Danger Zone"))
        reset_layout = QVBoxLayout()

        reset_hint = QLabel(
            tr(
                "Deletes ALL data: students, sessions, tasks, notes "
                "and settings. The app returns to its factory state."
            )
        )
        reset_hint.setWordWrap(True)

        reset_button = QPushButton(
            tr("🗑 Restore to Factory State")
        )
        reset_button.clicked.connect(
            self.reset_to_factory
        )

        reset_layout.addWidget(reset_hint)
        reset_layout.addWidget(reset_button)

        reset_group.setLayout(reset_layout)

        content_layout.addWidget(teacher_group)
        content_layout.addWidget(pricing_group)
        content_layout.addWidget(language_group)
        content_layout.addWidget(theme_group)
        content_layout.addWidget(vault_group)
        content_layout.addWidget(backup_group)
        content_layout.addWidget(notes_group)
        content_layout.addWidget(reset_group)

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

        # Los valores solo se editan con el teclado: sin scroll ni flechas.
        for field in (
            self.individual_price,
            self.group_price,
            self.discount_5_threshold,
            self.discount_5_percent,
            self.discount_10_threshold,
            self.discount_10_percent,
            self.language_combo,
            self.theme_mode,
        ):
            make_value_field_manual(field)

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

    def _default_backup_folder(self) -> str:
        """Carpeta por defecto sugerida para la copia de seguridad.

        Usa la carpeta "Documentos" del usuario (fuera del programa)
        si existe; si no, el directorio personal.
        """
        documents = Path.home() / "Documents"

        if documents.is_dir():
            return str(documents)

        return str(Path.home())

    def choose_backup_folder(self) -> None:
        """Abre un selector para elegir dónde guardar el .zip.

        La carpeta elegida debe quedar FUERA de la carpeta del
        programa; si el usuario elige una carpeta interna, se avisa y
        no se acepta. La ruta se guarda con el nombre de archivo
        del backup por defecto.
        """
        from tutor_heaven.data.backup import is_path_inside_program

        folder = QFileDialog.getExistingDirectory(
            self,
            tr("Choose Backup Folder"),
            self._default_backup_folder(),
        )

        if not folder:
            return

        if is_path_inside_program(folder):
            QMessageBox.warning(
                self,
                tr("Backup"),
                tr(
                    "The backup folder cannot be inside the app folder.\n\n"
                    "Choose an external location (for example Documents) "
                    "so the backup survives an uninstall."
                ),
            )
            return

        self.backup_path.setText(
            str(Path(folder) / "tutor_heaven_backup.zip")
        )

    def on_backup_enabled_changed(
        self,
        enabled: bool,
    ) -> None:
        """Al activar el backup exige una carpeta externa.

        Si el usuario marca la casilla sin tener una ruta válida, se
        abre el selector de carpeta. Si cancela o elige una ruta
        interna, se desmarca la casilla.
        """
        if not enabled:
            return

        from tutor_heaven.data.backup import is_path_inside_program

        current = self.backup_path.text().strip()

        if current and not is_path_inside_program(current):
            return

        self.backup_path.clear()
        self.choose_backup_folder()

        if not self.backup_path.text().strip():
            self.backup_enabled.setChecked(False)

    def reset_to_factory(self) -> None:
        """Restaura todos los datos al estado de fábrica.

        Pide confirmación antes de borrar nada. Al final recarga la
        configuración por defecto y avisa de que la app quedó limpia.
        """
        confirm = QMessageBox.warning(
            self,
            tr("Restore to Factory State"),
            tr(
                "This will delete ALL data:\n\n"
                "• Students, sessions and packages\n"
                "• Teacher tasks\n"
                "• Notes and settings\n\n"
                "This cannot be undone. Continue?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        from tutor_heaven.data.factory_reset import factory_reset

        factory_reset()

        # Recarga la configuración mostrada (ahora los valores por
        # defecto).
        self.refresh_after_restore()

        self.factory_reset_done = True

        QMessageBox.information(
            self,
            tr("Restore to Factory State"),
            tr(
                "The app has been restored to its factory state.\n"
                "All data was deleted."
            ),
        )

    def export_backup(self) -> None:
        """Exporta un .zip con todos los datos.

        El usuario elige dónde guardar el archivo; por defecto se
        sugiere la ruta configurada. La exportación no toca los datos
        actuales, solo produce una copia portable.
        """
        from tutor_heaven.data.backup import export_backup

        default = self.backup_path.text().strip() or str(
            Path(self._default_backup_folder())
            / "tutor_heaven_backup.zip"
        )

        target, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export Backup"),
            default,
            tr("Backup file (*.zip)"),
        )

        if not target:
            return

        try:
            export_backup(target)
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("Backup"),
                tr("Could not export the backup:\n{0}").format(
                    error
                ),
            )

            return

        QMessageBox.information(
            self,
            tr("Backup"),
            tr("Backup exported successfully to:\n{0}").format(
                target
            ),
        )

    def restore_backup(self) -> None:
        """Restaura todos los datos desde un .zip de backup.

        Pide confirmación antes de sobrescribir los datos actuales y
        avisa al terminar de qué se restauró.
        """
        from tutor_heaven.data.backup import restore_backup

        source, _ = QFileDialog.getOpenFileName(
            self,
            tr("Restore from Backup"),
            "",
            tr("Backup file (*.zip)"),
        )

        if not source:
            return

        confirm = QMessageBox.question(
            self,
            tr("Restore from Backup"),
            tr(
                "Restore all data from the backup?\n\n"
                "Current students, sessions and settings will be "
                "overwritten. This cannot be undone."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            payload = restore_backup(source)
        except Exception as error:
            QMessageBox.critical(
                self,
                tr("Restore from Backup"),
                tr(
                    "Could not restore from the backup:\n{0}"
                ).format(
                    error
                ),
            )

            return

        # Refresca la configuración mostrada por si el backup traía
        # valores distintos (idioma, tema, precios...).
        self.refresh_after_restore()

        # Regenera la bóveda de Obsidian y el backup con los datos
        # restaurados, por si la configuración o los datos cambiaron.
        from tutor_heaven.data.vault import sync_vault
        from tutor_heaven.data.backup import update_backup

        sync_vault()
        update_backup()

        QMessageBox.information(
            self,
            tr("Restore from Backup"),
            tr(
                "Data restored successfully:\n"
                "{0} students, {1} deleted, {2} teacher tasks."
            ).format(
                len(payload.get("students", [])),
                len(payload.get("deleted_students", [])),
                len(payload.get("teacher_tasks", [])),
            ),
        )

    def refresh_after_restore(self) -> None:
        """Recarga los campos del diálogo con la configuración
        restaurada desde el backup."""
        settings = reload_settings()

        self.settings = settings

        self.teacher_name.setText(settings.teacher_name)
        self.teacher_email.setText(settings.teacher_email)
        self.teacher_phone.setText(settings.teacher_phone)
        self.individual_price.setValue(settings.individual_price)
        self.group_price.setValue(settings.group_price)
        self.discount_5_threshold.setValue(
            settings.discount_5_threshold
        )
        self.discount_5_percent.setValue(
            settings.discount_5_percent
        )
        self.discount_10_threshold.setValue(
            settings.discount_10_threshold
        )
        self.discount_10_percent.setValue(
            settings.discount_10_percent
        )
        self.notes.setPlainText(settings.notes)

        self.language_combo.setCurrentIndex(
            self.language_combo.findData(
                settings.language
            )
        )

        self.theme_mode.setCurrentIndex(
            self.theme_mode.findData(
                settings.theme_mode
            )
        )

        self.theme_primary.setProperty(
            "color",
            settings.theme_primary,
        )
        self.theme_primary.setText(settings.theme_primary)

        self.theme_secondary.setProperty(
            "color",
            settings.theme_secondary,
        )
        self.theme_secondary.setText(settings.theme_secondary)

        self.vault_enabled.setChecked(settings.vault_enabled)
        self.vault_path.setText(settings.vault_path)

        # Primero la ruta, luego la casilla: al marcarla se comprueba si
        # la carpeta es válida (externa) antes de pedir que la elija.
        self.backup_path.setText(settings.backup_path)
        self.backup_enabled.setChecked(settings.backup_enabled)

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

        # Guarda el backup (activación y ruta del .zip).
        backup_enabled = self.backup_enabled.isChecked()
        backup_path = self.backup_path.text().strip()

        if backup_enabled:
            from tutor_heaven.data.backup import is_path_inside_program

            if not backup_path or is_path_inside_program(backup_path):
                QMessageBox.warning(
                    self,
                    tr("Backup"),
                    tr(
                        "Automatic backup needs a folder OUTSIDE the app.\n\n"
                        "Choose an external location (for example Documents) "
                        "so the backup survives an uninstall."
                    ),
                )

                return

        self.settings.backup_enabled = backup_enabled
        self.settings.backup_path = backup_path

        save_settings(
            self.settings
        )

        # Recarga la cache global para que el resto de la app use
        # los nuevos valores de inmediato.
        reload_settings()

        self.accept()

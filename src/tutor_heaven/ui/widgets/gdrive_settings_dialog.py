"""Diálogo de configuración de Google Drive.

Permite conectar/desconectar Google Drive, elegir modo de sync
(automático o manual) y forzar un sync manual.
"""

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from tutor_heaven.data.gdrive_service import GDriveService
from tutor_heaven.data.gdrive_sync import get_gdrive_sync
from tutor_heaven.data.settings_storage import (
    get_settings,
    save_settings,
)
from tutor_heaven.i18n import tr
from tutor_heaven.ui.dialog_utils import FitDialog


class _AuthWorker(QThread):
    """Ejecuta la autenticación OAuth2 en un hilo separado."""

    success = Signal()
    error = Signal(str)

    def __init__(self, service: GDriveService) -> None:
        super().__init__()
        self._service = service

    def run(self) -> None:
        try:
            self._service.authenticate()
            self.success.emit()
        except Exception as exc:
            self.error.emit(str(exc))


class GDriveSettingsDialog(FitDialog):
    """Diálogo de configuración de Google Drive."""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle(tr("Google Drive"))
        self.setMinimumWidth(480)

        self._service = GDriveService()
        self._auth_worker = None

        layout = QVBoxLayout(self)

        # -- Estado de conexión -------------------------------------------
        status_group = QGroupBox(tr("Connection"))
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel()
        status_layout.addWidget(self._status_label)

        btn_layout = QHBoxLayout()

        self._connect_btn = QPushButton(tr("Connect"))
        self._connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self._connect_btn)

        self._disconnect_btn = QPushButton(tr("Disconnect"))
        self._disconnect_btn.clicked.connect(self._on_disconnect)
        btn_layout.addWidget(self._disconnect_btn)

        status_layout.addLayout(btn_layout)
        layout.addWidget(status_group)

        # -- Configuración de sync ----------------------------------------
        sync_group = QGroupBox(tr("Sync"))
        sync_form = QFormLayout(sync_group)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem(tr("Automatic (on data change)"), "auto")
        self._mode_combo.addItem(tr("Manual (button only)"), "manual")
        sync_form.addRow(tr("Sync mode:"), self._mode_combo)

        self._root_folder_input = QLineEdit()
        self._root_folder_input.setPlaceholderText("TutorHeaven")
        sync_form.addRow(tr("Root folder:"), self._root_folder_input)

        layout.addWidget(sync_group)

        # -- Sync manual --------------------------------------------------
        manual_group = QGroupBox(tr("Manual Sync"))
        manual_layout = QVBoxLayout(manual_group)

        self._sync_btn = QPushButton(tr("Sync Now"))
        self._sync_btn.clicked.connect(self._on_sync_now)
        manual_layout.addWidget(self._sync_btn)

        self._sync_status = QLabel()
        manual_layout.addWidget(self._sync_status)

        layout.addWidget(manual_group)

        # -- Instrucciones ------------------------------------------------
        info_label = QLabel(
            tr(
                "To connect, you need a credentials.json file "
                "from Google Cloud Console. Place it at:\n{0}"
            ).format(
                str(self._service._secrets_path)
            )
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888;")
        layout.addWidget(info_label)

        layout.addStretch()

        # -- Botones ------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_state()

    def _load_state(self) -> None:
        """Carga el estado actual de la configuración."""
        settings = get_settings()

        # Estado de conexión.
        if self._service.is_authenticated():
            self._status_label.setText(
                tr("Status: Connected")
            )
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(True)
        elif self._service.is_configured():
            self._status_label.setText(
                tr("Status: Not authenticated")
            )
            self._connect_btn.setEnabled(True)
            self._disconnect_btn.setEnabled(False)
        else:
            self._status_label.setText(
                tr("Status: No credentials.json found")
            )
            self._connect_btn.setEnabled(False)
            self._disconnect_btn.setEnabled(False)

        # Configuración de sync.
        idx = self._mode_combo.findData(settings.gdrive_sync_mode)
        if idx >= 0:
            self._mode_combo.setCurrentIndex(idx)

        self._root_folder_input.setText(
            settings.gdrive_root_folder
        )

    def _on_connect(self) -> None:
        """Inicia la autenticación OAuth2."""
        self._connect_btn.setEnabled(False)
        self._connect_btn.setText(tr("Connecting..."))

        self._auth_worker = _AuthWorker(self._service)
        self._auth_worker.success.connect(self._on_auth_success)
        self._auth_worker.error.connect(self._on_auth_error)
        self._auth_worker.start()

    def _on_auth_success(self) -> None:
        self._status_label.setText(tr("Status: Connected"))
        self._connect_btn.setText(tr("Connect"))
        self._connect_btn.setEnabled(False)
        self._disconnect_btn.setEnabled(True)

        QMessageBox.information(
            self,
            tr("Google Drive"),
            tr("Connected successfully!"),
        )

    def _on_auth_error(self, message: str) -> None:
        self._connect_btn.setText(tr("Connect"))
        self._connect_btn.setEnabled(True)

        QMessageBox.warning(
            self,
            tr("Connection Error"),
            message,
        )

    def _on_disconnect(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("Disconnect"),
            tr("Disconnect from Google Drive?"),
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self._service.disconnect()
        self._load_state()

    def _on_sync_now(self) -> None:
        """Ejecuta un sync manual."""
        self._sync_btn.setEnabled(False)
        self._sync_btn.setText(tr("Syncing..."))
        self._sync_status.setText(tr("Sync in progress..."))

        manager = get_gdrive_sync()
        manager.sync_now()

        # Verificar resultado después de un momento.
        from PySide6.QtCore import QTimer

        QTimer.singleShot(500, self._check_sync_result)

    def _check_sync_result(self) -> None:
        manager = get_gdrive_sync()

        if manager.is_running():
            QTimer.singleShot(1000, self._check_sync_result)
            return

        self._sync_btn.setEnabled(True)
        self._sync_btn.setText(tr("Sync Now"))
        self._sync_status.setText(tr("Sync completed!"))

    def _save_and_accept(self) -> None:
        """Guarda la configuración y cierra."""
        settings = get_settings()
        settings.gdrive_sync_mode = (
            self._mode_combo.currentData()
        )
        settings.gdrive_root_folder = (
            self._root_folder_input.text().strip()
        )

        save_settings(settings)
        self.accept()

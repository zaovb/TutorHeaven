"""Sincronización automática del vault con Google Drive.

Observa cambios en el vault y los sube a Google Drive con debounce
para no saturar la API.  Soporta modo automático (se dispara solo)
y manual (solo cuando el usuario lo pide).
"""

import time
import traceback
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from tutor_heaven.data.gdrive_service import GDriveService
from tutor_heaven.data.settings_storage import get_settings
from tutor_heaven.data.vault import (
    ACTIVE_FOLDER,
    DELETED_FOLDER,
    vault_dir,
)
from tutor_heaven.i18n import tr


class _SyncWorker(QThread):
    """Ejecuta el sync en un hilo separado para no bloquear la UI."""

    finished = Signal(str)
    error = Signal(str)

    def __init__(self, service: GDriveService) -> None:
        super().__init__()
        self._service = service

    def run(self) -> None:
        try:
            self._do_sync()
            self.finished.emit(tr("Sync completed successfully"))
        except Exception as exc:
            self.error.emit(str(exc))
            traceback.print_exc()

    def _do_sync(self) -> None:
        """Sincroniza la estructura del vault con Google Drive."""
        settings = get_settings()
        vault_path = vault_dir()

        if not vault_path.is_dir():
            return

        # Crear o encontrar la carpeta raíz en Drive.
        root_name = settings.gdrive_root_folder or "TutorHeaven"
        root_id = self._service.find_or_create_folder(root_name)

        # Sincronizar carpeta de activos.
        active_dir = vault_path / ACTIVE_FOLDER
        if active_dir.is_dir():
            self._sync_folder(active_dir, root_id, ACTIVE_FOLDER)

        # Sincronizar carpeta de eliminados.
        deleted_dir = vault_path / DELETED_FOLDER
        if deleted_dir.is_dir():
            self._sync_folder(deleted_dir, root_id, DELETED_FOLDER)

        # Sincronizar el índice.
        index_file = vault_path / "_Estudiantes.md"
        if index_file.exists():
            self._service.upload_file(index_file, root_id)

    def _sync_folder(
        self,
        local_parent: Path,
        drive_parent_id: str,
        folder_label: str,
    ) -> None:
        """Sincroniza una carpeta de estudiantes (Estudiantes/ o Eliminados/)."""
        # Crear la carpeta contenedora en Drive.
        container_id = self._service.find_or_create_folder(
            folder_label, drive_parent_id
        )

        for student_dir in local_parent.iterdir():
            if not student_dir.is_dir():
                continue

            # Crear carpeta del estudiante.
            student_folder_id = self._service.find_or_create_folder(
                student_dir.name, container_id
            )

            # Subir cada archivo.
            for file_path in student_dir.iterdir():
                if file_path.is_file():
                    self._service.upload_file(
                        file_path, student_folder_id
                    )

            # Compartir con el estudiante si tiene email.
            self._maybe_share(student_dir.name, student_folder_id)

    def _maybe_share(
        self, student_name: str, folder_id: str
    ) -> None:
        """Comparte la carpeta con el email del estudiante (si tiene)."""
        from tutor_heaven.data.student_storage import load_students

        for student in load_students():
            if student.name == student_name and student.email:
                try:
                    self._service.share_folder(
                        folder_id, student.email, role="reader"
                    )
                except Exception:
                    # El permiso ya existe u otro error — ignorar.
                    pass
                return


class GDriveSyncManager(QObject):
    """Gestiona la sincronización del vault con Google Drive.

    Se instancia una vez y se conecta a las señales de la aplicación.
    """

    sync_started = Signal()
    sync_finished = Signal(str)
    sync_error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._service = GDriveService()
        self._worker: _SyncWorker | None = None

        # Timer de debounce para sync automático.
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(3000)  # 3 segundos
        self._debounce.timeout.connect(self._run_sync)

    @property
    def service(self) -> GDriveService:
        return self._service

    def is_running(self) -> bool:
        """True si hay un sync en curso."""
        return self._worker is not None and self._worker.isRunning()

    def request_sync(self) -> None:
        """Pide un sync.  En modo auto usa debounce, en manual ejecuta ya."""
        settings = get_settings()

        if not settings.gdrive_enabled:
            return

        if not self._service.is_authenticated():
            return

        if settings.gdrive_sync_mode == "auto":
            self._debounce.start()
        else:
            self._run_sync()

    def sync_now(self) -> None:
        """Fuerza un sync inmediato (para botón manual)."""
        if not self._service.is_authenticated():
            return

        self._run_sync()

    @Slot()
    def _run_sync(self) -> None:
        """Ejecuta el sync en un hilo separado."""
        if self.is_running():
            return

        self.sync_started.emit()
        self._worker = _SyncWorker(self._service)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.error.connect(self._on_sync_error)
        self._worker.start()

    def _on_sync_finished(self, message: str) -> None:
        self._worker = None
        self.sync_finished.emit(message)

    def _on_sync_error(self, message: str) -> None:
        self._worker = None
        self.sync_error.emit(message)


# Instancia global del gestor de sync.
_manager: GDriveSyncManager | None = None


def get_gdrive_sync() -> GDriveSyncManager:
    """Devuelve la instancia global del gestor de sync."""
    global _manager

    if _manager is None:
        _manager = GDriveSyncManager()

    return _manager


def start_gdrive_sync() -> None:
    """Conecta el sync de Google Drive a las señales de datos.

    Se llama una sola vez al arrancar la aplicación.
    """
    from tutor_heaven.data.data_bus import get_bus

    manager = get_gdrive_sync()

    get_bus().studentsChanged.connect(
        manager.request_sync
    )

    get_bus().teacherTasksChanged.connect(
        manager.request_sync
    )

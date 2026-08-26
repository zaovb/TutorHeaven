"""Servicio de Google Drive: autenticación, subida y compartir.

Maneja la autenticación OAuth2 con Google Drive API v3, la subida de
archivos y carpetas, y el compartido de carpetas con usuarios
específicos (estudiantes por email).
"""

import mimetypes
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from tutor_heaven.data.paths import data_dir
from tutor_heaven.i18n import tr

# Scopes necesarios: subir archivos y gestionar permisos.
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
]

# Carpeta donde se guardan las credenciales del usuario.
_CREDENTIALS_DIR = data_dir() / "google_drive"


class GDriveService:
    """Wrapper de Google Drive API v3.

    Maneja autenticación OAuth2, creación de carpetas, subida de
    archivos y compartido con usuarios.
    """

    def __init__(self) -> None:
        self._service = None

    # -- Autenticación ---------------------------------------------------

    @property
    def _token_path(self) -> Path:
        return _CREDENTIALS_DIR / "token.json"

    @property
    def _secrets_path(self) -> Path:
        return _CREDENTIALS_DIR / "credentials.json"

    def is_configured(self) -> bool:
        """True si existen las credenciales OAuth2."""
        return self._secrets_path.exists()

    def is_authenticated(self) -> bool:
        """True si hay un token válido (o refreshable)."""
        if not self._token_path.exists():
            return False

        try:
            creds = Credentials.from_authorized_user_file(
                str(self._token_path), SCOPES
            )
            return creds.valid or (
                creds.expired and creds.refresh_token
            )
        except Exception:
            return False

    def authenticate(self) -> None:
        """Abre el navegador para autenticar con Google.

        Lanza ``FileNotFoundError`` si no existe credentials.json.
        Lanza ``RuntimeError`` si falla la autenticación.
        """
        if not self._secrets_path.exists():
            raise FileNotFoundError(
                tr(
                    "credentials.json not found at:\n{0}\n\n"
                    "Download it from Google Cloud Console."
                ).format(self._secrets_path)
            )

        creds = None

        if self._token_path.exists():
            creds = Credentials.from_authorized_user_file(
                str(self._token_path), SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._secrets_path), SCOPES
                )
                creds = flow.run_local_server(
                    port=0,
                    prompt="consent",
                )

        _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)

        self._token_path.write_text(
            creds.to_json(),
            encoding="utf-8",
        )

        self._service = None

    def disconnect(self) -> None:
        """Elimina el token guardado y desconecta."""
        if self._token_path.exists():
            self._token_path.unlink()

        self._service = None

    def _get_service(self):
        """Devuelve el servicio de Drive (lazy init)."""
        if self._service is not None:
            return self._service

        if not self._token_path.exists():
            raise RuntimeError(tr("Not authenticated with Google Drive"))

        creds = Credentials.from_authorized_user_file(
            str(self._token_path), SCOPES
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            _CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
            self._token_path.write_text(
                creds.to_json(),
                encoding="utf-8",
            )

        self._service = build("drive", "v3", credentials=creds)
        return self._service

    # -- Operaciones de Drive -------------------------------------------

    def find_or_create_folder(
        self,
        name: str,
        parent_id: str = "root",
    ) -> str:
        """Busca una carpeta por nombre y padre, o la crea.

        Devuelve el ID de la carpeta.
        """
        service = self._get_service()

        query = (
            f"'{parent_id}' in parents "
            f"and name = '{name}' "
            f"and mimeType = 'application/vnd.google-apps.folder' "
            f"and trashed = false"
        )

        results = (
            service.files()
            .list(q=query, fields="files(id)", spaces="drive")
            .execute()
        )

        if results["files"]:
            return results["files"][0]["id"]

        folder = (
            service.files()
            .create(
                body={
                    "name": name,
                    "mimeType": (
                        "application/vnd.google-apps.folder"
                    ),
                    "parents": [parent_id],
                },
                fields="id",
            )
            .execute()
        )

        return folder["id"]

    def _find_file_in_folder(
        self,
        name: str,
        folder_id: str,
    ) -> dict | None:
        """Busca un archivo por nombre dentro de una carpeta."""
        service = self._get_service()

        query = (
            f"'{folder_id}' in parents "
            f"and name = '{name}' "
            f"and trashed = false"
        )

        results = (
            service.files()
            .list(
                q=query,
                fields="files(id, name)",
                spaces="drive",
            )
            .execute()
        )

        return results["files"][0] if results["files"] else None

    def upload_file(
        self,
        local_path: Path,
        folder_id: str,
    ) -> str:
        """Sube un archivo local a una carpeta de Drive.

        Si ya existe un archivo con el mismo nombre, lo actualiza.
        Devuelve el ID del archivo.
        """
        service = self._get_service()

        mime_type = (
            mimetypes.guess_type(str(local_path))[0]
            or "application/octet-stream"
        )

        existing = self._find_file_in_folder(
            local_path.name, folder_id
        )

        media = MediaFileUpload(
            str(local_path),
            mimetype=mime_type,
            resumable=True,
        )

        if existing:
            (
                service.files()
                .update(
                    fileId=existing["id"],
                    media_body=media,
                )
                .execute()
            )
            return existing["id"]

        file_metadata = {
            "name": local_path.name,
            "parents": [folder_id],
        }

        file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id",
            )
            .execute()
        )

        return file["id"]

    def share_folder(
        self,
        folder_id: str,
        email: str,
        role: str = "reader",
        send_notification: bool = True,
    ) -> str:
        """Comparte una carpeta con un usuario por email.

        Roles: "reader", "writer", "commenter".
        Devuelve el ID del permiso.
        """
        service = self._get_service()

        permission = {
            "type": "user",
            "role": role,
            "emailAddress": email,
        }

        result = (
            service.permissions()
            .create(
                fileId=folder_id,
                body=permission,
                sendNotificationEmail=send_notification,
                fields="id",
            )
            .execute()
        )

        return result["id"]

    def remove_permission(
        self,
        folder_id: str,
        permission_id: str,
    ) -> None:
        """Elimina un permiso de una carpeta."""
        service = self._get_service()

        (
            service.permissions()
            .deletePermissionId(
                fileId=folder_id,
                permissionId=permission_id,
            )
            .execute()
        )

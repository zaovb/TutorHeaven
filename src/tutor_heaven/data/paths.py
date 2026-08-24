"""Determina la ruta correcta para los archivos de datos.

En desarrollo (venv), los datos viven en ``data/`` junto al código.
Instalado en ``/opt/``, los datos van al directorio del usuario
(``~/.local/share/tutor-heaven/``) para no necesitar permisos root.
"""

import os
from pathlib import Path

# Raíz del proyecto fuente (src/tutor_heaven/data/paths.py → raíz).
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    """Devuelve el directorio de datos writable.

    Si el ``data/`` del proyecto existe y es escribible (desarrollo),
    lo usa.  Si no (instalación en /opt/), crea y devuelve
    ``~/.local/share/tutor-heaven/``.
    """
    dev_data = PROJECT_ROOT / "data"

    if dev_data.exists() and os.access(dev_data, os.W_OK):
        return dev_data

    user_data = Path.home() / ".local" / "share" / "tutor-heaven"
    user_data.mkdir(parents=True, exist_ok=True)

    return user_data

import json
from pathlib import Path

from tutor_heaven.models.settings_model import Settings

# Ruta absoluta al archivo de configuración. Igual que en
# student_storage.py, se resuelve desde la raíz del proyecto para que
# funcione sin importar el directorio de trabajo.
PROJECT_ROOT = Path(__file__).resolve().parents[3]

SETTINGS_FILE = PROJECT_ROOT / "data" / "settings.json"

# Cache en memoria para que toda la app comparta la misma instancia de
# Settings sin tener que pasarla por todos los constructores.
_settings_cache: Settings | None = None


def get_settings() -> Settings:
    """Devuelve la configuración actual (con cache).

    Carga el archivo la primera vez y mantiene la instancia en memoria;
    es la vía habitual de lectura desde toda la app.
    """
    global _settings_cache

    if _settings_cache is None:
        _settings_cache = load_settings()

    return _settings_cache


def reload_settings() -> Settings:
    """Recarga la configuración desde disco y actualiza la cache.

    Se llama después de guardar desde SettingsDialog para que el resto
    de la app vea inmediatamente los cambios.
    """
    global _settings_cache

    _settings_cache = load_settings()

    return _settings_cache


def save_settings(
    settings: Settings,
) -> None:
    """Persiste la configuración en data/settings.json."""
    SETTINGS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "teacher_name": settings.teacher_name,
        "teacher_email": settings.teacher_email,
        "teacher_phone": settings.teacher_phone,
        "individual_price": settings.individual_price,
        "group_price": settings.group_price,
        "discount_5_threshold": settings.discount_5_threshold,
        "discount_5_percent": settings.discount_5_percent,
        "discount_10_threshold": settings.discount_10_threshold,
        "discount_10_percent": settings.discount_10_percent,
        "notes": settings.notes,
        "language": settings.language,
        "theme_mode": settings.theme_mode,
        "theme_primary": settings.theme_primary,
        "theme_secondary": settings.theme_secondary,
        "calendar_show_marks": settings.calendar_show_marks,
        "calendar_marks_style": settings.calendar_marks_style,
        "vault_enabled": settings.vault_enabled,
        "vault_path": settings.vault_path,
    }

    SETTINGS_FILE.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_settings() -> Settings:
    """Carga la configuración desde data/settings.json.

    Si el archivo no existe devuelve los valores por defecto. Cada
    campo se lee con get() para tolerar archivos parciales (por
    ejemplo, versiones anteriores sin algún campo nuevo).
    """
    if not SETTINGS_FILE.exists():
        return Settings()

    data = json.loads(
        SETTINGS_FILE.read_text(
            encoding="utf-8"
        )
    )

    return Settings(
        teacher_name=data.get(
            "teacher_name",
            "",
        ),
        teacher_email=data.get(
            "teacher_email",
            "",
        ),
        teacher_phone=data.get(
            "teacher_phone",
            "",
        ),
        individual_price=data.get(
            "individual_price",
            20.0,
        ),
        group_price=data.get(
            "group_price",
            15.0,
        ),
        discount_5_threshold=data.get(
            "discount_5_threshold",
            5,
        ),
        discount_5_percent=data.get(
            "discount_5_percent",
            5,
        ),
        discount_10_threshold=data.get(
            "discount_10_threshold",
            10,
        ),
        discount_10_percent=data.get(
            "discount_10_percent",
            10,
        ),
        notes=data.get(
            "notes",
            "",
        ),
        language=data.get(
            "language",
            "en",
        ),
        theme_mode=data.get(
            "theme_mode",
            "light",
        ),
        theme_primary=data.get(
            "theme_primary",
            "#4A90D9",
        ),
        theme_secondary=data.get(
            "theme_secondary",
            "#7A8694",
        ),
        calendar_show_marks=data.get(
            "calendar_show_marks",
            True,
        ),
        calendar_marks_style=data.get(
            "calendar_marks_style",
            "dots",
        ),
        vault_enabled=data.get(
            "vault_enabled",
            False,
        ),
        vault_path=data.get(
            "vault_path",
            "",
        ),
    )

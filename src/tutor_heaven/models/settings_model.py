from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    """Application settings.

    Configuración de la aplicación: perfil del profesor, precios por
    defecto de los paquetes, reglas de descuento automático y un bloc
    de notas para ideas.
    """

    # Perfil del profesor.
    teacher_name: str = ""
    teacher_email: str = ""
    teacher_phone: str = ""

    # Precios por hora por defecto según el tipo de estudiante.
    individual_price: float = 20.0
    group_price: float = 15.0

    # Reglas de descuento automático por volumen.
    # Umbral de horas para el primer tramo (por defecto 5).
    discount_5_threshold: int = 5
    # Porcentaje de descuento para ese tramo (por defecto 5%).
    discount_5_percent: int = 5
    # Umbral de horas para el segundo tramo (por defecto 10).
    discount_10_threshold: int = 10
    # Porcentaje de descuento para ese tramo (por defecto 10%).
    discount_10_percent: int = 10

    # Bloc de notas para ideas y notas personales del tutor.
    notes: str = ""

    # Idioma de la interfaz: "en" (inglés) o "es" (español).
    language: str = "en"

    # Tema de la interfaz. El cambio de tema solo afecta a los colores:
    # se elige un modo (claro u oscuro) y dos colores de acento
    # (primary y secondary). El resto de la paleta se deriva de estos
    # valores con contraste automático para el texto.
    theme_mode: str = "light"
    theme_primary: str = "#4A90D9"
    theme_secondary: str = "#7A8694"

    # Bóveda de Obsidian (opcional): una nota Markdown por estudiante,
    # regenerada automáticamente al cambiar los datos.
    # vault_enabled: activa o desactiva la generación de la bóveda.
    # vault_path: carpeta de la bóveda (vacío = data/vault por defecto).
    vault_enabled: bool = False
    vault_path: str = ""

    # Backup en un .zip: un JSON consolidado con todos los datos (perfil
    # del profesor, configuración, estudiantes, papelera y tareas) y sus
    # notas Markdown. backup_enabled: genera/actualiza el .zip solo al
    # cambiar los datos. backup_path: ruta del .zip (vacío =
    # data/tutor_heaven_backup.zip).
    backup_enabled: bool = False
    backup_path: str = ""

    # Google Drive: sincronización automática del vault con Drive.
    # gdrive_enabled: activa o desactiva la sincronización.
    # gdrive_sync_mode: "auto" (al cambiar datos) o "manual" (botón).
    # gdrive_root_folder: nombre de la carpeta raíz en Drive.
    gdrive_enabled: bool = False
    gdrive_sync_mode: str = "auto"
    gdrive_root_folder: str = "TutorHeaven"

    def discount_for_hours(self, hours: float) -> int:
        """Descuento automático (%) que corresponde a una cantidad de horas.

        Aplica las reglas configuradas: el segundo tramo gana cuando el
        número de horas alcanza (o supera) su umbral, después el primer
        tramo, y 0% si no llega a ningún umbral. La comparación tolera
        un mínimo margen por redondeo binario de los floats.
        """
        if hours >= self.discount_10_threshold - 1e-9:
            return self.discount_10_percent

        if hours >= self.discount_5_threshold - 1e-9:
            return self.discount_5_percent

        return 0

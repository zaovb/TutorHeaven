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
    # Umbral de clases para el primer tramo (por defecto 5).
    discount_5_threshold: int = 5
    # Porcentaje de descuento para ese tramo (por defecto 5%).
    discount_5_percent: int = 5
    # Umbral de clases para el segundo tramo (por defecto 10).
    discount_10_threshold: int = 10
    # Porcentaje de descuento para ese tramo (por defecto 10%).
    discount_10_percent: int = 10

    # Bloc de notas para ideas y notas personales del tutor.
    notes: str = ""

    # Idioma de la interfaz: "en" (inglés) o "es" (español).
    language: str = "en"

    # Tema de la interfaz: "classic", "black_white" o "coffee_royal".
    theme: str = "classic"

    # Marcas de clase en el calendario.
    # calendar_show_marks: activa o desactiva las marcas (vista/pagada).
    # calendar_marks_style: "dots" (puntos de colores) o "text" (texto).
    calendar_show_marks: bool = True
    calendar_marks_style: str = "dots"

    def discount_for_classes(self, classes: int) -> int:
        """Descuento automático (%) que corresponde a un número de clases.

        Aplica las reglas configuradas: el segundo tramo gana cuando el
        número de clases alcanza (o supera) su umbral, después el primer
        tramo, y 0% si no llega a ningún umbral.
        """
        if classes >= self.discount_10_threshold:
            return self.discount_10_percent

        if classes >= self.discount_5_threshold:
            return self.discount_5_percent

        return 0

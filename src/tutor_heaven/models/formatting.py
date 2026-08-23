"""Utilidades de formato compartidas por la capa de datos y la UI."""


def format_hours(hours: float) -> str:
    """Formatea una cantidad de horas sin decimales innecesarios.

    "10" en vez de "10.0", "7.5" en vez de "7.50". Se usa tanto en la
    interfaz como en las notas de la bóveda para que las horas se
    muestren siempre iguales.
    """
    text = f"{hours:.2f}".rstrip("0").rstrip(".")

    return text or "0"

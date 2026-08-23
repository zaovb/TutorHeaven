from dataclasses import dataclass


@dataclass(slots=True)
class Package:
    """A class package purchase record.

    Registro de una compra de paquetes de horas. Cada vez que el tutor
    añade horas a un estudiante se crea un Package que guarda el tamaño
    del bloque (en horas), el precio negociado, el descuento aplicado,
    el modo de pago y las fechas relevantes. Sirve de historial para la
    pestaña Packages del perfil.

    Las horas compradas se guardan como float (se permiten medias
    horas, p. ej. 7.5) y el consumo en MINUTOS enteros, para que las
    cuentas nunca pierdan exactitud al sumar bloques distintos.
    """

    # Tamaño del bloque comprado en esta ocasión, en horas.
    hours_purchased: float

    # Minutos de este bloque que ya se han consumido.
    minutes_taken: int = 0

    # Precio por hora y descuento (% 0-100) negociados en este bloque.
    hourly_price: float = 0.0
    discount_percent: int = 0

    # Cómo y cuándo se pagó este bloque.
    payment_mode: str = "Pay in advance"
    payment_status: str = "Pending"

    # Fechas de pago y de inicio del bloque (formato "YYYY-MM-DD").
    date_of_payment: str = ""
    date_of_start: str = ""

    @property
    def capacity_minutes(self) -> int:
        """Capacidad del bloque en minutos (redondeo robusto)."""
        return round(self.hours_purchased * 60)

    @property
    def minutes_left(self) -> int:
        """Minutos de este bloque que aún quedan por consumir."""
        return self.capacity_minutes - self.minutes_taken

    @property
    def hours_taken(self) -> float:
        """Horas de este bloque que ya se han consumido."""
        return self.minutes_taken / 60

    @property
    def hours_left(self) -> float:
        """Horas de este bloque que aún quedan por consumir."""
        return self.minutes_left / 60

    @property
    def is_active(self) -> bool:
        """True mientras este bloque aún tenga minutos sin consumir."""
        return self.minutes_left > 0

    @property
    def status(self) -> str:
        """Estado del bloque: Active mientras queden horas, si no Completed."""
        return "Active" if self.is_active else "Completed"

    @property
    def total(self) -> float:
        """Precio de este bloque tras aplicar su descuento."""
        return self.hours_purchased * self.hourly_price * (
            1 - self.discount_percent / 100
        )

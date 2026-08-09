from dataclasses import dataclass


@dataclass(slots=True)
class Package:
    """A class package purchase record.

    Registro de una compra de paquetes de clases. Cada vez que el tutor
    añade clases a un estudiante se crea un Package que guarda el tamaño
    del bloque, el precio negociado, el descuento aplicado, el modo de
    pago y las fechas relevantes. Sirve de historial para la pestaña
    Packages del perfil.
    """

    # Tamaño del bloque comprado en esta ocasión.
    classes_purchased: int

    # Clases de este bloque que ya se han consumido.
    classes_taken: int = 0

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
    def classes_left(self) -> int:
        """Clases de este bloque que aún quedan por consumir."""
        return self.classes_purchased - self.classes_taken

    @property
    def is_active(self) -> bool:
        """True mientras este bloque aún tenga clases sin consumir."""
        return self.classes_left > 0

    @property
    def status(self) -> str:
        """Estado del bloque: Active mientras queden clases, si no Completed."""
        return "Active" if self.is_active else "Completed"

    @property
    def total(self) -> float:
        """Precio de este bloque tras aplicar su descuento."""
        return self.classes_purchased * self.hourly_price * (
            1 - self.discount_percent / 100
        )

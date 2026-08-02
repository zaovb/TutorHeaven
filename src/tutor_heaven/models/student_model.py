from dataclasses import dataclass, field

from tutor_heaven.models.session_model import Session


@dataclass(slots=True)
class Student:
    """Represents a student."""

    name: str
    student_type: str

    email: str
    phone: str

    classes_purchased: int
    classes_taken: int

    hourly_price: float

    payment_mode: str
    payment_status: str

    notes: str

    sessions: list[Session] = field(default_factory=list)

    @property
    def classes_left(self) -> int:
        return self.classes_purchased - self.classes_taken

    @property
    def package_price(self) -> float:
        return self.classes_purchased * self.hourly_price

    @property
    def discount_percent(self) -> int:
        if self.classes_purchased >= 10:
            return 10

        if self.classes_purchased >= 5:
            return 5

        return 0

    @property
    def total(self) -> float:
        return self.package_price * (
            1 - self.discount_percent / 100
        )
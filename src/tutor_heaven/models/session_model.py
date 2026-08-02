from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Session:
    """Represents a student session."""

    date: str

    start_time: str
    end_time: str

    topic: str
    status: str
    notes: str

    created_at: str = field(
        default_factory=lambda: datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    @property
    def start_datetime(self) -> datetime:
        return datetime.strptime(
            f"{self.date} {self.start_time}",
            "%Y-%m-%d %H:%M",
        )

    @property
    def end_datetime(self) -> datetime:
        return datetime.strptime(
            f"{self.date} {self.end_time}",
            "%Y-%m-%d %H:%M",
        )
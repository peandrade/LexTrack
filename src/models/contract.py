from src import db
from datetime import datetime, date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.party import Party
    from src.models.alert_config import AlertConfig


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contract_number = db.Column(db.String(50), nullable=True, unique=True)
    contract_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default="active")
    value = db.Column(db.Numeric(15, 2), nullable=True)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    signing_date = db.Column(db.Date, nullable=True)

    pdf_path = db.Column(db.String(500), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parties: db.Mapped[list["Party"]] = db.relationship(
        "Party", back_populates="contract", cascade="all, delete-orphan"
    )
    alert_config: db.Mapped["AlertConfig"] = db.relationship(
        "AlertConfig", back_populates="contract", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def days_until_expiration(self) -> int:
        delta = self.end_date - date.today()
        return delta.days

    @property
    def is_expired(self) -> bool:
        return self.end_date < date.today()

    @property
    def is_expiring_soon(self) -> bool:
        return 0 <= self.days_until_expiration <= 30

    def __repr__(self) -> str:
        return f"<Contract {self.title} (expires: {self.end_date})>"

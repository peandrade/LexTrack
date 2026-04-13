from src import db
from datetime import datetime


class Party(db.Model):
    __tablename__ = "parties"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    document = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    party_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=False)
    contract = db.relationship("Contract", back_populates="parties")

    def __repr__(self) -> str:
        return f"<Party {self.name} ({self.party_type})>"

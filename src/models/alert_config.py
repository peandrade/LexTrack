from src import db
from datetime import datetime


class AlertConfig(db.Model):
    __tablename__ = "alert_configs"

    id = db.Column(db.Integer, primary_key=True)
    alert_days = db.Column(db.String(100), default="90,60,30,15,7,1")
    email_recipients = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_alert_sent = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=False)
    contract = db.relationship("Contract", back_populates="alert_config")

    def get_alert_days_list(self) -> list[int]:
        return [int(d.strip()) for d in self.alert_days.split(",")]

    def get_recipients_list(self) -> list[str]:
        if not self.email_recipients:
            return []
        return [e.strip() for e in self.email_recipients.split(",")]

    def __repr__(self) -> str:
        return f"<AlertConfig contract_id={self.contract_id} active={self.is_active}>"

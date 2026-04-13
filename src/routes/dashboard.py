from flask import Blueprint, render_template, jsonify, current_app
from src.models import Contract, AuditLog
from datetime import date
from sqlalchemy import func
from src import db

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    return render_template("dashboard/index.html")


@bp.route("/api/stats")
def api_stats():
    today = date.today()

    total = Contract.query.count()
    active = Contract.query.filter(Contract.status == "active", Contract.end_date >= today).count()
    expired = Contract.query.filter(Contract.end_date < today).count()

    expiring_soon = Contract.query.filter(
        Contract.status == "active",
        Contract.end_date >= today,
        Contract.end_date <= func.date(today.isoformat(), '+30 days')
    ).count()

    total_value = db.session.query(func.sum(Contract.value)).filter(
        Contract.status == "active"
    ).scalar() or 0

    return jsonify({
        "total": total,
        "active": active,
        "expired": expired,
        "expiring_soon": expiring_soon,
        "total_value": float(total_value)
    })


@bp.route("/api/expiring")
def api_expiring():
    today = date.today()
    contracts = Contract.query.filter(
        Contract.status == "active",
        Contract.end_date >= today
    ).order_by(Contract.end_date.asc()).limit(10).all()

    return jsonify([{
        "id": c.id,
        "title": c.title,
        "end_date": c.end_date.isoformat(),
        "days_until_expiration": c.days_until_expiration,
        "contract_type": c.contract_type
    } for c in contracts])


@bp.route("/api/check-alerts", methods=["POST"])
def check_alerts():
    today = date.today()
    alerts_sent = []

    active_contracts = Contract.query.filter(
        Contract.status == "active",
        Contract.end_date >= today
    ).all()

    for contract in active_contracts:
        if not contract.alert_config or not contract.alert_config.is_active:
            continue

        days_remaining = contract.days_until_expiration
        alert_days = contract.alert_config.get_alert_days_list()

        if days_remaining in alert_days:
            recipients = contract.alert_config.get_recipients_list()
            if recipients:
                from src.services.mailer import send_alert_email
                success = send_alert_email(contract, days_remaining, recipients)

                log = AuditLog(
                    entity_type="Contract",
                    entity_id=contract.id,
                    action="alert_sent" if success else "alert_failed",
                    changes={"days_remaining": days_remaining, "recipients": recipients}
                )
                db.session.add(log)
                alerts_sent.append({
                    "contract_id": contract.id,
                    "title": contract.title,
                    "days_remaining": days_remaining,
                    "success": success
                })

    db.session.commit()

    return jsonify({
        "checked": len(active_contracts),
        "alerts_sent": alerts_sent
    })

from flask import Blueprint, render_template, jsonify
from src.models import Contract
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

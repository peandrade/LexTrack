from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from src import db
from src.models import Contract, Party, AlertConfig, AuditLog
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid

bp = Blueprint("contracts", __name__, url_prefix="/contracts")


@bp.route("/")
def index():
    status_filter = request.args.get("status", "all")
    search = request.args.get("search", "")

    query = Contract.query

    if status_filter == "active":
        query = query.filter(Contract.status == "active")
    elif status_filter == "expired":
        query = query.filter(Contract.status == "expired")
    elif status_filter == "expiring":
        query = query.filter(Contract.status == "active")

    if search:
        query = query.filter(Contract.title.ilike(f"%{search}%"))

    contracts = query.order_by(Contract.end_date.asc()).all()

    if status_filter == "expiring":
        contracts = [c for c in contracts if c.is_expiring_soon]

    return render_template("contracts/index.html", contracts=contracts, status_filter=status_filter, search=search)


@bp.route("/new", methods=["GET", "POST"])
def create():
    if request.method == "POST":
        contract = Contract(
            title=request.form["title"],
            description=request.form.get("description"),
            contract_number=request.form.get("contract_number") or None,
            contract_type=request.form["contract_type"],
            value=request.form.get("value") or None,
            start_date=datetime.strptime(request.form["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(request.form["end_date"], "%Y-%m-%d").date(),
            signing_date=datetime.strptime(request.form["signing_date"], "%Y-%m-%d").date() if request.form.get("signing_date") else None,
            notes=request.form.get("notes")
        )

        db.session.add(contract)
        db.session.flush()

        alert_config = AlertConfig(
            contract_id=contract.id,
            alert_days=request.form.get("alert_days", "90,60,30,15,7,1"),
            email_recipients=request.form.get("email_recipients"),
            is_active=request.form.get("alerts_active") == "on"
        )
        db.session.add(alert_config)

        _add_parties_from_form(contract, request.form)
        _log_action("Contract", contract.id, "create")

        db.session.commit()
        flash("Contrato criado com sucesso!", "success")
        return redirect(url_for("contracts.show", id=contract.id))

    return render_template("contracts/form.html", contract=None)


@bp.route("/<int:id>")
def show(id: int):
    contract = Contract.query.get_or_404(id)
    return render_template("contracts/show.html", contract=contract)


@bp.route("/<int:id>/edit", methods=["GET", "POST"])
def edit(id: int):
    contract = Contract.query.get_or_404(id)

    if request.method == "POST":
        old_values = _get_contract_dict(contract)

        contract.title = request.form["title"]
        contract.description = request.form.get("description")
        contract.contract_number = request.form.get("contract_number") or None
        contract.contract_type = request.form["contract_type"]
        contract.value = request.form.get("value") or None
        contract.start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        contract.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        contract.signing_date = datetime.strptime(request.form["signing_date"], "%Y-%m-%d").date() if request.form.get("signing_date") else None
        contract.notes = request.form.get("notes")
        contract.status = request.form.get("status", "active")

        if contract.alert_config:
            contract.alert_config.alert_days = request.form.get("alert_days", "90,60,30,15,7,1")
            contract.alert_config.email_recipients = request.form.get("email_recipients")
            contract.alert_config.is_active = request.form.get("alerts_active") == "on"

        Party.query.filter_by(contract_id=contract.id).delete()
        _add_parties_from_form(contract, request.form)

        new_values = _get_contract_dict(contract)
        changes = {k: {"old": old_values.get(k), "new": v} for k, v in new_values.items() if old_values.get(k) != v}
        _log_action("Contract", contract.id, "update", changes)

        db.session.commit()
        flash("Contrato atualizado com sucesso!", "success")
        return redirect(url_for("contracts.show", id=contract.id))

    return render_template("contracts/form.html", contract=contract)


@bp.route("/<int:id>/delete", methods=["POST"])
def delete(id: int):
    contract = Contract.query.get_or_404(id)
    _log_action("Contract", contract.id, "delete")
    db.session.delete(contract)
    db.session.commit()
    flash("Contrato excluído com sucesso!", "success")
    return redirect(url_for("contracts.index"))


@bp.route("/api/list")
def api_list():
    contracts = Contract.query.all()
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "contract_type": c.contract_type,
        "status": c.status,
        "end_date": c.end_date.isoformat(),
        "days_until_expiration": c.days_until_expiration,
        "is_expired": c.is_expired,
        "is_expiring_soon": c.is_expiring_soon,
        "value": float(c.value) if c.value else None
    } for c in contracts])


def _add_parties_from_form(contract: Contract, form) -> None:
    party_names = form.getlist("party_name[]")
    party_types = form.getlist("party_type[]")
    party_documents = form.getlist("party_document[]")
    party_emails = form.getlist("party_email[]")

    for i, name in enumerate(party_names):
        if not name.strip():
            continue
        party = Party(
            contract_id=contract.id,
            name=name.strip(),
            party_type=party_types[i] if i < len(party_types) else "contratante",
            document=party_documents[i] if i < len(party_documents) else None,
            email=party_emails[i] if i < len(party_emails) else None
        )
        db.session.add(party)


def _get_contract_dict(contract: Contract) -> dict:
    return {
        "title": contract.title,
        "description": contract.description,
        "contract_number": contract.contract_number,
        "contract_type": contract.contract_type,
        "status": contract.status,
        "value": str(contract.value) if contract.value else None,
        "start_date": contract.start_date.isoformat(),
        "end_date": contract.end_date.isoformat(),
        "signing_date": contract.signing_date.isoformat() if contract.signing_date else None,
        "notes": contract.notes
    }


def _log_action(entity_type: str, entity_id: int, action: str, changes: dict | None = None) -> None:
    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=changes,
        ip_address=request.remote_addr
    )
    db.session.add(log)


@bp.route("/api/extract-pdf", methods=["POST"])
def extract_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "Nenhum arquivo selecionado"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Arquivo deve ser PDF"}), 400

    upload_dir = Path(current_app.instance_path) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
    filepath = upload_dir / filename
    file.save(filepath)

    try:
        from src.services.pdf_extractor import extract_dates_from_pdf, extract_contract_value

        dates = extract_dates_from_pdf(filepath)
        value = extract_contract_value(filepath)

        return jsonify({
            "success": True,
            "filepath": str(filepath),
            "dates": {
                "start_date": dates.start_date.isoformat() if dates.start_date else None,
                "end_date": dates.end_date.isoformat() if dates.end_date else None,
                "signing_date": dates.signing_date.isoformat() if dates.signing_date else None,
                "all_dates": [d.isoformat() for d in dates.all_dates]
            },
            "value": value
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

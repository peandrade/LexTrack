from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date
from flask import Flask


scheduler = BackgroundScheduler()


def check_expiring_contracts():
    from src import db, create_app
    from src.models import Contract, AuditLog
    from src.services.mailer import send_alert_email

    app = create_app()
    with app.app_context():
        today = date.today()
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
                    send_alert_email(contract, days_remaining, recipients)

                    log = AuditLog(
                        entity_type="Contract",
                        entity_id=contract.id,
                        action="alert_sent",
                        changes={"days_remaining": days_remaining, "recipients": recipients}
                    )
                    db.session.add(log)

        db.session.commit()
        app.logger.info(f"Contract expiration check completed. Checked {len(active_contracts)} contracts.")


def init_scheduler(app: Flask) -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        func=check_expiring_contracts,
        trigger=CronTrigger(hour=8, minute=0),
        id="check_expiring_contracts",
        name="Check expiring contracts daily at 8:00",
        replace_existing=True
    )

    scheduler.start()
    app.logger.info("Scheduler started")


def shutdown_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()

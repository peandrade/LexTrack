import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models import Contract


def send_alert_email(contract: "Contract", days_remaining: int, recipients: list[str]) -> bool:
    if not recipients:
        return False

    config = current_app.config
    if not config.get("MAIL_USERNAME") or not config.get("MAIL_PASSWORD"):
        current_app.logger.warning("Email not configured, skipping alert")
        return False

    subject = f"[LexTrack] Contrato vence em {days_remaining} dias: {contract.title}"

    html_content = render_template(
        "emails/alert.html",
        contract=contract,
        days_remaining=days_remaining
    )

    text_content = f"""
Alerta de Vencimento de Contrato - LexTrack

O contrato "{contract.title}" vence em {days_remaining} dias.

Detalhes:
- Numero: {contract.contract_number or 'N/A'}
- Tipo: {contract.contract_type}
- Data de Vencimento: {contract.end_date.strftime('%d/%m/%Y')}
- Valor: R$ {contract.value or 'N/A'}

Acesse o sistema para mais informacoes.
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["MAIL_DEFAULT_SENDER"]
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"])
        if config["MAIL_USE_TLS"]:
            server.starttls()
        server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
        server.sendmail(config["MAIL_DEFAULT_SENDER"], recipients, msg.as_string())
        server.quit()
        current_app.logger.info(f"Alert email sent for contract {contract.id} to {recipients}")
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return False

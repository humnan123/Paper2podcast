import os
import smtplib
from email.message import EmailMessage


def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()

    msg["From"] = "noreply@papercms.com"
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.set_content(body)

    with smtplib.SMTP(
        os.getenv("SMTP_HOST", "mailpit"),
        int(os.getenv("SMTP_PORT", 1025))
    ) as smtp:
        smtp.send_message(msg)
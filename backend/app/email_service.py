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

# ---------------------------------------------------------------------------
# Part 5 (tasks 5.6 and 5.14)
# ---------------------------------------------------------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def send_reviewer_assigned_email(to_email, reviewer_name, paper_title, conference_name):
    """5.6: tell a reviewer they have a new paper, with a link to the My assignments page."""
    link = f"{FRONTEND_URL}/assignments"
    subject = f"New review request: {paper_title}"
    body = (
        f"Hello {reviewer_name},\n\n"
        f'You have been asked to review the paper "{paper_title}" for {conference_name}.\n\n'
        f"Please log in and accept or decline this request here:\n{link}\n"
    )
    send_email(to_email, subject, body)


def send_chair_response_email(to_email, reviewer_name, paper_title, status, reason=None):
    """5.14: tell the chairperson that a reviewer accepted or declined."""
    subject = f"Reviewer {status} the request: {paper_title}"
    body = f'{reviewer_name} has {status} the review request for "{paper_title}".\n'
    if status == "declined" and reason:
        body += f"\nReason given: {reason}\n"
    if status == "declined":
        body += "\nYou can now assign a different reviewer to this paper.\n"
    send_email(to_email, subject, body)

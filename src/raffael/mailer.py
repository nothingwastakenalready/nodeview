"""Small SMTP boundary for local Mailpit and later Proton delivery."""

import os
import smtplib
from email.message import EmailMessage as NativeEmailMessage

from .email_templates import EmailMessage


class SmtpMailer:
    def __init__(self, host: str | None = None, port: int | None = None, sender: str | None = None):
        self.provider = os.environ.get("RAFFAEL_MAIL_PROVIDER", "disabled")
        self.host = host or os.environ.get("RAFFAEL_SMTP_HOST", "")
        self.port = port or int(os.environ.get("RAFFAEL_SMTP_PORT", "1025"))
        self.sender = sender or os.environ.get("RAFFAEL_MAIL_FROM", "")
        self.username = os.environ.get("RAFFAEL_SMTP_USERNAME", "")
        self.password = os.environ.get("RAFFAEL_SMTP_PASSWORD", "")
        self.security = os.environ.get("RAFFAEL_SMTP_SECURITY", "none")

    @property
    def enabled(self) -> bool:
        return self.provider != "disabled" and bool(self.host and self.sender)

    def send(self, recipient: str, message: EmailMessage) -> bool:
        if not self.enabled:
            return False
        outgoing = NativeEmailMessage()
        outgoing["From"] = self.sender
        outgoing["To"] = recipient
        outgoing["Subject"] = message.subject
        outgoing.set_content(message.text)
        outgoing.add_alternative(message.html, subtype="html")
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            if self.security == "starttls":
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password)
            smtp.send_message(outgoing)
        return True

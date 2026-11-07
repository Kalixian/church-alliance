"""Contact Us messages: rate limiting, email composition and SMTP delivery.

Ported from the static site's stdlib-only CGI handler (static/cgi-bin/contact.py),
which stays independent so the static image needs no backend code.
"""

import logging
import smtplib
import ssl
import threading
import time
from email.message import EmailMessage
from email.utils import formataddr

from app.config.settings import Settings

logger = logging.getLogger(__name__)

RATE_LIMIT_COUNT = 5
RATE_LIMIT_WINDOW_SECONDS = 3600


class ContactNotConfigured(RuntimeError):
    """SMTP credentials or the recipient address are missing."""


class RateLimiter:
    """Best-effort per-client limit, kept in memory (resets on restart)."""

    def __init__(self, count=RATE_LIMIT_COUNT, window_seconds=RATE_LIMIT_WINDOW_SECONDS):
        self.count = count
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, client: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        with self._lock:
            self._hits = {
                addr: recent
                for addr, times in self._hits.items()
                if (recent := [t for t in times if now - t < self.window_seconds])
            }
            recent = self._hits.setdefault(client, [])
            if len(recent) >= self.count:
                return False
            recent.append(now)
            return True

    def reset(self):
        with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()


def smtp_settings(settings: Settings) -> dict:
    # Gmail displays app passwords in groups of four; the spaces are not part of it.
    password = (settings.contact_smtp_password or "").replace(" ", "")
    missing = [
        name
        for name, value in (
            ("CONTACT_SMTP_USER", settings.contact_smtp_user),
            ("CONTACT_SMTP_PASSWORD", password),
        )
        if not value
    ]
    if missing:
        raise ContactNotConfigured(f"missing settings: {', '.join(missing)}")
    return {
        "host": settings.contact_smtp_host,
        "port": settings.contact_smtp_port,
        "user": settings.contact_smtp_user,
        "password": password,
        "sender": settings.contact_sender or settings.contact_smtp_user,
        "sender_name": settings.contact_sender_name,
    }


def build_message(
    smtp: dict, recipient: str, name: str, email: str, subject: str, message: str, remote_addr: str
) -> EmailMessage:
    mail = EmailMessage()
    mail["Subject"] = f"Website contact: {subject or 'New message'}"
    mail["From"] = formataddr((smtp["sender_name"], smtp["sender"]))
    mail["To"] = recipient
    # Gmail only sends as the authenticated account, so the visitor goes in Reply-To.
    mail["Reply-To"] = formataddr((name, email))
    mail.set_content(
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Subject: {subject or '(none)'}\n"
        f"Sender IP: {remote_addr}\n"
        f"\n{message}\n"
    )
    return mail


def send_messages(smtp: dict, mails: list[EmailMessage]) -> list[str]:
    """Send each message over one SMTP connection; return the recipients that got theirs.

    A failure for one recipient is logged and doesn't stop the others. Connection
    and login failures raise (OSError / smtplib.SMTPException).
    """
    context = ssl.create_default_context()
    if smtp["port"] == 465:
        connection = smtplib.SMTP_SSL(smtp["host"], smtp["port"], timeout=20, context=context)
    else:
        connection = smtplib.SMTP(smtp["host"], smtp["port"], timeout=20)
    delivered = []
    with connection:
        if smtp["port"] != 465:
            connection.starttls(context=context)
        connection.login(smtp["user"], smtp["password"])
        for mail in mails:
            try:
                connection.send_message(mail)
            except smtplib.SMTPException as exc:
                logger.error("contact message to %s could not be sent: %r", mail["To"], exc)
            else:
                delivered.append(mail["To"])
    return delivered

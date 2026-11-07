import logging
import smtplib

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.contact.schemas import ContactMessage
from app.config.settings import settings
from app.db.database import get_db
from app.db.user import UserRole, get_users_by_role
from app.services import contact as contact_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])

SEND_FAILED = "Sorry, your message could not be sent. Please try again later."


@router.post("", status_code=status.HTTP_202_ACCEPTED)
def send_contact_message(payload: ContactMessage, request: Request, db: Session = Depends(get_db)):
    """Email a Contact Us message to every administrator. Public; rate limited per client."""
    if payload.website:
        # Bots fill the hidden field; pretend it worked so they don't adapt.
        return {"detail": "Message sent."}

    remote_addr = request.client.host if request.client else "unknown"
    if not contact_service.rate_limiter.allow(remote_addr):
        logger.warning("contact rate limit reached for %s", remote_addr)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="We have received several messages from your connection recently. Please try again in an hour.",
        )

    try:
        smtp = contact_service.smtp_settings(settings)
    except contact_service.ContactNotConfigured as exc:
        logger.error("contact form is not configured: %s", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SEND_FAILED)

    recipients = sorted({admin.email for admin in get_users_by_role(db, UserRole.ADMINISTRATOR) if admin.email})
    if not recipients:
        logger.error("contact message dropped: no administrator has an email address")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SEND_FAILED)

    mails = [
        contact_service.build_message(
            smtp,
            recipient=recipient,
            name=payload.name,
            email=payload.email,
            subject=payload.subject,
            message=payload.message,
            remote_addr=remote_addr,
        )
        for recipient in recipients
    ]
    try:
        delivered = contact_service.send_messages(smtp, mails)
    except (OSError, smtplib.SMTPException) as exc:
        logger.error("contact message could not be sent: %r", exc)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SEND_FAILED)

    if not delivered:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=SEND_FAILED)

    return {"detail": "Message sent."}

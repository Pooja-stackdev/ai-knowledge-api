"""Small, provider-independent email templates."""

from email.message import EmailMessage

from app.core.config import settings
from app.database.models.document import Document


def document_completed_message(document: Document, recipient_email: str) -> EmailMessage:
    """Render the document-processing completion message."""
    subject = f"Document ready: {document.filename}"
    document_url = (
        f"{settings.frontend_document_url.rstrip('/')}/{document.id}"
        if settings.frontend_document_url
        else None
    )
    plain_body = f"Your document '{document.filename}' is ready to query."
    if document_url:
        plain_body = f"{plain_body}\n\nOpen document: {document_url}"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.email_sender_name} <{settings.email_sender_address}>"
    message["To"] = recipient_email
    message.set_content(plain_body)
    html_link = f'<p><a href="{document_url}">Open document</a></p>' if document_url else ""
    message.add_alternative(
        f"<p>Your document <strong>{document.filename}</strong> is ready to query.</p>{html_link}",
        subtype="html",
    )
    return message



def password_reset_message(
    recipient_email: str,
    reset_token: str,
) -> EmailMessage:
    """Render the password reset email."""

    reset_url = (
        f"{settings.frontend_password_reset_url}"
        f"?token={reset_token}"
    )

    message = EmailMessage()
    message["Subject"] = "Reset your password"
    message["From"] = (
        f"{settings.email_sender_name} "
        f"<{settings.email_sender_address}>"
    )
    message["To"] = recipient_email

    message.set_content(
        "We received a request to reset your password.\n\n"
        f"Reset your password here:\n{reset_url}\n\n"
        "This link will expire in 30 minutes.\n"
        "If you did not request this, you can safely ignore this email."
    )

    message.add_alternative(
        f"""
        <p>We received a request to reset your password.</p>
        <p>
            <a href="{reset_url}">Reset your password</a>
        </p>
        <p>This link will expire in 30 minutes.</p>
        <p>
            If you did not request this, you can safely ignore this email.
        </p>
        """,
        subtype="html",
    )

    return message
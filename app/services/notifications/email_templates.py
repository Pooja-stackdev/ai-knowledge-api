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

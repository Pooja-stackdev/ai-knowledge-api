"""Database operations for the durable notification outbox."""

from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models.notification_outbox import NotificationOutbox


class NotificationOutboxRepository:
    """Claim and update notification records without duplicate delivery."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, document_id: int, recipient_emails: list[str]) -> list[NotificationOutbox]:
        """Create one idempotent completion notification per recipient."""
        notifications: list[NotificationOutbox] = []
        for email in recipient_emails:
            existing = self.session.scalar(
                select(NotificationOutbox).where(
                    NotificationOutbox.document_id == document_id,
                    NotificationOutbox.recipient_email == email,
                    NotificationOutbox.notification_type == "document.completed",
                )
            )
            if existing is None:
                notification = NotificationOutbox(
                    document_id=document_id,
                    recipient_email=email,
                    notification_type="document.completed",
                    status="PENDING",
                )
                self.session.add(notification)
                notifications.append(notification)
        self.session.flush()
        return notifications

    def claim_pending(self, limit: int, max_attempts: int) -> list[NotificationOutbox]:
        """Atomically claim due notifications for one dispatcher iteration."""
        now = datetime.now(timezone.utc)
        statement = (
            select(NotificationOutbox)
            .where(
                NotificationOutbox.status.in_(("PENDING", "RETRY")),
                NotificationOutbox.attempt_count < max_attempts,
                or_(
                    NotificationOutbox.next_attempt_at.is_(None),
                    NotificationOutbox.next_attempt_at <= now,
                ),
            )
            .order_by(NotificationOutbox.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        notifications = list(self.session.scalars(statement).all())
        for notification in notifications:
            notification.status = "SENDING"
            notification.attempt_count += 1
            notification.last_error = None
        self.session.flush()
        return notifications

    def mark_sent(self, notification: NotificationOutbox) -> None:
        """Record successful SMTP handoff."""
        notification.status = "SENT"
        notification.sent_at = datetime.now(timezone.utc)
        notification.next_attempt_at = None
        notification.last_error = None
        self.session.flush()

    def mark_retry_or_failed(
        self,
        notification: NotificationOutbox,
        error: str,
        max_attempts: int,
        retry_delay_seconds: int,
    ) -> None:
        """Persist a sanitized failure and calculate the next retry time."""
        notification.last_error = error[:1000]
        if notification.attempt_count >= max_attempts:
            notification.status = "FAILED"
            notification.next_attempt_at = None
        else:
            notification.status = "RETRY"
            notification.next_attempt_at = datetime.fromtimestamp(
                datetime.now(timezone.utc).timestamp() + retry_delay_seconds,
                tz=timezone.utc,
            )
        self.session.flush()

    def recover_stuck_sending(self, timeout_minutes: int) -> int:
        """Return abandoned sends to the retry queue after a worker restart."""
        cutoff = datetime.now(timezone.utc).timestamp() - timeout_minutes * 60
        statement = select(NotificationOutbox).where(
            NotificationOutbox.status == "SENDING",
            NotificationOutbox.updated_at < datetime.fromtimestamp(cutoff, tz=timezone.utc),
        )
        notifications = list(self.session.scalars(statement).all())
        for notification in notifications:
            notification.status = "RETRY"
            notification.next_attempt_at = datetime.now(timezone.utc)
            notification.last_error = "Notification dispatch was interrupted."
        self.session.flush()
        return len(notifications)

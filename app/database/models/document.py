from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.models.base import Base
from app.database.models.timestamp_mixin import TimestampMixin
from app.domain.enums.document import DocumentStatus

if TYPE_CHECKING:
    from app.database.models.notification_outbox import NotificationOutbox
    from app.database.models.role import Role

class Document(Base,TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    storage_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        String(50),
        nullable=False,
        default=DocumentStatus.PENDING,
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    attempt_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    roles: Mapped[list["Role"]] = relationship(
        secondary="document_roles",
        back_populates="documents",
    )

    notifications: Mapped[list["NotificationOutbox"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )

"""Add the persistent email notification outbox.

Revision ID: f7d91c8a4b2e
Revises: c6c08d68b3ee
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7d91c8a4b2e"
down_revision: str | Sequence[str] | None = "c6c08d68b3ee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create a retryable, idempotent notification outbox."""
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("recipient_email", sa.String(length=255), nullable=False),
        sa.Column("notification_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "document_id",
            "recipient_email",
            "notification_type",
            name="uq_notification_outbox_recipient",
        ),
    )
    op.create_index("ix_notification_outbox_document_id", "notification_outbox", ["document_id"])
    op.create_index("ix_notification_outbox_status", "notification_outbox", ["status"])
    op.create_index("ix_notification_outbox_next_attempt_at", "notification_outbox", ["next_attempt_at"])


def downgrade() -> None:
    """Remove durable notification records."""
    op.drop_index("ix_notification_outbox_next_attempt_at", table_name="notification_outbox")
    op.drop_index("ix_notification_outbox_status", table_name="notification_outbox")
    op.drop_index("ix_notification_outbox_document_id", table_name="notification_outbox")
    op.drop_table("notification_outbox")

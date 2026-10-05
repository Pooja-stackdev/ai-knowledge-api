"""add password reset tokens

Revision ID: b598451c76c8
Revises: f7d91c8a4b2e
Create Date: 2026-10-05 10:44:25.911307

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b598451c76c8"
down_revision: str | None = "f7d91c8a4b2e"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "token_hash",
            name="uq_password_reset_token_hash",
        ),
    )

    op.create_index(
        op.f("ix_password_reset_tokens_user_id"),
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_password_reset_tokens_expires_at"),
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_password_reset_tokens_expires_at"),
        table_name="password_reset_tokens",
    )

    op.drop_index(
        op.f("ix_password_reset_tokens_user_id"),
        table_name="password_reset_tokens",
    )

    op.drop_table("password_reset_tokens")


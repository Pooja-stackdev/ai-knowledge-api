from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "b8913275f88c"
down_revision = "770946c85e79"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_language = sa.Enum(
        "en",
        "hi",
        "gu",
        name="user_language",
    )

    user_language.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "language",
            user_language,
            nullable=False,
            server_default="en",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "language")

    user_language = sa.Enum(
        "en",
        "hi",
        "gu",
        name="user_language",
    )

    user_language.drop(op.get_bind(), checkfirst=True)

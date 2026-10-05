from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database.models.password_reset_token import PasswordResetToken


class PasswordResetTokenRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        user_id: int,
        token_hash: str,
        expires_at,
    ) -> PasswordResetToken:

        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(token)
        self.db.flush()

        return token

    from sqlalchemy import select


    def get_by_token_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:

        return self.db.scalar(
            select(PasswordResetToken)
            .where(
                PasswordResetToken.token_hash == token_hash
            )
        )

    def mark_as_used(
        self,
        token: PasswordResetToken,
    ) -> None:

        token.used_at = datetime.now(timezone.utc)

    def invalidate_active_tokens(
        self,
        user_id: int,
    ) -> None:

        self.db.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
            )
            .values(
                used_at=datetime.now(timezone.utc)
            )
        )
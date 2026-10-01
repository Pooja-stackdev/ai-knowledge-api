from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database.models.revoked_token import RevokedToken


class AuthRepository:

    def __init__(self, db: Session):
        self.db = db

    def revoke_token(
        self,
        jti: str,
        expires_at: datetime,
    ) -> None:
        revoked_token = RevokedToken(
            jti=jti,
            expires_at=expires_at,
        )

        self.db.add(revoked_token)

    def is_token_revoked(self, jti: str) -> bool:
        return (
            self.db.get(
                RevokedToken,
                jti,
            )
            is not None
        )

    def delete_expired_tokens(
        self,
        now: datetime,
    ) -> None:
        self.db.execute(
            delete(RevokedToken).where(
                RevokedToken.expires_at < now,
            )
        )

    
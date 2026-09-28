from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authentication import CurrentUser
from app.database.connection import get_db_session
from app.database.models.user import User
from app.services.auth.authorization_service import AuthorizationService


def require_permission(
    permission: str,
) -> Callable:

    def dependency(
        current_user: CurrentUser,
        db: Annotated[Session, Depends(get_db_session)],
    ) -> User:
        
        service = AuthorizationService(db)
        print(f"service--->{service}")
        if not service.has_permission(
            current_user,
            permission,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )

        return current_user

    return dependency


def require_role(
    role_name: str,
) -> Callable:

    def dependency(
        current_user: CurrentUser,
    ) -> User:
        with get_db_session() as session:
            service = AuthorizationService(session)

            if not service.has_role(
                current_user,
                role_name,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Role access denied",
                )

        return current_user

    return dependency
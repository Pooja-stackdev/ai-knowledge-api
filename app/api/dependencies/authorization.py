from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.authentication import get_current_user
from app.database.connection import get_db_session
from app.database.models.user import User
from app.database.repositories.role_repository import RoleRepository
from app.services.auth.authorization_service import AuthorizationService


def require_permission(
    permission: str,
) -> Callable:

    def dependency(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db_session)],
    ) -> User:
        
        service = AuthorizationService(db)
        
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
        current_user: Annotated[User, Depends(get_current_user)],
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

def get_role_repository(
    db: Annotated[Session, Depends(get_db_session)],
) -> RoleRepository:
    return RoleRepository(db)


def get_current_user_role_ids(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    repository: Annotated[
        RoleRepository,
        Depends(get_role_repository),
    ],
) -> list[int]:
    return repository.get_role_ids(
        user_id=current_user.id,
    )


from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.database.repositories.role_repository import RoleRepository
from app.database.repositories.user_repository import UserRepository
from app.services.auth.authorization_service import AuthorizationService
from app.services.auth.user_service import UserService


def get_user_service(
    db: Annotated[Session, Depends(get_db_session)],
) -> UserService:
    repository = UserRepository(db)
    role_repository = RoleRepository(db)
    authorization_service = AuthorizationService(db)

    return UserService(
        db=db,
        user_repository=repository,
        role_repository=role_repository,
        authorization_service=authorization_service,
    )


UserServiceDependency = Annotated[
    UserService,
    Depends(get_user_service),
]
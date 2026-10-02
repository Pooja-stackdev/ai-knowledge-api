from sqlalchemy.orm import Session

from app.database.models.user import User


class AuthorizationService:
    """Evaluate permissions derived from a user's assigned roles."""

    def __init__(self, session: Session):
        self.session = session

    def has_permission(
        self,
        user: User,
        permission: str,
    ) -> bool:
        user_permissions = {
            item.name
            for role in user.roles
            for item in role.permissions
        }

        return permission in user_permissions

    def has_role(
        self,
        user: User,
        role_name: str,
    ) -> bool:
        return any(
            role.name == role_name
            for role in user.roles
        )

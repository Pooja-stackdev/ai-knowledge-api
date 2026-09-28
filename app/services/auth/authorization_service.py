from sqlalchemy.orm import Session

from app.database.models.user import User


class AuthorizationService:

    def __init__(self, session: Session):
        self.session = session

    def has_permission(
        self,
        user: User,
        permission: str,
    ) -> bool:
        print("Requested permission:", permission)
        print("User:", user.email)

        print("Roles:")
        for role in user.roles:
            print(
                "  Role:",
                role.id,
                role.name,
            )

            print("  Permissions:")
            for item in role.permissions:
                print(
                    "    Permission:",
                    item.id,
                    item.name,
                    "|",
                    item.description,
                )

        user_permissions = {
            item.name
            for role in user.roles
            for item in role.permissions
        }

        print("User permissions:", user_permissions)
        print("Checking:", permission)

        result = permission in user_permissions

        print("Permission result:", result)

        return result

    def has_role(
        self,
        user: User,
        role_name: str,
    ) -> bool:
        return any(
            role.name == role_name
            for role in user.roles
        )
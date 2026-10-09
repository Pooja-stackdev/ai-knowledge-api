from dataclasses import dataclass

from app.database.models.user import User


@dataclass
class UserQueryResult:
    user: User
    role_ids: list[int] | None = None
    permissions: list[str] | None = None
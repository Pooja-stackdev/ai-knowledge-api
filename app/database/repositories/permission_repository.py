# app/database/repositories/permission_repository.py

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.permission import Permission


class PermissionRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_by_ids(
        self,
        permission_ids: list[int],
    ) -> list[Permission]:

        if not permission_ids:
            return []

        return list(
            self.session.scalars(
                select(Permission).where(
                    Permission.id.in_(permission_ids)
                )
            )
        )

    def get_all(self) -> list[Permission]:
        return list(
            self.session.scalars(
                select(Permission).order_by(Permission.name)
            )
        )
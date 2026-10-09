# app/database/repositories/document_role.py

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database.models.document import Document
from app.database.models.document_role import DocumentRole


class DocumentRoleRepository:

    def __init__(self, session: Session):
        self.session = session

    def get_role_ids(self, document_id: int) -> list[int]:
        return list(
            self.session.scalars(
                select(DocumentRole.role_id).where(
                    DocumentRole.document_id == document_id
                )
            )
        )

    def replace_roles(
        self,
        document_id: int,
        role_ids: list[int],
    ) -> None:
        self.session.execute(
            delete(DocumentRole).where(
                DocumentRole.document_id == document_id
            )
        )

        for role_id in role_ids:
            self.session.add(
                DocumentRole(
                    document_id=document_id,
                    role_id=role_id,
                )
            )

        self.session.flush()

    


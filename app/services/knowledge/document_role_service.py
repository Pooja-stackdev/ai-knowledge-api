# app/services/knowledge/document_role_service.py

from sqlalchemy.orm import Session

from app.database.repositories.document import (
    DocumentRepository,
)
from app.database.repositories.document_role import (
    DocumentRoleRepository,
)
from app.database.repositories.role_repository import (
    RoleRepository,
)
from app.exceptions.common import ResourceNotFoundException


class DocumentRoleService:

    def __init__(self, db: Session):
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.role_repository = RoleRepository(db)
        self.document_role_repository = DocumentRoleRepository(db)

    def replace_roles(
        self,
        document_id: int,
        role_ids: list[int],
    ) -> list[int]:

        document = self.document_repository.get_by_id(document_id)

        if document is None:
            raise ResourceNotFoundException(
                "Document not found"
            )

        # Empty list means all authenticated users.
        if role_ids:
            roles = self.role_repository.get_by_ids(role_ids)

            if len(roles) != len(set(role_ids)):
                raise ResourceNotFoundException(
                    "One or more roles not found"
                )

        self.document_role_repository.replace_roles(
            document_id=document_id,
            role_ids=role_ids,
        )

        self.db.commit()
        self.db.refresh(document)

        return role_ids
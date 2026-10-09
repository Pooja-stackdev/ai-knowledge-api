from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.authentication import get_email_provider
from app.api.dependencies.document import create_document_service
from app.application.document_worker_service import DocumentWorkerService
from app.core.config import settings
from app.core.rbac import SUPER_ADMIN_ROLE_NAME
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.database.connection import get_db_session
from app.database.models.base import Base
from app.database.models.document import Document
from app.database.models.notification_outbox import NotificationOutbox
from app.database.models.permission import Permission
from app.database.models.role import Role
from app.database.models.role_permission import RolePermission
from app.database.models.user import User
from app.database.models.user_role import UserRole
from app.database.repositories.document import (
    DocumentRepository,
)
from app.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.database.repositories.document_role import DocumentRoleRepository
from app.database.repositories.role_repository import RoleRepository
from app.database.repositories.user_repository import UserRepository
from app.database.seeders.rbac_seeder import seed_rbac
from app.domain.enums.document import DocumentStatus
from app.main import app
from app.services.knowledge.document_service import DocumentService
from app.storage.local_storage import LocalFileStorage

test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)

class FakeVectorService:
    def delete_document_vectors(self, document_id: int) -> None:
        pass

@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(
        base_path=tmp_path,
    )

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)

    db = TestSessionLocal()

    try:
        seed_rbac(db)
        yield
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


# def seed_roles(db_session):
#     roles = [
#         Role(
#             name="super_admin",
#         ),
#         Role(
#             name="Admin",
#         ),
#         Role(
#             name="User",
#         ),
#     ]

#     db_session.add_all(roles)
#     db_session.commit()

@pytest.fixture
def db_session():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db_session, None)
    # app.dependency_overrides.clear()


@pytest.fixture
def document(db_session):
    document = Document(
        filename="test.pdf",
        storage_path="storage/documents/test.pdf",
        content_type="application/pdf",
        status=DocumentStatus.PENDING,
    )

    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    return document


# @pytest.fixture
# def document_service(db_session):
#     repository = DocumentRepository(db_session)
#     document_role_repository = DocumentRoleRepository(db_session)
#     role_repository = RoleRepository(db_session)
#     chunk_repository = DocumentChunkRepository(db_session)

#     return DocumentService(
#         db=db_session,
#         repository=repository,
#         document_role_repository=document_role_repository,
#         role_repository=role_repository,
#         storage=None,
#         chunk_repository=chunk_repository,
#         vector_service=FakeVectorService(),
#     )
@pytest.fixture
def document_service(db_session):
    return create_document_service(
        db=db_session,
        storage=storage,
        chunk_repository=DocumentChunkRepository(db_session),
        vector_service=FakeVectorService(),
    )

@pytest.fixture
def document_worker_service(db_session):
    repository = DocumentRepository(db_session)

    return DocumentWorkerService(
        db=db_session,
        repository=repository,
        storage=None,
    )


@pytest.fixture
def active_user(db_session):
    user = User(
        email=f"auth-test-{uuid4().hex}@example.com",
        password_hash=hash_password("Test@123456"),
        is_active=True,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def inactive_user(db_session):
    user = User(
        email=f"inactive-{uuid4().hex}@example.com",
        password_hash=hash_password("Test@123456"),
        is_active=False,
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user


@pytest.fixture
def access_token(active_user):
    token, _ = create_access_token(active_user.id)
    return token


@pytest.fixture
def refresh_token(active_user):
    token, _ = create_refresh_token(active_user.id)
    return token


@pytest.fixture
def permission_1(db_session):
    permission = db_session.scalar(
        select(Permission).where(
            Permission.name == "test.document.read"
        )
    )

    if permission is None:
        permission = Permission(
            name="test.document.read",
            description="Test document read permission",
        )
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)

    return permission


@pytest.fixture
def permission_2(db_session):
    permission = db_session.scalar(
        select(Permission).where(
            Permission.name == "test.query.execute"
        )
    )

    if permission is None:
        permission = Permission(
            name="test.query.execute",
            description="Test query execute permission",
        )
        db_session.add(permission)
        db_session.commit()
        db_session.refresh(permission)

    return permission

@pytest.fixture
def upload_user(db_session):
    permission = db_session.scalar(
        select(Permission).where(
            Permission.name == "document.create"
        )
    )

    if permission is None:
        permission = Permission(
            name="document.create",
            description="Upload documents",
        )
        db_session.add(permission)
        db_session.flush()

    role = Role(
        name=f"upload-role-{uuid4().hex[:8]}",
        description="Test upload role",
    )

    db_session.add(role)
    db_session.flush()

    db_session.add(
        RolePermission(
            role_id=role.id,
            permission_id=permission.id,
        )
    )

    user = User(
        email=f"upload-{uuid4().hex}@example.com",
        password_hash=hash_password("Test@123456"),
        is_active=True,
    )

    db_session.add(user)
    db_session.flush()

    db_session.add(
        UserRole(
            user_id=user.id,
            role_id=role.id,
        )
    )

    db_session.commit()
    db_session.refresh(user)

    return user

@pytest.fixture
def upload_access_token(upload_user):
    token, _ = create_access_token(upload_user.id)
    return token

# @pytest.fixture
# def super_admin_role(
#     db_session,
#     super_admin_permissions,
# ):
#     role = db_session.scalar(
#         select(Role).where(Role.name == SUPER_ADMIN_ROLE_NAME)
#     )

#     if role is None:
#         role = Role(
#             name=SUPER_ADMIN_ROLE_NAME,
#             description="System super administrator",
#         )
#         db_session.add(role)
#         db_session.flush()

#     for permission in super_admin_permissions:
#         exists = db_session.scalar(
#             select(RolePermission).where(
#                 RolePermission.role_id == role.id,
#                 RolePermission.permission_id == permission.id,
#             )
#         )

#         if exists is None:
#             db_session.add(
#                 RolePermission(
#                     role_id=role.id,
#                     permission_id=permission.id,
#                 )
#             )

#     db_session.commit()
#     db_session.refresh(role)

#     return role

@pytest.fixture
def super_admin_user(db_session):

    repository = UserRepository(db_session)
    user = repository.get_super_admin_user()

    return user
        
    # user = User(
    #     email=f"super-admin-{uuid4().hex}@example.com",
    #     password_hash=hash_password("Admin@123456"),
    #     is_active=True,
    # )

    # db_session.add(user)
    # db_session.flush()

    # db_session.add(
    #     UserRole(
    #         user_id=user.id,
    #         role_id=super_admin_role.id,
    #     )
    # )
    # print(f"USER IDDDDD------{user.id}")
    # print(settings.test_database_url)

    # db_session.commit()
    # db_session.refresh(user)

    # return user

@pytest.fixture
def super_admin_access_token(super_admin_user):
    print(super_admin_user.id)
    token, _ = create_access_token(super_admin_user.id)
    return token

# @pytest.fixture
# def super_admin_permissions(db_session):
#     permission_names = [
#         "user.read",
#         "user.create",
#         "user.update",
#         "user.delete",
#     ]

#     permissions = []

#     for name in permission_names:
#         permission = db_session.scalar(
#             select(Permission).where(
#                 Permission.name == name
#             )
#         )

#         if permission is None:
#             permission = Permission(
#                 name=name,
#                 description=f"{name} permission",
#             )
#             db_session.add(permission)
#             db_session.flush()

#         permissions.append(permission)

#     return permissions

class FakeEmailProvider:
    def __init__(self):
        self.messages = []

    def send(self, message):
        self.messages.append(message)


@pytest.fixture
def fake_email_provider():
    provider = FakeEmailProvider()

    app.dependency_overrides[get_email_provider] = (
        lambda: provider
    )

    yield provider

    app.dependency_overrides.pop(get_email_provider, None)


    
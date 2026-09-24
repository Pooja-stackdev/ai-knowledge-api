import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.application.document_worker_service import DocumentWorkerService
from app.core.config import settings
from app.database.base import Base
from app.database.connection import get_db_session
from app.database.models.document import Document
from app.database.repositories.document import (
    DocumentRepository,
)
from app.database.repositories.document_chunk import (
    DocumentChunkRepository,
)
from app.domain.enums.document import DocumentStatus
from app.main import app
from app.services.document_service import DocumentService

test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


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

    app.dependency_overrides.clear()


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


@pytest.fixture
def document_service(db_session):
    repository = DocumentRepository(db_session)

    chunk_repository = DocumentChunkRepository(db_session)

    return DocumentService(
        db=db_session,
        repository=repository,
        storage=None,
        chunk_repository=chunk_repository,
    )

@pytest.fixture
def document_worker_service(db_session):
    repository = DocumentRepository(db_session)

    return DocumentWorkerService(
        db=db_session,
        repository=repository,
        storage=None,
    )
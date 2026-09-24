import io
from datetime import datetime, timedelta, timezone

import pytest

from app.domain.enums.document import DocumentStatus
from app.exceptions import AppException


def test_upload_document_success(client):
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "test.pdf",
                io.BytesIO(b"%PDF-1.4 test"),
                "application/pdf",
            )
        },
        data={
            "description": "Test document",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["filename"] == "test.pdf"
    assert data["status"] == "PENDING"
    assert data["content_type"] == "application/pdf"


def test_upload_invalid_extension(client):
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "malware.exe",
                io.BytesIO(b"test"),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400


def test_pending_to_processing(
    document_service,
    document,
):
    document.status = DocumentStatus.PENDING

    result = document_service.mark_processing(
        document
    )

    assert result.status == DocumentStatus.PROCESSING


def test_processing_to_completed(
    document_service,
    document,
):
    document.status = DocumentStatus.PROCESSING

    result = document_service.mark_completed(
        document
    )

    assert result.status == DocumentStatus.COMPLETED


def test_processing_to_failed(
    document_service,
    document,
):
    document.status = DocumentStatus.PROCESSING

    result = document_service.mark_failed(
        document,
        "PDF parsing failed",
    )

    assert result.status == DocumentStatus.FAILED
    assert result.last_error == "PDF parsing failed"


def test_completed_cannot_become_processing(
    document_service,
    document,
):
    document.status = DocumentStatus.COMPLETED

    with pytest.raises(AppException):
        document_service.mark_processing(
            document
        )


def test_claim_increments_attempt_count(document_service):
    
    document_service.repository.create(
        filename="test.pdf",
        content_type="application/pdf",
        description="Test document",
        storage_path="storage/documents/test.pdf",
    )

    document_service.repository.db.commit()

    documents = document_service.repository.claim_pending_documents(
        limit=1
    )

    assert len(documents) == 1
    assert documents[0].status == DocumentStatus.PROCESSING
    assert documents[0].attempt_count == 1
    assert documents[0].processing_started_at is not None
    assert documents[0].last_error is None


def test_failed_document_stores_error(
    document_service,
    document,
):
    document.status = DocumentStatus.PROCESSING

    result = document_service.mark_failed(
        document,
        "PDF parsing failed",
    )

    assert result.status == DocumentStatus.FAILED
    assert result.last_error == "PDF parsing failed"
    assert result.processing_started_at is None


def test_retry_failed_document(
    document_service,
    document,
):
    document.status = DocumentStatus.FAILED
    document.attempt_count = 1
    document.last_error = "PDF parsing failed"

    result = document_service.retry_document(
        document.id
    )

    assert result.status == DocumentStatus.PENDING
    assert result.processing_started_at is None
    assert result.last_error is None


def test_completed_document_cannot_be_retried(
    document_service,
    document,
):
    document.status = DocumentStatus.COMPLETED

    with pytest.raises(AppException):
        document_service.retry_document(
            document.id
        )


def test_stuck_document_exceeds_max_attempts(
    document_service,
    document,
):
    document.status = DocumentStatus.PROCESSING
    document.processing_started_at = (
        datetime.now(timezone.utc) - timedelta(minutes=30)
    )
    document.attempt_count = 3
    document_service.db.commit()

    document_service.recover_stuck_documents(
        timeout_minutes=15
    )

    print(f"document -> {document}")
    print(f"id -> {document.id}")
    print(f"status -> {document.status}")
    print(f"attempt_count -> {document.attempt_count}")
    print(f"error -> {document.last_error}")

    assert document.status == DocumentStatus.FAILED
    assert document.last_error == (
        "Maximum processing attempts exceeded"
    )
    assert document.processing_started_at is None


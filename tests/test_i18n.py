"""Localization tests covering request isolation and non-request execution."""

from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

from app.application.document_worker_service import DocumentWorkerService
from app.core.i18n import get_message
from app.core.i18n.context import get_current_language
from app.exceptions.auth import AuthorizationException


def test_english_request_uses_english_error(client):
    response = client.get("/auth/me", headers={"Accept-Language": "en"})

    assert response.status_code == 401
    assert response.json()["message"] == "Unauthorized."


def test_hindi_request_uses_hindi_error(client):
    response = client.get("/auth/me", headers={"Accept-Language": "hi-IN"})

    assert response.status_code == 401
    assert response.json()["message"] == "प्रमाणीकरण आवश्यक है।"


def test_unsupported_and_missing_language_fall_back_to_english(client):
    unsupported = client.get("/auth/me", headers={"Accept-Language": "fr-FR"})
    missing = client.get("/auth/me")

    assert unsupported.json()["message"] == "Unauthorized."
    assert missing.json()["message"] == "Unauthorized."


def test_concurrent_requests_keep_their_own_language(client):
    def get_message_for(language: str) -> str:
        response = client.get("/auth/me", headers={"Accept-Language": language})
        return response.json()["message"]

    with ThreadPoolExecutor(max_workers=2) as executor:
        english, hindi = executor.map(get_message_for, ["en", "hi"])

    assert english == "Unauthorized."
    assert hindi == "प्रमाणीकरण आवश्यक है।"


def test_validation_errors_are_localized(client):
    response = client.post(
        "/auth/refresh",
        headers={"Accept-Language": "hi"},
        json={},
    )

    assert response.status_code == 422
    assert response.json()["message"] == "अनुरोध सत्यापन विफल रहा।"
    assert response.json()["errors"][0]["message"] == "यह फ़ील्ड आवश्यक है।"


def test_authorization_service_error_is_localized(client, access_token):
    response = client.get(
        "/documents",
        headers={
            "Accept-Language": "hi",
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["message"] == "आपको यह कार्रवाई करने की अनुमति नहीं है।"


def test_service_error_key_uses_the_request_language(client):
    response = client.get("/auth/me", headers={"Accept-Language": "hi"})

    assert response.status_code == 401
    assert get_message("document.forbidden", lang="hi") == (
        "आप इस दस्तावेज़ को एक्सेस करने के लिए अधिकृत नहीं हैं।"
    )


def test_worker_default_is_english_without_request_context():
    class DocumentService:
        def get_chunks(self, document_id):
            return []

        def clear_document_chunks(self, document_id):
            pass

        def mark_failed(self, document, error):
            self.error = error

    class VectorService:
        def delete_embeddings(self, chunk_ids):
            pass

    class IngestionService:
        def extract_text(self, **kwargs):
            return object()

    class EmptyChunker:
        def chunk(self, loaded_document):
            return []

    document_service = DocumentService()
    worker = DocumentWorkerService(
        document_service=document_service,
        ingestion_service=IngestionService(),
        chunker=EmptyChunker(),
        embedding_service=object(),
        vector_service=VectorService(),
    )

    # Worker processes do not install HTTP middleware or receive request state.
    document = SimpleNamespace(
        id=1,
        filename="empty.txt",
        storage_path="storage/documents/empty.txt",
    )
    assert worker.process_document(document) is False
    assert get_current_language() == "en"
    assert get_message("worker.no_usable_chunks") == "Document contains no usable chunks."
    assert document_service.error == "worker.no_usable_chunks"
    assert AuthorizationException("auth.forbidden").message == "auth.forbidden"

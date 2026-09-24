from pathlib import Path

from app.domain.models.document_content import DocumentPage, LoadedDocument
from app.rag.loaders.text import TextDocumentLoader
from app.services.knowledge.ingestion_service import DocumentIngestionService


def test_text_loader(tmp_path: Path):
    file_path = tmp_path / "test.txt"

    file_path.write_text(
        "Hello production RAG",
        encoding="utf-8",
    )

    loader = TextDocumentLoader()

    result = loader.load(file_path)

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "Hello production RAG"


def test_ingestion_service():
    class FakeLoader:

        def load(self, path: Path) -> LoadedDocument:
            return LoadedDocument(
                pages=[
                    DocumentPage(
                        page_number=1,
                        text="Extracted document text",
                    )
                ]
            )

    class FakeFactory:

        def get_loader(self, filename):
            return FakeLoader()

    service = DocumentIngestionService(
        loader_factory=FakeFactory(),
    )

    result = service.extract_text(
        filename="test.pdf",
        storage_path="/tmp/test.pdf",
    )

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == "Extracted document text"
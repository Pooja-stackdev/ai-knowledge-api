"""Plain-text document loader."""

from pathlib import Path

from app.domain.models.document_content import (
    DocumentPage,
    LoadedDocument,
)


class TextDocumentLoader:
    """Load plain-text documents."""

    def load(self, path: Path) -> LoadedDocument:
        """Read a text document and return its content as one page.

        Args:
            path: Path to the text file.

        Returns:
            A loaded document containing the extracted text.
        """
        text = path.read_text(encoding="utf-8").strip()

        if not text:
            return LoadedDocument(pages=[])

        return LoadedDocument(
            pages=[
                DocumentPage(
                    page_number=1,
                    text=text,
                )
            ]
        )
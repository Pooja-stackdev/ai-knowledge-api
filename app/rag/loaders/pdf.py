"""PDF document loader."""
import logging
from pathlib import Path

from pypdf import PdfReader

from app.domain.models.document_content import (
    DocumentPage,
    LoadedDocument,
)

logger = logging.getLogger(__name__)


class PdfDocumentLoader:
    """Load text content from PDF documents."""

    def load(self, path: Path) -> LoadedDocument:
        """Extract text from each non-empty PDF page.

        Args:
            path: Path to the PDF file.

        Returns:
            A loaded document containing extracted page content.

        Raises:
            OSError: If the PDF file cannot be accessed.
            Exception: If the PDF cannot be parsed by pypdf.
        """
        reader = PdfReader(path)

        pages: list[DocumentPage] = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()

            if not text:
                logger.info(
                    "Text not found."
                )
                continue

            logger.info(
                f"page_number: {page_number}"
            )

            pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=text,
                )
            )

        return LoadedDocument(pages=pages)
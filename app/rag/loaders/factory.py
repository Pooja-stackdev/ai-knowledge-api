"""Factory for selecting document loaders."""
import logging
from pathlib import Path

from app.core.config import settings
from app.rag.loaders.base import DocumentLoader
from app.rag.loaders.pdf import PdfDocumentLoader
from app.rag.loaders.text import TextDocumentLoader

logger = logging.getLogger(__name__)

class DocumentLoaderFactory:
    """Create the appropriate loader for a supported document type."""

    def get_loader(self, filename: str) -> DocumentLoader:
        """Return a document loader based on the file extension.

        Args:
            filename: Name or path of the document.

        Returns:
            A loader capable of processing the document type.

        Raises:
            ValueError: If the document extension is unsupported.
        """
        extension = Path(filename).suffix.lower()

        if extension not in settings.allowed_extensions:
            logger.info(
                f"Unsupported document type: {extension}"
            )
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        loaders: dict[str, DocumentLoader] = {
            ".pdf": PdfDocumentLoader(),
            ".txt": TextDocumentLoader(),
        }

        try:
            return loaders[extension]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported document extension: {extension}"
            ) from exc
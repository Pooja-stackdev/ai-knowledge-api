import logging
from pathlib import Path

from app.domain.models.document_content import LoadedDocument
from app.rag.loaders.factory import DocumentLoaderFactory


logger = logging.getLogger(__name__)

class DocumentIngestionService:
    """Extract document content using the appropriate document loader."""

    def __init__(
        self,
        loader_factory: DocumentLoaderFactory,
    ):
        self.loader_factory = loader_factory

    def extract_text(
        self,
        *,
        filename: str,
        storage_path: str,
    ) -> LoadedDocument:
        """Load and validate the content of a stored document."""
        logger.info(
            "extract_text: %s",
            extra={"document_filename": filename},
        )
        loader = self.loader_factory.get_loader(filename)

        loaded_document:LoadedDocument = loader.load(
            Path(storage_path),
        )

        if not loaded_document.pages:
            raise ValueError(
                "Document contains no extractable text."
            )

        logger.info(
            "Document text extracted",
            extra={
                "document_filename": filename,
                "page_count": len(loaded_document.pages),
            },
        )

        return loaded_document

        # text = "\n".join( page.text for page in loaded_document.pages )

        # if not text.strip(): 
        #     raise ValueError( "Document contains no extractable text." )

        # logger.info(
        #     "extract_text: %s",
        #     extra={"text": text},
        # )
        # return text
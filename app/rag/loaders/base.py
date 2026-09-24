"""Contracts for document loading."""

from pathlib import Path
from typing import Protocol

from app.domain.models.document_content import LoadedDocument


class DocumentLoader(Protocol):
    """Define the interface implemented by document loaders."""

    def load(self, path: Path) -> LoadedDocument:
        """Load a document from the given filesystem path."""
        ...
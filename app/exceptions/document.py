"""Knowledge document-related exception classes."""

from app.exceptions.base import AppException


class DocumentAlreadyExistsException(AppException):
    """Exception raised when a document already exists."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Document already exists: {file_path}")

class DocumentNotFoundException(AppException):
    """Exception raised when a document is not found."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Document not found: {file_path}")
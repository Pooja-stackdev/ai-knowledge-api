"""Document status enumeration."""

from enum import Enum


class DocumentStatus(str, Enum):
    """Enumeration of possible document statuses."""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
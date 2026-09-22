from app.exceptions import AppException
from app.domain.enums.document import DocumentStatus


ALLOWED_TRANSITIONS = {
    DocumentStatus.PENDING: {
        DocumentStatus.PROCESSING,
        DocumentStatus.FAILED,
    },
    DocumentStatus.PROCESSING: {
        DocumentStatus.COMPLETED,
        DocumentStatus.FAILED,
    },
    DocumentStatus.FAILED: {
        DocumentStatus.PROCESSING,
    },
    DocumentStatus.FAILED: {
        DocumentStatus.PENDING,   # manual retry
    },
    DocumentStatus.COMPLETED: set(),
}


def validate_transition(
    current: DocumentStatus,
    new: DocumentStatus,
) -> None:
    allowed = ALLOWED_TRANSITIONS.get(current, set())

    if new not in allowed:
        raise AppException(
            f"Invalid document status transition: "
            f"{current} -> {new}"
        )
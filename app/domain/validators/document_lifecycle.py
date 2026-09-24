"""Document status lifecycle validation."""

from app.domain.enums.document import DocumentStatus
from app.exceptions.common import ValidationException

ALLOWED_TRANSITIONS: dict[
    DocumentStatus,
    set[DocumentStatus],
] = {
    DocumentStatus.PENDING: {
        DocumentStatus.PROCESSING,
        DocumentStatus.FAILED,
    },
    DocumentStatus.PROCESSING: {
        DocumentStatus.COMPLETED,
        DocumentStatus.FAILED,
    },
    DocumentStatus.FAILED: {
        DocumentStatus.PENDING,
        DocumentStatus.PROCESSING,
    },
    DocumentStatus.COMPLETED: set(),
}


def validate_transition(
    current: DocumentStatus,
    new: DocumentStatus,
) -> None:
    """Validate whether a document status transition is allowed.

    Args:
        current: Current document status.
        new: Requested new document status.

    Raises:
        ValidationException: If the requested transition is not allowed.
    """
    allowed = ALLOWED_TRANSITIONS.get(current, set())

    if new not in allowed:
        raise ValidationException(
            message=(
                f"Invalid document status transition: "
                f"{current.value} -> {new.value}"
            ),
        )


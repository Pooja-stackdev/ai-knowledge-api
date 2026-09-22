from pathlib import Path

from app.core.config import settings
from app.exceptions.base import AppException


class DocumentValidator:
    @staticmethod
    def validate(
        filename: str,
        content_type: str | None,
        file_size: int,
    ) -> None:
        if not filename:
            raise AppException("Filename is required")

        extension = Path(filename).suffix.lower()

        if extension not in settings.allowed_extensions:
            raise AppException(
                f"File type '{extension}' is not allowed"
            )

        if content_type not in settings.allowed_content_types:
            raise AppException(
                f"Content type '{content_type}' is not allowed"
            )

        if file_size > settings.max_upload_size:
            raise AppException(
                "File size exceeds the maximum allowed limit"
            )
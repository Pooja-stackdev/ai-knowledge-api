from typing import Any

from api.client import APIClient


class DocumentsAPI:
    def __init__(self) -> None:
        self.client = APIClient()

    def list_documents(self) -> list[dict[str, Any]]:
        response = self.client.get("/documents")
        response.raise_for_status()

        return response.json()

    def get_document(
        self,
        document_id: int,
    ) -> dict[str, Any]:
        response = self.client.get(
            f"/documents/{document_id}"
        )
        response.raise_for_status()

        return response.json()

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        files = {
            "file": (
                filename,
                file_bytes,
                content_type,
            )
        }

        data: dict[str, str] = {}

        if description:
            data["description"] = description

        response = self.client.post(
            "/documents/upload",
            files=files,
            data=data,
        )

        response.raise_for_status()

        return response.json()

    def retry_document(
        self,
        document_id: int,
    ) -> dict[str, Any]:
        response = self.client.post(
            f"/documents/{document_id}/retry"
        )

        response.raise_for_status()

        return response.json()

    def delete_document(
        self,
        document_id: int,
    ) -> None:
        response = self.client.delete(
            f"/documents/{document_id}"
        )
        response.raise_for_status()
from typing import Any

from api.client import APIClient


class QueryAPI:
    def __init__(self) -> None:
        self.client = APIClient()

    def query(
        self,
        query: str,
        top_k: int = 5,
    ) -> dict[str, Any]:
        response = self.client.post(
            "/query",
            json={
                "query": query,
                "top_k": top_k,
            },
        )

        response.raise_for_status()

        return response.json()
from typing import Any

import requests
from config import settings
from utils.session import get_access_token


class APIClient:
    def __init__(self) -> None:
        self.base_url = settings.API_BASE_URL.rstrip("/")
        self.timeout = settings.API_TIMEOUT

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
        }

        token = get_access_token()

        if token:
            headers["Authorization"] = f"Bearer {token}"

        return headers

    def get(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return requests.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )

    def post(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return requests.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )

    def put(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return requests.put(
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )


    def delete(
        self,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        return requests.delete(
            f"{self.base_url}{path}",
            headers=self._headers(),
            timeout=self.timeout,
            **kwargs,
        )
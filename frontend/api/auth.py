from typing import Any

from api.client import APIClient


class AuthAPI:
    def __init__(self) -> None:
        self.client = APIClient()

    def login(
        self,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        response = self.client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password,
            },
        )

        response.raise_for_status()

        return response.json()

    def get_me(self) -> dict[str, Any]:
        response = self.client.get("/auth/me")

        response.raise_for_status()

        return response.json()

    def refresh(
        self,
        refresh_token: str,
    ) -> dict[str, Any]:
        response = self.client.post(
            "/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )

        response.raise_for_status()

        return response.json()

    def logout(self) -> None:
        response = self.client.post("/auth/logout")

        response.raise_for_status()
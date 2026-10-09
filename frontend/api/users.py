from typing import Any

from api.client import APIClient


class UsersAPI:
    def __init__(self) -> None:
        self.client = APIClient()

    def list_users(self):
        response = self.client.get("/users")
        response.raise_for_status()
        return response.json()

    def create_user(
        self,
        email: str,
        password: str,
        role_ids: list[int],
    ) -> dict[str, Any]:
        response = self.client.post(
            "/users",
            json={
                "email": email,
                "password": password,
                "role_ids": role_ids,
            },
        )

        response.raise_for_status()
        return response.json()

    def get_user(
        self,
        user_id: int,
    ) -> dict[str, Any]:
        response = self.client.get(
            f"/users/{user_id}",
        )

        response.raise_for_status()
        return response.json()

    def update_user(
        self,
        user_id: int,
        email: str | None = None,
        role_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        response = self.client.put(
            f"/users/{user_id}",
            json={
                "email": email,
                "role_ids": role_ids,
            },
        )

        response.raise_for_status()
        return response.json()

    def delete_user(
        self,
        user_id: int,
    ) -> None:
        response = self.client.delete(
            f"/users/{user_id}",
        )

        response.raise_for_status()
from api.client import APIClient


class RolesAPI:
    def __init__(self):
        self.client = APIClient()

    def list_roles(self):
        response = self.client.get("/roles")
        response.raise_for_status()
        return response.json()

    def get_role(self, role_id: int):
        response = self.client.get(f"/roles/{role_id}")
        response.raise_for_status()
        return response.json()

    def create_role(
        self,
        name: str,
        description: str | None,
        permission_ids: list[int],
    ):
        response = self.client.post(
            "/roles",
            json={
                "name": name,
                "description": description,
                "permission_ids": permission_ids,
            },
        )
        response.raise_for_status()
        return response.json()

    def update_role(
        self,
        role_id: int,
        name: str,
        description: str | None,
        permission_ids: list[int],
    ):
        response = self.client.put(
            f"/roles/{role_id}",
            json={
                "name": name,
                "description": description,
                "permission_ids": permission_ids,
            },
        )
        response.raise_for_status()
        return response.json()

    def delete_role(self, role_id: int):
        response = self.client.delete(f"/roles/{role_id}")
        response.raise_for_status()
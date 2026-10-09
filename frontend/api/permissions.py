from api.client import APIClient


class PermissionsAPI:
    def __init__(self):
        self.client = APIClient()

    def list_permissions(self):
        response = self.client.get("/permissions")
        response.raise_for_status()
        return response.json()
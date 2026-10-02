"""Public operational health endpoint tests."""


def test_liveness_is_public(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_is_public_when_database_is_available(client, monkeypatch):
    """Readiness uses a lightweight database check without authentication."""
    from app import main

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def execute(self, statement):
            return None

    monkeypatch.setattr(main, "SessionLocal", Session)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

import os
import app.routes as routes
from app import create_app


def make_client(env: str):
    os.environ["APP_ENV"] = env
    app = create_app()
    app.testing = True
    return app.test_client(), app


def test_create_app_dev_config():
    _, app = make_client("development")
    assert app.config["USE_CACHE"] is False


def test_create_app_pro_config():
    _, app = make_client("production")
    assert app.config["USE_CACHE"] is True


def test_health_pro_requires_db_and_redis(monkeypatch):
    # Simulamos conectividad, sin servicios reales
    monkeypatch.setattr(routes, "check_db", lambda: True)
    monkeypatch.setattr(routes, "check_cache", lambda: True)

    client, _ = make_client("production")
    resp = client.get("/health")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["ok"] is True
    assert data["db"] is True
    assert data["cache"] is True
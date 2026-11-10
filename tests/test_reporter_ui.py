from fastapi.testclient import TestClient

from app.main import app


def test_reporter_page_loads_as_html() -> None:
    response = TestClient(app).get("/reporter/ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_reporter_page_contains_prototype_banner() -> None:
    response = TestClient(app).get("/reporter/ui")

    assert "PROTOTYPE: Not for real reports. Fictional data only." in response.text

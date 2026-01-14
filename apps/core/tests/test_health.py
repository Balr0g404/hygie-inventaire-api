import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_ok():
    client = APIClient()
    r = client.get("/api/v1/health/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.django_db
def test_version_ok():
    client = APIClient()
    r = client.get("/api/v1/version/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert "version" in data

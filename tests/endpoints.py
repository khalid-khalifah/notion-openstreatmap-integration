import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app

@pytest.fixture(scope='module')
def test_client():
    client = TestClient(app)
    yield client

@pytest.mark.asyncio
async def test_get_locations(test_client):
    response = test_client.get("/api/locations")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_index_page(test_client):
    response = test_client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

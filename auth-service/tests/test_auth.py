import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_register_user_success():
    # Usamos httpx.AsyncClient para interactuar con los endpoints asíncronos de FastAPI
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {
            "email": "test_engineer@ticketflow.com",
            "password": "SecurePassword123!",
            "role": "Customer"
        }
        response = await ac.post("/api/v1/auth/register", json=payload)
        
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert "id" in data
    assert data["role"] == "Customer"
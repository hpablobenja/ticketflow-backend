import pytest
from fastapi.testclient import TestClient

# Importamos la app de tu servicio de autenticación
from app.main import app

client = TestClient(app)


def test_health_check_auth():
    """
    Verifica que el servicio responda correctamente en su raíz o docs
    """
    response = client.get("/docs")
    assert response.status_code == 200


def test_password_hash_logic():
    """
    Verifica que nuestra lógica criptográfica nativa no rompa strings
    """
    from app.main import get_password_hash, verify_password

    secret = "MiPasswordSuperSeguro123!"
    hashed = get_password_hash(secret)

    assert hashed != secret
    assert verify_password(secret, hashed) is True

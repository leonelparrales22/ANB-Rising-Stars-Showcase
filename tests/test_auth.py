import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.main import app
from shared.db.config import Base, get_db
from shared.db.models.user import User
from app.core.security import get_password_hash

# Configuración de base de datos de prueba (usando SQLite en memoria para simplicidad)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    yield
    # Limpiar tablas después de cada test
    Base.metadata.drop_all(bind=engine)


def test_signup_success(test_db):
    """Prueba de registro exitoso de un nuevo usuario."""
    response = client.post(
        "/api/auth/signup",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "StrongPass123",
            "password2": "StrongPass123",
            "city": "Bogotá",
            "country": "Colombia",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "message" in data
    assert data["message"] == "Usuario creado exitosamente."


def test_signup_email_duplicate(test_db):
    """Prueba de registro con email duplicado."""
    # Crear usuario primero
    db = TestingSessionLocal()
    hashed_password = get_password_hash("StrongPass123")
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password_hash=hashed_password,
        city="Bogotá",
        country="Colombia",
    )
    db.add(user)
    db.commit()
    db.close()

    # Intentar registrar con el mismo email
    response = client.post(
        "/api/auth/signup",
        json={
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password1": "StrongPass123",
            "password2": "StrongPass123",
            "city": "Bogotá",
            "country": "Colombia",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert (
        "email duplicado, contraseñas no coinciden" in str(data).lower()
    )  # Busca "email duplicado, contraseñas no coinciden" en el mensaje


def test_signup_password_mismatch(test_db):
    """Prueba de registro con contraseñas no coincidentes."""
    response = client.post(
        "/api/auth/signup",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "StrongPass123",
            "password2": "DifferentPass456",
            "city": "Bogotá",
            "country": "Colombia",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert (
        "contraseñas" in str(data).lower()
    )  # Busca "contraseñas" en el mensaje


def test_login_success(test_db):
    """Prueba de login exitoso."""
    # Crear usuario primero
    db = TestingSessionLocal()
    hashed_password = get_password_hash("StrongPass123")
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password_hash=hashed_password,
        city="Bogotá",
        country="Colombia",
    )
    db.add(user)
    db.commit()
    db.close()

    response = client.post(
        "/api/auth/login",
        json={"email": "john@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "Bearer"
    assert "expires_in" in data


def test_login_invalid_credentials(test_db):
    """Prueba de login con credenciales inválidas."""
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "WrongPass"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "inválidas" in str(data).lower()  # Busca "inválidas" en el mensaje

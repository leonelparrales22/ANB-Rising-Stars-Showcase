import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event
import datetime
import uuid

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.video import Video, VideoStatus
from app.models.vote import Vote
from app.core.security import get_password_hash

# Configuración de base de datos de prueba (usando SQLite en memoria para simplicidad)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


@event.listens_for(engine, 'connect')
def enable_foreign_keys(conn, branch):
    conn.execute('PRAGMA foreign_keys = ON')


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
def test_data():
    # Before tests
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    db.query(Vote).delete()
    db.query(Video).delete()
    db.query(User).delete()

    password_plain = "StrongPass123"
    password_hased = get_password_hash(password_plain)
    user1 = User(id=str(uuid.uuid4()),
                 first_name="John",
                 last_name="Doe",
                 email="john.doe@mail.com",
                 password_hash=password_hased,
                 city="Bogotá",
                 country="Colombia")
    user2 = User(id=str(uuid.uuid4()),
                 first_name="Bob",
                 last_name="Marley",
                 email="bob.marley@mail.com",
                 password_hash=password_hased,
                 city="Bogotá",
                 country="Colombia")

    db.add(user1)
    db.add(user2)
    db.commit()

    video1 = Video(id=str(uuid.uuid4()),
                   title="Canasta desde media cancha",
                   status=VideoStatus.UPLOADED.value,
                   id_user=user1.id,
                   uploaded_at=datetime.datetime.now(datetime.UTC),
                   file_uploaded_url="file://ruta/video.mp4")
    video2 = Video(id=str(uuid.uuid4()),
                   title="Volcada 360",
                   status=VideoStatus.PROCESSED.value,
                   id_user=user2.id,
                   uploaded_at=datetime.datetime.now(datetime.UTC),
                   file_uploaded_url="file://ruta/video.mp4")

    db.add(video1)
    db.add(video2)
    db.commit()

    vote = Vote(id_video=video1.id,
                id_user=user1.id,
                voted_at=datetime.datetime.now(datetime.UTC))

    db.add(vote)
    db.commit()

    yield {'users': [{'email': user1.email, 'password': password_plain},
                     {'email': user2.email, 'password': password_plain}],
           'id_videos': [video1.id, video2.id]}

    # After tests
    Base.metadata.drop_all(bind=engine)
    db.close()


def test_delete_video_with_votes_success(test_data):
    """Borrar video existente con votos registrados."""

    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})

    assert response_auth.status_code == 200

    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']

    id_video_to_delete = test_data['id_videos'][0]

    response1 = client.delete(f"/api/videos/{id_video_to_delete}",
                              headers={'Authorization': f"Bearer {token}"})

    assert response1.status_code == 200

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == f"El video con id {id_video_to_delete} fue eliminado del sistema."

    db = TestingSessionLocal()
    votes = db.query(Vote).filter(Vote.id_video == id_video_to_delete).all()

    assert len(votes) == 0

    db.close()


def test_delete_video_error_invalid_id_video(test_data):
    """Borrar video con id inválido."""

    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})

    assert response_auth.status_code == 200

    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']

    id_video_to_delete = "invalid-id-video"

    response1 = client.delete(f"/api/videos/{id_video_to_delete}",
                              headers={'Authorization': f"Bearer {token}"})

    assert response1.status_code == 400

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado."


def test_delete_video_error_not_found_id_video(test_data):
    """Borrar video con id no existente."""

    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})

    assert response_auth.status_code == 200

    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']

    id_video_to_delete = str(uuid.uuid4())

    response1 = client.delete(f"/api/videos/{id_video_to_delete}",
                              headers={'Authorization': f"Bearer {token}"})

    assert response1.status_code == 404

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado."


def test_delete_video_error_video_not_owned_by_user(test_data):
    """Borrar video con id de un video diferente."""

    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})

    assert response_auth.status_code == 200

    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']

    id_video_to_delete = test_data['id_videos'][1]

    response1 = client.delete(f"/api/videos/{id_video_to_delete}",
                              headers={'Authorization': f"Bearer {token}"})

    assert response1.status_code == 404

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado."


def test_delete_video_error_video_is_processed(test_data):
    """Borrar video con id de un video diferente."""

    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][1]['email'],
                                      'password': test_data['users'][1]['password']})

    assert response_auth.status_code == 200

    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']

    id_video_to_delete = test_data['id_videos'][1]

    response1 = client.delete(f"/api/videos/{id_video_to_delete}",
                              headers={'Authorization': f"Bearer {token}"})

    assert response1.status_code == 400

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == "El video no puede ser eliminado porque no cumple las condiciones."

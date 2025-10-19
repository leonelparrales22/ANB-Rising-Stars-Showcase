import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event
import datetime
import uuid
import io
from unittest.mock import patch, MagicMock

from app.main import app
from shared.db.config import Base, get_db
from shared.db.models.user import User
from shared.db.models.video import Video, VideoStatus
from shared.db.models.vote import Vote
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
                   uploaded_at=datetime.datetime.now(datetime.timezone.utc),
                   file_original_url="file://ruta/video.mp4")
    video2 = Video(id=str(uuid.uuid4()),
                   title="Volcada 360",
                   status=VideoStatus.PROCESSED.value,
                   id_user=user2.id,
                   uploaded_at=datetime.datetime.now(datetime.timezone.utc),
                   file_original_url="file://ruta/video.mp4")

    db.add(video1)
    db.add(video2)
    db.commit()

    vote = Vote(id_video=video1.id,
                id_user=user1.id,
                voted_at=datetime.datetime.now(datetime.timezone.utc))

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
    assert response1_json['message'] == "El vìdeo fue eliminado exitosamente"

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

    assert response1.status_code == 404

    response1_json = response1.json()
    assert 'message' in response1_json
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado"


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
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado"


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
    assert response1_json['message'] == "El video con id especificado no existe o no pertence al usuario autenticado"


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
    assert response1_json['message'] == "El video no puede ser eliminado porque no cumple las condiciones"


# ==================== NUEVAS PRUEBAS PARA ENDPOINTS DE VIDEOS ====================

def test_upload_video_success(test_data):
    """Prueba de subida exitosa de video."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    # Crear archivo de prueba
    test_video_content = b"fake video content" * 1000  # Simular contenido de video
    test_file = io.BytesIO(test_video_content)
    
    with patch('app.api.videos_api.Celery') as mock_celery:
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_celery.return_value.send_task.return_value = mock_task
        
        response = client.post(
            "/api/videos/upload",
            headers={'Authorization': f"Bearer {token}"},
            data={'title': 'Video de prueba'},
            files={'video_file': ('test_video.mp4', test_file, 'video/mp4')}
        )
        
        assert response.status_code == 201
        response_json = response.json()
        assert 'message' in response_json
        assert 'task_id' in response_json
        assert response_json['message'] == "Video subido correctamente. Procesamiento en curso."


def test_upload_video_invalid_format(test_data):
    """Prueba de subida de video con formato inválido."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    # Crear archivo con formato inválido
    test_file = io.BytesIO(b"fake content")
    
    response = client.post(
        "/api/videos/upload",
        headers={'Authorization': f"Bearer {token}"},
        data={'title': 'Video de prueba'},
        files={'video_file': ('test_video.txt', test_file, 'text/plain')}
    )
    
    assert response.status_code == 400
    response_json = response.json()
    assert 'message' in response_json
    assert response_json['message'] == "El archivo debe ser MP4"


def test_upload_video_file_too_large(test_data):
    """Prueba de subida de video que excede el límite de tamaño."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    # Crear archivo muy grande (>100MB)
    large_content = b"fake video content" * (100 * 1024 * 1024)  # Simular archivo >100MB
    test_file = io.BytesIO(large_content)
    
    response = client.post(
        "/api/videos/upload",
        headers={'Authorization': f"Bearer {token}"},
        data={'title': 'Video de prueba'},
        files={'video_file': ('test_video.mp4', test_file, 'video/mp4')}
    )
    
    assert response.status_code == 400
    response_json = response.json()
    assert 'message' in response_json
    assert response_json['message'] == "El archivo excede el límite de 100MB"


def test_get_videos_success(test_data):
    """Prueba de obtención exitosa de videos del usuario."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    response = client.get("/api/videos/", headers={'Authorization': f"Bearer {token}"})
    
    assert response.status_code == 200
    response_json = response.json()
    assert isinstance(response_json, list)
    
    # Verificar que se incluyen los videos del usuario
    video_ids = [video['video_id'] for video in response_json]
    assert test_data['id_videos'][0] in video_ids


def test_get_videos_unauthorized():
    """Prueba de obtención de videos sin autenticación."""
    
    response = client.get("/api/videos/")
    assert response.status_code == 403


def test_get_video_specific_success(test_data):
    """Prueba de obtención exitosa de un video específico."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    video_id = test_data['id_videos'][0]
    response = client.get(f"/api/videos/{video_id}", headers={'Authorization': f"Bearer {token}"})
    
    assert response.status_code == 200
    response_json = response.json()
    assert 'video_id' in response_json
    assert 'title' in response_json
    assert 'status' in response_json
    assert response_json['video_id'] == video_id


def test_get_video_specific_not_found(test_data):
    """Prueba de obtención de video que no existe."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    fake_video_id = str(uuid.uuid4())
    response = client.get(f"/api/videos/{fake_video_id}", headers={'Authorization': f"Bearer {token}"})
    
    assert response.status_code == 404
    response_json = response.json()
    assert 'message' in response_json
    assert "no existe o no pertence al usuario" in response_json['message']


def test_get_video_specific_unauthorized(test_data):
    """Prueba de obtención de video de otro usuario."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    # Intentar acceder a video de otro usuario
    other_user_video_id = test_data['id_videos'][1]
    response = client.get(f"/api/videos/{other_user_video_id}", headers={'Authorization': f"Bearer {token}"})
    
    assert response.status_code == 404
    response_json = response.json()
    assert 'message' in response_json
    assert "no existe o no pertence al usuario" in response_json['message']


def test_upload_video_missing_file(test_data):
    """Prueba de subida sin archivo."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    response = client.post(
        "/api/videos/upload",
        headers={'Authorization': f"Bearer {token}"},
        data={'title': 'Video de prueba'}
        # Sin archivo
    )
    
    assert response.status_code == 422  # Unprocessable Entity por falta de archivo


def test_upload_video_empty_title(test_data):
    """Prueba de subida con título vacío."""
    
    response_auth = client.post('/api/auth/login',
                                json={'email': test_data['users'][0]['email'],
                                      'password': test_data['users'][0]['password']})
    
    assert response_auth.status_code == 200
    response_auth_json = response_auth.json()
    token = response_auth_json['access_token']
    
    test_file = io.BytesIO(b"fake video content")
    
    response = client.post(
        "/api/videos/upload",
        headers={'Authorization': f"Bearer {token}"},
        data={'title': ''},  # Título vacío
        files={'video_file': ('test_video.mp4', test_file, 'video/mp4')}
    )
    
    assert response.status_code == 422  # Unprocessable Entity por título vacío

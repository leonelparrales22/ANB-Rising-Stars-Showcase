import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event
import datetime
import uuid
from unittest.mock import patch

from app.main import app
from shared.db.config import Base, get_db
from shared.db.models.user import User
from shared.db.models.video import Video, VideoStatus
from shared.db.models.vote import Vote
from app.core.security import get_password_hash

# Configuración de base de datos de prueba
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
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    db.query(Vote).delete()
    db.query(Video).delete()
    db.query(User).delete()
    db.commit()

    password_plain = "StrongPass123"
    password_hashed = get_password_hash(password_plain)

    user1 = User(
        id=str(uuid.uuid4()),
        first_name="John",
        last_name="Doe",
        email="john.doe@mail.com",
        password_hash=password_hashed,
        city="Bogotá",
        country="Colombia"
    )
    user2 = User(
        id=str(uuid.uuid4()),
        first_name="Bob",
        last_name="Marley",
        email="bob.marley@mail.com",
        password_hash=password_hashed,
        city="Bogotá",
        country="Colombia"
    )

    db.add(user1)
    db.add(user2)
    db.commit()

    now = datetime.datetime.now(datetime.timezone.utc)

    video1 = Video(
        id=str(uuid.uuid4()),
        title="Canasta desde media cancha",
        status=VideoStatus.UPLOADED.value,
        id_user=user1.id,
        uploaded_at=now,
        file_original_url="file://ruta/video1.mp4",
        file_processed_url=None,
        file_size_bytes=123456,
        original_duration_seconds=90,
        original_resolution="640x360",
        processed_duration_seconds=None,
        processed_resolution=None,
        processing_started_at=None,
        celery_task_id=None,
        votes=1
    )
    video2 = Video(
        id=str(uuid.uuid4()),
        title="Volcada 360",
        status=VideoStatus.PROCESSED.value,
        id_user=user2.id,
        uploaded_at=now,
        processed_at=now,
        file_original_url="file://ruta/video2.mp4",
        file_processed_url="file://ruta/video2_procesado.mp4",
        file_size_bytes=654321,
        original_duration_seconds=120,
        original_resolution="1280x720",
        processed_duration_seconds=118,
        processed_resolution="1280x720",
        processing_started_at=now,
        celery_task_id=None,
        votes=0
    )
    video3 = Video(
        id=str(uuid.uuid4()),
        title="Canasta desde inicio de cancha",
        status=VideoStatus.PROCESSED.value,
        id_user=user1.id,
        uploaded_at=now,
        file_original_url="file://ruta/video3.mp4",
        file_processed_url=None,
        file_size_bytes=123456,
        original_duration_seconds=90,
        original_resolution="640x360",
        processed_duration_seconds=None,
        processed_resolution=None,
        processing_started_at=None,
        celery_task_id=None,
        votes=1
    )

    db.add(video1)
    db.add(video2)
    db.add(video3)
    db.commit()

    vote = Vote(
        id_video=video3.id,
        id_user=user1.id,
        voted_at=now
    )

    db.add(vote)
    db.commit()

    yield {
        'users': [
            {'email': user1.email, 'password': password_plain, 'id': user1.id},
            {'email': user2.email, 'password': password_plain, 'id': user2.id}
        ],
        'videos': [video1, video2,video3],
        'db': db
    }

    Base.metadata.drop_all(bind=engine)
    db.close()


def test_get_all_public_videos_returns_only_processed(test_data):
    response = client.get("/api/public/videos")
    assert response.status_code == 200
    data = response.json()
    ids = [v["id"] for v in data]
    assert test_data["videos"][1].id in ids
    assert test_data["videos"][0].id not in ids


def test_vote_for_video_success(test_data):
    user = test_data["users"][0]
    video = test_data["videos"][1]

    db = test_data["db"]
    existing_vote = db.query(Vote).filter(Vote.id_user == user['id'], Vote.id_video == video.id).first()
    if existing_vote:
        db.delete(existing_vote)
        db.commit()

    with patch("app.api.public.verify_token", return_value=user['email']):
        response = client.post(f"/api/public/videos/{video.id}/vote", headers={"Authorization": "Bearer faketoken"})
        assert response.status_code == 200
        json_resp = response.json()
        assert json_resp["message"] == "Voto registrado exitosamente."

        vote_in_db = db.query(Vote).filter(Vote.id_user == user['id'], Vote.id_video == video.id).first()
        assert vote_in_db is not None

        video_in_db = db.query(Video).filter(Video.id == video.id).first()
        db.refresh(video_in_db)
        assert video_in_db.votes == 1


def test_vote_for_video_already_voted(test_data):
    user = test_data["users"][0]
    video = test_data["videos"][2]

    with patch("app.api.public.verify_token", return_value=user['email']):
        response = client.post(f"/api/public/videos/{video.id}/vote", headers={"Authorization": "Bearer faketoken"})
        assert response.status_code == 400
        assert response.json()["message"] == "Ya has votado por este video"


def test_vote_for_video_not_found(test_data):
    user = test_data["users"][0]
    fake_video_id = str(uuid.uuid4())

    with patch("app.api.public.verify_token", return_value=user['email']):
        response = client.post(f"/api/public/videos/{fake_video_id}/vote", headers={"Authorization": "Bearer faketoken"})
        assert response.status_code == 404
        assert response.json()["message"] == "Video no encontrado o aún no está disponible públicamente"


def test_vote_for_video_unauthorized(test_data):
    with patch("app.api.public.verify_token", return_value="noexiste@example.com"):
        response = client.post(f"/api/public/videos/{test_data['videos'][0].id}/vote", headers={"Authorization": "Bearer faketoken"})
        assert response.status_code == 401
        assert response.json()["message"] == "Usuario no autorizado"


def test_get_rankings_no_filter(test_data):
    response = client.get("/api/public/rankings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    votes = [item["votes"] for item in data]
    assert votes == sorted(votes, reverse=True)


def test_get_rankings_with_city_filter(test_data):
    city = "bogotá"
    response = client.get(f"/api/public/rankings?city={city}")
    assert response.status_code == 200
    data = response.json()
    assert all(item["city"].lower() == city for item in data)


def test_get_rankings_with_city_filter_no_results(test_data):
    city = "noexiste"
    response = client.get(f"/api/public/rankings?city={city}")
    assert response.status_code == 200
    data = response.json()
    assert data == []

from shared.db.config import engine, Base
from shared.db.models.user import User
from shared.db.models.video import Video
from shared.db.models.vote import Vote


def init_db():
    print("Creando tablas...")
    print(f"Base: {Base}")
    print(f"User: {User}")
    print(f"Video: {Video}")
    print(f"Vote: {Vote}")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")


if __name__ == "__main__":
    init_db()
    print("Tablas de la base de datos creadas.")

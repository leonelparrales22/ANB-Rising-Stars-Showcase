from .core.database import engine, Base
from .models.user import User


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Tablas de la base de datos creadas.")

from .core.database import engine, Base
from .models.user import User


def init_db():
    print("Creando tablas...")
    print(f"Base: {Base}")
    print(f"User: {User}")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")


if __name__ == "__main__":
    init_db()
    print("Tablas de la base de datos creadas.")

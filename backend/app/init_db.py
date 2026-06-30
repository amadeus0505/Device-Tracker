from app.core.database import Base, engine
from app.main import startup


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    startup()


if __name__ == "__main__":
    init_db()
    print("Database initialized")

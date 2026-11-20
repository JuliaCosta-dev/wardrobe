from collections.abc import Generator

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# monta o endereço com a conexão com o banco
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    database=settings.postgres_db,
)

# monta o banco de testes, sem modificar o banco principal
TEST_DATABASE_URL = DATABASE_URL.set(database=settings.postgres_test_db)

# Gerencia as conexões com o PostgreSQL
engine = create_engine(
    DATABASE_URL,
    # verifica se uma conexão do pool ainda está válida antes de reutilizá-la
    pool_pre_ping=True,
)

# Cria sessões independentes para operações no banco
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# Classe-base dos futuros modelos ORM
class Base(DeclarativeBase):
    pass


# Disponibiliza uma sessão e garante seu fechamento
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

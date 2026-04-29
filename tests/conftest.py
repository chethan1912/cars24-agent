import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from db.schemas import Base
from core.config import settings

url = make_url(settings.DATABASE_URL)
if url.drivername == "sqlite":
    database_path = Path(url.database)
    test_db_path = database_path.parent / \
        f"{database_path.stem}_test{database_path.suffix}"
    test_database_url = f"sqlite:///{test_db_path.as_posix()}"
else:
    test_database_url = settings.DATABASE_URL.replace("cars24", "cars24_test")

# Use a test database
engine = create_engine(test_database_url, echo=False)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    if url.drivername == "sqlite" and test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def db_session(db_engine):
    session = TestSessionLocal()
    yield session
    session.close()

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.schemas import Base
from core.config import settings

# Use a test database
test_engine = create_engine(
    settings.DATABASE_URL.replace("cars24", "cars24_test"))
TestSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(db_engine):
    session = TestSessionLocal()
    yield session
    session.close()

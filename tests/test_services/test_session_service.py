import pytest
from services.session_service import SessionService
from core.models import SessionContext


def test_session_service_save_load(db_session):
    svc = SessionService()
    context = SessionContext(session_id="test123", stage="intake")
    svc.save(context)
    loaded = svc.load("test123")
    assert loaded.session_id == "test123"
    assert loaded.stage == "intake"

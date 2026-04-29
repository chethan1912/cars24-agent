from fastapi import Depends
from sqlalchemy.orm import Session
from db.postgres import get_db as get_db_session
from services.session_service import SessionService


def get_db() -> Session:
    return next(get_db_session())


def get_session_svc() -> SessionService:
    return SessionService()

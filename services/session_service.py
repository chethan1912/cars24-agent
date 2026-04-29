import json
import redis
from datetime import timedelta
from core.models import SessionContext
from db.redis_client import get_redis

CONTEXT_TTL = timedelta(hours=24)
KEY_PREFIX = "session:"


class SessionService:
    def __init__(self):
        self.redis = get_redis()

    def load(self, session_id: str) -> SessionContext:
        key = f"{KEY_PREFIX}{session_id}"
        raw = self.redis.get(key)
        if raw is None:
            # New session — create fresh context
            return SessionContext(session_id=session_id)
        return SessionContext.model_validate_json(raw)

    def save(self, context: SessionContext) -> None:
        key = f"{KEY_PREFIX}{context.session_id}"
        self.redis.setex(
            key,
            CONTEXT_TTL,
            context.model_dump_json()
        )

    def patch(self, session_id: str, patch: dict) -> SessionContext:
        """Apply a partial update without rewriting the full object."""
        context = self.load(session_id)
        # Apply patch at top level or into nested profile
        for field, value in patch.items():
            if hasattr(context.profile, field):
                setattr(context.profile, field, value)
            elif hasattr(context, field):
                setattr(context, field, value)
        self.save(context)
        return context

    def delete(self, session_id: str) -> None:
        self.redis.delete(f"{KEY_PREFIX}{session_id}")

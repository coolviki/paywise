"""Personal API keys for the PayWise MCP connector (Phase 1 auth).

Each key belongs to exactly one user. The MCP endpoint resolves the user
from the key on every request, so tools never accept a user identifier.
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from ..models.mcp_key import McpApiKey
from ..models.user import User

KEY_PREFIX = "pw_live_"
MAX_ACTIVE_KEYS_PER_USER = 5
# Avoid a DB write on every single tool call
LAST_USED_WRITE_INTERVAL = timedelta(minutes=5)


class McpKeyLimitError(Exception):
    pass


def hash_key(raw_key: str) -> str:
    # Keys are 256-bit random values, so a fast hash is appropriate
    # (no dictionary attack is possible, unlike passwords).
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class McpKeyService:
    @staticmethod
    def create_key(db: Session, user_id: UUID, name: str) -> Tuple[McpApiKey, str]:
        """Create a key. Returns (record, raw_key). raw_key is never stored."""
        active = McpKeyService.list_keys(db, user_id, include_revoked=False)
        if len(active) >= MAX_ACTIVE_KEYS_PER_USER:
            raise McpKeyLimitError(
                f"You can have at most {MAX_ACTIVE_KEYS_PER_USER} active keys. Revoke one first."
            )

        raw_key = KEY_PREFIX + secrets.token_urlsafe(32)
        record = McpApiKey(
            user_id=user_id,
            name=(name or "Claude").strip()[:100] or "Claude",
            key_prefix=raw_key[: len(KEY_PREFIX) + 4],
            key_hash=hash_key(raw_key),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record, raw_key

    @staticmethod
    def list_keys(db: Session, user_id: UUID, include_revoked: bool = False) -> List[McpApiKey]:
        q = db.query(McpApiKey).filter(McpApiKey.user_id == user_id)
        if not include_revoked:
            q = q.filter(McpApiKey.revoked_at.is_(None))
        return q.order_by(McpApiKey.created_at.desc()).all()

    @staticmethod
    def revoke_key(db: Session, user_id: UUID, key_id: UUID) -> bool:
        """Revoke a key. Scoped by user_id so users can only revoke their own keys."""
        record = (
            db.query(McpApiKey)
            .filter(McpApiKey.id == key_id, McpApiKey.user_id == user_id)
            .first()
        )
        if not record:
            return False
        if record.revoked_at is None:
            record.revoked_at = datetime.utcnow()
            db.commit()
        return True

    @staticmethod
    def authenticate(db: Session, raw_key: Optional[str]) -> Optional[User]:
        """Resolve a raw key to its owner. Returns None for unknown/revoked keys."""
        if not raw_key or not raw_key.startswith(KEY_PREFIX):
            return None

        record = (
            db.query(McpApiKey)
            .filter(McpApiKey.key_hash == hash_key(raw_key), McpApiKey.revoked_at.is_(None))
            .first()
        )
        if not record:
            return None

        now = datetime.utcnow()
        if record.last_used_at is None or now - record.last_used_at > LAST_USED_WRITE_INTERVAL:
            record.last_used_at = now
            db.commit()

        return db.query(User).filter(User.id == record.user_id).first()

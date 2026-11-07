import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class McpApiKey(Base):
    """Personal API key a user pastes into Claude's custom connector settings.

    Only a SHA-256 hash of the key is stored. The raw key is shown to the
    user exactly once, at creation time.
    """

    __tablename__ = "mcp_api_keys"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(16), nullable=False)  # e.g. "pw_live_ab12" - for display only
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User")

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def __repr__(self):
        return f"<McpApiKey {self.key_prefix}… user={self.user_id}>"

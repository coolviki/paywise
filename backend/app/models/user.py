import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from ..core.database import Base
from ..core.types import UUID


class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    profile_picture = Column(String, nullable=True)
    auth_provider = Column(String(50), nullable=False)  # 'google', 'apple', 'email'
    auth_provider_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    payment_methods = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    recommendation_logs = relationship("RecommendationLog", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"

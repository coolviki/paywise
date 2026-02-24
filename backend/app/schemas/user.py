from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    profile_picture: Optional[str] = None
    auth_provider: str
    auth_provider_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    profile_picture: Optional[str] = None
    auth_provider: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class GoogleAuthRequest(BaseModel):
    id_token: str

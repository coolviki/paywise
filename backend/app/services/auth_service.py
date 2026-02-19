from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import httpx
from ..models.user import User
from ..schemas.user import UserCreate, TokenResponse, UserResponse
from ..core.security import create_access_token
from ..core.config import settings


class AuthService:
    GOOGLE_TOKEN_INFO_URL = "https://oauth2.googleapis.com/tokeninfo"

    @staticmethod
    async def verify_google_token(id_token: str) -> Optional[dict]:
        """Verify Google ID token and return user info."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{AuthService.GOOGLE_TOKEN_INFO_URL}?id_token={id_token}"
            )
            if response.status_code == 200:
                return response.json()
            return None

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_data.email,
            name=user_data.name,
            profile_picture=user_data.profile_picture,
            auth_provider=user_data.auth_provider,
            auth_provider_id=user_data.auth_provider_id,
            last_login=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_last_login(db: Session, user: User) -> User:
        """Update user's last login time."""
        user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    async def authenticate_google(db: Session, id_token: str) -> Optional[TokenResponse]:
        """Authenticate user with Google ID token."""
        token_info = await AuthService.verify_google_token(id_token)

        if not token_info:
            return None

        email = token_info.get("email")
        if not email:
            return None

        user = AuthService.get_user_by_email(db, email)

        if user:
            user = AuthService.update_last_login(db, user)
        else:
            user_data = UserCreate(
                email=email,
                name=token_info.get("name", email.split("@")[0]),
                profile_picture=token_info.get("picture"),
                auth_provider="google",
                auth_provider_id=token_info.get("sub"),
            )
            user = AuthService.create_user(db, user_data)

        access_token = create_access_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            user=UserResponse.model_validate(user),
        )

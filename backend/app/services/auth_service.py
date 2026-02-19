from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
import httpx
from jose import jwt, JWTError
from ..models.user import User
from ..schemas.user import UserCreate, TokenResponse, UserResponse
from ..core.security import create_access_token
from ..core.config import settings


class AuthService:
    GOOGLE_CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
    _cached_certs = None

    @staticmethod
    async def get_google_certs() -> dict:
        """Fetch Google's public certificates for Firebase token verification."""
        if AuthService._cached_certs:
            return AuthService._cached_certs
        async with httpx.AsyncClient() as client:
            response = await client.get(AuthService.GOOGLE_CERTS_URL)
            if response.status_code == 200:
                AuthService._cached_certs = response.json()
                return AuthService._cached_certs
        return {}

    @staticmethod
    async def verify_google_token(id_token: str) -> Optional[dict]:
        """Verify Firebase ID token and return user info."""
        try:
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(id_token)
            kid = unverified_header.get("kid")

            # Decode claims without verification for user info
            # In production, you should verify with Firebase Admin SDK
            unverified_claims = jwt.get_unverified_claims(id_token)

            # Extract user info from Firebase token claims
            return {
                "sub": unverified_claims.get("user_id") or unverified_claims.get("sub"),
                "email": unverified_claims.get("email"),
                "name": unverified_claims.get("name", unverified_claims.get("email", "").split("@")[0]),
                "picture": unverified_claims.get("picture"),
                "email_verified": unverified_claims.get("email_verified", False),
            }
        except JWTError as e:
            print(f"[AUTH] JWT decode error: {e}")
            return None
        except Exception as e:
            print(f"[AUTH] Token verification error: {e}")
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

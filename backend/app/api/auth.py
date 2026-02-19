from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.user import TokenResponse, GoogleAuthRequest
from ..services.auth_service import AuthService

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """Authenticate with Google ID token."""
    result = await AuthService.authenticate_google(db, request.id_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )

    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token():
    """Refresh access token."""
    # TODO: Implement refresh token logic
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Not implemented",
    )

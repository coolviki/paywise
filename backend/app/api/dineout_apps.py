"""
Dine-out payment apps API.
Manages user's selected dine-in payment apps (Swiggy Dineout, EazyDiner, District).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.card import PaymentMethod

router = APIRouter()


# Available dine-out apps
DINEOUT_APPS = {
    "swiggy_dineout": {
        "code": "swiggy_dineout",
        "name": "Swiggy Dineout",
        "logo_url": "https://res.cloudinary.com/swiggy/image/upload/fl_lossy,f_auto,q_auto/portal/m/dineout_logo.png",
        "color": "#FC8019",
    },
    "eazydiner": {
        "code": "eazydiner",
        "name": "EazyDiner",
        "logo_url": "https://www.eazydiner.com/images/logo.png",
        "color": "#8B5CF6",
    },
    "district": {
        "code": "district",
        "name": "District",
        "logo_url": "https://www.district.in/images/logo.png",
        "color": "#3B82F6",
    },
}


class DineoutApp(BaseModel):
    """Dine-out app info."""
    code: str
    name: str
    logo_url: str | None = None
    color: str
    is_enabled: bool = False
    coming_soon: bool = False


class DineoutAppsResponse(BaseModel):
    """Response with all dine-out apps and their enabled status."""
    apps: List[DineoutApp]


class EnableDineoutAppRequest(BaseModel):
    """Request to enable/disable a dine-out app."""
    app_code: str
    enabled: bool


@router.get("", response_model=DineoutAppsResponse)
async def get_dineout_apps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all dine-out apps with user's enabled status."""
    # Get user's enabled dine-out apps
    enabled_apps = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.payment_type == "dineout_app",
            PaymentMethod.is_active == True,
        )
        .all()
    )
    enabled_codes = {pm.nickname for pm in enabled_apps}

    # Build response
    apps = []
    for code, info in DINEOUT_APPS.items():
        apps.append(DineoutApp(
            code=info["code"],
            name=info["name"],
            logo_url=info.get("logo_url"),
            color=info["color"],
            is_enabled=code in enabled_codes,
            coming_soon=info.get("coming_soon", False),
        ))

    return DineoutAppsResponse(apps=apps)


@router.post("/toggle", response_model=DineoutApp)
async def toggle_dineout_app(
    request: EnableDineoutAppRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Enable or disable a dine-out app for the user."""
    app_code = request.app_code

    if app_code not in DINEOUT_APPS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown dine-out app: {app_code}",
        )

    app_info = DINEOUT_APPS[app_code]

    if app_info.get("coming_soon"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{app_info['name']} is coming soon",
        )

    # Find existing payment method for this app
    existing = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.payment_type == "dineout_app",
            PaymentMethod.nickname == app_code,
        )
        .first()
    )

    if request.enabled:
        # Enable the app
        if existing:
            existing.is_active = True
        else:
            new_pm = PaymentMethod(
                user_id=current_user.id,
                payment_type="dineout_app",
                nickname=app_code,
                is_active=True,
            )
            db.add(new_pm)
        db.commit()
    else:
        # Disable the app
        if existing:
            existing.is_active = False
            db.commit()

    return DineoutApp(
        code=app_info["code"],
        name=app_info["name"],
        logo_url=app_info.get("logo_url"),
        color=app_info["color"],
        is_enabled=request.enabled,
        coming_soon=False,
    )


@router.get("/enabled", response_model=List[str])
async def get_enabled_dineout_apps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of enabled dine-out app codes for the user."""
    enabled_apps = (
        db.query(PaymentMethod)
        .filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.payment_type == "dineout_app",
            PaymentMethod.is_active == True,
        )
        .all()
    )
    return [pm.nickname for pm in enabled_apps if pm.nickname]

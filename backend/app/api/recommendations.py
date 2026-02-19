from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.recommendation import RecommendationRequest, RecommendationResponse
from ..services.recommendation_service import RecommendationService

router = APIRouter()


@router.post("", response_model=RecommendationResponse)
async def get_recommendation(
    request: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment recommendation for a merchant."""
    result = await RecommendationService.get_recommendation(
        db, current_user.id, request
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to generate recommendation. Please add payment methods first.",
        )

    return result


@router.get("/merchant/{merchant_id}", response_model=RecommendationResponse)
async def get_recommendation_for_merchant(
    merchant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment recommendation for a merchant (GET endpoint)."""
    request = RecommendationRequest(merchant_id=merchant_id)

    result = await RecommendationService.get_recommendation(
        db, current_user.id, request
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unable to generate recommendation. Please add payment methods first.",
        )

    return result

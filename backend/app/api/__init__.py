from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .cards import router as cards_router
from .search import router as search_router
from .recommendations import router as recommendations_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(cards_router, prefix="/cards", tags=["Cards"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])

__all__ = ["api_router"]

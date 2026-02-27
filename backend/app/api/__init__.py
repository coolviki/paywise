from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .cards import router as cards_router
from .search import router as search_router
from .recommendations import router as recommendations_router
from .admin import router as admin_router
from .restaurant_offers import router as restaurant_offers_router
from .dineout_apps import router as dineout_apps_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(cards_router, prefix="/cards", tags=["Cards"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])
api_router.include_router(restaurant_offers_router, prefix="/restaurant-offers", tags=["Restaurant Offers"])
api_router.include_router(dineout_apps_router, prefix="/dineout-apps", tags=["Dine-out Apps"])

__all__ = ["api_router"]

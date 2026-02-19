from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..schemas.recommendation import SearchQuery, MerchantSearchResult, MerchantLocationResult
from ..services.location_service import LocationService

router = APIRouter()


@router.get("/merchants", response_model=List[MerchantSearchResult])
async def search_merchants(
    q: str = Query(..., min_length=1, description="Search query"),
    latitude: Optional[float] = Query(None, description="User's latitude"),
    longitude: Optional[float] = Query(None, description="User's longitude"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search merchants by name with optional location context."""
    results = LocationService.search_merchants(
        db, q, latitude, longitude, limit
    )

    return [
        MerchantSearchResult(
            id=merchant.id,
            name=merchant.name,
            category=merchant.category.name if merchant.category else None,
            logo_url=merchant.logo_url,
            is_chain=merchant.is_chain,
            locations=[
                MerchantLocationResult(
                    id=loc.id,
                    address=loc.address,
                    city=loc.city,
                    distance_km=getattr(loc, "distance_km", None),
                    has_offer=offer_count > 0,
                )
                for loc in locations
            ],
            offer_count=offer_count,
        )
        for merchant, locations, offer_count in results
    ]


@router.get("/nearby", response_model=List[MerchantSearchResult])
async def get_nearby_merchants(
    latitude: float = Query(..., description="User's latitude"),
    longitude: float = Query(..., description="User's longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=50, description="Search radius in km"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get merchants near a location."""
    results = LocationService.get_nearby_merchants(
        db, latitude, longitude, radius_km, limit
    )

    # Group by merchant
    merchant_map = {}
    for merchant, location, distance in results:
        if merchant.id not in merchant_map:
            merchant_map[merchant.id] = {
                "merchant": merchant,
                "locations": [],
            }
        merchant_map[merchant.id]["locations"].append((location, distance))

    return [
        MerchantSearchResult(
            id=data["merchant"].id,
            name=data["merchant"].name,
            category=data["merchant"].category.name if data["merchant"].category else None,
            logo_url=data["merchant"].logo_url,
            is_chain=data["merchant"].is_chain,
            locations=[
                MerchantLocationResult(
                    id=loc.id,
                    address=loc.address,
                    city=loc.city,
                    distance_km=round(dist, 1),
                    has_offer=False,
                )
                for loc, dist in data["locations"]
            ],
            offer_count=0,
        )
        for data in merchant_map.values()
    ]


@router.get("/places")
async def search_google_places(
    q: str = Query(..., min_length=1, description="Search query"),
    latitude: Optional[float] = Query(None, description="User's latitude"),
    longitude: Optional[float] = Query(None, description="User's longitude"),
):
    """Search places using Google Places API."""
    results = await LocationService.search_google_places(q, latitude, longitude)

    return [
        {
            "place_id": place.get("place_id"),
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "location": place.get("geometry", {}).get("location"),
            "types": place.get("types", []),
        }
        for place in results
    ]

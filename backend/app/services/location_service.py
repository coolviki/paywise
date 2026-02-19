from typing import List, Optional, Tuple
from uuid import UUID
import httpx
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from decimal import Decimal
from math import radians, sin, cos, sqrt, atan2

from ..models.merchant import Merchant, MerchantLocation, Category
from ..models.offer import Offer
from ..core.config import settings


class LocationService:
    GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place"

    @staticmethod
    def calculate_distance(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """Calculate distance between two coordinates in km using Haversine formula."""
        R = 6371  # Earth's radius in kilometers

        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lon = radians(lon2 - lon1)

        a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c

    @staticmethod
    async def search_google_places(
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> List[dict]:
        """Search for places using Google Places API."""
        if not settings.google_places_api_key:
            return []

        params = {
            "query": query,
            "key": settings.google_places_api_key,
        }

        if latitude and longitude:
            params["location"] = f"{latitude},{longitude}"
            params["radius"] = "5000"  # 5km radius

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LocationService.GOOGLE_PLACES_URL}/textsearch/json",
                params=params,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])

        return []

    @staticmethod
    def search_merchants(
        db: Session,
        query: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        limit: int = 10,
    ) -> List[Tuple[Merchant, List[MerchantLocation], int]]:
        """Search merchants by name with optional location filtering."""
        merchants = (
            db.query(Merchant)
            .options(
                joinedload(Merchant.category),
                joinedload(Merchant.locations),
            )
            .filter(
                Merchant.is_active == True,
                Merchant.name.ilike(f"%{query}%"),
            )
            .limit(limit)
            .all()
        )

        results = []
        for merchant in merchants:
            locations = []
            for loc in merchant.locations:
                if loc.is_active:
                    if latitude and longitude and loc.latitude and loc.longitude:
                        distance = LocationService.calculate_distance(
                            latitude, longitude,
                            float(loc.latitude), float(loc.longitude)
                        )
                        loc.distance_km = round(distance, 1)
                    else:
                        loc.distance_km = None
                    locations.append(loc)

            # Sort locations by distance if coordinates provided
            if latitude and longitude:
                locations.sort(key=lambda x: x.distance_km if x.distance_km else float("inf"))

            # Count offers for this merchant
            offer_count = (
                db.query(func.count(Offer.id))
                .filter(
                    Offer.merchant_id == merchant.id,
                    Offer.is_active == True,
                )
                .scalar()
            )

            results.append((merchant, locations[:5], offer_count))

        return results

    @staticmethod
    def get_nearby_merchants(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        limit: int = 20,
    ) -> List[Tuple[Merchant, MerchantLocation, float]]:
        """Get merchants near a location."""
        # Calculate bounding box for initial filtering
        lat_delta = radius_km / 111  # 1 degree latitude ≈ 111 km
        lon_delta = radius_km / (111 * cos(radians(latitude)))

        locations = (
            db.query(MerchantLocation)
            .options(joinedload(MerchantLocation.merchant).joinedload(Merchant.category))
            .filter(
                MerchantLocation.is_active == True,
                MerchantLocation.latitude.between(
                    latitude - lat_delta, latitude + lat_delta
                ),
                MerchantLocation.longitude.between(
                    longitude - lon_delta, longitude + lon_delta
                ),
            )
            .all()
        )

        # Calculate actual distances and filter
        results = []
        for loc in locations:
            if loc.latitude and loc.longitude:
                distance = LocationService.calculate_distance(
                    latitude, longitude,
                    float(loc.latitude), float(loc.longitude)
                )
                if distance <= radius_km:
                    results.append((loc.merchant, loc, distance))

        # Sort by distance and limit
        results.sort(key=lambda x: x[2])
        return results[:limit]

    @staticmethod
    def get_merchant_by_id(db: Session, merchant_id: UUID) -> Optional[Merchant]:
        """Get merchant by ID with locations."""
        return (
            db.query(Merchant)
            .options(
                joinedload(Merchant.category),
                joinedload(Merchant.locations),
            )
            .filter(Merchant.id == merchant_id)
            .first()
        )

    @staticmethod
    def get_categories(db: Session, parent_id: Optional[UUID] = None) -> List[Category]:
        """Get categories, optionally filtered by parent."""
        query = db.query(Category).filter(Category.is_active == True)
        if parent_id:
            query = query.filter(Category.parent_id == parent_id)
        else:
            query = query.filter(Category.parent_id.is_(None))
        return query.order_by(Category.name).all()

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


# ============================================
# Brand Schemas
# ============================================

class KeywordCreate(BaseModel):
    keyword: str


class KeywordResponse(BaseModel):
    id: UUID
    keyword: str
    created_at: datetime

    class Config:
        from_attributes = True


class BrandCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = []


class BrandUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class BrandResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    keywords: List[KeywordResponse] = []

    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool
    keyword_count: int = 0

    class Config:
        from_attributes = True


# ============================================
# Ecosystem Benefit Schemas
# ============================================

class EcosystemBenefitCreate(BaseModel):
    card_id: UUID
    brand_id: UUID
    benefit_rate: Decimal
    benefit_type: str
    description: Optional[str] = None


class EcosystemBenefitUpdate(BaseModel):
    benefit_rate: Optional[Decimal] = None
    benefit_type: Optional[str] = None
    description: Optional[str] = None


class EcosystemBenefitResponse(BaseModel):
    id: UUID
    card_id: UUID
    card_name: str
    bank_name: str
    brand_id: UUID
    brand_name: str
    benefit_rate: Decimal
    benefit_type: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# Card Schemas (for dropdowns)
# ============================================

class CardSimple(BaseModel):
    id: UUID
    name: str
    bank_name: str

    class Config:
        from_attributes = True


# ============================================
# Pending Changes Schemas (for scraper)
# ============================================

class PendingChangeResponse(BaseModel):
    id: UUID
    card_id: Optional[UUID] = None
    card_name: Optional[str] = None
    brand_id: Optional[UUID] = None
    brand_name: Optional[str] = None
    benefit_rate: Optional[Decimal] = None
    benefit_type: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    change_type: str  # 'new', 'update', 'delete'
    old_values: Optional[dict] = None
    status: str  # 'pending', 'approved', 'rejected'
    scraped_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PendingChangeUpdate(BaseModel):
    benefit_rate: Optional[Decimal] = None
    benefit_type: Optional[str] = None
    description: Optional[str] = None


class ScraperStatusResponse(BaseModel):
    status: str  # 'idle', 'running', 'completed', 'failed'
    last_run: Optional[datetime] = None
    last_bank: Optional[str] = None
    pending_count: int = 0
    error: Optional[str] = None

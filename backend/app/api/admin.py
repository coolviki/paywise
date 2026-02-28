from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_admin
from ..models.user import User
from ..models.merchant import Brand, BrandKeyword
from ..models.card import Card, Bank, CardEcosystemBenefit
from ..models.pending import PendingEcosystemChange, PendingBrandChange, PendingCardChange
from ..models.campaign import Campaign, PendingCampaign
from ..schemas.admin import (
    BrandCreate, BrandUpdate, BrandResponse, BrandListResponse,
    KeywordCreate, KeywordResponse,
    EcosystemBenefitCreate, EcosystemBenefitUpdate, EcosystemBenefitResponse,
    CardSimple, CardCreate, CardUpdate, CardResponse, BankSimple, MergeCardsRequest,
    PendingChangeResponse, PendingChangeUpdate, ScraperStatusResponse,
    PendingBrandResponse, PendingBrandUpdate,
    PendingCardResponse, PendingCardUpdate, PendingCardCreate,
    CampaignCreate, CampaignUpdate, CampaignResponse,
    PendingCampaignCreate, PendingCampaignUpdate, PendingCampaignResponse,
)
from ..services.scraper import ScraperService

router = APIRouter()


# ============================================
# BRANDS CRUD
# ============================================

@router.get("/brands", response_model=List[BrandListResponse])
async def list_brands(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all brands with keyword counts."""
    brands = db.query(Brand).options(joinedload(Brand.keywords)).order_by(Brand.name).all()
    result = []
    for brand in brands:
        result.append(BrandListResponse(
            id=brand.id,
            name=brand.name,
            code=brand.code,
            description=brand.description,
            is_active=brand.is_active if brand.is_active is not None else True,
            keyword_count=len(brand.keywords),
        ))
    return result


@router.get("/brands/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get a brand with all its keywords."""
    brand = db.query(Brand).options(joinedload(Brand.keywords)).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return brand


@router.post("/brands", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    data: BrandCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new brand with optional keywords."""
    # Check if code already exists
    existing = db.query(Brand).filter(Brand.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Brand with code '{data.code}' already exists")

    brand = Brand(
        name=data.name,
        code=data.code,
        description=data.description,
    )
    db.add(brand)
    db.flush()

    # Add keywords
    for kw in data.keywords or []:
        db.add(BrandKeyword(brand_id=brand.id, keyword=kw.lower()))

    db.commit()
    db.refresh(brand)
    return db.query(Brand).options(joinedload(Brand.keywords)).filter(Brand.id == brand.id).first()


@router.put("/brands/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    data: BrandUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    if data.name is not None:
        brand.name = data.name
    if data.code is not None:
        # Check uniqueness
        existing = db.query(Brand).filter(Brand.code == data.code, Brand.id != brand_id).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Brand with code '{data.code}' already exists")
        brand.code = data.code
    if data.description is not None:
        brand.description = data.description

    db.commit()
    return db.query(Brand).options(joinedload(Brand.keywords)).filter(Brand.id == brand_id).first()


@router.delete("/brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a brand and all its keywords."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    db.delete(brand)
    db.commit()


# ============================================
# KEYWORDS CRUD
# ============================================

@router.post("/brands/{brand_id}/keywords", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
async def add_keyword(
    brand_id: UUID,
    data: KeywordCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Add a keyword to a brand."""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Check if keyword already exists for this brand
    existing = db.query(BrandKeyword).filter(
        BrandKeyword.brand_id == brand_id,
        BrandKeyword.keyword == data.keyword.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Keyword already exists for this brand")

    keyword = BrandKeyword(brand_id=brand_id, keyword=data.keyword.lower())
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    return keyword


@router.delete("/brands/{brand_id}/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    brand_id: UUID,
    keyword_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a keyword from a brand."""
    keyword = db.query(BrandKeyword).filter(
        BrandKeyword.id == keyword_id,
        BrandKeyword.brand_id == brand_id
    ).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")

    db.delete(keyword)
    db.commit()


# ============================================
# ECOSYSTEM BENEFITS CRUD
# ============================================

@router.get("/ecosystem-benefits", response_model=List[EcosystemBenefitResponse])
async def list_ecosystem_benefits(
    brand_id: Optional[UUID] = None,
    bank_code: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all ecosystem benefits with optional filters."""
    query = db.query(CardEcosystemBenefit).options(
        joinedload(CardEcosystemBenefit.card).joinedload(Card.bank),
        joinedload(CardEcosystemBenefit.brand),
    )

    if brand_id:
        query = query.filter(CardEcosystemBenefit.brand_id == brand_id)

    if bank_code:
        query = query.join(Card).join(Bank).filter(Bank.code == bank_code)

    benefits = query.order_by(CardEcosystemBenefit.created_at.desc()).all()

    result = []
    for b in benefits:
        result.append(EcosystemBenefitResponse(
            id=b.id,
            card_id=b.card_id,
            card_name=b.card.name if b.card else "Unknown",
            bank_name=b.card.bank.name if b.card and b.card.bank else "Unknown",
            brand_id=b.brand_id,
            brand_name=b.brand.name if b.brand else "Unknown",
            benefit_rate=b.benefit_rate,
            benefit_type=b.benefit_type,
            description=b.description,
            is_active=b.is_active if b.is_active is not None else True,
            created_at=b.created_at,
        ))
    return result


@router.post("/ecosystem-benefits", response_model=EcosystemBenefitResponse, status_code=status.HTTP_201_CREATED)
async def create_ecosystem_benefit(
    data: EcosystemBenefitCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new ecosystem benefit."""
    # Validate card exists
    card = db.query(Card).options(joinedload(Card.bank)).filter(Card.id == data.card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == data.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Check if benefit already exists for this card-brand combo
    existing = db.query(CardEcosystemBenefit).filter(
        CardEcosystemBenefit.card_id == data.card_id,
        CardEcosystemBenefit.brand_id == data.brand_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ecosystem benefit already exists for this card-brand combination")

    benefit = CardEcosystemBenefit(
        card_id=data.card_id,
        brand_id=data.brand_id,
        benefit_rate=data.benefit_rate,
        benefit_type=data.benefit_type,
        description=data.description,
    )
    db.add(benefit)
    db.commit()
    db.refresh(benefit)

    return EcosystemBenefitResponse(
        id=benefit.id,
        card_id=benefit.card_id,
        card_name=card.name,
        bank_name=card.bank.name if card.bank else "Unknown",
        brand_id=benefit.brand_id,
        brand_name=brand.name,
        benefit_rate=benefit.benefit_rate,
        benefit_type=benefit.benefit_type,
        description=benefit.description,
        is_active=benefit.is_active if benefit.is_active is not None else True,
        created_at=benefit.created_at,
    )


@router.put("/ecosystem-benefits/{benefit_id}", response_model=EcosystemBenefitResponse)
async def update_ecosystem_benefit(
    benefit_id: UUID,
    data: EcosystemBenefitUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update an ecosystem benefit."""
    benefit = db.query(CardEcosystemBenefit).options(
        joinedload(CardEcosystemBenefit.card).joinedload(Card.bank),
        joinedload(CardEcosystemBenefit.brand),
    ).filter(CardEcosystemBenefit.id == benefit_id).first()

    if not benefit:
        raise HTTPException(status_code=404, detail="Ecosystem benefit not found")

    if data.benefit_rate is not None:
        benefit.benefit_rate = data.benefit_rate
    if data.benefit_type is not None:
        benefit.benefit_type = data.benefit_type
    if data.description is not None:
        benefit.description = data.description

    db.commit()
    db.refresh(benefit)

    return EcosystemBenefitResponse(
        id=benefit.id,
        card_id=benefit.card_id,
        card_name=benefit.card.name if benefit.card else "Unknown",
        bank_name=benefit.card.bank.name if benefit.card and benefit.card.bank else "Unknown",
        brand_id=benefit.brand_id,
        brand_name=benefit.brand.name if benefit.brand else "Unknown",
        benefit_rate=benefit.benefit_rate,
        benefit_type=benefit.benefit_type,
        description=benefit.description,
        is_active=benefit.is_active if benefit.is_active is not None else True,
        created_at=benefit.created_at,
    )


@router.delete("/ecosystem-benefits/{benefit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ecosystem_benefit(
    benefit_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete an ecosystem benefit."""
    benefit = db.query(CardEcosystemBenefit).filter(CardEcosystemBenefit.id == benefit_id).first()
    if not benefit:
        raise HTTPException(status_code=404, detail="Ecosystem benefit not found")

    db.delete(benefit)
    db.commit()


# ============================================
# CARDS (for dropdowns)
# ============================================

@router.get("/cards", response_model=List[CardSimple])
async def list_cards(
    search: Optional[str] = None,
    bank_code: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all cards for dropdown selection."""
    query = db.query(Card).options(joinedload(Card.bank)).filter(Card.is_active == True)

    if bank_code:
        query = query.join(Bank).filter(Bank.code == bank_code)

    if search:
        query = query.filter(Card.name.ilike(f"%{search}%"))

    cards = query.order_by(Card.name).limit(100).all()

    return [
        CardSimple(
            id=card.id,
            name=card.name,
            bank_name=card.bank.name if card.bank else "Unknown",
        )
        for card in cards
    ]


# ============================================
# CARDS CRUD
# ============================================

@router.get("/banks", response_model=List[BankSimple])
async def list_banks(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all banks for dropdown selection."""
    banks = db.query(Bank).filter(Bank.is_active == True).order_by(Bank.name).all()
    return [
        BankSimple(id=b.id, name=b.name, code=b.code)
        for b in banks
    ]


@router.get("/cards/all", response_model=List[CardResponse])
async def list_all_cards(
    search: Optional[str] = None,
    bank_id: Optional[UUID] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all cards with full details for admin management."""
    query = db.query(Card).options(joinedload(Card.bank))

    if not include_inactive:
        query = query.filter(Card.is_active == True)

    if bank_id:
        query = query.filter(Card.bank_id == bank_id)

    if search:
        query = query.filter(Card.name.ilike(f"%{search}%"))

    cards = query.order_by(Card.name).all()

    return [
        CardResponse(
            id=card.id,
            bank_id=card.bank_id,
            bank_name=card.bank.name if card.bank else "Unknown",
            name=card.name,
            card_type=card.card_type,
            card_network=card.card_network,
            annual_fee=card.annual_fee,
            reward_type=card.reward_type,
            base_reward_rate=card.base_reward_rate,
            terms_url=card.terms_url,
            is_active=card.is_active if card.is_active is not None else True,
            created_at=card.created_at,
        )
        for card in cards
    ]


@router.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Get a single card by ID."""
    card = db.query(Card).options(joinedload(Card.bank)).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    return CardResponse(
        id=card.id,
        bank_id=card.bank_id,
        bank_name=card.bank.name if card.bank else "Unknown",
        name=card.name,
        card_type=card.card_type,
        card_network=card.card_network,
        annual_fee=card.annual_fee,
        reward_type=card.reward_type,
        base_reward_rate=card.base_reward_rate,
        terms_url=card.terms_url,
        is_active=card.is_active if card.is_active is not None else True,
        created_at=card.created_at,
    )


@router.post("/cards/new", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    data: CardCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new card."""
    # Validate bank exists
    bank = db.query(Bank).filter(Bank.id == data.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    # Check for duplicate card name within same bank
    existing = db.query(Card).filter(
        Card.bank_id == data.bank_id,
        Card.name.ilike(data.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Card '{data.name}' already exists for this bank")

    card = Card(
        bank_id=data.bank_id,
        name=data.name,
        card_type=data.card_type,
        card_network=data.card_network,
        annual_fee=data.annual_fee,
        reward_type=data.reward_type,
        base_reward_rate=data.base_reward_rate,
        terms_url=data.terms_url,
        is_active=True,
    )
    db.add(card)
    db.commit()
    db.refresh(card)

    return CardResponse(
        id=card.id,
        bank_id=card.bank_id,
        bank_name=bank.name,
        name=card.name,
        card_type=card.card_type,
        card_network=card.card_network,
        annual_fee=card.annual_fee,
        reward_type=card.reward_type,
        base_reward_rate=card.base_reward_rate,
        terms_url=card.terms_url,
        is_active=card.is_active,
        created_at=card.created_at,
    )


@router.put("/cards/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: UUID,
    data: CardUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a card."""
    card = db.query(Card).options(joinedload(Card.bank)).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if data.name is not None:
        card.name = data.name
    if data.card_type is not None:
        card.card_type = data.card_type
    if data.card_network is not None:
        card.card_network = data.card_network
    if data.annual_fee is not None:
        card.annual_fee = data.annual_fee
    if data.reward_type is not None:
        card.reward_type = data.reward_type
    if data.base_reward_rate is not None:
        card.base_reward_rate = data.base_reward_rate
    if data.terms_url is not None:
        card.terms_url = data.terms_url
    if data.is_active is not None:
        card.is_active = data.is_active

    db.commit()
    db.refresh(card)

    return CardResponse(
        id=card.id,
        bank_id=card.bank_id,
        bank_name=card.bank.name if card.bank else "Unknown",
        name=card.name,
        card_type=card.card_type,
        card_network=card.card_network,
        annual_fee=card.annual_fee,
        reward_type=card.reward_type,
        base_reward_rate=card.base_reward_rate,
        terms_url=card.terms_url,
        is_active=card.is_active if card.is_active is not None else True,
        created_at=card.created_at,
    )


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a card (soft delete by setting is_active=False)."""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Soft delete
    card.is_active = False
    db.commit()


# ============================================
# SCRAPER ENDPOINTS
# ============================================

def run_scraper_background(db: Session, bank: Optional[str] = None):
    """Background task to run the scraper."""
    service = ScraperService(db)
    service.run_sync(bank)


@router.post("/scraper/run")
async def run_scraper(
    background_tasks: BackgroundTasks,
    bank: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Trigger the scraper to fetch card benefits from bank websites.

    Args:
        bank: Optional bank to scrape (hdfc, icici, sbi). If not provided, scrapes all.
    """
    status_info = ScraperService.get_status()
    if status_info["is_running"]:
        raise HTTPException(status_code=400, detail="Scraper is already running")

    # Run in background
    background_tasks.add_task(run_scraper_background, db, bank)

    return {"message": f"Scraper started for {'all banks' if not bank else bank.upper()}"}


@router.get("/scraper/status")
async def get_scraper_status(
    admin: User = Depends(get_current_admin),
):
    """Get the current scraper status."""
    return ScraperService.get_status()


# ============================================
# PENDING CHANGES ENDPOINTS
# ============================================

@router.get("/pending", response_model=List[PendingChangeResponse])
async def list_pending_changes(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    List pending ecosystem changes.

    Args:
        status: Optional status filter (pending, approved, rejected)
    """
    changes = db.query(PendingEcosystemChange).options(
        joinedload(PendingEcosystemChange.card).joinedload(Card.bank),
        joinedload(PendingEcosystemChange.brand),
    )

    if status:
        changes = changes.filter(PendingEcosystemChange.status == status)

    changes = changes.order_by(PendingEcosystemChange.created_at.desc()).all()

    result = []
    for change in changes:
        result.append(PendingChangeResponse(
            id=change.id,
            card_id=change.card_id,
            card_name=change.card.name if change.card else None,
            brand_id=change.brand_id,
            brand_name=change.brand.name if change.brand else None,
            benefit_rate=change.benefit_rate,
            benefit_type=change.benefit_type,
            description=change.description,
            source_url=change.source_url,
            change_type=change.change_type,
            old_values=change.old_values,
            status=change.status,
            scraped_at=change.scraped_at,
            reviewed_at=change.reviewed_at,
        ))
    return result


@router.put("/pending/{change_id}", response_model=PendingChangeResponse)
async def update_pending_change(
    change_id: UUID,
    data: PendingChangeUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a pending change before approval."""
    service = ScraperService(db)
    change = service.update_pending_change(
        change_id,
        benefit_rate=float(data.benefit_rate) if data.benefit_rate else None,
        benefit_type=data.benefit_type,
        description=data.description,
    )

    if not change:
        raise HTTPException(status_code=404, detail="Pending change not found or already processed")

    # Reload with relationships
    change = db.query(PendingEcosystemChange).options(
        joinedload(PendingEcosystemChange.card).joinedload(Card.bank),
        joinedload(PendingEcosystemChange.brand),
    ).filter(PendingEcosystemChange.id == change_id).first()

    return PendingChangeResponse(
        id=change.id,
        card_id=change.card_id,
        card_name=change.card.name if change.card else None,
        brand_id=change.brand_id,
        brand_name=change.brand.name if change.brand else None,
        benefit_rate=change.benefit_rate,
        benefit_type=change.benefit_type,
        description=change.description,
        source_url=change.source_url,
        change_type=change.change_type,
        old_values=change.old_values,
        status=change.status,
        scraped_at=change.scraped_at,
        reviewed_at=change.reviewed_at,
    )


@router.post("/pending/{change_id}/approve")
async def approve_pending_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve a pending change and apply it to production."""
    service = ScraperService(db)
    success = service.approve_change(change_id, admin.id)

    if not success:
        raise HTTPException(status_code=404, detail="Pending change not found or already processed")

    return {"message": "Change approved and applied"}


@router.post("/pending/{change_id}/reject")
async def reject_pending_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Reject a pending change."""
    service = ScraperService(db)
    success = service.reject_change(change_id, admin.id)

    if not success:
        raise HTTPException(status_code=404, detail="Pending change not found or already processed")

    return {"message": "Change rejected"}


@router.delete("/pending/{change_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_change(
    change_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a pending change."""
    service = ScraperService(db)
    success = service.delete_pending_change(change_id)

    if not success:
        raise HTTPException(status_code=404, detail="Pending change not found")


@router.post("/pending/approve-all")
async def approve_all_pending(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve all pending changes."""
    changes = db.query(PendingEcosystemChange).filter(
        PendingEcosystemChange.status == "pending"
    ).all()

    if not changes:
        return {"message": "No pending changes to approve", "approved": 0, "failed": 0}

    service = ScraperService(db)
    change_ids = [c.id for c in changes]
    result = service.bulk_approve(change_ids, admin.id)

    return {
        "message": f"Processed {len(change_ids)} changes",
        **result
    }


# ============================================
# PENDING BRANDS ENDPOINTS
# ============================================

@router.get("/pending-brands", response_model=List[PendingBrandResponse])
async def list_pending_brands(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    List pending brand changes.

    Args:
        status: Optional status filter (pending, approved, rejected)
    """
    service = ScraperService(db)
    brands = service.get_pending_brands(status)

    return [
        PendingBrandResponse(
            id=b.id,
            name=b.name,
            code=b.code,
            description=b.description,
            keywords=b.keywords or [],
            source_url=b.source_url,
            source_bank=b.source_bank,
            status=b.status,
            scraped_at=b.scraped_at,
            reviewed_at=b.reviewed_at,
        )
        for b in brands
    ]


@router.put("/pending-brands/{brand_id}", response_model=PendingBrandResponse)
async def update_pending_brand(
    brand_id: UUID,
    data: PendingBrandUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a pending brand before approval."""
    service = ScraperService(db)
    brand = service.update_pending_brand(
        brand_id,
        name=data.name,
        code=data.code,
        description=data.description,
        keywords=data.keywords,
    )

    if not brand:
        raise HTTPException(status_code=404, detail="Pending brand not found or already processed")

    return PendingBrandResponse(
        id=brand.id,
        name=brand.name,
        code=brand.code,
        description=brand.description,
        keywords=brand.keywords or [],
        source_url=brand.source_url,
        source_bank=brand.source_bank,
        status=brand.status,
        scraped_at=brand.scraped_at,
        reviewed_at=brand.reviewed_at,
    )


@router.post("/pending-brands/{brand_id}/approve")
async def approve_pending_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve a pending brand and create it in the database."""
    service = ScraperService(db)
    brand = service.approve_brand(brand_id, admin.id)

    if not brand:
        raise HTTPException(status_code=404, detail="Pending brand not found or already processed")

    return {"message": f"Brand '{brand.name}' approved and created"}


@router.post("/pending-brands/{brand_id}/reject")
async def reject_pending_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Reject a pending brand."""
    service = ScraperService(db)
    success = service.reject_brand(brand_id, admin.id)

    if not success:
        raise HTTPException(status_code=404, detail="Pending brand not found or already processed")

    return {"message": "Brand rejected"}


@router.delete("/pending-brands/{brand_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_brand(
    brand_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a pending brand."""
    service = ScraperService(db)
    success = service.delete_pending_brand(brand_id)

    if not success:
        raise HTTPException(status_code=404, detail="Pending brand not found")


# ============================================
# PENDING CARDS ENDPOINTS
# ============================================

@router.get("/pending-cards", response_model=List[PendingCardResponse])
async def list_pending_cards(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    List pending card changes.

    Args:
        status_filter: Optional status filter (pending, approved, rejected)
    """
    query = db.query(PendingCardChange).options(
        joinedload(PendingCardChange.bank),
    )

    if status_filter:
        query = query.filter(PendingCardChange.status == status_filter)

    cards = query.order_by(PendingCardChange.created_at.desc()).all()

    return [
        PendingCardResponse(
            id=c.id,
            bank_id=c.bank_id,
            bank_name=c.bank.name if c.bank else "Unknown",
            existing_card_id=c.existing_card_id,
            name=c.name,
            card_type=c.card_type,
            card_network=c.card_network,
            annual_fee=c.annual_fee,
            reward_type=c.reward_type,
            base_reward_rate=c.base_reward_rate,
            terms_url=c.terms_url,
            change_type=c.change_type,
            old_values=c.old_values,
            source_url=c.source_url,
            source_bank=c.source_bank,
            status=c.status,
            scraped_at=c.scraped_at,
            reviewed_at=c.reviewed_at,
        )
        for c in cards
    ]


@router.post("/pending-cards", response_model=PendingCardResponse)
async def create_pending_card(
    data: PendingCardCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Manually create a pending card for approval."""
    # Verify bank exists
    bank = db.query(Bank).filter(Bank.id == data.bank_id).first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    # Check if card already exists
    existing = db.query(Card).filter(
        Card.bank_id == data.bank_id,
        Card.name == data.name,
    ).first()

    pending = PendingCardChange(
        bank_id=data.bank_id,
        existing_card_id=existing.id if existing else None,
        name=data.name,
        card_type=data.card_type,
        card_network=data.card_network,
        annual_fee=data.annual_fee,
        reward_type=data.reward_type,
        base_reward_rate=data.base_reward_rate,
        terms_url=data.terms_url,
        change_type="update" if existing else "new",
        source_url=data.source_url,
        source_bank=bank.code,
        status="pending",
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    return PendingCardResponse(
        id=pending.id,
        bank_id=pending.bank_id,
        bank_name=bank.name,
        existing_card_id=pending.existing_card_id,
        name=pending.name,
        card_type=pending.card_type,
        card_network=pending.card_network,
        annual_fee=pending.annual_fee,
        reward_type=pending.reward_type,
        base_reward_rate=pending.base_reward_rate,
        terms_url=pending.terms_url,
        change_type=pending.change_type,
        old_values=pending.old_values,
        source_url=pending.source_url,
        source_bank=pending.source_bank,
        status=pending.status,
        scraped_at=pending.scraped_at,
        reviewed_at=pending.reviewed_at,
    )


@router.put("/pending-cards/{card_id}", response_model=PendingCardResponse)
async def update_pending_card(
    card_id: UUID,
    data: PendingCardUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a pending card before approval."""
    pending = db.query(PendingCardChange).filter(
        PendingCardChange.id == card_id,
        PendingCardChange.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending card not found or already processed")

    if data.name is not None:
        pending.name = data.name
    if data.card_type is not None:
        pending.card_type = data.card_type
    if data.card_network is not None:
        pending.card_network = data.card_network
    if data.annual_fee is not None:
        pending.annual_fee = data.annual_fee
    if data.reward_type is not None:
        pending.reward_type = data.reward_type
    if data.base_reward_rate is not None:
        pending.base_reward_rate = data.base_reward_rate
    if data.terms_url is not None:
        pending.terms_url = data.terms_url

    db.commit()
    db.refresh(pending)

    bank = db.query(Bank).filter(Bank.id == pending.bank_id).first()

    return PendingCardResponse(
        id=pending.id,
        bank_id=pending.bank_id,
        bank_name=bank.name if bank else "Unknown",
        existing_card_id=pending.existing_card_id,
        name=pending.name,
        card_type=pending.card_type,
        card_network=pending.card_network,
        annual_fee=pending.annual_fee,
        reward_type=pending.reward_type,
        base_reward_rate=pending.base_reward_rate,
        terms_url=pending.terms_url,
        change_type=pending.change_type,
        old_values=pending.old_values,
        source_url=pending.source_url,
        source_bank=pending.source_bank,
        status=pending.status,
        scraped_at=pending.scraped_at,
        reviewed_at=pending.reviewed_at,
    )


@router.post("/pending-cards/{card_id}/approve")
async def approve_pending_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve a pending card and create/update it in the database."""
    from datetime import datetime

    pending = db.query(PendingCardChange).filter(
        PendingCardChange.id == card_id,
        PendingCardChange.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending card not found or already processed")

    if pending.change_type == "new":
        # Create new card
        card = Card(
            bank_id=pending.bank_id,
            name=pending.name,
            card_type=pending.card_type,
            card_network=pending.card_network,
            annual_fee=pending.annual_fee,
            reward_type=pending.reward_type,
            base_reward_rate=pending.base_reward_rate,
            terms_url=pending.terms_url,
            is_active=True,
        )
        db.add(card)
    else:
        # Update existing card
        card = db.query(Card).filter(Card.id == pending.existing_card_id).first()
        if card:
            card.name = pending.name
            card.card_type = pending.card_type
            card.card_network = pending.card_network
            card.annual_fee = pending.annual_fee
            card.reward_type = pending.reward_type
            card.base_reward_rate = pending.base_reward_rate
            card.terms_url = pending.terms_url

    # Update pending status
    pending.status = "approved"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = admin.id

    db.commit()

    return {"message": f"Card '{pending.name}' approved and {'created' if pending.change_type == 'new' else 'updated'}"}


@router.post("/pending-cards/{card_id}/reject")
async def reject_pending_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Reject a pending card."""
    from datetime import datetime

    pending = db.query(PendingCardChange).filter(
        PendingCardChange.id == card_id,
        PendingCardChange.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending card not found or already processed")

    pending.status = "rejected"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = admin.id
    db.commit()

    return {"message": "Card rejected"}


@router.delete("/pending-cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_card(
    card_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a pending card."""
    pending = db.query(PendingCardChange).filter(PendingCardChange.id == card_id).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending card not found")

    db.delete(pending)
    db.commit()


# ============================================
# CAMPAIGNS CRUD
# ============================================

@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    brand_id: Optional[UUID] = None,
    card_id: Optional[UUID] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List all campaigns with optional filters."""
    from datetime import date

    query = db.query(Campaign).options(
        joinedload(Campaign.card).joinedload(Card.bank),
        joinedload(Campaign.brand),
    )

    if brand_id:
        query = query.filter(Campaign.brand_id == brand_id)

    if card_id:
        query = query.filter(Campaign.card_id == card_id)

    if active_only:
        today = date.today()
        query = query.filter(
            Campaign.is_active == True,
            Campaign.start_date <= today,
            Campaign.end_date >= today,
        )

    campaigns = query.order_by(Campaign.end_date.desc()).all()

    result = []
    today = date.today()
    for c in campaigns:
        is_currently_active = c.is_active and c.start_date <= today <= c.end_date
        result.append(CampaignResponse(
            id=c.id,
            card_id=c.card_id,
            card_name=c.card.name if c.card else "Unknown",
            bank_name=c.card.bank.name if c.card and c.card.bank else "Unknown",
            brand_id=c.brand_id,
            brand_name=c.brand.name if c.brand else "Unknown",
            benefit_rate=c.benefit_rate,
            benefit_type=c.benefit_type,
            description=c.description,
            terms_url=c.terms_url,
            start_date=c.start_date,
            end_date=c.end_date,
            is_active=c.is_active if c.is_active is not None else True,
            is_currently_active=is_currently_active,
            created_at=c.created_at,
        ))
    return result


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Create a new campaign."""
    from datetime import date

    # Validate card exists
    card = db.query(Card).options(joinedload(Card.bank)).filter(Card.id == data.card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Validate brand exists
    brand = db.query(Brand).filter(Brand.id == data.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Validate dates
    if data.start_date > data.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    campaign = Campaign(
        card_id=data.card_id,
        brand_id=data.brand_id,
        benefit_rate=data.benefit_rate,
        benefit_type=data.benefit_type,
        description=data.description,
        terms_url=data.terms_url,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    today = date.today()
    is_currently_active = campaign.is_active and campaign.start_date <= today <= campaign.end_date

    return CampaignResponse(
        id=campaign.id,
        card_id=campaign.card_id,
        card_name=card.name,
        bank_name=card.bank.name if card.bank else "Unknown",
        brand_id=campaign.brand_id,
        brand_name=brand.name,
        benefit_rate=campaign.benefit_rate,
        benefit_type=campaign.benefit_type,
        description=campaign.description,
        terms_url=campaign.terms_url,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        is_active=campaign.is_active if campaign.is_active is not None else True,
        is_currently_active=is_currently_active,
        created_at=campaign.created_at,
    )


@router.put("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a campaign."""
    from datetime import date

    campaign = db.query(Campaign).options(
        joinedload(Campaign.card).joinedload(Card.bank),
        joinedload(Campaign.brand),
    ).filter(Campaign.id == campaign_id).first()

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if data.benefit_rate is not None:
        campaign.benefit_rate = data.benefit_rate
    if data.benefit_type is not None:
        campaign.benefit_type = data.benefit_type
    if data.description is not None:
        campaign.description = data.description
    if data.terms_url is not None:
        campaign.terms_url = data.terms_url
    if data.start_date is not None:
        campaign.start_date = data.start_date
    if data.end_date is not None:
        campaign.end_date = data.end_date
    if data.is_active is not None:
        campaign.is_active = data.is_active

    # Validate dates after updates
    if campaign.start_date > campaign.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    db.commit()
    db.refresh(campaign)

    today = date.today()
    is_currently_active = campaign.is_active and campaign.start_date <= today <= campaign.end_date

    return CampaignResponse(
        id=campaign.id,
        card_id=campaign.card_id,
        card_name=campaign.card.name if campaign.card else "Unknown",
        bank_name=campaign.card.bank.name if campaign.card and campaign.card.bank else "Unknown",
        brand_id=campaign.brand_id,
        brand_name=campaign.brand.name if campaign.brand else "Unknown",
        benefit_rate=campaign.benefit_rate,
        benefit_type=campaign.benefit_type,
        description=campaign.description,
        terms_url=campaign.terms_url,
        start_date=campaign.start_date,
        end_date=campaign.end_date,
        is_active=campaign.is_active if campaign.is_active is not None else True,
        is_currently_active=is_currently_active,
        created_at=campaign.created_at,
    )


@router.delete("/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a campaign."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    db.delete(campaign)
    db.commit()


# ============================================
# PENDING CAMPAIGNS ENDPOINTS
# ============================================

@router.get("/pending-campaigns", response_model=List[PendingCampaignResponse])
async def list_pending_campaigns(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """List pending campaign changes."""
    query = db.query(PendingCampaign).options(
        joinedload(PendingCampaign.card).joinedload(Card.bank),
        joinedload(PendingCampaign.brand),
    )

    if status_filter:
        query = query.filter(PendingCampaign.status == status_filter)

    campaigns = query.order_by(PendingCampaign.created_at.desc()).all()

    return [
        PendingCampaignResponse(
            id=c.id,
            card_id=c.card_id,
            card_name=c.card.name if c.card else "Unknown",
            brand_id=c.brand_id,
            brand_name=c.brand.name if c.brand else "Unknown",
            benefit_rate=c.benefit_rate,
            benefit_type=c.benefit_type,
            description=c.description,
            terms_url=c.terms_url,
            start_date=c.start_date,
            end_date=c.end_date,
            source_url=c.source_url,
            change_type=c.change_type,
            existing_campaign_id=c.existing_campaign_id,
            status=c.status,
            scraped_at=c.scraped_at,
            reviewed_at=c.reviewed_at,
        )
        for c in campaigns
    ]


@router.post("/pending-campaigns", response_model=PendingCampaignResponse)
async def create_pending_campaign(
    data: PendingCampaignCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Manually create a pending campaign for approval."""
    # Verify card exists
    card = db.query(Card).options(joinedload(Card.bank)).filter(Card.id == data.card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == data.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Validate dates
    if data.start_date > data.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    pending = PendingCampaign(
        card_id=data.card_id,
        brand_id=data.brand_id,
        benefit_rate=data.benefit_rate,
        benefit_type=data.benefit_type,
        description=data.description,
        terms_url=data.terms_url,
        start_date=data.start_date,
        end_date=data.end_date,
        source_url=data.source_url,
        change_type="new",
        status="pending",
    )
    db.add(pending)
    db.commit()
    db.refresh(pending)

    return PendingCampaignResponse(
        id=pending.id,
        card_id=pending.card_id,
        card_name=card.name,
        brand_id=pending.brand_id,
        brand_name=brand.name,
        benefit_rate=pending.benefit_rate,
        benefit_type=pending.benefit_type,
        description=pending.description,
        terms_url=pending.terms_url,
        start_date=pending.start_date,
        end_date=pending.end_date,
        source_url=pending.source_url,
        change_type=pending.change_type,
        existing_campaign_id=pending.existing_campaign_id,
        status=pending.status,
        scraped_at=pending.scraped_at,
        reviewed_at=pending.reviewed_at,
    )


@router.put("/pending-campaigns/{campaign_id}", response_model=PendingCampaignResponse)
async def update_pending_campaign(
    campaign_id: UUID,
    data: PendingCampaignUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Update a pending campaign before approval."""
    pending = db.query(PendingCampaign).options(
        joinedload(PendingCampaign.card),
        joinedload(PendingCampaign.brand),
    ).filter(
        PendingCampaign.id == campaign_id,
        PendingCampaign.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending campaign not found or already processed")

    if data.benefit_rate is not None:
        pending.benefit_rate = data.benefit_rate
    if data.benefit_type is not None:
        pending.benefit_type = data.benefit_type
    if data.description is not None:
        pending.description = data.description
    if data.terms_url is not None:
        pending.terms_url = data.terms_url
    if data.start_date is not None:
        pending.start_date = data.start_date
    if data.end_date is not None:
        pending.end_date = data.end_date

    # Validate dates after updates
    if pending.start_date > pending.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")

    db.commit()
    db.refresh(pending)

    return PendingCampaignResponse(
        id=pending.id,
        card_id=pending.card_id,
        card_name=pending.card.name if pending.card else "Unknown",
        brand_id=pending.brand_id,
        brand_name=pending.brand.name if pending.brand else "Unknown",
        benefit_rate=pending.benefit_rate,
        benefit_type=pending.benefit_type,
        description=pending.description,
        terms_url=pending.terms_url,
        start_date=pending.start_date,
        end_date=pending.end_date,
        source_url=pending.source_url,
        change_type=pending.change_type,
        existing_campaign_id=pending.existing_campaign_id,
        status=pending.status,
        scraped_at=pending.scraped_at,
        reviewed_at=pending.reviewed_at,
    )


@router.post("/pending-campaigns/{campaign_id}/approve")
async def approve_pending_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Approve a pending campaign and create/update it in the database."""
    from datetime import datetime

    pending = db.query(PendingCampaign).filter(
        PendingCampaign.id == campaign_id,
        PendingCampaign.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending campaign not found or already processed")

    if pending.change_type == "new":
        # Create new campaign
        campaign = Campaign(
            card_id=pending.card_id,
            brand_id=pending.brand_id,
            benefit_rate=pending.benefit_rate,
            benefit_type=pending.benefit_type,
            description=pending.description,
            terms_url=pending.terms_url,
            start_date=pending.start_date,
            end_date=pending.end_date,
            is_active=True,
        )
        db.add(campaign)
    elif pending.change_type == "update" and pending.existing_campaign_id:
        # Update existing campaign
        campaign = db.query(Campaign).filter(Campaign.id == pending.existing_campaign_id).first()
        if campaign:
            campaign.benefit_rate = pending.benefit_rate
            campaign.benefit_type = pending.benefit_type
            campaign.description = pending.description
            campaign.terms_url = pending.terms_url
            campaign.start_date = pending.start_date
            campaign.end_date = pending.end_date
    elif pending.change_type == "delete" and pending.existing_campaign_id:
        # Delete existing campaign
        campaign = db.query(Campaign).filter(Campaign.id == pending.existing_campaign_id).first()
        if campaign:
            db.delete(campaign)

    # Update pending status
    pending.status = "approved"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = admin.id

    db.commit()

    return {"message": f"Campaign {pending.change_type}d successfully"}


@router.post("/pending-campaigns/{campaign_id}/reject")
async def reject_pending_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Reject a pending campaign."""
    from datetime import datetime

    pending = db.query(PendingCampaign).filter(
        PendingCampaign.id == campaign_id,
        PendingCampaign.status == "pending",
    ).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending campaign not found or already processed")

    pending.status = "rejected"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = admin.id
    db.commit()

    return {"message": "Campaign rejected"}


@router.delete("/pending-campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pending_campaign(
    campaign_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Delete a pending campaign."""
    pending = db.query(PendingCampaign).filter(PendingCampaign.id == campaign_id).first()

    if not pending:
        raise HTTPException(status_code=404, detail="Pending campaign not found")

    db.delete(pending)
    db.commit()


# ============================================
# DUPLICATE CARDS ENDPOINTS
# ============================================

@router.get("/cards/duplicates")
async def find_duplicate_cards(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Find duplicate cards based on normalized card names.
    Returns groups of cards that appear to be duplicates.
    """
    service = ScraperService(db)
    duplicates = service.find_duplicate_cards()

    # Convert to response format
    result = []
    for key, cards in duplicates.items():
        bank_code, normalized_name = key.split(":", 1)
        result.append({
            "normalized_name": normalized_name,
            "bank_code": bank_code,
            "cards": [
                {
                    "id": str(card.id),
                    "name": card.name,
                    "bank_name": card.bank.name if card.bank else "Unknown",
                    "card_type": card.card_type,
                    "card_network": card.card_network,
                    "annual_fee": float(card.annual_fee) if card.annual_fee else None,
                    "is_active": card.is_active,
                }
                for card in cards
            ]
        })

    return {
        "duplicate_groups": result,
        "total_groups": len(result),
        "total_duplicates": sum(len(group["cards"]) for group in result)
    }


@router.post("/cards/merge")
async def merge_duplicate_cards(
    data: MergeCardsRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Merge duplicate cards into a single card.
    All references (benefits, campaigns, etc.) are moved to the kept card.
    Duplicate cards are deleted after merging.
    """
    service = ScraperService(db)
    success = service.merge_duplicate_cards(data.keep_card_id, list(data.duplicate_card_ids))

    if not success:
        raise HTTPException(status_code=400, detail="Failed to merge cards")

    return {"message": f"Successfully merged {len(data.duplicate_card_ids)} cards"}


@router.post("/cards/auto-dedupe")
async def auto_dedupe_cards(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """
    Automatically deduplicate cards by keeping the shorter-named card
    (e.g., "ICICI Coral" over "ICICI Coral Credit Card").
    """
    service = ScraperService(db)
    duplicates = service.find_duplicate_cards()

    merged_count = 0
    for key, cards in duplicates.items():
        if len(cards) < 2:
            continue

        # Sort by name length - keep the shortest name (usually the cleaner one)
        sorted_cards = sorted(cards, key=lambda c: len(c.name))
        keep_card = sorted_cards[0]
        duplicate_ids = [c.id for c in sorted_cards[1:]]

        if service.merge_duplicate_cards(keep_card.id, duplicate_ids):
            merged_count += len(duplicate_ids)

    return {
        "message": f"Auto-deduplication complete",
        "groups_processed": len(duplicates),
        "cards_merged": merged_count
    }

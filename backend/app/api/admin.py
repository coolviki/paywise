from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_admin
from ..models.user import User
from ..models.merchant import Brand, BrandKeyword
from ..models.card import Card, Bank, CardEcosystemBenefit
from ..models.pending import PendingEcosystemChange, PendingBrandChange
from ..schemas.admin import (
    BrandCreate, BrandUpdate, BrandResponse, BrandListResponse,
    KeywordCreate, KeywordResponse,
    EcosystemBenefitCreate, EcosystemBenefitUpdate, EcosystemBenefitResponse,
    CardSimple, CardCreate, CardUpdate, CardResponse, BankSimple,
    PendingChangeResponse, PendingChangeUpdate, ScraperStatusResponse,
    PendingBrandResponse, PendingBrandUpdate,
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

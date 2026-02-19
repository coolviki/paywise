from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..schemas.card import (
    BankResponse,
    CardResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    PaymentMethodUpdate,
    BankWithCardsResponse,
)
from ..services.card_service import CardService

router = APIRouter()


@router.get("/banks", response_model=List[BankResponse])
async def get_banks(
    db: Session = Depends(get_db),
):
    """Get all available banks."""
    banks = CardService.get_all_banks(db)
    return banks


@router.get("/banks/{bank_id}", response_model=BankWithCardsResponse)
async def get_bank_with_cards(
    bank_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a bank with its cards."""
    bank = CardService.get_bank_by_id(db, bank_id)
    if not bank:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bank not found",
        )

    cards = CardService.get_cards_by_bank(db, bank_id)

    return BankWithCardsResponse(
        id=bank.id,
        name=bank.name,
        code=bank.code,
        logo_url=bank.logo_url,
        cards=[CardResponse.model_validate(c) for c in cards],
    )


@router.get("/cards/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a specific card."""
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )
    return card


@router.get("/cards/search/{query}", response_model=List[CardResponse])
async def search_cards(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search cards by name."""
    cards = CardService.search_cards(db, query, limit)
    return cards


@router.get("/payment-methods", response_model=List[PaymentMethodResponse])
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user's payment methods."""
    methods = CardService.get_user_payment_methods(db, current_user.id)
    return methods


@router.post("/payment-methods", response_model=PaymentMethodResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    data: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new payment method."""
    # Verify card exists
    card = CardService.get_card_by_id(db, data.card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found",
        )

    method = CardService.create_payment_method(db, current_user.id, data)
    return method


@router.put("/payment-methods/{payment_method_id}", response_model=PaymentMethodResponse)
async def update_payment_method(
    payment_method_id: UUID,
    data: PaymentMethodUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a payment method."""
    method = CardService.update_payment_method(
        db, payment_method_id, current_user.id, data
    )
    if not method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )
    return method


@router.delete("/payment-methods/{payment_method_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_method(
    payment_method_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a payment method."""
    success = CardService.delete_payment_method(db, payment_method_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment method not found",
        )
    return None

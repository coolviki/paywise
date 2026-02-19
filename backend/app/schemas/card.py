from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class BankResponse(BaseModel):
    id: UUID
    name: str
    code: str
    logo_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class CardResponse(BaseModel):
    id: UUID
    bank_id: UUID
    name: str
    card_type: str
    card_network: Optional[str] = None
    annual_fee: Optional[Decimal] = None
    reward_type: Optional[str] = None
    base_reward_rate: Optional[Decimal] = None
    is_active: bool
    bank: Optional[BankResponse] = None

    class Config:
        from_attributes = True


class PaymentMethodCreate(BaseModel):
    bank_id: UUID
    card_id: UUID
    payment_type: str
    last_four_digits: Optional[str] = None
    nickname: Optional[str] = None


class PaymentMethodUpdate(BaseModel):
    nickname: Optional[str] = None
    last_four_digits: Optional[str] = None
    is_active: Optional[bool] = None


class PaymentMethodResponse(BaseModel):
    id: UUID
    user_id: UUID
    bank_id: Optional[UUID] = None
    card_id: Optional[UUID] = None
    payment_type: str
    last_four_digits: Optional[str] = None
    nickname: Optional[str] = None
    is_active: bool
    created_at: datetime
    bank: Optional[BankResponse] = None
    card: Optional[CardResponse] = None

    class Config:
        from_attributes = True


class BankWithCardsResponse(BaseModel):
    id: UUID
    name: str
    code: str
    logo_url: Optional[str] = None
    cards: List[CardResponse] = []

    class Config:
        from_attributes = True

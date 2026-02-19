from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from ..models.card import Bank, Card, PaymentMethod
from ..schemas.card import PaymentMethodCreate, PaymentMethodUpdate


class CardService:
    @staticmethod
    def get_all_banks(db: Session, active_only: bool = True) -> List[Bank]:
        """Get all banks."""
        query = db.query(Bank)
        if active_only:
            query = query.filter(Bank.is_active == True)
        return query.order_by(Bank.name).all()

    @staticmethod
    def get_bank_by_id(db: Session, bank_id: UUID) -> Optional[Bank]:
        """Get bank by ID."""
        return db.query(Bank).filter(Bank.id == bank_id).first()

    @staticmethod
    def get_bank_by_code(db: Session, code: str) -> Optional[Bank]:
        """Get bank by code."""
        return db.query(Bank).filter(Bank.code == code).first()

    @staticmethod
    def get_cards_by_bank(db: Session, bank_id: UUID, active_only: bool = True) -> List[Card]:
        """Get all cards for a bank."""
        query = db.query(Card).filter(Card.bank_id == bank_id)
        if active_only:
            query = query.filter(Card.is_active == True)
        return query.order_by(Card.name).all()

    @staticmethod
    def get_card_by_id(db: Session, card_id: UUID) -> Optional[Card]:
        """Get card by ID with bank relationship."""
        return (
            db.query(Card)
            .options(joinedload(Card.bank))
            .filter(Card.id == card_id)
            .first()
        )

    @staticmethod
    def search_cards(db: Session, query: str, limit: int = 20) -> List[Card]:
        """Search cards by name."""
        return (
            db.query(Card)
            .options(joinedload(Card.bank))
            .filter(Card.name.ilike(f"%{query}%"))
            .filter(Card.is_active == True)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_user_payment_methods(
        db: Session, user_id: UUID, active_only: bool = True
    ) -> List[PaymentMethod]:
        """Get all payment methods for a user."""
        query = (
            db.query(PaymentMethod)
            .options(joinedload(PaymentMethod.bank), joinedload(PaymentMethod.card))
            .filter(PaymentMethod.user_id == user_id)
        )
        if active_only:
            query = query.filter(PaymentMethod.is_active == True)
        return query.order_by(PaymentMethod.created_at.desc()).all()

    @staticmethod
    def get_payment_method_by_id(
        db: Session, payment_method_id: UUID, user_id: UUID
    ) -> Optional[PaymentMethod]:
        """Get payment method by ID for a specific user."""
        return (
            db.query(PaymentMethod)
            .options(joinedload(PaymentMethod.bank), joinedload(PaymentMethod.card))
            .filter(
                PaymentMethod.id == payment_method_id,
                PaymentMethod.user_id == user_id,
            )
            .first()
        )

    @staticmethod
    def create_payment_method(
        db: Session, user_id: UUID, data: PaymentMethodCreate
    ) -> PaymentMethod:
        """Create a new payment method for a user."""
        payment_method = PaymentMethod(
            user_id=user_id,
            bank_id=data.bank_id,
            card_id=data.card_id,
            payment_type=data.payment_type,
            last_four_digits=data.last_four_digits,
            nickname=data.nickname,
        )
        db.add(payment_method)
        db.commit()
        db.refresh(payment_method)
        return CardService.get_payment_method_by_id(db, payment_method.id, user_id)

    @staticmethod
    def update_payment_method(
        db: Session,
        payment_method_id: UUID,
        user_id: UUID,
        data: PaymentMethodUpdate,
    ) -> Optional[PaymentMethod]:
        """Update a payment method."""
        payment_method = CardService.get_payment_method_by_id(
            db, payment_method_id, user_id
        )
        if not payment_method:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(payment_method, key, value)

        db.commit()
        db.refresh(payment_method)
        return payment_method

    @staticmethod
    def delete_payment_method(
        db: Session, payment_method_id: UUID, user_id: UUID
    ) -> bool:
        """Delete a payment method."""
        payment_method = CardService.get_payment_method_by_id(
            db, payment_method_id, user_id
        )
        if not payment_method:
            return False

        db.delete(payment_method)
        db.commit()
        return True

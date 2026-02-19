import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import {
  fetchBanks,
  fetchPaymentMethods,
  addPaymentMethod,
  deletePaymentMethod,
  clearCardsError,
} from '../store/cardsSlice';
import api from '../services/api';
import { Card } from '../types';

interface BankWithCards {
  id: string;
  name: string;
  code: string;
  logo_url?: string;
  cards: Card[];
}

export function useCards() {
  const dispatch = useDispatch<AppDispatch>();
  const { banks, paymentMethods, isLoading, error } = useSelector(
    (state: RootState) => state.cards
  );

  useEffect(() => {
    dispatch(fetchBanks());
    dispatch(fetchPaymentMethods());
  }, [dispatch]);

  const addCard = async (data: {
    bank_id: string;
    card_id: string;
    payment_type: string;
    last_four_digits?: string;
    nickname?: string;
  }) => {
    return dispatch(addPaymentMethod(data)).unwrap();
  };

  const removeCard = async (id: string) => {
    return dispatch(deletePaymentMethod(id)).unwrap();
  };

  const clearError = () => {
    dispatch(clearCardsError());
  };

  return {
    banks,
    paymentMethods,
    isLoading,
    error,
    addCard,
    removeCard,
    clearError,
  };
}

export function useBankCards(bankId: string | null) {
  const [cards, setCards] = useState<Card[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!bankId) {
      setCards([]);
      return;
    }

    const fetchCards = async () => {
      setIsLoading(true);
      try {
        const response = await api.get<BankWithCards>(`/cards/banks/${bankId}`);
        // Ensure cards is always an array
        const cardsList = Array.isArray(response.data?.cards) ? response.data.cards : [];
        setCards(cardsList);
      } catch (err) {
        console.error('Error fetching cards:', err);
        setCards([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCards();
  }, [bankId]);

  return { cards, isLoading };
}

import React, { useState } from 'react';
import { X, ArrowLeft, CreditCard, Check } from 'lucide-react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { BankSelector } from './BankSelector';
import { Bank, Card as CardType } from '../../types';
import { useBankCards } from '../../hooks/useCards';
import { Loading } from '../common/Loading';

interface AddCardModalProps {
  isOpen: boolean;
  onClose: () => void;
  banks: Bank[];
  onAdd: (data: {
    bank_id: string;
    card_id: string;
    payment_type: string;
    last_four_digits?: string;
    nickname?: string;
  }) => Promise<void>;
}

type Step = 'bank' | 'card' | 'details';

export function AddCardModal({ isOpen, onClose, banks, onAdd }: AddCardModalProps) {
  const [step, setStep] = useState<Step>('bank');
  const [selectedBank, setSelectedBank] = useState<Bank | null>(null);
  const [selectedCard, setSelectedCard] = useState<CardType | null>(null);
  const [lastFour, setLastFour] = useState('');
  const [nickname, setNickname] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { cards, isLoading: cardsLoading } = useBankCards(selectedBank?.id || null);

  if (!isOpen) return null;

  const handleBankSelect = (bank: Bank) => {
    setSelectedBank(bank);
    setStep('card');
  };

  const handleCardSelect = (card: CardType) => {
    setSelectedCard(card);
    setStep('details');
  };

  const handleSubmit = async () => {
    if (!selectedBank || !selectedCard) return;

    setIsSubmitting(true);
    try {
      await onAdd({
        bank_id: selectedBank.id,
        card_id: selectedCard.id,
        payment_type: selectedCard.card_type === 'credit' ? 'credit_card' : 'debit_card',
        last_four_digits: lastFour || undefined,
        nickname: nickname || undefined,
      });
      handleClose();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setStep('bank');
    setSelectedBank(null);
    setSelectedCard(null);
    setLastFour('');
    setNickname('');
    onClose();
  };

  const handleBack = () => {
    if (step === 'card') {
      setSelectedBank(null);
      setStep('bank');
    } else if (step === 'details') {
      setSelectedCard(null);
      setStep('card');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      <div className="absolute inset-0 bg-black/50" onClick={handleClose} />
      <div className="relative bg-white dark:bg-gray-900 w-full max-w-lg max-h-[90vh] rounded-t-2xl sm:rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            {step !== 'bank' && (
              <button onClick={handleBack} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}
            <h2 className="text-lg font-semibold">
              {step === 'bank' && 'Select Bank'}
              {step === 'card' && selectedBank?.name}
              {step === 'details' && 'Card Details'}
            </h2>
          </div>
          <button onClick={handleClose} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[70vh]">
          {step === 'bank' && (
            <BankSelector banks={banks} onSelect={handleBankSelect} />
          )}

          {step === 'card' && (
            <div className="space-y-3">
              {cardsLoading ? (
                <Loading text="Loading cards..." />
              ) : (
                (Array.isArray(cards) ? cards : []).map((card) => (
                  <button
                    key={card.id}
                    onClick={() => handleCardSelect(card)}
                    className="w-full flex items-center gap-3 p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors text-left"
                  >
                    <CreditCard className="w-6 h-6 text-primary-500" />
                    <div>
                      <p className="font-medium">{card.name}</p>
                      <p className="text-sm text-gray-500">
                        {card.card_type === 'credit' ? 'Credit Card' : 'Debit Card'}
                        {card.reward_type && ` - ${card.reward_type}`}
                      </p>
                    </div>
                  </button>
                ))
              )}
              {!cardsLoading && (!Array.isArray(cards) || cards.length === 0) && (
                <p className="text-center text-gray-500 py-8">No cards available</p>
              )}
            </div>
          )}

          {step === 'details' && selectedCard && (
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-3">
                  <CreditCard className="w-8 h-8 text-primary-500" />
                  <div>
                    <p className="font-medium">{selectedCard.name}</p>
                    <p className="text-sm text-gray-500">{selectedBank?.name}</p>
                  </div>
                </div>
              </div>

              <Input
                label="Last 4 digits (optional)"
                placeholder="1234"
                value={lastFour}
                onChange={(e) => setLastFour(e.target.value.replace(/\D/g, '').slice(0, 4))}
                maxLength={4}
              />

              <Input
                label="Nickname (optional)"
                placeholder="e.g., Personal Card"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
              />

              <Button
                className="w-full"
                onClick={handleSubmit}
                isLoading={isSubmitting}
                leftIcon={<Check className="w-5 h-5" />}
              >
                Add Card
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

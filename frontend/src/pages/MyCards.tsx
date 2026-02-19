import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, CreditCard, Smartphone, Wallet } from 'lucide-react';
import { Button } from '../components/common/Button';
import { CardList } from '../components/cards/CardList';
import { AddCardModal } from '../components/cards/AddCardModal';
import { useCards } from '../hooks/useCards';

export function MyCards() {
  const navigate = useNavigate();
  const [showAddCard, setShowAddCard] = useState(false);
  const { banks, paymentMethods, isLoading, addCard, removeCard } = useCards();

  const creditCards = paymentMethods.filter((pm) => pm.payment_type === 'credit_card');
  const debitCards = paymentMethods.filter((pm) => pm.payment_type === 'debit_card');

  const handleAddCard = async (data: {
    bank_id: string;
    card_id: string;
    payment_type: string;
    last_four_digits?: string;
    nickname?: string;
  }) => {
    await addCard(data);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to remove this card?')) {
      await removeCard(id);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            My Payment Methods
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Credit Cards */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              Credit Cards ({creditCards.length})
            </h2>
          </div>
          <CardList
            paymentMethods={creditCards}
            onDelete={handleDelete}
          />
          <button
            onClick={() => setShowAddCard(true)}
            className="w-full mt-3 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-gray-500 dark:text-gray-400 font-medium hover:border-primary-500 hover:text-primary-500 transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add New Card
          </button>
        </section>

        {/* Debit Cards */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <CreditCard className="w-4 h-4" />
              Debit Cards ({debitCards.length})
            </h2>
          </div>
          <CardList
            paymentMethods={debitCards}
            onDelete={handleDelete}
          />
          <button
            onClick={() => setShowAddCard(true)}
            className="w-full mt-3 py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl text-gray-500 dark:text-gray-400 font-medium hover:border-primary-500 hover:text-primary-500 transition-colors flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            Add New Debit Card
          </button>
        </section>

        {/* Coming Soon sections */}
        <section className="opacity-60">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2 mb-3">
            <Smartphone className="w-4 h-4" />
            UPI (Coming Soon)
          </h2>
        </section>

        <section className="opacity-60">
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2 mb-3">
            <Wallet className="w-4 h-4" />
            Wallets (Coming Soon)
          </h2>
        </section>
      </div>

      {/* Add Card Modal */}
      <AddCardModal
        isOpen={showAddCard}
        onClose={() => setShowAddCard(false)}
        banks={banks}
        onAdd={handleAddCard}
      />
    </div>
  );
}

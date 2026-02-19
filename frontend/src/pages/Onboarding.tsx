import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, CreditCard, Smartphone, Wallet, ChevronRight } from 'lucide-react';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { AddCardModal } from '../components/cards/AddCardModal';
import { useCards } from '../hooks/useCards';

export function Onboarding() {
  const navigate = useNavigate();
  const [showAddCard, setShowAddCard] = useState(false);
  const { banks, paymentMethods, addCard } = useCards();

  const handleSkip = () => {
    navigate('/');
  };

  const handleContinue = () => {
    navigate('/');
  };

  const handleAddCard = async (data: {
    bank_id: string;
    card_id: string;
    payment_type: string;
    last_four_digits?: string;
    nickname?: string;
  }) => {
    await addCard(data);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-100 dark:border-gray-800">
        <button onClick={() => navigate(-1)} className="p-2">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <button onClick={handleSkip} className="text-primary-500 font-medium">
          Skip
        </button>
      </div>

      {/* Content */}
      <div className="p-6 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Add Your Payment Methods
          </h1>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            We'll find the best rewards for you
          </p>
        </div>

        {/* Payment method options */}
        <div className="space-y-3">
          <Card
            hoverable
            onClick={() => setShowAddCard(true)}
            className="p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900 rounded-xl flex items-center justify-center">
                  <CreditCard className="w-6 h-6 text-primary-500" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Credit/Debit Cards
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {paymentMethods.length > 0
                      ? `${paymentMethods.length} card(s) added`
                      : 'Add your cards'}
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </div>
          </Card>

          <Card className="p-4 opacity-60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                  <Smartphone className="w-6 h-6 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    UPI (Coming Soon)
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Google Pay, PhonePe
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </div>
          </Card>

          <Card className="p-4 opacity-60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-gray-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    Wallets (Coming Soon)
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Paytm, Amazon Pay
                  </p>
                </div>
              </div>
              <ChevronRight className="w-5 h-5 text-gray-400" />
            </div>
          </Card>
        </div>

        {/* Continue button */}
        <div className="pt-4">
          <Button className="w-full" size="lg" onClick={handleContinue}>
            Continue
          </Button>
        </div>
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

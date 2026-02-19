import React from 'react';
import { CreditCard, Edit2, Trash2 } from 'lucide-react';
import { Card, CardContent } from '../common/Card';
import { PaymentMethod } from '../../types';

interface CardListProps {
  paymentMethods: PaymentMethod[];
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

export function CardList({ paymentMethods, onEdit, onDelete }: CardListProps) {
  if (paymentMethods.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <CreditCard className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No payment methods added yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {paymentMethods.map((pm) => (
        <PaymentMethodCard
          key={pm.id}
          paymentMethod={pm}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

interface PaymentMethodCardProps {
  paymentMethod: PaymentMethod;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
}

function PaymentMethodCard({ paymentMethod, onEdit, onDelete }: PaymentMethodCardProps) {
  const cardName = paymentMethod.card?.name || 'Unknown Card';
  const bankName = paymentMethod.bank?.name || paymentMethod.card?.bank?.name || '';
  const lastFour = paymentMethod.last_four_digits;

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-lg flex items-center justify-center">
            <CreditCard className="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">
              {paymentMethod.nickname || cardName}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {bankName}
              {lastFour && ` \u2022\u2022\u2022\u2022 ${lastFour}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onEdit && (
            <button
              onClick={() => onEdit(paymentMethod.id)}
              className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <Edit2 className="w-4 h-4" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(paymentMethod.id)}
              className="p-2 text-gray-400 hover:text-red-500"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </Card>
  );
}

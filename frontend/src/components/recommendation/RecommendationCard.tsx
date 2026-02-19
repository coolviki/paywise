import React from 'react';
import { CreditCard, Check, Calendar, Receipt } from 'lucide-react';
import { Card, CardContent } from '../common/Card';
import { CardRecommendation } from '../../types';

interface RecommendationCardProps {
  recommendation: CardRecommendation;
  isBest?: boolean;
}

export function RecommendationCard({ recommendation, isBest = false }: RecommendationCardProps) {
  return (
    <Card
      className={`overflow-hidden ${
        isBest ? 'ring-2 ring-primary-500 border-primary-500' : ''
      }`}
    >
      {isBest && (
        <div className="bg-primary-500 text-white px-4 py-2 text-sm font-medium flex items-center gap-2">
          <span>Best Payment Option</span>
        </div>
      )}
      <CardContent className={isBest ? 'pt-4' : ''}>
        <div className="flex items-start gap-4">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isBest
                ? 'bg-primary-100 dark:bg-primary-900'
                : 'bg-gray-100 dark:bg-gray-700'
            }`}
          >
            <CreditCard
              className={`w-6 h-6 ${
                isBest ? 'text-primary-500' : 'text-gray-500'
              }`}
            />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg text-gray-900 dark:text-white">
              {recommendation.card_name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {recommendation.bank_name}
            </p>

            <div className="mt-3 space-y-2">
              <div className="flex items-center gap-2 text-accent-600 dark:text-accent-400">
                <span className="font-bold text-xl">{recommendation.estimated_savings}</span>
                <span className="text-sm">savings</span>
              </div>

              <p className="text-sm text-gray-600 dark:text-gray-300">
                {recommendation.reason}
              </p>

              {recommendation.offer && (
                <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-2">
                  <div className="flex items-center gap-2 text-sm">
                    <Check className="w-4 h-4 text-accent-500" />
                    <span>{recommendation.offer.title}</span>
                  </div>
                  {recommendation.offer.min_transaction && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Receipt className="w-4 h-4" />
                      <span>Min transaction: Rs.{recommendation.offer.min_transaction}</span>
                    </div>
                  )}
                  {recommendation.offer.valid_until && (
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Calendar className="w-4 h-4" />
                      <span>Valid till {recommendation.offer.valid_until}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

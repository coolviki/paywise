import React, { useEffect } from 'react';
import { useRestaurantOffersWithFetch } from '../../hooks/useRestaurantOffers';
import { RestaurantOffer } from '../../types';

interface RestaurantOffersProps {
  restaurantName: string;
  city: string;
  /** Auto-fetch on mount */
  autoFetch?: boolean;
  /** Platforms to search (default: all) */
  platforms?: string[];
}

/**
 * Displays real-time restaurant offers from Swiggy Dineout, Zomato, EazyDiner, etc.
 * Shows offers as they stream in from the LLM search.
 */
export function RestaurantOffers({
  restaurantName,
  city,
  autoFetch = true,
  platforms,
}: RestaurantOffersProps) {
  const {
    offers,
    isLoading,
    isStreaming,
    summary,
    error,
    streamOffers,
    clearOffers,
  } = useRestaurantOffersWithFetch();

  useEffect(() => {
    if (autoFetch && restaurantName && city) {
      streamOffers(restaurantName, city, platforms);
    }

    return () => {
      clearOffers();
    };
  }, [restaurantName, city, autoFetch, platforms, streamOffers, clearOffers]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">
          Dine-in Offers
        </h3>
        {isStreaming && (
          <span className="flex items-center text-xs text-blue-600">
            <span className="animate-pulse mr-1">●</span>
            Finding offers...
          </span>
        )}
      </div>

      {/* Loading state */}
      {isLoading && offers.length === 0 && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
          <span className="ml-2 text-sm text-gray-500">Searching platforms...</span>
        </div>
      )}

      {/* Offers list */}
      {offers.length > 0 && (
        <div className="space-y-2">
          {offers.map((offer, index) => (
            <OfferCard key={index} offer={offer} isNew={isStreaming && index === offers.length - 1} />
          ))}
        </div>
      )}

      {/* No offers found */}
      {!isLoading && !isStreaming && offers.length === 0 && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No dine-in offers found for this restaurant.
        </div>
      )}

      {/* Summary */}
      {summary && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800">
          <span className="font-medium">Tip: </span>
          {summary}
        </div>
      )}
    </div>
  );
}

interface OfferCardProps {
  offer: RestaurantOffer;
  isNew?: boolean;
}

function OfferCard({ offer, isNew }: OfferCardProps) {
  const platformColors: Record<string, string> = {
    swiggy_dineout: 'bg-orange-100 text-orange-800 border-orange-200',
    zomato: 'bg-red-100 text-red-800 border-red-200',
    eazydiner: 'bg-purple-100 text-purple-800 border-purple-200',
    dineout: 'bg-pink-100 text-pink-800 border-pink-200',
    magicpin: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    unknown: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const offerTypeLabels: Record<string, string> = {
    'pre-booked': 'Pre-book',
    'walk-in': 'Walk-in',
    'bank_offer': 'Bank Offer',
    coupon: 'Coupon',
    general: 'Offer',
  };

  return (
    <div
      className={`border rounded-lg p-3 transition-all duration-300 ${
        isNew ? 'ring-2 ring-blue-400 ring-opacity-50' : ''
      } ${platformColors[offer.platform] || platformColors.unknown}`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {/* Platform & Type badges */}
          <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-white bg-opacity-50">
              {offer.platform_display_name}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-white bg-opacity-30">
              {offerTypeLabels[offer.offer_type] || offer.offer_type}
            </span>
            {offer.bank_name && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                {offer.bank_name}
              </span>
            )}
          </div>

          {/* Discount text */}
          <p className="text-sm font-medium">
            {offer.discount_text}
          </p>

          {/* Conditions */}
          {offer.conditions && (
            <p className="text-xs opacity-75 mt-1">
              {offer.conditions}
            </p>
          )}

          {/* Coupon code */}
          {offer.coupon_code && (
            <div className="mt-1.5">
              <span className="inline-flex items-center px-2 py-1 bg-white bg-opacity-50 rounded font-mono text-xs">
                Code: {offer.coupon_code}
              </span>
            </div>
          )}
        </div>

        {/* Discount percentage badge */}
        {offer.discount_percentage && (
          <div className="flex-shrink-0 text-right">
            <span className="text-lg font-bold">
              {offer.discount_percentage}%
            </span>
            <span className="block text-xs opacity-75">off</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default RestaurantOffers;

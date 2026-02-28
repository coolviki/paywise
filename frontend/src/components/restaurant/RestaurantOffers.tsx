import React, { useEffect, useState } from 'react';
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
  const [useParallelCalls, setUseParallelCalls] = useState(true);

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
      streamOffers(restaurantName, city, platforms, useParallelCalls);
    }

    return () => {
      clearOffers();
    };
  }, [restaurantName, city, autoFetch, platforms, useParallelCalls, streamOffers, clearOffers]);

  const handleModeChange = (parallel: boolean) => {
    setUseParallelCalls(parallel);
    // Re-fetch with new mode
    if (restaurantName && city) {
      clearOffers();
      streamOffers(restaurantName, city, platforms, parallel);
    }
  };

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
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Dine-in Offers
        </h3>
        {isStreaming && (
          <span className="flex items-center text-xs text-blue-600">
            <span className="animate-pulse mr-1">●</span>
            Finding offers...
          </span>
        )}
      </div>

      {/* Search Mode Toggle */}
      <div className="flex items-center gap-4 text-xs">
        <span className="text-gray-500 dark:text-gray-400">Search mode:</span>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="radio"
            name="searchMode"
            checked={useParallelCalls}
            onChange={() => handleModeChange(true)}
            disabled={isLoading || isStreaming}
            className="w-3 h-3 text-blue-600"
          />
          <span className={`${useParallelCalls ? 'text-blue-600 font-medium' : 'text-gray-600 dark:text-gray-400'}`}>
            Thorough (per platform)
          </span>
        </label>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input
            type="radio"
            name="searchMode"
            checked={!useParallelCalls}
            onChange={() => handleModeChange(false)}
            disabled={isLoading || isStreaming}
            className="w-3 h-3 text-blue-600"
          />
          <span className={`${!useParallelCalls ? 'text-blue-600 font-medium' : 'text-gray-600 dark:text-gray-400'}`}>
            Quick (single search)
          </span>
        </label>
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
  /**
   * Try to open the native app first, fall back to website.
   * Uses app_link for mobile devices, platform_url for web.
   */
  const handleOpenPlatform = (offer: RestaurantOffer) => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (isMobile && offer.app_link) {
      // On mobile, try to open the app
      // Create a hidden iframe to try the app link
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      document.body.appendChild(iframe);

      // Set a timeout to open web URL if app doesn't open
      const timeout = setTimeout(() => {
        if (offer.platform_url) {
          window.open(offer.platform_url, '_blank');
        }
        document.body.removeChild(iframe);
      }, 1500);

      // Try to open app
      try {
        iframe.contentWindow?.location.replace(offer.app_link);
        // If we're still here after a short delay, the app might have opened
        setTimeout(() => {
          clearTimeout(timeout);
          document.body.removeChild(iframe);
        }, 100);
      } catch {
        // App link failed, open web
        clearTimeout(timeout);
        if (offer.platform_url) {
          window.open(offer.platform_url, '_blank');
        }
        document.body.removeChild(iframe);
      }
    } else if (offer.platform_url) {
      // On desktop or if no app link, open website
      window.open(offer.platform_url, '_blank');
    }
  };

  const platformColors: Record<string, string> = {
    swiggy_dineout: 'bg-orange-100 text-orange-800 border-orange-200',
    zomato_pay: 'bg-red-100 text-red-800 border-red-200',
    eazydiner: 'bg-purple-100 text-purple-800 border-purple-200',
    district: 'bg-blue-100 text-blue-800 border-blue-200',
    unknown: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const platformLogos: Record<string, string> = {
    swiggy_dineout: '🍽️',
    zomato_pay: '🔴',
    eazydiner: '🍴',
    district: '📍',
    unknown: '🏪',
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

          {/* Platform link - tries app first, falls back to web */}
          {(offer.app_link || offer.platform_url) && (
            <button
              onClick={() => handleOpenPlatform(offer)}
              className="inline-flex items-center gap-1 mt-2 text-xs font-medium underline opacity-75 hover:opacity-100"
            >
              Open in {offer.platform_display_name} →
            </button>
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

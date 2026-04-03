import React, { useEffect, useState, useMemo } from 'react';
import { useRestaurantOffersWithFetch } from '../../hooks/useRestaurantOffers';
import { RestaurantOffer, RestaurantOfferPlatform } from '../../types';

interface GroupedPlatformOffers {
  platform: RestaurantOfferPlatform;
  platform_display_name: string;
  restaurantOffers: RestaurantOffer[];
  bankOffers: RestaurantOffer[];
  combinedMaxSavings: number | null;
  combinedPercentage: number | null;
  platformUrl?: string;
  appLink?: string;
}

function groupOffersByPlatform(offers: RestaurantOffer[]): GroupedPlatformOffers[] {
  const grouped = new Map<RestaurantOfferPlatform, GroupedPlatformOffers>();

  for (const offer of offers) {
    if (!grouped.has(offer.platform)) {
      grouped.set(offer.platform, {
        platform: offer.platform,
        platform_display_name: offer.platform_display_name,
        restaurantOffers: [],
        bankOffers: [],
        combinedMaxSavings: null,
        combinedPercentage: null,
        platformUrl: offer.platform_url,
        appLink: offer.app_link,
      });
    }

    const group = grouped.get(offer.platform)!;
    if (offer.offer_type === 'bank_offer' || offer.bank_name) {
      group.bankOffers.push(offer);
    } else {
      group.restaurantOffers.push(offer);
    }
  }

  // Calculate combined savings for each platform
  for (const group of grouped.values()) {
    const restaurantMax = Math.max(
      ...group.restaurantOffers.map((o) => o.max_discount || 0),
      0
    );
    const bankMax = Math.max(
      ...group.bankOffers.map((o) => o.max_discount || 0),
      0
    );
    group.combinedMaxSavings = restaurantMax + bankMax > 0 ? restaurantMax + bankMax : null;

    const restaurantPct = Math.max(
      ...group.restaurantOffers.map((o) => o.discount_percentage || 0),
      0
    );
    const bankPct = Math.max(
      ...group.bankOffers.map((o) => o.discount_percentage || 0),
      0
    );
    group.combinedPercentage = restaurantPct + bankPct > 0 ? restaurantPct + bankPct : null;
  }

  return Array.from(grouped.values());
}

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

      {/* Search Mode Toggle - Hidden, defaulting to Thorough (parallel) mode */}
      {/* Uncomment to re-enable:
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
      */}

      {/* Loading state with animated illustration */}
      {(isLoading || isStreaming) && offers.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8">
          {/* Animated food/dining illustration */}
          <div className="relative w-24 h-24 mb-4">
            {/* Plate */}
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-20 h-3 bg-gray-200 dark:bg-gray-600 rounded-full"></div>
            {/* Bowl */}
            <div className="absolute bottom-2 left-1/2 -translate-x-1/2 w-16 h-10 bg-gradient-to-b from-orange-100 to-orange-200 dark:from-orange-900 dark:to-orange-800 rounded-b-full border-2 border-orange-300 dark:border-orange-700"></div>
            {/* Steam lines - animated */}
            <div className="absolute bottom-12 left-1/2 -translate-x-1/2 flex gap-2">
              <div className="w-1 h-4 bg-gray-300 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms', animationDuration: '1s' }}></div>
              <div className="w-1 h-6 bg-gray-300 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms', animationDuration: '1s' }}></div>
              <div className="w-1 h-4 bg-gray-300 dark:bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms', animationDuration: '1s' }}></div>
            </div>
            {/* Searching indicator */}
            <div className="absolute -right-2 -top-2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center animate-pulse">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          {/* Loading text */}
          <div className="text-center">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Finding the best deals</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Searching Swiggy Dineout, EazyDiner, District...
            </p>
          </div>
          {/* Animated dots */}
          <div className="flex gap-1 mt-3">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
      )}

      {/* Offers list - Grouped by platform with combined view */}
      {offers.length > 0 && (
        <GroupedOffersView offers={offers} isStreaming={isStreaming} />
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

interface GroupedOffersViewProps {
  offers: RestaurantOffer[];
  isStreaming: boolean;
}

function GroupedOffersView({ offers, isStreaming }: GroupedOffersViewProps) {
  const groupedOffers = useMemo(() => groupOffersByPlatform(offers), [offers]);

  return (
    <div className="space-y-4">
      {groupedOffers.map((group) => (
        <CombinedOfferCard key={group.platform} group={group} isStreaming={isStreaming} />
      ))}
    </div>
  );
}

interface CombinedOfferCardProps {
  group: GroupedPlatformOffers;
  isStreaming: boolean;
}

function CombinedOfferCard({ group, isStreaming }: CombinedOfferCardProps) {
  const platformColors: Record<string, { bg: string; border: string; header: string }> = {
    swiggy_dineout: {
      bg: 'bg-orange-50',
      border: 'border-orange-200',
      header: 'bg-orange-500 text-white',
    },
    eazydiner: {
      bg: 'bg-purple-50',
      border: 'border-purple-200',
      header: 'bg-purple-500 text-white',
    },
    district: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      header: 'bg-blue-500 text-white',
    },
    unknown: {
      bg: 'bg-gray-50',
      border: 'border-gray-200',
      header: 'bg-gray-500 text-white',
    },
  };

  const colors = platformColors[group.platform] || platformColors.unknown;
  const hasRestaurantOffers = group.restaurantOffers.length > 0;
  const hasBankOffers = group.bankOffers.length > 0;
  const canStack = hasRestaurantOffers && hasBankOffers;

  const handleOpenPlatform = () => {
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (isMobile && group.appLink) {
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      document.body.appendChild(iframe);

      const timeout = setTimeout(() => {
        if (group.platformUrl) {
          window.open(group.platformUrl, '_blank');
        }
        document.body.removeChild(iframe);
      }, 1500);

      try {
        iframe.contentWindow?.location.replace(group.appLink);
        setTimeout(() => {
          clearTimeout(timeout);
          document.body.removeChild(iframe);
        }, 100);
      } catch {
        clearTimeout(timeout);
        if (group.platformUrl) {
          window.open(group.platformUrl, '_blank');
        }
        document.body.removeChild(iframe);
      }
    } else if (group.platformUrl) {
      window.open(group.platformUrl, '_blank');
    }
  };

  return (
    <div className={`rounded-lg border-2 ${colors.border} overflow-hidden`}>
      {/* Platform Header */}
      <div className={`px-4 py-2 ${colors.header} flex items-center justify-between`}>
        <span className="font-semibold">{group.platform_display_name}</span>
        {isStreaming && (
          <span className="text-xs opacity-75 animate-pulse">Finding more...</span>
        )}
      </div>

      <div className={`${colors.bg} p-4 space-y-3`}>
        {/* Restaurant Offers Section */}
        {hasRestaurantOffers && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Restaurant Offer
            </div>
            {group.restaurantOffers.map((offer, idx) => (
              <StackableOfferItem key={`rest-${idx}`} offer={offer} type="restaurant" />
            ))}
          </div>
        )}

        {/* Plus sign between stackable offers */}
        {canStack && (
          <div className="flex items-center justify-center">
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-500 text-white font-bold text-lg shadow-sm">
              +
            </div>
          </div>
        )}

        {/* Bank Offers Section */}
        {hasBankOffers && (
          <div className="space-y-2">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Bank / Payment Offer
            </div>
            {group.bankOffers.map((offer, idx) => (
              <StackableOfferItem key={`bank-${idx}`} offer={offer} type="bank" />
            ))}
          </div>
        )}

        {/* Combined Savings */}
        {canStack && (group.combinedMaxSavings || group.combinedPercentage) && (
          <div className="border-t-2 border-dashed border-gray-300 pt-3 mt-3">
            <div className="bg-green-100 border border-green-300 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-green-700 uppercase tracking-wide">
                    Combined Savings
                  </div>
                  <div className="text-sm text-green-800 mt-0.5">
                    Stack both offers for maximum discount
                  </div>
                </div>
                <div className="text-right">
                  {group.combinedPercentage && (
                    <div className="text-xl font-bold text-green-700">
                      Up to {Math.min(group.combinedPercentage, 100)}%
                    </div>
                  )}
                  {group.combinedMaxSavings && (
                    <div className="text-sm text-green-600">
                      Save up to ₹{group.combinedMaxSavings}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Open in Platform button */}
        {(group.appLink || group.platformUrl) && (
          <button
            onClick={handleOpenPlatform}
            className="w-full mt-2 py-2 px-4 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Open in {group.platform_display_name} →
          </button>
        )}
      </div>
    </div>
  );
}

interface StackableOfferItemProps {
  offer: RestaurantOffer;
  type: 'restaurant' | 'bank';
}

function StackableOfferItem({ offer, type }: StackableOfferItemProps) {
  const bgColor = type === 'bank' ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200';

  return (
    <div className={`${bgColor} border rounded-lg p-3`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Bank badge for bank offers */}
          {offer.bank_name && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 mb-1.5">
              {offer.bank_name}
            </span>
          )}

          {/* Discount text */}
          <p className="text-sm font-medium text-gray-900">{offer.discount_text}</p>

          {/* Conditions */}
          {offer.conditions && (
            <p className="text-xs text-gray-500 mt-1">{offer.conditions}</p>
          )}

          {/* Coupon code */}
          {offer.coupon_code && (
            <div className="mt-1.5">
              <span className="inline-flex items-center px-2 py-1 bg-gray-100 rounded font-mono text-xs">
                Code: {offer.coupon_code}
              </span>
            </div>
          )}
        </div>

        {/* Discount percentage badge */}
        {offer.discount_percentage && (
          <div className="flex-shrink-0 text-right">
            <span className="text-lg font-bold text-gray-900">
              {offer.discount_percentage}%
            </span>
            <span className="block text-xs text-gray-500">off</span>
            {offer.max_discount && (
              <span className="block text-xs text-gray-400">
                max ₹{offer.max_discount}
              </span>
            )}
          </div>
        )}
      </div>
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
    eazydiner: 'bg-purple-100 text-purple-800 border-purple-200',
    district: 'bg-blue-100 text-blue-800 border-blue-200',
    unknown: 'bg-gray-100 text-gray-800 border-gray-200',
  };

  const platformLogos: Record<string, string> = {
    swiggy_dineout: '🍽️',
    eazydiner: '🍴',
    district: '📍',
    unknown: '🏪',
  };

  const offerTypeLabels: Record<string, string> = {
    'restaurant': 'Restaurant Offer',
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

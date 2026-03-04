import { useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';
import { AIInsight } from '../components/recommendation/AIInsight';
import { Loading } from '../components/common/Loading';
import { useRecommendation } from '../hooks/useRecommendation';
import { RestaurantOffers } from '../components/restaurant/RestaurantOffers';

// Categories that should show dine-in offers
// Includes Google Places types + custom categories
const DINEOUT_CATEGORIES = [
  // Google Places types
  'restaurant',
  'cafe',
  'coffee',
  'coffee_shop',
  'bar',
  'food',
  'bakery',
  'meal_delivery',
  'meal_takeaway',
  'night_club',
  'pub',
  'bistro',
  'diner',
  'pizzeria',
  'ice_cream',
  'dessert',
  'fast_food',
  'food_court',
  'brewery',
  'wine_bar',
  'cocktail',
  'lounge',
  // Custom/app categories
  'Food & Dining',
  'Dining',
  'Cafe',
  'Coffee',
  'Starbucks',
  'CCD',
  'Costa',
];

// Food delivery aggregators - these don't need dine-in offers
// as they are platforms, not physical restaurants
const FOOD_AGGREGATORS = [
  'zomato',
  'swiggy',
  'uber eats',
  'ubereats',
  'foodpanda',
  'dunzo',
  'zepto',
  'blinkit',
  'instamart',
  'bigbasket',
  'grofers',
  'jiomart',
  'amazon fresh',
  'eatclub',
  'box8',
  'faasos',
  'behrouz',
  'oven story',
  'licious',
  'freshmenu',
];

export function Recommendation() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Get place info from URL params
  const placeName = searchParams.get('name') || '';
  const placeCategory = searchParams.get('category') || undefined;
  const placeAddress = searchParams.get('address') || undefined;
  const placeId = searchParams.get('placeId') || undefined;

  const { recommendation, isLoading, error, getRecommendation } = useRecommendation();

  useEffect(() => {
    if (placeName) {
      getRecommendation(placeName, placeCategory, placeAddress, placeId);
    }
  }, [placeName, placeCategory, placeAddress, placeId, getRecommendation]);

  // Determine if this is a restaurant/dining place (but not an aggregator)
  const isDiningPlace = useMemo(() => {
    const category = recommendation?.place_category || placeCategory || '';
    const name = placeName.toLowerCase();

    // First, check if this is a food aggregator platform - these don't need dine-in offers
    const isAggregator = FOOD_AGGREGATORS.some((agg) => name.includes(agg));
    if (isAggregator) return false;

    // Check category
    const categoryMatch = DINEOUT_CATEGORIES.some((c) =>
      category.toLowerCase().includes(c.toLowerCase())
    );
    if (categoryMatch) return true;

    // Also check place name for known dining brands
    const diningBrands = [
      'starbucks', 'ccd', 'cafe coffee day', 'costa', 'barista',
      'mcdonald', 'burger king', 'kfc', 'domino', 'pizza hut',
      'subway', 'dunkin', 'tim hortons', 'chaayos', 'chai point',
      'haldiram', 'bikanervala', 'saravana bhavan', 'sagar ratna',
      'social', 'imperfecto', 'cafe delhi heights', 'big chill',
    ];
    return diningBrands.some((brand) => name.includes(brand));
  }, [recommendation?.place_category, placeCategory, placeName]);

  // Extract city from address (simple heuristic)
  const city = useMemo(() => {
    const address = placeAddress || '';
    // Try to extract city from address (last part before pincode/country)
    const parts = address.split(',').map((p) => p.trim());
    if (parts.length >= 2) {
      // Usually city is second-to-last or third-to-last
      const cityPart = parts[parts.length - 2] || parts[parts.length - 1];
      // Remove pincode if present
      return cityPart.replace(/\d{6}/, '').trim() || 'Delhi';
    }
    return 'Delhi'; // Default fallback
  }, [placeAddress]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg self-start mt-1"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1 min-w-0">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {recommendation?.place_name || placeName || 'Loading...'}
            </h1>
            {(recommendation?.place_category || placeCategory) && (
              <p className="text-sm text-gray-500">{recommendation?.place_category || placeCategory}</p>
            )}
            {/* Address - show first 3 lines */}
            {placeAddress && (
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1 space-y-0.5">
                {placeAddress.split(',').slice(0, 3).map((part, index) => (
                  <p key={index} className="truncate">
                    {part.trim()}
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {isLoading ? (
          <Loading text="Getting best payment option..." />
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-500 mb-4">{error}</p>
            <button
              onClick={() => navigate('/cards')}
              className="text-primary-500 font-medium hover:underline"
            >
              Add payment methods
            </button>
          </div>
        ) : recommendation ? (
          <>
            {/* Best option */}
            <RecommendationCard
              recommendation={recommendation.best_option}
              isBest
            />

            {/* AI Insight - Hidden for now
            {recommendation.ai_insight && (
              <AIInsight insight={recommendation.ai_insight} />
            )}
            */}

            {/* Restaurant Offers (for dining places only) - Shown before Other Options */}
            {isDiningPlace && placeName && (
              <div className="mt-4 bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                <RestaurantOffers
                  restaurantName={placeName}
                  city={city}
                  autoFetch={true}
                />
              </div>
            )}

            {/* Alternatives - Now shown after Dine-in Offers */}
            {Array.isArray(recommendation.alternatives) && recommendation.alternatives.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Other Options
                </h2>
                {recommendation.alternatives.map((alt) => (
                  <RecommendationCard
                    key={alt.card_id}
                    recommendation={alt}
                  />
                ))}
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}

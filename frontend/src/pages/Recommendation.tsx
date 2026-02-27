import { useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';
import { AIInsight } from '../components/recommendation/AIInsight';
import { Loading } from '../components/common/Loading';
import { useRecommendation } from '../hooks/useRecommendation';
import { RestaurantOffers } from '../components/restaurant/RestaurantOffers';

// Categories that should show restaurant offers
const DINEOUT_CATEGORIES = [
  'restaurant',
  'cafe',
  'bar',
  'food',
  'bakery',
  'meal_delivery',
  'meal_takeaway',
  'night_club',
  'Food & Dining',
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

  // Determine if this is a restaurant/dining place
  const isDiningPlace = useMemo(() => {
    const category = recommendation?.place_category || placeCategory || '';
    return DINEOUT_CATEGORIES.some((c) => category.toLowerCase().includes(c.toLowerCase()));
  }, [recommendation?.place_category, placeCategory]);

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
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {recommendation?.place_name || placeName || 'Loading...'}
            </h1>
            {(recommendation?.place_category || placeCategory) && (
              <p className="text-sm text-gray-500">{recommendation?.place_category || placeCategory}</p>
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

            {/* AI Insight */}
            {recommendation.ai_insight && (
              <AIInsight insight={recommendation.ai_insight} />
            )}

            {/* Alternatives */}
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

            {/* Restaurant Offers (for dining places only) */}
            {isDiningPlace && placeName && (
              <div className="mt-6 bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700">
                <RestaurantOffers
                  restaurantName={placeName}
                  city={city}
                  autoFetch={true}
                />
              </div>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}

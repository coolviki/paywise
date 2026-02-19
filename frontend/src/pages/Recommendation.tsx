import React, { useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { RecommendationCard } from '../components/recommendation/RecommendationCard';
import { AIInsight } from '../components/recommendation/AIInsight';
import { Loading } from '../components/common/Loading';
import { useRecommendation } from '../hooks/useRecommendation';

export function Recommendation() {
  const { merchantId } = useParams<{ merchantId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const locationId = searchParams.get('location') || undefined;

  const { recommendation, isLoading, error, getRecommendation } = useRecommendation();

  useEffect(() => {
    if (merchantId) {
      getRecommendation(merchantId, locationId);
    }
  }, [merchantId, locationId, getRecommendation]);

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
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            {recommendation?.merchant_name || 'Loading...'}
          </h1>
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
            {recommendation.alternatives.length > 0 && (
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

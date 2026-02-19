import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { PlacesList } from '../components/search/PlacesList';
import { Loading } from '../components/common/Loading';
import { useLocation } from '../hooks/useLocation';
import { useSearch } from '../hooks/useRecommendation';
import { Merchant } from '../types';

export function Search() {
  const navigate = useNavigate();
  const { location } = useLocation();
  const { results, isLoading, search, clearResults } = useSearch();
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.length >= 2) {
        search(searchQuery, location?.latitude, location?.longitude);
      } else {
        clearResults();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, location, search, clearResults]);

  const handleMerchantSelect = (merchant: Merchant, locationId?: string) => {
    navigate(`/recommendation/${merchant.id}${locationId ? `?location=${locationId}` : ''}`);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              autoFocus
              placeholder="Search restaurant, store, or place..."
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {isLoading ? (
          <Loading text="Searching..." />
        ) : searchQuery.length < 2 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <p>Start typing to search for merchants</p>
          </div>
        ) : !Array.isArray(results) || results.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <p>No results found for "{searchQuery}"</p>
          </div>
        ) : (
          <>
            {/* Near You section */}
            {results.some((m) => (m.locations || []).some((l) => l.distance_km !== undefined)) && (
              <PlacesList
                merchants={results.filter((m) =>
                  (m.locations || []).some((l) => l.distance_km !== undefined)
                )}
                onSelect={handleMerchantSelect}
                title="Near You"
              />
            )}

            {/* All Locations section */}
            {results.some((m) => (m.locations || []).length === 0 || m.is_chain) && (
              <div className="mt-6">
                <PlacesList
                  merchants={results.filter(
                    (m) => (m.locations || []).length === 0 || m.is_chain
                  )}
                  onSelect={handleMerchantSelect}
                  title="All Locations"
                />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { PlacesList } from '../components/search/PlacesList';
import { Loading } from '../components/common/Loading';
import { useLocation } from '../hooks/useLocation';
import { useSearch } from '../hooks/useRecommendation';
import { Merchant } from '../types';

// Popular online shopping portals in India
const ONLINE_PORTALS: Merchant[] = [
  { id: 'online-amazon', name: 'Amazon', category: 'Online Shopping', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-flipkart', name: 'Flipkart', category: 'Online Shopping', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-myntra', name: 'Myntra', category: 'Online Fashion', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-swiggy', name: 'Swiggy', category: 'Food Delivery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-zomato', name: 'Zomato', category: 'Food Delivery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-bigbasket', name: 'BigBasket', category: 'Grocery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-blinkit', name: 'Blinkit', category: 'Grocery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-zepto', name: 'Zepto', category: 'Grocery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-nykaa', name: 'Nykaa', category: 'Beauty & Wellness', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-ajio', name: 'AJIO', category: 'Online Fashion', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-tatacliq', name: 'Tata CLiQ', category: 'Online Shopping', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-croma', name: 'Croma', category: 'Electronics', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-bookmyshow', name: 'BookMyShow', category: 'Entertainment', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-makemytrip', name: 'MakeMyTrip', category: 'Travel', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-irctc', name: 'IRCTC', category: 'Travel', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-uber', name: 'Uber', category: 'Cab & Transport', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-ola', name: 'Ola', category: 'Cab & Transport', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-rapido', name: 'Rapido', category: 'Cab & Transport', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-jiomart', name: 'JioMart', category: 'Grocery', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-meesho', name: 'Meesho', category: 'Online Shopping', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
];

export function Search() {
  const navigate = useNavigate();
  const { location } = useLocation();
  const { results, isLoading, search, clearResults } = useSearch();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter online portals based on search query
  const matchingOnlinePortals = useMemo(() => {
    if (searchQuery.length < 2) return [];
    const query = searchQuery.toLowerCase();
    return ONLINE_PORTALS.filter(
      (portal) =>
        portal.name.toLowerCase().includes(query) ||
        portal.category?.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  // Show popular portals when no search query
  const popularPortals = useMemo(() => {
    return ONLINE_PORTALS.slice(0, 8); // Show first 8 popular portals
  }, []);

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

  const handleMerchantSelect = (merchant: Merchant) => {
    const params = new URLSearchParams({
      name: merchant.name,
      placeId: merchant.id,
    });
    if (merchant.category) params.append('category', merchant.category);
    if (merchant.locations?.[0]?.address) params.append('address', merchant.locations[0].address);
    // Mark as online portal for recommendation engine
    if (merchant.id.startsWith('online-')) params.append('is_online', 'true');
    navigate(`/recommendation?${params.toString()}`);
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
        {searchQuery.length < 2 ? (
          <div className="space-y-6">
            {/* Popular Online Portals */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-primary-600" />
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Popular Online Portals
                </h3>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {popularPortals.map((portal) => (
                  <button
                    key={portal.id}
                    onClick={() => handleMerchantSelect(portal)}
                    className="flex flex-col items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                  >
                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg font-semibold text-primary-600">
                        {portal.name[0]}
                      </span>
                    </div>
                    <span className="text-xs text-gray-700 dark:text-gray-300 text-center truncate w-full">
                      {portal.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              <p>Or type to search for stores near you</p>
            </div>
          </div>
        ) : (
          <>
            {/* Online Portals matching search */}
            {matchingOnlinePortals.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="w-4 h-4 text-primary-600" />
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Online Portals
                  </h3>
                </div>
                <div className="space-y-2">
                  {matchingOnlinePortals.map((portal) => (
                    <button
                      key={portal.id}
                      onClick={() => handleMerchantSelect(portal)}
                      className="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors text-left"
                    >
                      <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-lg font-semibold text-primary-600">
                          {portal.name[0]}
                        </span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {portal.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {portal.category}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Loading indicator for places search */}
            {isLoading && (
              <div className="mb-4">
                <Loading text="Searching nearby places..." />
              </div>
            )}

            {/* Near You section */}
            {!isLoading && results.some((m) => (m.locations || []).some((l) => l.distance_km !== undefined)) && (
              <PlacesList
                merchants={results.filter((m) =>
                  (m.locations || []).some((l) => l.distance_km !== undefined)
                )}
                onSelect={handleMerchantSelect}
                title="Near You"
              />
            )}

            {/* All Locations section */}
            {!isLoading && results.some((m) => (m.locations || []).length === 0 || m.is_chain) && (
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

            {/* No results message */}
            {!isLoading && matchingOnlinePortals.length === 0 && (!Array.isArray(results) || results.length === 0) && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <p>No results found for "{searchQuery}"</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

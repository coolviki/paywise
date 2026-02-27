import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, User, Shield, Globe } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { PlacesList } from '../components/search/PlacesList';
import { Loading } from '../components/common/Loading';
import { useAuth } from '../hooks/useAuth';
import { useLocation } from '../hooks/useLocation';
import { useSearch } from '../hooks/useRecommendation';
import { Merchant, User as UserType } from '../types';

// Popular online shopping portals in India (primary display)
const FEATURED_PORTALS: Merchant[] = [
  { id: 'online-amazon', name: 'Amazon', category: 'Online Shopping', logo_url: 'https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg', is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-flipkart', name: 'Flipkart', category: 'Online Shopping', logo_url: 'https://static-assets-web.flixcart.com/batman-returns/batman-returns/p/images/fkheaderlogo_exploreplus-44005d.svg', is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-zomato', name: 'Zomato', category: 'Food Delivery', logo_url: 'https://b.zmtcdn.com/web_assets/b40b97e677bc7b2ca77c58c61db266fe1603954218.png', is_chain: true, locations: [], offer_count: 0 },
  { id: 'online-swiggy', name: 'Swiggy', category: 'Food Delivery', logo_url: 'https://upload.wikimedia.org/wikipedia/en/1/12/Swiggy_logo.svg', is_chain: true, locations: [], offer_count: 0 },
];

// All online portals for search
const ONLINE_PORTALS: Merchant[] = [
  ...FEATURED_PORTALS,
  { id: 'online-myntra', name: 'Myntra', category: 'Online Fashion', logo_url: undefined, is_chain: true, locations: [], offer_count: 0 },
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

export function Home() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { location } = useLocation();
  const { results, isLoading, search, searchNearby, clearResults } = useSearch();
  const [searchQuery, setSearchQuery] = useState('');
  const [showMenu, setShowMenu] = useState(false);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  }, []);

  const firstName = user?.name?.split(' ')[0] || 'there';

  // Filter online portals based on search query
  const matchingOnlinePortals = useMemo(() => {
    if (!searchQuery || searchQuery.length < 2) return [];
    const query = searchQuery.toLowerCase();
    return ONLINE_PORTALS.filter(
      (portal) =>
        portal.name.toLowerCase().includes(query) ||
        portal.category?.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  useEffect(() => {
    if (location && !searchQuery) {
      searchNearby(location.latitude, location.longitude);
    }
  }, [location, searchNearby, searchQuery]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery) {
        search(searchQuery, location?.latitude, location?.longitude);
      } else if (location) {
        searchNearby(location.latitude, location.longitude);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, location, search, searchNearby]);

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-20">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="flex items-center justify-between p-4">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <Menu className="w-6 h-6" />
          </button>
          <button
            onClick={() => navigate('/settings')}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            {user?.profile_picture ? (
              <img
                src={user.profile_picture}
                alt={user.name}
                className="w-8 h-8 rounded-full"
              />
            ) : (
              <User className="w-6 h-6" />
            )}
          </button>
        </div>

        <div className="px-4 pb-4">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            {greeting}, {firstName}
          </h1>
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            placeholder="Search restaurant, store, or place..."
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {searchQuery ? (
          <>
            {/* Online Portals matching search */}
            {matchingOnlinePortals.length > 0 && (
              <div>
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
                      className="w-full flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors text-left shadow-sm"
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

            {/* Search results */}
            {isLoading ? (
              <Loading text="Finding places..." />
            ) : (
              <PlacesList
                merchants={results}
                onSelect={handleMerchantSelect}
                title="Search Results"
              />
            )}
          </>
        ) : (
          <>
            {/* Popular Online Portals - Single Row */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-primary-600" />
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Popular Online Portals
                </h3>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {FEATURED_PORTALS.map((portal) => (
                  <button
                    key={portal.id}
                    onClick={() => handleMerchantSelect(portal)}
                    className="flex flex-col items-center p-3 bg-white dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors shadow-sm"
                  >
                    <div className="w-10 h-10 rounded-full flex items-center justify-center mb-2 overflow-hidden bg-white">
                      {portal.logo_url ? (
                        <img
                          src={portal.logo_url}
                          alt={portal.name}
                          className="w-8 h-8 object-contain"
                          onError={(e) => {
                            // Fallback to initial letter if logo fails to load
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            target.parentElement!.innerHTML = `<span class="text-lg font-semibold text-primary-600">${portal.name[0]}</span>`;
                          }}
                        />
                      ) : (
                        <span className="text-lg font-semibold text-primary-600">
                          {portal.name[0]}
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-700 dark:text-gray-300 text-center truncate w-full">
                      {portal.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Nearby Places */}
            {isLoading ? (
              <Loading text="Finding nearby places..." />
            ) : (
              <PlacesList
                merchants={results}
                onSelect={handleMerchantSelect}
                title="Nearby Places"
              />
            )}
          </>
        )}
      </div>

      {/* Bottom Navigation */}
      <BottomNav user={user} />
    </div>
  );
}

function BottomNav({ user }: { user: UserType | null }) {
  const navigate = useNavigate();
  const currentPath = window.location.pathname;

  const tabs = [
    { icon: '🏠', label: 'Home', path: '/' },
    { icon: '💳', label: 'Cards', path: '/cards' },
    { icon: '⚙️', label: 'Settings', path: '/settings' },
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 safe-bottom">
      <div className="flex justify-around py-2">
        {tabs.map((tab) => (
          <button
            key={tab.path}
            onClick={() => navigate(tab.path)}
            className={`flex flex-col items-center py-2 px-4 ${
              currentPath === tab.path
                ? 'text-primary-500'
                : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <span className="text-xl">{tab.icon}</span>
            <span className="text-xs mt-1">{tab.label}</span>
          </button>
        ))}
        {user?.is_admin && (
          <button
            onClick={() => navigate('/admin')}
            className={`flex flex-col items-center py-2 px-4 ${
              currentPath.startsWith('/admin')
                ? 'text-primary-500'
                : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            <Shield className="w-5 h-5" />
            <span className="text-xs mt-1">Admin</span>
          </button>
        )}
      </div>
    </div>
  );
}

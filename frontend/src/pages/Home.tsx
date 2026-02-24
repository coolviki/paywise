import React, { useEffect, useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, User, Tag, Shield } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { PlacesList } from '../components/search/PlacesList';
import { Card } from '../components/common/Card';
import { Loading } from '../components/common/Loading';
import { useAuth } from '../hooks/useAuth';
import { useLocation } from '../hooks/useLocation';
import { useSearch } from '../hooks/useRecommendation';
import { Merchant, User as UserType } from '../types';

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
        {isLoading ? (
          <Loading text="Finding places..." />
        ) : (
          <>
            {/* Search results or nearby places */}
            <PlacesList
              merchants={results}
              onSelect={handleMerchantSelect}
              title={searchQuery ? 'Search Results' : 'Nearby Places'}
            />

            {/* Hot offers section */}
            {!searchQuery && (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Hot Offers Today
                </h3>
                <Card className="p-4 bg-gradient-to-r from-primary-500 to-primary-600 text-white border-0">
                  <p className="font-medium">20% off at Swiggy with HDFC</p>
                  <p className="text-sm text-primary-100 mt-1">
                    Max discount Rs. 100
                  </p>
                </Card>
              </div>
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
    { icon: '🔍', label: 'Search', path: '/search' },
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

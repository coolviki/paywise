import React from 'react';
import { MapPin, Tag, ChevronRight } from 'lucide-react';
import { Card } from '../common/Card';
import { Merchant } from '../../types';
import { locationService } from '../../services/locationService';

interface PlacesListProps {
  merchants: Merchant[];
  onSelect: (merchant: Merchant, locationId?: string) => void;
  title?: string;
}

export function PlacesList({ merchants, onSelect, title }: PlacesListProps) {
  // Ensure merchants is an array
  const merchantList = Array.isArray(merchants) ? merchants : [];

  if (merchantList.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <MapPin className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No places found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {title && (
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 flex items-center gap-2">
          <MapPin className="w-4 h-4" />
          {title}
        </h3>
      )}
      <div className="space-y-2">
        {merchantList.map((merchant) => (
          <PlaceCard key={merchant.id} merchant={merchant} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

interface PlaceCardProps {
  merchant: Merchant;
  onSelect: (merchant: Merchant, locationId?: string) => void;
}

function PlaceCard({ merchant, onSelect }: PlaceCardProps) {
  const locations = merchant.locations || [];
  const nearestLocation = locations[0];

  return (
    <Card
      hoverable
      onClick={() => onSelect(merchant, nearestLocation?.id)}
      className="p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center text-xl">
            {getCategoryEmoji(merchant.category)}
          </div>
          <div>
            <p className="font-medium text-gray-900 dark:text-white">{merchant.name}</p>
            <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
              {nearestLocation?.distance_km !== undefined && (
                <span>{locationService.formatDistance(nearestLocation.distance_km)}</span>
              )}
              {nearestLocation?.distance_km !== undefined && merchant.category && (
                <span>-</span>
              )}
              {merchant.category && <span>{merchant.category}</span>}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {merchant.offer_count > 0 && (
            <span className="flex items-center gap-1 px-2 py-1 bg-accent-100 dark:bg-accent-900 text-accent-600 dark:text-accent-400 text-xs font-medium rounded-full">
              <Tag className="w-3 h-3" />
              {merchant.offer_count} offer{merchant.offer_count > 1 ? 's' : ''}
            </span>
          )}
          <ChevronRight className="w-5 h-5 text-gray-400" />
        </div>
      </div>
    </Card>
  );
}

function getCategoryEmoji(category?: string): string {
  if (!category) return '📍';

  const categoryLower = category.toLowerCase();

  if (categoryLower.includes('food') || categoryLower.includes('dining') || categoryLower.includes('restaurant')) {
    return '🍕';
  }
  if (categoryLower.includes('cafe') || categoryLower.includes('coffee')) {
    return '☕';
  }
  if (categoryLower.includes('grocery') || categoryLower.includes('supermarket')) {
    return '🛒';
  }
  if (categoryLower.includes('shopping') || categoryLower.includes('retail')) {
    return '🛍️';
  }
  if (categoryLower.includes('fuel') || categoryLower.includes('petrol') || categoryLower.includes('gas')) {
    return '⛽';
  }
  if (categoryLower.includes('travel') || categoryLower.includes('hotel')) {
    return '✈️';
  }
  if (categoryLower.includes('entertainment') || categoryLower.includes('movie')) {
    return '🎬';
  }
  if (categoryLower.includes('health') || categoryLower.includes('pharmacy')) {
    return '💊';
  }

  return '📍';
}

import { useState, useCallback } from 'react';
import api from '../services/api';
import { Recommendation, Merchant } from '../types';

export function useRecommendation() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendation = useCallback(async (
    placeName: string,
    placeCategory?: string,
    placeAddress?: string,
    placeId?: string,
    transactionAmount?: number
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<Recommendation>('/recommendations', {
        place_name: placeName,
        place_category: placeCategory,
        place_address: placeAddress,
        place_id: placeId,
        transaction_amount: transactionAmount,
      });
      setRecommendation(response.data);
      return response.data;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to get recommendation';
      setError(message);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearRecommendation = useCallback(() => {
    setRecommendation(null);
    setError(null);
  }, []);

  return {
    recommendation,
    isLoading,
    error,
    getRecommendation,
    clearRecommendation,
  };
}

export function useSearch() {
  const [results, setResults] = useState<Merchant[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const search = useCallback(
    async (query: string, latitude?: number, longitude?: number) => {
      if (!query.trim()) {
        setResults([]);
        return;
      }

      setIsLoading(true);

      try {
        const params = new URLSearchParams({ q: query });
        if (latitude) params.append('latitude', latitude.toString());
        if (longitude) params.append('longitude', longitude.toString());

        // Search using Google Places API only
        const placesResponse = await api.get<any[]>(`/search/places?${params}`);
        const placesData = Array.isArray(placesResponse.data) ? placesResponse.data : [];

        // Convert Google Places results to Merchant format
        const placesResults: Merchant[] = placesData.map((place) => ({
          id: place.place_id,
          name: place.name,
          category: place.types?.[0] || 'Other',
          logo_url: null,
          is_chain: false,
          locations: place.address ? [{
            id: place.place_id,
            address: place.address,
            city: '',
            distance_km: undefined,
            has_offer: false,
          }] : [],
          offer_count: 0,
        }));

        setResults(placesResults);
      } catch (err) {
        console.error('Search error:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const searchNearby = useCallback(
    async (latitude: number, longitude: number) => {
      setIsLoading(true);

      try {
        const params = new URLSearchParams({
          q: 'restaurant cafe store', // Default nearby search
          latitude: latitude.toString(),
          longitude: longitude.toString(),
        });

        // Use Google Places API for nearby search
        const placesResponse = await api.get<any[]>(`/search/places?${params}`);
        const placesData = Array.isArray(placesResponse.data) ? placesResponse.data : [];

        // Convert Google Places results to Merchant format
        const placesResults: Merchant[] = placesData.map((place) => ({
          id: place.place_id,
          name: place.name,
          category: place.types?.[0] || 'Other',
          logo_url: null,
          is_chain: false,
          locations: place.address ? [{
            id: place.place_id,
            address: place.address,
            city: '',
            distance_km: undefined,
            has_offer: false,
          }] : [],
          offer_count: 0,
        }));

        setResults(placesResults);
      } catch (err) {
        console.error('Nearby search error:', err);
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  return {
    results,
    isLoading,
    search,
    searchNearby,
    clearResults,
  };
}

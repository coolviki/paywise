import { useState, useCallback } from 'react';
import api from '../services/api';
import { Recommendation, Merchant } from '../types';

export function useRecommendation() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendation = useCallback(async (merchantId: string, locationId?: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post<Recommendation>('/recommendations', {
        merchant_id: merchantId,
        location_id: locationId,
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

        const response = await api.get<Merchant[]>(`/search/merchants?${params}`);
        // Ensure response.data is an array
        const data = Array.isArray(response.data) ? response.data : [];
        setResults(data);
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
          latitude: latitude.toString(),
          longitude: longitude.toString(),
        });

        const response = await api.get<Merchant[]>(`/search/nearby?${params}`);
        setResults(response.data);
      } catch {
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

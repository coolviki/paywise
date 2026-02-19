import { useState, useEffect, useCallback } from 'react';
import { locationService } from '../services/locationService';

interface Location {
  latitude: number;
  longitude: number;
}

export function useLocation() {
  const [location, setLocation] = useState<Location | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const requestLocation = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const coords = await locationService.getCurrentPosition();
      setLocation(coords);
    } catch (err: any) {
      if (err.code === 1) {
        setError('Location permission denied');
      } else if (err.code === 2) {
        setError('Location unavailable');
      } else if (err.code === 3) {
        setError('Location request timed out');
      } else {
        setError(err.message || 'Failed to get location');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  return {
    location,
    error,
    isLoading,
    refresh: requestLocation,
  };
}

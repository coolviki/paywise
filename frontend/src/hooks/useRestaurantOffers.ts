import { useState, useCallback, useRef } from 'react';
import { RestaurantOffer, RestaurantOffersState } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Hook for fetching restaurant offers via SSE streaming.
 * Shows offers in real-time as they are discovered.
 */
export function useRestaurantOffers() {
  const [state, setState] = useState<RestaurantOffersState>({
    offers: [],
    isLoading: false,
    isStreaming: false,
    summary: undefined,
    error: undefined,
  });

  const eventSourceRef = useRef<EventSource | null>(null);

  /**
   * Stream restaurant offers via SSE.
   * Offers will appear one by one as they are found.
   */
  const streamOffers = useCallback(
    (restaurantName: string, city: string, platforms?: string[]) => {
      // Close any existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      // Reset state
      setState({
        offers: [],
        isLoading: true,
        isStreaming: true,
        summary: undefined,
        error: undefined,
      });

      // Build URL
      const params = new URLSearchParams({
        restaurant_name: restaurantName,
        city: city,
      });
      if (platforms && platforms.length > 0) {
        params.append('platforms', platforms.join(','));
      }

      // Get auth token
      const token = localStorage.getItem('token');
      if (!token) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isStreaming: false,
          error: 'Authentication required',
        }));
        return;
      }

      // Note: EventSource doesn't support custom headers directly
      // We need to use a workaround by adding token as query param
      // or use fetch with ReadableStream instead
      const url = `${API_URL}/api/restaurant-offers/stream?${params}&token=${token}`;

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setState((prev) => ({ ...prev, isLoading: false }));
      };

      eventSource.onmessage = (event) => {
        try {
          const offer: RestaurantOffer = JSON.parse(event.data);
          setState((prev) => ({
            ...prev,
            offers: [...prev.offers, offer],
          }));
        } catch (e) {
          console.error('Failed to parse offer:', e);
        }
      };

      eventSource.addEventListener('start', (event) => {
        // Connection started
        setState((prev) => ({ ...prev, isLoading: false }));
      });

      eventSource.addEventListener('done', (event) => {
        try {
          const data = JSON.parse((event as MessageEvent).data);
          setState((prev) => ({
            ...prev,
            isStreaming: false,
            summary: data.summary,
          }));
        } catch (e) {
          console.error('Failed to parse done event:', e);
        }
        eventSource.close();
        eventSourceRef.current = null;
      });

      eventSource.addEventListener('error', (event) => {
        try {
          const data = JSON.parse((event as MessageEvent).data);
          setState((prev) => ({
            ...prev,
            isLoading: false,
            isStreaming: false,
            error: data.error,
          }));
        } catch (e) {
          // Generic error
          setState((prev) => ({
            ...prev,
            isLoading: false,
            isStreaming: false,
            error: 'Failed to stream offers',
          }));
        }
        eventSource.close();
        eventSourceRef.current = null;
      });

      eventSource.onerror = () => {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isStreaming: false,
          error: 'Connection error',
        }));
        eventSource.close();
        eventSourceRef.current = null;
      };
    },
    []
  );

  /**
   * Fetch all offers at once (non-streaming).
   * Use this when you don't want incremental updates.
   */
  const fetchOffers = useCallback(
    async (restaurantName: string, city: string, platforms?: string[]) => {
      setState({
        offers: [],
        isLoading: true,
        isStreaming: false,
        summary: undefined,
        error: undefined,
      });

      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/api/restaurant-offers`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            restaurant_name: restaurantName,
            city: city,
            platforms: platforms,
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to fetch offers');
        }

        const data = await response.json();
        setState({
          offers: data.offers,
          isLoading: false,
          isStreaming: false,
          summary: data.summary,
          error: undefined,
        });
      } catch (e: any) {
        setState({
          offers: [],
          isLoading: false,
          isStreaming: false,
          error: e.message || 'Failed to fetch offers',
        });
      }
    },
    []
  );

  /**
   * Cancel any ongoing stream.
   */
  const cancelStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      isLoading: false,
      isStreaming: false,
    }));
  }, []);

  /**
   * Clear all offers.
   */
  const clearOffers = useCallback(() => {
    cancelStream();
    setState({
      offers: [],
      isLoading: false,
      isStreaming: false,
      summary: undefined,
      error: undefined,
    });
  }, [cancelStream]);

  return {
    ...state,
    streamOffers,
    fetchOffers,
    cancelStream,
    clearOffers,
  };
}

/**
 * Alternative hook using fetch + ReadableStream for SSE
 * (Works better with auth headers)
 */
export function useRestaurantOffersWithFetch() {
  const [state, setState] = useState<RestaurantOffersState>({
    offers: [],
    isLoading: false,
    isStreaming: false,
    summary: undefined,
    error: undefined,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const streamOffers = useCallback(
    async (restaurantName: string, city: string, platforms?: string[]) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      setState({
        offers: [],
        isLoading: true,
        isStreaming: true,
        summary: undefined,
        error: undefined,
      });

      try {
        const token = localStorage.getItem('token');
        const params = new URLSearchParams({
          restaurant_name: restaurantName,
          city: city,
        });
        if (platforms && platforms.length > 0) {
          params.append('platforms', platforms.join(','));
        }

        const response = await fetch(
          `${API_URL}/api/restaurant-offers/stream?${params}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
            signal: abortController.signal,
          }
        );

        if (!response.ok) {
          throw new Error('Failed to stream offers');
        }

        setState((prev) => ({ ...prev, isLoading: false }));

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No reader available');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          // Process complete SSE events
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);
                // Check if it's an offer or a done event
                if (parsed.platform) {
                  setState((prev) => ({
                    ...prev,
                    offers: [...prev.offers, parsed as RestaurantOffer],
                  }));
                } else if (parsed.total_offers !== undefined) {
                  // Done event
                  setState((prev) => ({
                    ...prev,
                    isStreaming: false,
                    summary: parsed.summary,
                  }));
                }
              } catch (e) {
                // Ignore parse errors
              }
            } else if (line.startsWith('event: done')) {
              setState((prev) => ({ ...prev, isStreaming: false }));
            } else if (line.startsWith('event: error')) {
              // Next data line will have the error
            }
          }
        }

        setState((prev) => ({ ...prev, isStreaming: false }));
      } catch (e: any) {
        if (e.name === 'AbortError') {
          // Cancelled, ignore
          return;
        }
        setState({
          offers: [],
          isLoading: false,
          isStreaming: false,
          error: e.message || 'Failed to stream offers',
        });
      }
    },
    []
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      isLoading: false,
      isStreaming: false,
    }));
  }, []);

  const clearOffers = useCallback(() => {
    cancelStream();
    setState({
      offers: [],
      isLoading: false,
      isStreaming: false,
      summary: undefined,
      error: undefined,
    });
  }, [cancelStream]);

  return {
    ...state,
    streamOffers,
    cancelStream,
    clearOffers,
  };
}

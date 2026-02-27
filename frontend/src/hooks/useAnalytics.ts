import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { trackPageView } from '../utils/analytics';

/**
 * Hook to track page views on route changes.
 * Add this to your App component.
 */
export function usePageTracking(): void {
  const location = useLocation();

  useEffect(() => {
    // Track page view when route changes
    trackPageView(location.pathname + location.search);
  }, [location]);
}

export { analytics, trackEvent } from '../utils/analytics';

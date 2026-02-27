/**
 * Google Analytics 4 integration for PayWise.
 *
 * Setup:
 * 1. Create a GA4 property at https://analytics.google.com/
 * 2. Get your Measurement ID (starts with G-)
 * 3. Set VITE_GA_MEASUREMENT_ID in your .env file
 */

declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;

/**
 * Initialize Google Analytics 4.
 * Call this once when the app loads.
 */
export function initGA(): void {
  if (!GA_MEASUREMENT_ID) {
    console.log('Google Analytics not configured (VITE_GA_MEASUREMENT_ID not set)');
    return;
  }

  // Don't initialize in development unless explicitly enabled
  if (import.meta.env.DEV && !import.meta.env.VITE_GA_DEBUG) {
    console.log('Google Analytics disabled in development');
    return;
  }

  // Load gtag.js script
  const script = document.createElement('script');
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  // Initialize dataLayer and gtag function
  window.dataLayer = window.dataLayer || [];
  window.gtag = function gtag() {
    window.dataLayer.push(arguments);
  };

  window.gtag('js', new Date());
  window.gtag('config', GA_MEASUREMENT_ID, {
    send_page_view: false, // We'll track page views manually for SPA
  });

  console.log('Google Analytics initialized');
}

/**
 * Track a page view.
 * Call this on route changes.
 */
export function trackPageView(path: string, title?: string): void {
  if (!GA_MEASUREMENT_ID || !window.gtag) return;

  window.gtag('event', 'page_view', {
    page_path: path,
    page_title: title || document.title,
  });
}

/**
 * Track a custom event.
 */
export function trackEvent(
  eventName: string,
  params?: Record<string, any>
): void {
  if (!GA_MEASUREMENT_ID || !window.gtag) return;

  window.gtag('event', eventName, params);
}

// Pre-defined event trackers for common actions
export const analytics = {
  // User actions
  login: (method: string) => trackEvent('login', { method }),
  signup: (method: string) => trackEvent('sign_up', { method }),

  // Card actions
  addCard: (bankName: string, cardName: string) =>
    trackEvent('add_card', { bank_name: bankName, card_name: cardName }),
  removeCard: (bankName: string, cardName: string) =>
    trackEvent('remove_card', { bank_name: bankName, card_name: cardName }),

  // Search actions
  search: (query: string) => trackEvent('search', { search_term: query }),
  selectPlace: (placeName: string, category: string) =>
    trackEvent('select_place', { place_name: placeName, category }),

  // Recommendation actions
  viewRecommendation: (placeName: string, bestCard: string) =>
    trackEvent('view_recommendation', {
      place_name: placeName,
      best_card: bestCard,
    }),

  // Dine-out app actions
  toggleDineoutApp: (appName: string, enabled: boolean) =>
    trackEvent('toggle_dineout_app', {
      app_name: appName,
      enabled: enabled ? 'yes' : 'no',
    }),

  // Restaurant offers
  viewRestaurantOffers: (restaurantName: string, offersCount: number) =>
    trackEvent('view_restaurant_offers', {
      restaurant_name: restaurantName,
      offers_count: offersCount,
    }),
  clickOfferLink: (platform: string, restaurantName: string) =>
    trackEvent('click_offer_link', {
      platform,
      restaurant_name: restaurantName,
    }),
};

export interface User {
  id: string;
  email: string;
  name: string;
  profile_picture?: string;
  auth_provider: string;
  created_at: string;
  last_login?: string;
  is_admin?: boolean;
}

export interface Bank {
  id: string;
  name: string;
  code: string;
  logo_url?: string;
  is_active: boolean;
}

export interface Card {
  id: string;
  bank_id: string;
  name: string;
  card_type: 'credit' | 'debit';
  card_network?: 'visa' | 'mastercard' | 'rupay' | 'amex';
  annual_fee?: number;
  reward_type?: 'cashback' | 'points' | 'miles';
  base_reward_rate?: number;
  is_active: boolean;
  bank?: Bank;
}

export interface PaymentMethod {
  id: string;
  user_id: string;
  bank_id?: string;
  card_id?: string;
  payment_type: 'credit_card' | 'debit_card' | 'upi' | 'wallet';
  last_four_digits?: string;
  nickname?: string;
  is_active: boolean;
  created_at: string;
  bank?: Bank;
  card?: Card;
}

export interface MerchantLocation {
  id: string;
  address?: string;
  city?: string;
  distance_km?: number;
  has_offer: boolean;
}

export interface Merchant {
  id: string;
  name: string;
  category?: string;
  logo_url?: string;
  is_chain: boolean;
  locations: MerchantLocation[];
  offer_count: number;
}

export interface Offer {
  id: string;
  card_id?: string;
  card_name?: string;
  bank_name?: string;
  title: string;
  description?: string;
  discount_type: 'percentage' | 'flat' | 'cashback' | 'points';
  discount_value: number;
  min_transaction?: number;
  max_discount?: number;
  valid_until?: string;
}

export interface CardRecommendation {
  card_id: string;
  card_name: string;
  bank_name: string;
  estimated_savings: string;
  reason: string;
  offers: string[];  // List of offer descriptions from LLM
  source_url?: string;  // Link to bank's T&C page
}

export interface Recommendation {
  place_name: string;
  place_category?: string;
  best_option: CardRecommendation;
  alternatives: CardRecommendation[];
  ai_insight?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface CardsState {
  banks: Bank[];
  paymentMethods: PaymentMethod[];
  isLoading: boolean;
  error: string | null;
}

// Admin Types
export interface BrandKeyword {
  id: string;
  keyword: string;
  created_at: string;
}

export interface Brand {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  keywords: BrandKeyword[];
}

export interface BrandListItem {
  id: string;
  name: string;
  code: string;
  description?: string;
  is_active: boolean;
  keyword_count: number;
}

export interface EcosystemBenefit {
  id: string;
  card_id: string;
  card_name: string;
  bank_name: string;
  brand_id: string;
  brand_name: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
  is_active: boolean;
  created_at: string;
}

export interface CardSimple {
  id: string;
  name: string;
  bank_name: string;
}

export interface BankSimple {
  id: string;
  name: string;
  code: string;
}

export interface CardFull {
  id: string;
  bank_id: string;
  bank_name: string;
  name: string;
  card_type: string;
  card_network?: string;
  annual_fee?: number;
  reward_type?: string;
  base_reward_rate?: number;
  terms_url?: string;
  is_active: boolean;
  created_at?: string;
}

// Scraper Types
export interface PendingChange {
  id: string;
  card_id?: string;
  card_name?: string;
  brand_id?: string;
  brand_name?: string;
  benefit_rate?: number;
  benefit_type?: string;
  description?: string;
  source_url?: string;
  change_type: 'new' | 'update' | 'delete';
  old_values?: {
    benefit_rate?: number;
    benefit_type?: string;
    description?: string;
  };
  status: 'pending' | 'approved' | 'rejected';
  scraped_at: string;
  reviewed_at?: string;
}

export interface ScraperStatus {
  is_running: boolean;
  current_bank?: string;
  last_run?: string;
  last_result?: 'success' | 'partial' | 'failed';
  benefits_found: number;
  pending_created: number;
  brands_created: number;
  cards_created: number;
  errors: string[];
}

export interface PendingBrand {
  id: string;
  name: string;
  code: string;
  description?: string;
  keywords: string[];
  source_url?: string;
  source_bank?: string;
  status: 'pending' | 'approved' | 'rejected';
  scraped_at: string;
  reviewed_at?: string;
}

export interface PendingCard {
  id: string;
  bank_id: string;
  bank_name: string;
  existing_card_id?: string;
  name: string;
  card_type: string;
  card_network?: string;
  annual_fee?: number;
  reward_type?: string;
  base_reward_rate?: number;
  terms_url?: string;
  change_type: 'new' | 'update';
  old_values?: Record<string, any>;
  source_url?: string;
  source_bank?: string;
  status: 'pending' | 'approved' | 'rejected';
  scraped_at: string;
  reviewed_at?: string;
}

// Campaign Types
export interface Campaign {
  id: string;
  card_id: string;
  card_name: string;
  bank_name: string;
  brand_id: string;
  brand_name: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
  terms_url?: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
  is_currently_active: boolean;
  created_at?: string;
}

export interface PendingCampaign {
  id: string;
  card_id: string;
  card_name: string;
  brand_id: string;
  brand_name: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
  terms_url?: string;
  start_date: string;
  end_date: string;
  source_url?: string;
  change_type: 'new' | 'update' | 'delete';
  existing_campaign_id?: string;
  status: 'pending' | 'approved' | 'rejected';
  scraped_at: string;
  reviewed_at?: string;
}

// Restaurant Offers Types (from Swiggy Dineout, Zomato Pay, EazyDiner, etc.)
export type RestaurantOfferPlatform =
  | 'swiggy_dineout'
  | 'zomato_pay'
  | 'eazydiner'
  | 'district'
  | 'unknown';

export interface RestaurantOffer {
  platform: RestaurantOfferPlatform;
  platform_display_name: string;
  offer_type: 'pre-booked' | 'walk-in' | 'bank_offer' | 'coupon' | 'general';
  discount_text: string;
  discount_percentage?: number;
  max_discount?: number;
  min_order?: number;
  bank_name?: string;
  card_type?: string;
  conditions?: string;
  coupon_code?: string;
  valid_days?: string;
  source_url?: string;
  platform_url?: string;  // Link to restaurant on platform
  app_link?: string;      // Deep link to app
}

export interface RestaurantOffersState {
  offers: RestaurantOffer[];
  isLoading: boolean;
  isStreaming: boolean;
  summary?: string;
  error?: string;
}

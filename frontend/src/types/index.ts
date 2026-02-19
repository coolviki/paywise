export interface User {
  id: string;
  email: string;
  name: string;
  profile_picture?: string;
  auth_provider: string;
  created_at: string;
  last_login?: string;
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
  offer?: Offer;
}

export interface Recommendation {
  merchant_id: string;
  merchant_name: string;
  category?: string;
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

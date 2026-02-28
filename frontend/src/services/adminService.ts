import api from './api';
import { Brand, BrandListItem, EcosystemBenefit, CardSimple, CardFull, BankSimple, PendingChange, ScraperStatus, PendingBrand, PendingCard, Campaign, PendingCampaign, DuplicateCardsResponse } from '../types';

// Brands
export const getBrands = async (): Promise<BrandListItem[]> => {
  const response = await api.get('/admin/brands');
  return response.data;
};

export const getBrand = async (brandId: string): Promise<Brand> => {
  const response = await api.get(`/admin/brands/${brandId}`);
  return response.data;
};

export const createBrand = async (data: {
  name: string;
  code: string;
  description?: string;
  keywords?: string[];
}): Promise<Brand> => {
  const response = await api.post('/admin/brands', data);
  return response.data;
};

export const updateBrand = async (
  brandId: string,
  data: { name?: string; code?: string; description?: string }
): Promise<Brand> => {
  const response = await api.put(`/admin/brands/${brandId}`, data);
  return response.data;
};

export const deleteBrand = async (brandId: string): Promise<void> => {
  await api.delete(`/admin/brands/${brandId}`);
};

// Keywords
export const addKeyword = async (
  brandId: string,
  keyword: string
): Promise<{ id: string; keyword: string }> => {
  const response = await api.post(`/admin/brands/${brandId}/keywords`, { keyword });
  return response.data;
};

export const deleteKeyword = async (brandId: string, keywordId: string): Promise<void> => {
  await api.delete(`/admin/brands/${brandId}/keywords/${keywordId}`);
};

// Ecosystem Benefits
export const getEcosystemBenefits = async (params?: {
  brand_id?: string;
  bank_code?: string;
}): Promise<EcosystemBenefit[]> => {
  const response = await api.get('/admin/ecosystem-benefits', { params });
  return response.data;
};

export const createEcosystemBenefit = async (data: {
  card_id: string;
  brand_id: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
}): Promise<EcosystemBenefit> => {
  const response = await api.post('/admin/ecosystem-benefits', data);
  return response.data;
};

export const updateEcosystemBenefit = async (
  benefitId: string,
  data: { benefit_rate?: number; benefit_type?: string; description?: string }
): Promise<EcosystemBenefit> => {
  const response = await api.put(`/admin/ecosystem-benefits/${benefitId}`, data);
  return response.data;
};

export const deleteEcosystemBenefit = async (benefitId: string): Promise<void> => {
  await api.delete(`/admin/ecosystem-benefits/${benefitId}`);
};

// Cards (for dropdown)
export const getCards = async (params?: {
  search?: string;
  bank_code?: string;
}): Promise<CardSimple[]> => {
  const response = await api.get('/admin/cards', { params });
  return response.data;
};

// Banks
export const getBanks = async (): Promise<BankSimple[]> => {
  const response = await api.get('/admin/banks');
  return response.data;
};

// Cards CRUD
export const getAllCards = async (params?: {
  search?: string;
  bank_id?: string;
  include_inactive?: boolean;
}): Promise<CardFull[]> => {
  const response = await api.get('/admin/cards/all', { params });
  return response.data;
};

export const getCard = async (cardId: string): Promise<CardFull> => {
  const response = await api.get(`/admin/cards/${cardId}`);
  return response.data;
};

export const createCard = async (data: {
  bank_id: string;
  name: string;
  card_type?: string;
  card_network?: string;
  annual_fee?: number;
  reward_type?: string;
  base_reward_rate?: number;
  terms_url?: string;
}): Promise<CardFull> => {
  const response = await api.post('/admin/cards/new', data);
  return response.data;
};

export const updateCard = async (
  cardId: string,
  data: {
    name?: string;
    card_type?: string;
    card_network?: string;
    annual_fee?: number;
    reward_type?: string;
    base_reward_rate?: number;
    terms_url?: string;
    is_active?: boolean;
  }
): Promise<CardFull> => {
  const response = await api.put(`/admin/cards/${cardId}`, data);
  return response.data;
};

export const deleteCard = async (cardId: string): Promise<void> => {
  await api.delete(`/admin/cards/${cardId}`);
};

// Scraper
export const runScraper = async (bank?: string): Promise<{ message: string }> => {
  const response = await api.post('/admin/scraper/run', null, {
    params: bank ? { bank } : undefined,
  });
  return response.data;
};

export const getScraperStatus = async (): Promise<ScraperStatus> => {
  const response = await api.get('/admin/scraper/status');
  return response.data;
};

// Pending Changes
export const getPendingChanges = async (status?: string): Promise<PendingChange[]> => {
  const response = await api.get('/admin/pending', {
    params: status ? { status } : undefined,
  });
  return response.data;
};

export const updatePendingChange = async (
  changeId: string,
  data: { benefit_rate?: number; benefit_type?: string; description?: string }
): Promise<PendingChange> => {
  const response = await api.put(`/admin/pending/${changeId}`, data);
  return response.data;
};

export const approvePendingChange = async (
  changeId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending/${changeId}/approve`);
  return response.data;
};

export const rejectPendingChange = async (
  changeId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending/${changeId}/reject`);
  return response.data;
};

export const deletePendingChange = async (changeId: string): Promise<void> => {
  await api.delete(`/admin/pending/${changeId}`);
};

export const approveAllPending = async (): Promise<{
  message: string;
  approved: number;
  failed: number;
}> => {
  const response = await api.post('/admin/pending/approve-all');
  return response.data;
};

// Pending Brands
export const getPendingBrands = async (status?: string): Promise<PendingBrand[]> => {
  const response = await api.get('/admin/pending-brands', {
    params: status ? { status } : undefined,
  });
  return response.data;
};

export const updatePendingBrand = async (
  brandId: string,
  data: { name?: string; code?: string; description?: string; keywords?: string[] }
): Promise<PendingBrand> => {
  const response = await api.put(`/admin/pending-brands/${brandId}`, data);
  return response.data;
};

export const approvePendingBrand = async (
  brandId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-brands/${brandId}/approve`);
  return response.data;
};

export const rejectPendingBrand = async (
  brandId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-brands/${brandId}/reject`);
  return response.data;
};

export const deletePendingBrand = async (brandId: string): Promise<void> => {
  await api.delete(`/admin/pending-brands/${brandId}`);
};

// Pending Cards
export const getPendingCards = async (status?: string): Promise<PendingCard[]> => {
  const response = await api.get('/admin/pending-cards', {
    params: status ? { status_filter: status } : undefined,
  });
  return response.data;
};

export const updatePendingCard = async (
  cardId: string,
  data: {
    name?: string;
    card_type?: string;
    card_network?: string;
    annual_fee?: number;
    reward_type?: string;
    base_reward_rate?: number;
    terms_url?: string;
  }
): Promise<PendingCard> => {
  const response = await api.put(`/admin/pending-cards/${cardId}`, data);
  return response.data;
};

export const approvePendingCard = async (
  cardId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-cards/${cardId}/approve`);
  return response.data;
};

export const rejectPendingCard = async (
  cardId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-cards/${cardId}/reject`);
  return response.data;
};

export const deletePendingCard = async (cardId: string): Promise<void> => {
  await api.delete(`/admin/pending-cards/${cardId}`);
};

// Campaigns
export const getCampaigns = async (params?: {
  brand_id?: string;
  card_id?: string;
  active_only?: boolean;
}): Promise<Campaign[]> => {
  const response = await api.get('/admin/campaigns', { params });
  return response.data;
};

export const createCampaign = async (data: {
  card_id: string;
  brand_id: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
  terms_url?: string;
  start_date: string;
  end_date: string;
}): Promise<Campaign> => {
  const response = await api.post('/admin/campaigns', data);
  return response.data;
};

export const updateCampaign = async (
  campaignId: string,
  data: {
    benefit_rate?: number;
    benefit_type?: string;
    description?: string;
    terms_url?: string;
    start_date?: string;
    end_date?: string;
    is_active?: boolean;
  }
): Promise<Campaign> => {
  const response = await api.put(`/admin/campaigns/${campaignId}`, data);
  return response.data;
};

export const deleteCampaign = async (campaignId: string): Promise<void> => {
  await api.delete(`/admin/campaigns/${campaignId}`);
};

// Pending Campaigns
export const getPendingCampaigns = async (status?: string): Promise<PendingCampaign[]> => {
  const response = await api.get('/admin/pending-campaigns', {
    params: status ? { status_filter: status } : undefined,
  });
  return response.data;
};

export const createPendingCampaign = async (data: {
  card_id: string;
  brand_id: string;
  benefit_rate: number;
  benefit_type: string;
  description?: string;
  terms_url?: string;
  start_date: string;
  end_date: string;
  source_url?: string;
}): Promise<PendingCampaign> => {
  const response = await api.post('/admin/pending-campaigns', data);
  return response.data;
};

export const updatePendingCampaign = async (
  campaignId: string,
  data: {
    benefit_rate?: number;
    benefit_type?: string;
    description?: string;
    terms_url?: string;
    start_date?: string;
    end_date?: string;
  }
): Promise<PendingCampaign> => {
  const response = await api.put(`/admin/pending-campaigns/${campaignId}`, data);
  return response.data;
};

export const approvePendingCampaign = async (
  campaignId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-campaigns/${campaignId}/approve`);
  return response.data;
};

export const rejectPendingCampaign = async (
  campaignId: string
): Promise<{ message: string }> => {
  const response = await api.post(`/admin/pending-campaigns/${campaignId}/reject`);
  return response.data;
};

export const deletePendingCampaign = async (campaignId: string): Promise<void> => {
  await api.delete(`/admin/pending-campaigns/${campaignId}`);
};

// Duplicate Cards
export const findDuplicateCards = async (): Promise<DuplicateCardsResponse> => {
  const response = await api.get('/admin/cards/duplicates');
  return response.data;
};

export const mergeCards = async (
  keepCardId: string,
  duplicateCardIds: string[]
): Promise<{ message: string }> => {
  const response = await api.post('/admin/cards/merge', {
    keep_card_id: keepCardId,
    duplicate_card_ids: duplicateCardIds,
  });
  return response.data;
};

export const autoDedupeCards = async (): Promise<{
  message: string;
  groups_processed: number;
  cards_merged: number;
}> => {
  const response = await api.post('/admin/cards/auto-dedupe');
  return response.data;
};

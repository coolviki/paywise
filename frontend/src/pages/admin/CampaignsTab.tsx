import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, X, Calendar } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { Campaign, BrandListItem, CardSimple } from '../../types';
import * as adminService from '../../services/adminService';

export function CampaignsTab() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'upcoming' | 'expired'>('all');

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getCampaigns();
      setCampaigns(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load campaigns');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (campaignId: string) => {
    if (!confirm('Are you sure you want to delete this campaign?')) return;
    try {
      await adminService.deleteCampaign(campaignId);
      setCampaigns(campaigns.filter((c) => c.id !== campaignId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete campaign');
    }
  };

  const getCampaignStatus = (campaign: Campaign): 'active' | 'upcoming' | 'expired' => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const startDate = new Date(campaign.start_date);
    const endDate = new Date(campaign.end_date);

    if (!campaign.is_active || endDate < today) {
      return 'expired';
    }
    if (startDate > today) {
      return 'upcoming';
    }
    return 'active';
  };

  const getStatusBadge = (status: 'active' | 'upcoming' | 'expired') => {
    switch (status) {
      case 'active':
        return (
          <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-xs font-medium">
            Active
          </span>
        );
      case 'upcoming':
        return (
          <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
            Upcoming
          </span>
        );
      case 'expired':
        return (
          <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded text-xs font-medium">
            Expired
          </span>
        );
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const filteredCampaigns = campaigns.filter((campaign) => {
    if (filterStatus === 'all') return true;
    return getCampaignStatus(campaign) === filterStatus;
  });

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading campaigns...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Campaigns ({filteredCampaigns.length})
          </h2>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="upcoming">Upcoming</option>
            <option value="expired">Expired</option>
          </select>
        </div>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Campaign
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              <th className="pb-3 font-medium">Card</th>
              <th className="pb-3 font-medium">Brand</th>
              <th className="pb-3 font-medium">Rate</th>
              <th className="pb-3 font-medium">Type</th>
              <th className="pb-3 font-medium">Date Range</th>
              <th className="pb-3 font-medium">Status</th>
              <th className="pb-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredCampaigns.map((campaign) => {
              const status = getCampaignStatus(campaign);
              return (
                <tr key={campaign.id} className="text-sm">
                  <td className="py-3">
                    <div>
                      <span className="text-gray-900 dark:text-white">{campaign.card_name}</span>
                      <span className="block text-xs text-gray-500 dark:text-gray-400">
                        {campaign.bank_name}
                      </span>
                    </div>
                  </td>
                  <td className="py-3">
                    <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded text-xs font-medium">
                      {campaign.brand_name}
                    </span>
                  </td>
                  <td className="py-3 font-semibold text-green-600 dark:text-green-400">
                    {campaign.benefit_rate}%
                  </td>
                  <td className="py-3 text-gray-600 dark:text-gray-300">{campaign.benefit_type}</td>
                  <td className="py-3">
                    <div className="flex items-center gap-1 text-gray-600 dark:text-gray-300">
                      <Calendar className="w-3 h-3" />
                      <span className="text-xs">
                        {formatDate(campaign.start_date)} - {formatDate(campaign.end_date)}
                      </span>
                    </div>
                  </td>
                  <td className="py-3">{getStatusBadge(status)}</td>
                  <td className="py-3">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEditingCampaign(campaign)}
                        className="p-1 text-gray-400 hover:text-primary-600"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(campaign.id)}
                        className="p-1 text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {filteredCampaigns.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          {filterStatus === 'all'
            ? 'No campaigns found. Add one to get started.'
            : `No ${filterStatus} campaigns found.`}
        </div>
      )}

      {showAddModal && (
        <AddCampaignModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadCampaigns();
          }}
        />
      )}

      {editingCampaign && (
        <EditCampaignModal
          campaign={editingCampaign}
          onClose={() => setEditingCampaign(null)}
          onSuccess={() => {
            setEditingCampaign(null);
            loadCampaigns();
          }}
        />
      )}
    </div>
  );
}

function AddCampaignModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [brands, setBrands] = useState<BrandListItem[]>([]);
  const [cards, setCards] = useState<CardSimple[]>([]);
  const [cardSearch, setCardSearch] = useState('');
  const [selectedCard, setSelectedCard] = useState<CardSimple | null>(null);
  const [brandId, setBrandId] = useState('');
  const [benefitRate, setBenefitRate] = useState('');
  const [benefitType, setBenefitType] = useState('cashback');
  const [description, setDescription] = useState('');
  const [termsUrl, setTermsUrl] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBrands();
  }, []);

  useEffect(() => {
    if (cardSearch.length >= 2) {
      searchCards();
    } else {
      setCards([]);
    }
  }, [cardSearch]);

  const loadBrands = async () => {
    try {
      const data = await adminService.getBrands();
      setBrands(data);
    } catch (err) {
      console.error('Failed to load brands:', err);
    }
  };

  const searchCards = async () => {
    try {
      const data = await adminService.getCards({ search: cardSearch });
      setCards(data);
    } catch (err) {
      console.error('Failed to search cards:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCard) {
      setError('Please select a card');
      return;
    }
    if (!startDate || !endDate) {
      setError('Please select start and end dates');
      return;
    }
    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      await adminService.createCampaign({
        card_id: selectedCard.id,
        brand_id: brandId,
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
        terms_url: termsUrl || undefined,
        start_date: startDate,
        end_date: endDate,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create campaign');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add Campaign
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Card
            </label>
            {selectedCard ? (
              <div className="flex items-center justify-between px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700">
                <span className="text-gray-900 dark:text-white">{selectedCard.name}</span>
                <button
                  type="button"
                  onClick={() => setSelectedCard(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="relative">
                <input
                  type="text"
                  value={cardSearch}
                  onChange={(e) => setCardSearch(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Search for a card..."
                />
                {cards.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-48 overflow-y-auto">
                    {cards.map((card) => (
                      <button
                        key={card.id}
                        type="button"
                        onClick={() => {
                          setSelectedCard(card);
                          setCardSearch('');
                          setCards([]);
                        }}
                        className="w-full px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-600 text-sm"
                      >
                        <span className="text-gray-900 dark:text-white">{card.name}</span>
                        <span className="text-gray-500 dark:text-gray-400 ml-2">
                          ({card.bank_name})
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Brand
            </label>
            <select
              value={brandId}
              onChange={(e) => setBrandId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            >
              <option value="">Select brand...</option>
              {brands.map((brand) => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benefit Rate (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={benefitRate}
                onChange={(e) => setBenefitRate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="10.0"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benefit Type
              </label>
              <select
                value={benefitType}
                onChange={(e) => setBenefitType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="cashback">Cashback</option>
                <option value="points">Points</option>
                <option value="miles">Miles</option>
                <option value="neucoins">NeuCoins</option>
                <option value="discount">Discount</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., 10% cashback on all purchases"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Terms URL
            </label>
            <input
              type="url"
              value={termsUrl}
              onChange={(e) => setTermsUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="https://..."
            />
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" isLoading={isLoading} className="flex-1">
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function EditCampaignModal({
  campaign,
  onClose,
  onSuccess,
}: {
  campaign: Campaign;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [benefitRate, setBenefitRate] = useState(campaign.benefit_rate.toString());
  const [benefitType, setBenefitType] = useState(campaign.benefit_type);
  const [description, setDescription] = useState(campaign.description || '');
  const [termsUrl, setTermsUrl] = useState(campaign.terms_url || '');
  const [startDate, setStartDate] = useState(campaign.start_date);
  const [endDate, setEndDate] = useState(campaign.end_date);
  const [isActive, setIsActive] = useState(campaign.is_active);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (new Date(startDate) > new Date(endDate)) {
      setError('Start date must be before end date');
      return;
    }
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updateCampaign(campaign.id, {
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
        terms_url: termsUrl || undefined,
        start_date: startDate,
        end_date: endDate,
        is_active: isActive,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update campaign');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Campaign
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>{campaign.card_name}</strong> ({campaign.bank_name})
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Brand: {campaign.brand_name}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benefit Rate (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={benefitRate}
                onChange={(e) => setBenefitRate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Benefit Type
              </label>
              <select
                value={benefitType}
                onChange={(e) => setBenefitType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="cashback">Cashback</option>
                <option value="points">Points</option>
                <option value="miles">Miles</option>
                <option value="neucoins">NeuCoins</option>
                <option value="discount">Discount</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Terms URL
            </label>
            <input
              type="url"
              value={termsUrl}
              onChange={(e) => setTermsUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="https://..."
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded border-gray-300"
            />
            <label htmlFor="is_active" className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Active
            </label>
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}

          <div className="flex gap-3 pt-2">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
            <Button type="submit" isLoading={isLoading} className="flex-1">
              Update
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

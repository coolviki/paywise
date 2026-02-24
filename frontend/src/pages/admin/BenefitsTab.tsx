import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, X } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { EcosystemBenefit, BrandListItem, CardSimple } from '../../types';
import * as adminService from '../../services/adminService';

export function BenefitsTab() {
  const [benefits, setBenefits] = useState<EcosystemBenefit[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingBenefit, setEditingBenefit] = useState<EcosystemBenefit | null>(null);

  useEffect(() => {
    loadBenefits();
  }, []);

  const loadBenefits = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getEcosystemBenefits();
      setBenefits(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load benefits');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (benefitId: string) => {
    if (!confirm('Are you sure you want to delete this ecosystem benefit?')) return;
    try {
      await adminService.deleteEcosystemBenefit(benefitId);
      setBenefits(benefits.filter((b) => b.id !== benefitId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete benefit');
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading benefits...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Ecosystem Benefits ({benefits.length})
        </h2>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Benefit
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-500 dark:text-gray-400 border-b border-gray-200 dark:border-gray-700">
              <th className="pb-3 font-medium">Card</th>
              <th className="pb-3 font-medium">Bank</th>
              <th className="pb-3 font-medium">Brand</th>
              <th className="pb-3 font-medium">Rate</th>
              <th className="pb-3 font-medium">Type</th>
              <th className="pb-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {benefits.map((benefit) => (
              <tr key={benefit.id} className="text-sm">
                <td className="py-3 text-gray-900 dark:text-white">{benefit.card_name}</td>
                <td className="py-3 text-gray-600 dark:text-gray-300">{benefit.bank_name}</td>
                <td className="py-3">
                  <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded text-xs font-medium">
                    {benefit.brand_name}
                  </span>
                </td>
                <td className="py-3 font-semibold text-green-600 dark:text-green-400">
                  {benefit.benefit_rate}%
                </td>
                <td className="py-3 text-gray-600 dark:text-gray-300">{benefit.benefit_type}</td>
                <td className="py-3">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setEditingBenefit(benefit)}
                      className="p-1 text-gray-400 hover:text-primary-600"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(benefit.id)}
                      className="p-1 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {benefits.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No ecosystem benefits found. Add one to get started.
        </div>
      )}

      {showAddModal && (
        <AddBenefitModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadBenefits();
          }}
        />
      )}

      {editingBenefit && (
        <EditBenefitModal
          benefit={editingBenefit}
          onClose={() => setEditingBenefit(null)}
          onSuccess={() => {
            setEditingBenefit(null);
            loadBenefits();
          }}
        />
      )}
    </div>
  );
}

function AddBenefitModal({
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
    setIsLoading(true);
    setError(null);

    try {
      await adminService.createEcosystemBenefit({
        card_id: selectedCard.id,
        brand_id: brandId,
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create benefit');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Add Ecosystem Benefit
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
                placeholder="5.0"
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

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., 5% cashback on all purchases"
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

function EditBenefitModal({
  benefit,
  onClose,
  onSuccess,
}: {
  benefit: EcosystemBenefit;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [benefitRate, setBenefitRate] = useState(benefit.benefit_rate.toString());
  const [benefitType, setBenefitType] = useState(benefit.benefit_type);
  const [description, setDescription] = useState(benefit.description || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updateEcosystemBenefit(benefit.id, {
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update benefit');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Ecosystem Benefit
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>{benefit.card_name}</strong> ({benefit.bank_name})
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Brand: {benefit.brand_name}
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

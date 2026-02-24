import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit2, Trash2, CreditCard, X, Check, ExternalLink } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { CardFull, BankSimple } from '../../types';
import * as adminService from '../../services/adminService';

export function CardsTab() {
  const [cards, setCards] = useState<CardFull[]>([]);
  const [banks, setBanks] = useState<BankSimple[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBank, setSelectedBank] = useState<string>('');
  const [showInactive, setShowInactive] = useState(false);
  const [editingCard, setEditingCard] = useState<CardFull | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [newCard, setNewCard] = useState({
    bank_id: '',
    name: '',
    card_type: 'credit',
    card_network: '',
    annual_fee: '',
    reward_type: 'points',
    base_reward_rate: '',
    terms_url: '',
  });

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadCards();
  }, [searchQuery, selectedBank, showInactive]);

  const loadData = async () => {
    try {
      const [cardsData, banksData] = await Promise.all([
        adminService.getAllCards({ include_inactive: showInactive }),
        adminService.getBanks(),
      ]);
      setCards(cardsData);
      setBanks(banksData);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCards = async () => {
    try {
      const data = await adminService.getAllCards({
        search: searchQuery || undefined,
        bank_id: selectedBank || undefined,
        include_inactive: showInactive,
      });
      setCards(data);
    } catch (err) {
      console.error('Failed to load cards:', err);
    }
  };

  const handleCreate = async () => {
    if (!newCard.bank_id || !newCard.name) {
      alert('Bank and card name are required');
      return;
    }

    try {
      await adminService.createCard({
        bank_id: newCard.bank_id,
        name: newCard.name,
        card_type: newCard.card_type,
        card_network: newCard.card_network || undefined,
        annual_fee: newCard.annual_fee ? parseFloat(newCard.annual_fee) : undefined,
        reward_type: newCard.reward_type || undefined,
        base_reward_rate: newCard.base_reward_rate ? parseFloat(newCard.base_reward_rate) : undefined,
        terms_url: newCard.terms_url || undefined,
      });
      setIsCreating(false);
      setNewCard({
        bank_id: '',
        name: '',
        card_type: 'credit',
        card_network: '',
        annual_fee: '',
        reward_type: 'points',
        base_reward_rate: '',
        terms_url: '',
      });
      loadCards();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create card');
    }
  };

  const handleUpdate = async () => {
    if (!editingCard) return;

    try {
      await adminService.updateCard(editingCard.id, {
        name: editingCard.name,
        card_type: editingCard.card_type,
        card_network: editingCard.card_network || undefined,
        annual_fee: editingCard.annual_fee,
        reward_type: editingCard.reward_type || undefined,
        base_reward_rate: editingCard.base_reward_rate,
        terms_url: editingCard.terms_url || undefined,
        is_active: editingCard.is_active,
      });
      setEditingCard(null);
      loadCards();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update card');
    }
  };

  const handleDelete = async (cardId: string, cardName: string) => {
    if (!confirm(`Are you sure you want to deactivate "${cardName}"?`)) return;

    try {
      await adminService.deleteCard(cardId);
      loadCards();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete card');
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading cards...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3">
          <CreditCard className="w-6 h-6 text-primary-600" />
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Cards Inventory
            </h2>
            <p className="text-sm text-gray-500">{cards.length} cards</p>
          </div>
        </div>
        <Button
          onClick={() => setIsCreating(true)}
          leftIcon={<Plus className="w-4 h-4" />}
        >
          Add Card
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search cards..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
            />
          </div>
          <select
            value={selectedBank}
            onChange={(e) => setSelectedBank(e.target.value)}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
          >
            <option value="">All Banks</option>
            {banks.map((bank) => (
              <option key={bank.id} value={bank.id}>{bank.name}</option>
            ))}
          </select>
          <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded border-gray-300"
            />
            Show Inactive
          </label>
        </div>
      </Card>

      {/* Create Card Form */}
      {isCreating && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Add New Card</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Bank *</label>
              <select
                value={newCard.bank_id}
                onChange={(e) => setNewCard({ ...newCard, bank_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">Select Bank</option>
                {banks.map((bank) => (
                  <option key={bank.id} value={bank.id}>{bank.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Card Name *</label>
              <input
                type="text"
                value={newCard.name}
                onChange={(e) => setNewCard({ ...newCard, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="e.g., Platinum Rewards"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Card Type</label>
              <select
                value={newCard.card_type}
                onChange={(e) => setNewCard({ ...newCard, card_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="credit">Credit</option>
                <option value="debit">Debit</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Network</label>
              <select
                value={newCard.card_network}
                onChange={(e) => setNewCard({ ...newCard, card_network: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">Select Network</option>
                <option value="visa">Visa</option>
                <option value="mastercard">Mastercard</option>
                <option value="rupay">RuPay</option>
                <option value="amex">American Express</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Annual Fee (₹)</label>
              <input
                type="number"
                value={newCard.annual_fee}
                onChange={(e) => setNewCard({ ...newCard, annual_fee: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="0"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Reward Type</label>
              <select
                value={newCard.reward_type}
                onChange={(e) => setNewCard({ ...newCard, reward_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">None</option>
                <option value="points">Points</option>
                <option value="cashback">Cashback</option>
                <option value="miles">Miles</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Base Reward Rate (%)</label>
              <input
                type="number"
                step="0.01"
                value={newCard.base_reward_rate}
                onChange={(e) => setNewCard({ ...newCard, base_reward_rate: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="1.0"
              />
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium mb-1">Terms & Conditions URL</label>
              <input
                type="url"
                value={newCard.terms_url}
                onChange={(e) => setNewCard({ ...newCard, terms_url: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="https://bank.com/card-terms"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <Button onClick={handleCreate}>Create Card</Button>
            <Button variant="ghost" onClick={() => setIsCreating(false)}>Cancel</Button>
          </div>
        </Card>
      )}

      {/* Cards Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Card Name</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Bank</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Network</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Base Rate</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Annual Fee</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {cards.map((card) => (
                <tr key={card.id} className={!card.is_active ? 'opacity-50' : ''}>
                  {editingCard?.id === card.id ? (
                    // Edit mode
                    <>
                      <td className="px-4 py-3">
                        <input
                          type="text"
                          value={editingCard.name}
                          onChange={(e) => setEditingCard({ ...editingCard, name: e.target.value })}
                          className="w-full px-2 py-1 border rounded mb-1"
                        />
                        <input
                          type="url"
                          value={editingCard.terms_url || ''}
                          onChange={(e) => setEditingCard({ ...editingCard, terms_url: e.target.value })}
                          className="w-full px-2 py-1 border rounded text-xs"
                          placeholder="Terms URL"
                        />
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{card.bank_name}</td>
                      <td className="px-4 py-3">
                        <select
                          value={editingCard.card_type}
                          onChange={(e) => setEditingCard({ ...editingCard, card_type: e.target.value })}
                          className="px-2 py-1 border rounded"
                        >
                          <option value="credit">Credit</option>
                          <option value="debit">Debit</option>
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <select
                          value={editingCard.card_network || ''}
                          onChange={(e) => setEditingCard({ ...editingCard, card_network: e.target.value })}
                          className="px-2 py-1 border rounded"
                        >
                          <option value="">-</option>
                          <option value="visa">Visa</option>
                          <option value="mastercard">Mastercard</option>
                          <option value="rupay">RuPay</option>
                          <option value="amex">Amex</option>
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          step="0.01"
                          value={editingCard.base_reward_rate || ''}
                          onChange={(e) => setEditingCard({ ...editingCard, base_reward_rate: parseFloat(e.target.value) || 0 })}
                          className="w-20 px-2 py-1 border rounded"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <input
                          type="number"
                          value={editingCard.annual_fee || ''}
                          onChange={(e) => setEditingCard({ ...editingCard, annual_fee: parseFloat(e.target.value) || 0 })}
                          className="w-24 px-2 py-1 border rounded"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <label className="flex items-center gap-1">
                          <input
                            type="checkbox"
                            checked={editingCard.is_active}
                            onChange={(e) => setEditingCard({ ...editingCard, is_active: e.target.checked })}
                          />
                          Active
                        </label>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={handleUpdate}
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setEditingCard(null)}
                            className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </>
                  ) : (
                    // View mode
                    <>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900 dark:text-white">{card.name}</span>
                          {card.terms_url && (
                            <a
                              href={card.terms_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary-600 hover:text-primary-700"
                              title="View Terms & Conditions"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{card.bank_name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 capitalize">{card.card_type}</td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 capitalize">{card.card_network || '-'}</td>
                      <td className="px-4 py-3 text-sm">
                        {card.base_reward_rate ? (
                          <span className="text-primary-600 font-medium">{card.base_reward_rate}% {card.reward_type}</span>
                        ) : '-'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {card.annual_fee ? `₹${card.annual_fee.toLocaleString()}` : 'Free'}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          card.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-gray-100 text-gray-600'
                        }`}>
                          {card.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => setEditingCard(card)}
                            className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                            title="Edit"
                          >
                            <Edit2 className="w-4 h-4" />
                          </button>
                          {card.is_active && (
                            <button
                              onClick={() => handleDelete(card.id, card.name)}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                              title="Deactivate"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {cards.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No cards found
          </div>
        )}
      </Card>
    </div>
  );
}

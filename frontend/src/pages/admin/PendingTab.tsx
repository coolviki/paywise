import React, { useState, useEffect } from 'react';
import { Check, X, Pencil, Trash2, CheckCircle, XCircle, AlertCircle, ExternalLink, Tag, CreditCard, Wallet, Calendar } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { PendingChange, PendingBrand, PendingCard as PendingCardType, PendingCampaign } from '../../types';
import * as adminService from '../../services/adminService';

type TabType = 'benefits' | 'brands' | 'cards' | 'campaigns';

export function PendingTab() {
  const [activeTab, setActiveTab] = useState<TabType>('benefits');
  const [changes, setChanges] = useState<PendingChange[]>([]);
  const [brands, setBrands] = useState<PendingBrand[]>([]);
  const [cards, setCards] = useState<PendingCardType[]>([]);
  const [campaigns, setCampaigns] = useState<PendingCampaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [editingChange, setEditingChange] = useState<PendingChange | null>(null);
  const [editingBrand, setEditingBrand] = useState<PendingBrand | null>(null);
  const [editingCard, setEditingCard] = useState<PendingCardType | null>(null);
  const [editingCampaign, setEditingCampaign] = useState<PendingCampaign | null>(null);

  useEffect(() => {
    loadData();
  }, [statusFilter, activeTab]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      if (activeTab === 'benefits') {
        const data = await adminService.getPendingChanges(statusFilter || undefined);
        setChanges(data);
      } else if (activeTab === 'brands') {
        const data = await adminService.getPendingBrands(statusFilter || undefined);
        setBrands(data);
      } else if (activeTab === 'cards') {
        const data = await adminService.getPendingCards(statusFilter || undefined);
        setCards(data);
      } else {
        const data = await adminService.getPendingCampaigns(statusFilter || undefined);
        setCampaigns(data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load pending items');
    } finally {
      setIsLoading(false);
    }
  };

  // Benefits handlers
  const handleApproveBenefit = async (changeId: string) => {
    try {
      await adminService.approvePendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve change');
    }
  };

  const handleRejectBenefit = async (changeId: string) => {
    try {
      await adminService.rejectPendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject change');
    }
  };

  const handleDeleteBenefit = async (changeId: string) => {
    if (!confirm('Are you sure you want to delete this pending change?')) return;
    try {
      await adminService.deletePendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete change');
    }
  };

  const handleApproveAllBenefits = async () => {
    if (!confirm(`Are you sure you want to approve all ${changes.length} pending changes?`)) return;
    try {
      const result = await adminService.approveAllPending();
      alert(`Approved: ${result.approved}, Failed: ${result.failed}`);
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve all changes');
    }
  };

  // Brands handlers
  const handleApproveBrand = async (brandId: string) => {
    try {
      await adminService.approvePendingBrand(brandId);
      setBrands(brands.filter((b) => b.id !== brandId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve brand');
    }
  };

  const handleRejectBrand = async (brandId: string) => {
    try {
      await adminService.rejectPendingBrand(brandId);
      setBrands(brands.filter((b) => b.id !== brandId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject brand');
    }
  };

  const handleDeleteBrand = async (brandId: string) => {
    if (!confirm('Are you sure you want to delete this pending brand?')) return;
    try {
      await adminService.deletePendingBrand(brandId);
      setBrands(brands.filter((b) => b.id !== brandId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete brand');
    }
  };

  // Cards handlers
  const handleApproveCard = async (cardId: string) => {
    try {
      await adminService.approvePendingCard(cardId);
      setCards(cards.filter((c) => c.id !== cardId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve card');
    }
  };

  const handleRejectCard = async (cardId: string) => {
    try {
      await adminService.rejectPendingCard(cardId);
      setCards(cards.filter((c) => c.id !== cardId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject card');
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    if (!confirm('Are you sure you want to delete this pending card?')) return;
    try {
      await adminService.deletePendingCard(cardId);
      setCards(cards.filter((c) => c.id !== cardId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete card');
    }
  };

  // Campaigns handlers
  const handleApproveCampaign = async (campaignId: string) => {
    try {
      await adminService.approvePendingCampaign(campaignId);
      setCampaigns(campaigns.filter((c) => c.id !== campaignId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve campaign');
    }
  };

  const handleRejectCampaign = async (campaignId: string) => {
    try {
      await adminService.rejectPendingCampaign(campaignId);
      setCampaigns(campaigns.filter((c) => c.id !== campaignId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject campaign');
    }
  };

  const handleDeleteCampaign = async (campaignId: string) => {
    if (!confirm('Are you sure you want to delete this pending campaign?')) return;
    try {
      await adminService.deletePendingCampaign(campaignId);
      setCampaigns(campaigns.filter((c) => c.id !== campaignId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete campaign');
    }
  };

  const getChangeTypeBadge = (type: string) => {
    switch (type) {
      case 'new':
        return (
          <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-xs font-medium">
            New
          </span>
        );
      case 'update':
        return (
          <span className="px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300 rounded text-xs font-medium">
            Update
          </span>
        );
      case 'delete':
        return (
          <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded text-xs font-medium">
            Delete
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'pending':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
            <AlertCircle className="w-3 h-3" /> Pending
          </span>
        );
      case 'approved':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded text-xs font-medium">
            <CheckCircle className="w-3 h-3" /> Approved
          </span>
        );
      case 'rejected':
        return (
          <span className="flex items-center gap-1 px-2 py-0.5 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded text-xs font-medium">
            <XCircle className="w-3 h-3" /> Rejected
          </span>
        );
      default:
        return null;
    }
  };

  const pendingBenefitsCount = changes.filter((c) => c.status === 'pending').length;
  const pendingBrandsCount = brands.filter((b) => b.status === 'pending').length;
  const pendingCardsCount = cards.filter((c) => c.status === 'pending').length;
  const pendingCampaignsCount = campaigns.filter((c) => c.status === 'pending').length;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>;
  }

  return (
    <div>
      {/* Tab Switcher */}
      <div className="flex items-center gap-4 mb-6 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setActiveTab('benefits')}
          className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'benefits'
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          <CreditCard className="w-4 h-4" />
          Benefits
          {pendingBenefitsCount > 0 && (
            <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs">
              {pendingBenefitsCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('brands')}
          className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'brands'
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          <Tag className="w-4 h-4" />
          Brands
          {pendingBrandsCount > 0 && (
            <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs">
              {pendingBrandsCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('cards')}
          className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'cards'
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          <Wallet className="w-4 h-4" />
          Cards
          {pendingCardsCount > 0 && (
            <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs">
              {pendingCardsCount}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('campaigns')}
          className={`flex items-center gap-2 py-3 px-1 border-b-2 text-sm font-medium transition-colors ${
            activeTab === 'campaigns'
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          <Calendar className="w-4 h-4" />
          Campaigns
          {pendingCampaignsCount > 0 && (
            <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs">
              {pendingCampaignsCount}
            </span>
          )}
        </button>
      </div>

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Pending {activeTab === 'benefits' ? 'Benefits' : activeTab === 'brands' ? 'Brands' : activeTab === 'cards' ? 'Cards' : 'Campaigns'} ({activeTab === 'benefits' ? changes.length : activeTab === 'brands' ? brands.length : activeTab === 'cards' ? cards.length : campaigns.length})
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {activeTab === 'benefits'
              ? 'Review and approve scraped ecosystem benefit changes'
              : activeTab === 'brands'
              ? 'Review and approve new brands discovered by the scraper'
              : activeTab === 'cards'
              ? 'Review and approve new cards discovered by the scraper'
              : 'Review and approve time-limited promotional campaigns'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
          >
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
          {activeTab === 'benefits' && pendingBenefitsCount > 0 && (
            <Button onClick={handleApproveAllBenefits} leftIcon={<Check className="w-4 h-4" />}>
              Approve All ({pendingBenefitsCount})
            </Button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : activeTab === 'campaigns' ? (
        // Campaigns List
        campaigns.length === 0 ? (
          <Card className="p-12 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Pending Campaigns
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {statusFilter === 'pending'
                ? 'All campaign changes have been reviewed.'
                : `No ${statusFilter} campaigns found.`}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {campaigns.map((campaign) => (
              <Card key={campaign.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getChangeTypeBadge(campaign.change_type)}
                      {getStatusBadge(campaign.status)}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {campaign.card_name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Brand: {campaign.brand_name}
                    </p>

                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Rate</p>
                        <p className="font-semibold text-green-600 dark:text-green-400">
                          {campaign.benefit_rate}% {campaign.benefit_type}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Start Date</p>
                        <p className="font-medium">{formatDate(campaign.start_date)}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">End Date</p>
                        <p className="font-medium">{formatDate(campaign.end_date)}</p>
                      </div>
                    </div>

                    {campaign.description && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        {campaign.description}
                      </p>
                    )}

                    {campaign.source_url && (
                      <a
                        href={campaign.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View Source
                      </a>
                    )}

                    <p className="mt-2 text-xs text-gray-400">
                      Discovered: {new Date(campaign.scraped_at).toLocaleString()}
                    </p>
                  </div>

                  {campaign.status === 'pending' && (
                    <div className="flex flex-col gap-2 ml-4">
                      <Button size="sm" onClick={() => handleApproveCampaign(campaign.id)} leftIcon={<Check className="w-4 h-4" />}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleRejectCampaign(campaign.id)} leftIcon={<X className="w-4 h-4" />}>
                        Reject
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingCampaign(campaign)} leftIcon={<Pencil className="w-4 h-4" />}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={() => handleDeleteCampaign(campaign.id)} leftIcon={<Trash2 className="w-4 h-4" />}>
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )
      ) : activeTab === 'cards' ? (
        // Cards List
        cards.length === 0 ? (
          <Card className="p-12 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Pending Cards
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {statusFilter === 'pending'
                ? 'All card changes have been reviewed. Run the scraper to discover new cards.'
                : `No ${statusFilter} cards found.`}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {cards.map((card) => (
              <Card key={card.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getChangeTypeBadge(card.change_type)}
                      {getStatusBadge(card.status)}
                      {card.source_bank && (
                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs">
                          from {card.source_bank.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {card.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Bank: {card.bank_name}
                    </p>

                    <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Type</p>
                        <p className="font-medium capitalize">{card.card_type}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Network</p>
                        <p className="font-medium capitalize">{card.card_network || '-'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Annual Fee</p>
                        <p className="font-medium">{card.annual_fee ? `₹${card.annual_fee}` : '-'}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Base Rate</p>
                        <p className="font-medium">{card.base_reward_rate ? `${card.base_reward_rate}%` : '-'}</p>
                      </div>
                    </div>

                    {card.source_url && (
                      <a
                        href={card.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View Source
                      </a>
                    )}

                    <p className="mt-2 text-xs text-gray-400">
                      Discovered: {new Date(card.scraped_at).toLocaleString()}
                    </p>
                  </div>

                  {card.status === 'pending' && (
                    <div className="flex flex-col gap-2 ml-4">
                      <Button size="sm" onClick={() => handleApproveCard(card.id)} leftIcon={<Check className="w-4 h-4" />}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleRejectCard(card.id)} leftIcon={<X className="w-4 h-4" />}>
                        Reject
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingCard(card)} leftIcon={<Pencil className="w-4 h-4" />}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={() => handleDeleteCard(card.id)} leftIcon={<Trash2 className="w-4 h-4" />}>
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )
      ) : activeTab === 'benefits' ? (
        // Benefits List
        changes.length === 0 ? (
          <Card className="p-12 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Pending Benefits
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {statusFilter === 'pending'
                ? 'All benefit changes have been reviewed. Run the scraper to find new updates.'
                : `No ${statusFilter} changes found.`}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {changes.map((change) => (
              <Card key={change.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      {getChangeTypeBadge(change.change_type)}
                      {getStatusBadge(change.status)}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {change.card_name || 'Unknown Card'}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      Brand: {change.brand_name || 'Unknown'}
                    </p>

                    <div className="mt-3 grid grid-cols-2 gap-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div>
                        <p className="text-xs text-gray-500 dark:text-gray-400">New Value</p>
                        <p className="font-semibold text-green-600 dark:text-green-400">
                          {change.benefit_rate}% {change.benefit_type}
                        </p>
                      </div>
                      {change.old_values && (
                        <div>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Old Value</p>
                          <p className="font-semibold text-gray-500 dark:text-gray-400 line-through">
                            {change.old_values.benefit_rate}% {change.old_values.benefit_type}
                          </p>
                        </div>
                      )}
                    </div>

                    {change.description && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        {change.description}
                      </p>
                    )}

                    {change.source_url && (
                      <a
                        href={change.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View Source
                      </a>
                    )}

                    <p className="mt-2 text-xs text-gray-400">
                      Scraped: {new Date(change.scraped_at).toLocaleString()}
                    </p>
                  </div>

                  {change.status === 'pending' && (
                    <div className="flex flex-col gap-2 ml-4">
                      <Button size="sm" onClick={() => handleApproveBenefit(change.id)} leftIcon={<Check className="w-4 h-4" />}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleRejectBenefit(change.id)} leftIcon={<X className="w-4 h-4" />}>
                        Reject
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingChange(change)} leftIcon={<Pencil className="w-4 h-4" />}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={() => handleDeleteBenefit(change.id)} leftIcon={<Trash2 className="w-4 h-4" />}>
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )
      ) : (
        // Brands List
        brands.length === 0 ? (
          <Card className="p-12 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No Pending Brands
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              {statusFilter === 'pending'
                ? 'All brand changes have been reviewed. Run the scraper to discover new brands.'
                : `No ${statusFilter} brands found.`}
            </p>
          </Card>
        ) : (
          <div className="space-y-4">
            {brands.map((brand) => (
              <Card key={brand.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded text-xs font-medium">
                        New Brand
                      </span>
                      {getStatusBadge(brand.status)}
                      {brand.source_bank && (
                        <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded text-xs">
                          from {brand.source_bank.toUpperCase()}
                        </span>
                      )}
                    </div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {brand.name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">
                      Code: {brand.code}
                    </p>

                    {brand.description && (
                      <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                        {brand.description}
                      </p>
                    )}

                    {brand.keywords && brand.keywords.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        <span className="text-xs text-gray-500">Keywords:</span>
                        {brand.keywords.map((kw, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs"
                          >
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}

                    {brand.source_url && (
                      <a
                        href={brand.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-sm text-primary-600 hover:text-primary-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                        View Source
                      </a>
                    )}

                    <p className="mt-2 text-xs text-gray-400">
                      Discovered: {new Date(brand.scraped_at).toLocaleString()}
                    </p>
                  </div>

                  {brand.status === 'pending' && (
                    <div className="flex flex-col gap-2 ml-4">
                      <Button size="sm" onClick={() => handleApproveBrand(brand.id)} leftIcon={<Check className="w-4 h-4" />}>
                        Approve
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleRejectBrand(brand.id)} leftIcon={<X className="w-4 h-4" />}>
                        Reject
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setEditingBrand(brand)} leftIcon={<Pencil className="w-4 h-4" />}>
                        Edit
                      </Button>
                      <Button size="sm" variant="ghost" className="text-red-500 hover:text-red-600" onClick={() => handleDeleteBrand(brand.id)} leftIcon={<Trash2 className="w-4 h-4" />}>
                        Delete
                      </Button>
                    </div>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )
      )}

      {/* Edit Benefit Modal */}
      {editingChange && (
        <EditChangeModal
          change={editingChange}
          onClose={() => setEditingChange(null)}
          onSuccess={() => {
            setEditingChange(null);
            loadData();
          }}
        />
      )}

      {/* Edit Brand Modal */}
      {editingBrand && (
        <EditBrandModal
          brand={editingBrand}
          onClose={() => setEditingBrand(null)}
          onSuccess={() => {
            setEditingBrand(null);
            loadData();
          }}
        />
      )}

      {/* Edit Card Modal */}
      {editingCard && (
        <EditCardModal
          card={editingCard}
          onClose={() => setEditingCard(null)}
          onSuccess={() => {
            setEditingCard(null);
            loadData();
          }}
        />
      )}

      {/* Edit Campaign Modal */}
      {editingCampaign && (
        <EditCampaignModal
          campaign={editingCampaign}
          onClose={() => setEditingCampaign(null)}
          onSuccess={() => {
            setEditingCampaign(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}

function EditChangeModal({
  change,
  onClose,
  onSuccess,
}: {
  change: PendingChange;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [benefitRate, setBenefitRate] = useState(change.benefit_rate?.toString() || '');
  const [benefitType, setBenefitType] = useState(change.benefit_type || 'cashback');
  const [description, setDescription] = useState(change.description || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updatePendingChange(change.id, {
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update change');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Pending Change
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>{change.card_name}</strong>
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Brand: {change.brand_name}
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

function EditBrandModal({
  brand,
  onClose,
  onSuccess,
}: {
  brand: PendingBrand;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState(brand.name);
  const [code, setCode] = useState(brand.code);
  const [description, setDescription] = useState(brand.description || '');
  const [keywords, setKeywords] = useState(brand.keywords?.join(', ') || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updatePendingBrand(brand.id, {
        name,
        code,
        description: description || undefined,
        keywords: keywords.split(',').map((k) => k.trim().toLowerCase()).filter(Boolean),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update brand');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Pending Brand
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Code
            </label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono"
              required
            />
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
              Keywords (comma-separated)
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="e.g., swiggy, swiggy app"
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

function EditCardModal({
  card,
  onClose,
  onSuccess,
}: {
  card: PendingCardType;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState(card.name);
  const [cardType, setCardType] = useState(card.card_type);
  const [cardNetwork, setCardNetwork] = useState(card.card_network || '');
  const [annualFee, setAnnualFee] = useState(card.annual_fee?.toString() || '');
  const [rewardType, setRewardType] = useState(card.reward_type || '');
  const [baseRewardRate, setBaseRewardRate] = useState(card.base_reward_rate?.toString() || '');
  const [termsUrl, setTermsUrl] = useState(card.terms_url || '');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updatePendingCard(card.id, {
        name,
        card_type: cardType,
        card_network: cardNetwork || undefined,
        annual_fee: annualFee ? parseFloat(annualFee) : undefined,
        reward_type: rewardType || undefined,
        base_reward_rate: baseRewardRate ? parseFloat(baseRewardRate) : undefined,
        terms_url: termsUrl || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update card');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Pending Card
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            Bank: <strong>{card.bank_name}</strong>
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Card Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Card Type
              </label>
              <select
                value={cardType}
                onChange={(e) => setCardType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="credit">Credit</option>
                <option value="debit">Debit</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Network
              </label>
              <select
                value={cardNetwork}
                onChange={(e) => setCardNetwork(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Select Network</option>
                <option value="visa">Visa</option>
                <option value="mastercard">Mastercard</option>
                <option value="rupay">RuPay</option>
                <option value="amex">Amex</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Annual Fee (₹)
              </label>
              <input
                type="number"
                value={annualFee}
                onChange={(e) => setAnnualFee(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Reward Type
              </label>
              <select
                value={rewardType}
                onChange={(e) => setRewardType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">None</option>
                <option value="cashback">Cashback</option>
                <option value="points">Points</option>
                <option value="miles">Miles</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Base Reward Rate (%)
            </label>
            <input
              type="number"
              step="0.01"
              value={baseRewardRate}
              onChange={(e) => setBaseRewardRate(e.target.value)}
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

function EditCampaignModal({
  campaign,
  onClose,
  onSuccess,
}: {
  campaign: PendingCampaign;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [benefitRate, setBenefitRate] = useState(campaign.benefit_rate?.toString() || '');
  const [benefitType, setBenefitType] = useState(campaign.benefit_type || 'cashback');
  const [description, setDescription] = useState(campaign.description || '');
  const [termsUrl, setTermsUrl] = useState(campaign.terms_url || '');
  const [startDate, setStartDate] = useState(campaign.start_date || '');
  const [endDate, setEndDate] = useState(campaign.end_date || '');
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
      await adminService.updatePendingCampaign(campaign.id, {
        benefit_rate: parseFloat(benefitRate),
        benefit_type: benefitType,
        description: description || undefined,
        terms_url: termsUrl || undefined,
        start_date: startDate,
        end_date: endDate,
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
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Edit Pending Campaign
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            <strong>{campaign.card_name}</strong>
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

import React, { useState, useEffect } from 'react';
import { Bot, Play, RefreshCw, CheckCircle, XCircle, AlertCircle, Clock, Copy, Trash2, Merge } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { ScraperStatus, DuplicateCardsResponse } from '../../types';
import * as adminService from '../../services/adminService';

export function ScraperTab() {
  const [status, setStatus] = useState<ScraperStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [runningBank, setRunningBank] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateCardsResponse | null>(null);
  const [isLoadingDuplicates, setIsLoadingDuplicates] = useState(false);
  const [isDeduping, setIsDeduping] = useState(false);

  useEffect(() => {
    loadStatus();
    // Poll status every 3 seconds while scraper is running
    const interval = setInterval(() => {
      if (status?.is_running) {
        loadStatus();
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [status?.is_running]);

  const loadStatus = async () => {
    try {
      const data = await adminService.getScraperStatus();
      setStatus(data);
    } catch (err) {
      console.error('Failed to load scraper status:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunScraper = async (bank?: string) => {
    try {
      setRunningBank(bank || 'all');
      await adminService.runScraper(bank);
      // Start polling for status
      setTimeout(loadStatus, 1000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start scraper');
    } finally {
      setRunningBank(null);
    }
  };

  const loadDuplicates = async () => {
    setIsLoadingDuplicates(true);
    try {
      const data = await adminService.findDuplicateCards();
      setDuplicates(data);
    } catch (err) {
      console.error('Failed to load duplicates:', err);
    } finally {
      setIsLoadingDuplicates(false);
    }
  };

  const handleAutoDedupe = async () => {
    if (!confirm('This will automatically merge duplicate cards, keeping the shorter-named version. Continue?')) {
      return;
    }
    setIsDeduping(true);
    try {
      const result = await adminService.autoDedupeCards();
      alert(`Auto-deduplication complete: ${result.cards_merged} cards merged`);
      loadDuplicates();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to dedupe cards');
    } finally {
      setIsDeduping(false);
    }
  };

  const handleMergeGroup = async (keepCardId: string, duplicateIds: string[]) => {
    try {
      await adminService.mergeCards(keepCardId, duplicateIds);
      alert('Cards merged successfully');
      loadDuplicates();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to merge cards');
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleString();
  };

  const getStatusIcon = (result?: string) => {
    switch (result) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'partial':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading scraper status...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Bot className="w-8 h-8 text-primary-600" />
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Web Scraper
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Fetch card benefits from bank websites
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {status?.is_running ? (
              <span className="flex items-center gap-2 px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm">
                <RefreshCw className="w-4 h-4 animate-spin" />
                Running {status.current_bank?.toUpperCase() || ''}...
              </span>
            ) : (
              <span className="flex items-center gap-2 px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-full text-sm">
                {getStatusIcon(status?.last_result)}
                {status?.last_result ? status.last_result.charAt(0).toUpperCase() + status.last_result.slice(1) : 'Idle'}
              </span>
            )}
          </div>
        </div>

        {/* Last Run Info */}
        <div className="grid grid-cols-3 md:grid-cols-6 gap-4 mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Last Run</p>
            <p className="font-medium text-gray-900 dark:text-white text-sm">
              {formatDate(status?.last_run)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Benefits</p>
            <p className="font-medium text-gray-900 dark:text-white">
              {status?.benefits_found || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Campaigns</p>
            <p className="font-medium text-blue-600 dark:text-blue-400">
              {status?.campaigns_found || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Pending Benefits</p>
            <p className="font-medium text-green-600 dark:text-green-400">
              {status?.pending_created || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Pending Campaigns</p>
            <p className="font-medium text-orange-600 dark:text-orange-400">
              {status?.pending_campaigns_created || 0}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">New Brands/Cards</p>
            <p className="font-medium text-purple-600 dark:text-purple-400">
              {status?.brands_created || 0} / {status?.cards_created || 0}
            </p>
          </div>
        </div>

        {/* Errors */}
        {status?.errors && status.errors.length > 0 && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <h3 className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
              Errors ({status.errors.length})
            </h3>
            <ul className="text-sm text-red-600 dark:text-red-400 space-y-1">
              {status.errors.map((error, i) => (
                <li key={i}>{error}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          <Button
            onClick={() => handleRunScraper()}
            disabled={status?.is_running || runningBank !== null}
            leftIcon={<Play className="w-4 h-4" />}
          >
            {runningBank === 'all' ? 'Starting...' : 'Scrape All Banks'}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleRunScraper('hdfc')}
            disabled={status?.is_running || runningBank !== null}
          >
            {runningBank === 'hdfc' ? 'Starting...' : 'HDFC Only'}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleRunScraper('icici')}
            disabled={status?.is_running || runningBank !== null}
          >
            {runningBank === 'icici' ? 'Starting...' : 'ICICI Only'}
          </Button>
          <Button
            variant="outline"
            onClick={() => handleRunScraper('sbi')}
            disabled={status?.is_running || runningBank !== null}
          >
            {runningBank === 'sbi' ? 'Starting...' : 'SBI Only'}
          </Button>
          <Button
            variant="ghost"
            onClick={loadStatus}
            leftIcon={<RefreshCw className="w-4 h-4" />}
          >
            Refresh Status
          </Button>
        </div>
      </Card>

      {/* Bank Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <BankCard
          name="HDFC Bank"
          logo="https://upload.wikimedia.org/wikipedia/commons/2/28/HDFC_Bank_Logo.svg"
          description="Infinia, Regalia, Diners Club, Tata Neu, Swiggy cards"
          cardsTracked={12}
        />
        <BankCard
          name="ICICI Bank"
          logo="https://upload.wikimedia.org/wikipedia/commons/1/12/ICICI_Bank_Logo.svg"
          description="Amazon Pay, Emeralde, Sapphiro, MakeMyTrip cards"
          cardsTracked={8}
        />
        <BankCard
          name="SBI Card"
          logo="https://upload.wikimedia.org/wikipedia/commons/c/cc/SBI_Card_Logo.svg"
          description="SimplyCLICK, Ola Money, BPCL, IRCTC, Air India cards"
          cardsTracked={11}
        />
      </div>

      {/* How It Works */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          How It Works
        </h3>
        <ol className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs font-medium">
              1
            </span>
            <span>
              <strong>Scrape:</strong> The scraper visits bank websites and extracts card benefit
              information (cashback rates, partner brands, campaigns, etc.)
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs font-medium">
              2
            </span>
            <span>
              <strong>Match:</strong> Scraped data is matched to existing cards and brands in the
              database using fuzzy matching
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs font-medium">
              3
            </span>
            <span>
              <strong>Review:</strong> New and updated benefits are added to the Pending tab for
              your review before going live
            </span>
          </li>
          <li className="flex items-start gap-3">
            <span className="flex-shrink-0 w-6 h-6 flex items-center justify-center bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full text-xs font-medium">
              4
            </span>
            <span>
              <strong>Approve:</strong> Approve individual changes or bulk approve all pending
              changes to update the production database
            </span>
          </li>
        </ol>
      </Card>

      {/* Duplicate Cards Cleanup */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Copy className="w-6 h-6 text-yellow-600" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Duplicate Cards
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Find and merge duplicate cards (e.g., "ICICI Coral" vs "ICICI Coral Credit Card")
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={loadDuplicates}
              disabled={isLoadingDuplicates}
              leftIcon={<RefreshCw className={`w-4 h-4 ${isLoadingDuplicates ? 'animate-spin' : ''}`} />}
            >
              {isLoadingDuplicates ? 'Scanning...' : 'Find Duplicates'}
            </Button>
            {duplicates && duplicates.total_groups > 0 && (
              <Button
                variant="primary"
                onClick={handleAutoDedupe}
                disabled={isDeduping}
                leftIcon={<Merge className="w-4 h-4" />}
              >
                {isDeduping ? 'Merging...' : 'Auto-Merge All'}
              </Button>
            )}
          </div>
        </div>

        {duplicates && (
          <div className="space-y-4">
            {duplicates.total_groups === 0 ? (
              <div className="text-center py-8 text-green-600 dark:text-green-400">
                <CheckCircle className="w-12 h-12 mx-auto mb-2" />
                <p>No duplicate cards found!</p>
              </div>
            ) : (
              <>
                <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg text-sm text-yellow-800 dark:text-yellow-200">
                  Found {duplicates.total_groups} duplicate groups with {duplicates.total_duplicates} total cards
                </div>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {duplicates.duplicate_groups.map((group, idx) => (
                    <div key={idx} className="border dark:border-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {group.bank_code.toUpperCase()}: "{group.normalized_name}"
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            const keepCard = group.cards.reduce((a, b) =>
                              a.name.length <= b.name.length ? a : b
                            );
                            const duplicateIds = group.cards
                              .filter(c => c.id !== keepCard.id)
                              .map(c => c.id);
                            handleMergeGroup(keepCard.id, duplicateIds);
                          }}
                          leftIcon={<Merge className="w-3 h-3" />}
                        >
                          Merge
                        </Button>
                      </div>
                      <div className="space-y-2">
                        {group.cards.map((card, cardIdx) => (
                          <div
                            key={card.id}
                            className={`flex items-center justify-between p-2 rounded ${
                              cardIdx === 0
                                ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                                : 'bg-gray-50 dark:bg-gray-800'
                            }`}
                          >
                            <div>
                              <span className="text-sm font-medium text-gray-900 dark:text-white">
                                {card.name}
                              </span>
                              {cardIdx === 0 && (
                                <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                                  (will keep)
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              {card.card_type} · {card.card_network || 'N/A'}
                              {card.annual_fee !== null && ` · ₹${card.annual_fee}`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

function BankCard({
  name,
  logo,
  description,
  cardsTracked,
}: {
  name: string;
  logo: string;
  description: string;
  cardsTracked: number;
}) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3 mb-3">
        <img
          src={logo}
          alt={name}
          className="w-10 h-10 object-contain"
          onError={(e) => {
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />
        <div>
          <h3 className="font-semibold text-gray-900 dark:text-white">{name}</h3>
          <p className="text-xs text-gray-500 dark:text-gray-400">{cardsTracked} cards tracked</p>
        </div>
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-300">{description}</p>
    </Card>
  );
}

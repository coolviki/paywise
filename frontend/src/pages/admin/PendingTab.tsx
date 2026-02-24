import React, { useState, useEffect } from 'react';
import { Check, X, Pencil, Trash2, CheckCircle, XCircle, AlertCircle, ExternalLink } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { PendingChange } from '../../types';
import * as adminService from '../../services/adminService';

export function PendingTab() {
  const [changes, setChanges] = useState<PendingChange[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('pending');
  const [editingChange, setEditingChange] = useState<PendingChange | null>(null);

  useEffect(() => {
    loadChanges();
  }, [statusFilter]);

  const loadChanges = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getPendingChanges(statusFilter || undefined);
      setChanges(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load pending changes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (changeId: string) => {
    try {
      await adminService.approvePendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve change');
    }
  };

  const handleReject = async (changeId: string) => {
    try {
      await adminService.rejectPendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject change');
    }
  };

  const handleDelete = async (changeId: string) => {
    if (!confirm('Are you sure you want to delete this pending change?')) return;
    try {
      await adminService.deletePendingChange(changeId);
      setChanges(changes.filter((c) => c.id !== changeId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete change');
    }
  };

  const handleApproveAll = async () => {
    if (!confirm(`Are you sure you want to approve all ${changes.length} pending changes?`)) return;
    try {
      const result = await adminService.approveAllPending();
      alert(`Approved: ${result.approved}, Failed: ${result.failed}`);
      loadChanges();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve all changes');
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

  const pendingCount = changes.filter((c) => c.status === 'pending').length;

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading pending changes...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Pending Changes ({changes.length})
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Review and approve scraped ecosystem benefit changes
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
          {pendingCount > 0 && (
            <Button onClick={handleApproveAll} leftIcon={<Check className="w-4 h-4" />}>
              Approve All ({pendingCount})
            </Button>
          )}
        </div>
      </div>

      {/* Changes List */}
      {changes.length === 0 ? (
        <Card className="p-12 text-center">
          <CheckCircle className="w-16 h-16 mx-auto text-green-400 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No Pending Changes
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {statusFilter === 'pending'
              ? 'All changes have been reviewed. Run the scraper to find new updates.'
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

                  {/* Benefit Details */}
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

                {/* Actions */}
                {change.status === 'pending' && (
                  <div className="flex flex-col gap-2 ml-4">
                    <Button
                      size="sm"
                      onClick={() => handleApprove(change.id)}
                      leftIcon={<Check className="w-4 h-4" />}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleReject(change.id)}
                      leftIcon={<X className="w-4 h-4" />}
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setEditingChange(change)}
                      leftIcon={<Pencil className="w-4 h-4" />}
                    >
                      Edit
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-500 hover:text-red-600"
                      onClick={() => handleDelete(change.id)}
                      leftIcon={<Trash2 className="w-4 h-4" />}
                    >
                      Delete
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Edit Modal */}
      {editingChange && (
        <EditChangeModal
          change={editingChange}
          onClose={() => setEditingChange(null)}
          onSuccess={() => {
            setEditingChange(null);
            loadChanges();
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

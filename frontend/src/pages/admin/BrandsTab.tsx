import React, { useState, useEffect } from 'react';
import { Plus, Pencil, Trash2, X, Tag } from 'lucide-react';
import { Button } from '../../components/common/Button';
import { Card } from '../../components/common/Card';
import { BrandListItem, Brand } from '../../types';
import * as adminService from '../../services/adminService';

export function BrandsTab() {
  const [brands, setBrands] = useState<BrandListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null);

  useEffect(() => {
    loadBrands();
  }, []);

  const loadBrands = async () => {
    try {
      setIsLoading(true);
      const data = await adminService.getBrands();
      setBrands(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load brands');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (brandId: string) => {
    if (!confirm('Are you sure you want to delete this brand?')) return;
    try {
      await adminService.deleteBrand(brandId);
      setBrands(brands.filter((b) => b.id !== brandId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete brand');
    }
  };

  const handleEdit = async (brandId: string) => {
    try {
      const brand = await adminService.getBrand(brandId);
      setEditingBrand(brand);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to load brand');
    }
  };

  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">Loading brands...</div>;
  }

  if (error) {
    return <div className="text-center py-8 text-red-500">{error}</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Brands ({brands.length})
        </h2>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<Plus className="w-4 h-4" />}>
          Add Brand
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {brands.map((brand) => (
          <Card key={brand.id} className="p-4">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white">{brand.name}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">{brand.code}</p>
                {brand.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                    {brand.description}
                  </p>
                )}
                <div className="flex items-center gap-1 mt-2 text-sm text-gray-500">
                  <Tag className="w-3 h-3" />
                  {brand.keyword_count} keywords
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleEdit(brand.id)}
                  className="p-1 text-gray-400 hover:text-primary-600"
                >
                  <Pencil className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleDelete(brand.id)}
                  className="p-1 text-gray-400 hover:text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {showAddModal && (
        <AddBrandModal
          onClose={() => setShowAddModal(false)}
          onSuccess={() => {
            setShowAddModal(false);
            loadBrands();
          }}
        />
      )}

      {editingBrand && (
        <EditBrandModal
          brand={editingBrand}
          onClose={() => setEditingBrand(null)}
          onSuccess={() => {
            setEditingBrand(null);
            loadBrands();
          }}
        />
      )}
    </div>
  );
}

function AddBrandModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [keywords, setKeywords] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      await adminService.createBrand({
        name,
        code: code.toLowerCase().replace(/\s+/g, ''),
        description: description || undefined,
        keywords: keywords
          .split(',')
          .map((k) => k.trim().toLowerCase())
          .filter(Boolean),
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create brand');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Add Brand</h3>
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
              placeholder="e.g., Tata Group"
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
              placeholder="e.g., tata"
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
              placeholder="e.g., Tata Group retail properties"
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
              placeholder="e.g., westside, croma, bigbasket"
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

function EditBrandModal({
  brand,
  onClose,
  onSuccess,
}: {
  brand: Brand;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [name, setName] = useState(brand.name);
  const [code, setCode] = useState(brand.code);
  const [description, setDescription] = useState(brand.description || '');
  const [keywords, setKeywords] = useState(brand.keywords);
  const [newKeyword, setNewKeyword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpdate = async () => {
    setIsLoading(true);
    setError(null);

    try {
      await adminService.updateBrand(brand.id, {
        name,
        code: code.toLowerCase().replace(/\s+/g, ''),
        description: description || undefined,
      });
      onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update brand');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddKeyword = async () => {
    if (!newKeyword.trim()) return;
    try {
      const kw = await adminService.addKeyword(brand.id, newKeyword.trim());
      setKeywords([...keywords, { id: kw.id, keyword: kw.keyword, created_at: new Date().toISOString() }]);
      setNewKeyword('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add keyword');
    }
  };

  const handleDeleteKeyword = async (keywordId: string) => {
    try {
      await adminService.deleteKeyword(brand.id, keywordId);
      setKeywords(keywords.filter((k) => k.id !== keywordId));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete keyword');
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Edit Brand</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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

          {error && <p className="text-sm text-red-500">{error}</p>}

          <Button onClick={handleUpdate} isLoading={isLoading} className="w-full">
            Update Brand
          </Button>

          <hr className="border-gray-200 dark:border-gray-700" />

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Keywords ({keywords.length})
            </label>
            <div className="flex flex-wrap gap-2 mb-3">
              {keywords.map((kw) => (
                <span
                  key={kw.id}
                  className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-sm"
                >
                  {kw.keyword}
                  <button
                    onClick={() => handleDeleteKeyword(kw.id)}
                    className="text-gray-400 hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={newKeyword}
                onChange={(e) => setNewKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
                placeholder="Add keyword..."
              />
              <Button type="button" size="sm" onClick={handleAddKeyword}>
                Add
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

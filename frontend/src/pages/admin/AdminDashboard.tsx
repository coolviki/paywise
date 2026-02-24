import React from 'react';
import { Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { Shield, Tags, CreditCard, Bot, Clock } from 'lucide-react';
import { BrandsTab } from './BrandsTab';
import { BenefitsTab } from './BenefitsTab';
import { ScraperTab } from './ScraperTab';
import { PendingTab } from './PendingTab';

const tabs = [
  { id: 'brands', label: 'Brands', icon: Tags, path: '/admin/brands' },
  { id: 'benefits', label: 'Benefits', icon: CreditCard, path: '/admin/benefits' },
  { id: 'scraper', label: 'Scraper', icon: Bot, path: '/admin/scraper' },
  { id: 'pending', label: 'Pending', icon: Clock, path: '/admin/pending' },
];

export function AdminDashboard() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-primary-600" />
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Admin Dashboard
              </h1>
            </div>
            <NavLink
              to="/"
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-primary-600"
            >
              Back to App
            </NavLink>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8" aria-label="Tabs">
            {tabs.map((tab) => (
              <NavLink
                key={tab.id}
                to={tab.path}
                className={({ isActive }) =>
                  `flex items-center gap-2 py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }`
                }
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Navigate to="/admin/brands" replace />} />
          <Route path="/brands" element={<BrandsTab />} />
          <Route path="/benefits" element={<BenefitsTab />} />
          <Route path="/scraper" element={<ScraperTab />} />
          <Route path="/pending" element={<PendingTab />} />
        </Routes>
      </main>
    </div>
  );
}

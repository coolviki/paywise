import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  User,
  Bell,
  MapPin,
  Palette,
  DollarSign,
  FileText,
  Lock,
  Info,
  LogOut,
  ChevronRight,
  Moon,
  Sun,
  Shield,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { useAuth } from '../hooks/useAuth';

export function Settings() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    const isDark = document.documentElement.classList.contains('dark');
    setIsDarkMode(isDark);
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    if (newMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to sign out?')) {
      await logout();
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 pb-20">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
            Settings
          </h1>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6">
        {/* Account Section */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">
            Account
          </h2>
          <Card>
            <SettingsItem
              icon={<User className="w-5 h-5" />}
              label="Profile"
              value={user?.name}
              onClick={() => {}}
            />
            <SettingsItem
              icon={<Bell className="w-5 h-5" />}
              label="Notifications"
              onClick={() => {}}
            />
            <SettingsItem
              icon={<MapPin className="w-5 h-5" />}
              label="Location Settings"
              onClick={() => {}}
              isLast
            />
          </Card>
        </section>

        {/* Preferences Section */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">
            Preferences
          </h2>
          <Card>
            <SettingsItem
              icon={isDarkMode ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
              label="Appearance"
              value={isDarkMode ? 'Dark' : 'Light'}
              onClick={toggleDarkMode}
            />
            <SettingsItem
              icon={<DollarSign className="w-5 h-5" />}
              label="Default Currency"
              value="INR"
              onClick={() => {}}
              isLast
            />
          </Card>
        </section>

        {/* Admin Section (only for admins) */}
        {user?.is_admin && (
          <section>
            <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">
              Admin
            </h2>
            <Card>
              <SettingsItem
                icon={<Shield className="w-5 h-5" />}
                label="Admin Dashboard"
                value="Manage ecosystem benefits"
                onClick={() => navigate('/admin')}
                isLast
              />
            </Card>
          </section>
        )}

        {/* About Section */}
        <section>
          <h2 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3 px-1">
            About
          </h2>
          <Card>
            <SettingsItem
              icon={<FileText className="w-5 h-5" />}
              label="Terms of Service"
              onClick={() => {}}
            />
            <SettingsItem
              icon={<Lock className="w-5 h-5" />}
              label="Privacy Policy"
              onClick={() => {}}
            />
            <SettingsItem
              icon={<Info className="w-5 h-5" />}
              label="About PayWise"
              value="v1.0.0"
              onClick={() => {}}
              isLast
            />
          </Card>
        </section>

        {/* Sign Out */}
        <Button
          variant="outline"
          className="w-full border-red-500 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20"
          leftIcon={<LogOut className="w-5 h-5" />}
          onClick={handleLogout}
        >
          Sign Out
        </Button>
      </div>
    </div>
  );
}

interface SettingsItemProps {
  icon: React.ReactNode;
  label: string;
  value?: string;
  onClick: () => void;
  isLast?: boolean;
}

function SettingsItem({ icon, label, value, onClick, isLast = false }: SettingsItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
        !isLast ? 'border-b border-gray-100 dark:border-gray-700' : ''
      }`}
    >
      <div className="flex items-center gap-3">
        <span className="text-gray-500 dark:text-gray-400">{icon}</span>
        <span className="font-medium text-gray-900 dark:text-white">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        {value && (
          <span className="text-sm text-gray-500 dark:text-gray-400">{value}</span>
        )}
        <ChevronRight className="w-5 h-5 text-gray-400" />
      </div>
    </button>
  );
}

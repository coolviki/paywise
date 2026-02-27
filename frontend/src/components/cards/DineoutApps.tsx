import React, { useEffect, useState } from 'react';
import { Check } from 'lucide-react';
import api from '../../services/api';

interface DineoutApp {
  code: string;
  name: string;
  logo_url: string | null;
  color: string;
  is_enabled: boolean;
  coming_soon: boolean;
}

interface DineoutAppsProps {
  onUpdate?: () => void;
}

export function DineoutApps({ onUpdate }: DineoutAppsProps) {
  const [apps, setApps] = useState<DineoutApp[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [togglingApp, setTogglingApp] = useState<string | null>(null);

  useEffect(() => {
    fetchApps();
  }, []);

  const fetchApps = async () => {
    try {
      const response = await api.get<{ apps: DineoutApp[] }>('/dineout-apps');
      setApps(response.data.apps);
    } catch (error) {
      console.error('Failed to fetch dineout apps:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleApp = async (appCode: string, currentEnabled: boolean) => {
    setTogglingApp(appCode);
    try {
      const response = await api.post<DineoutApp>('/dineout-apps/toggle', {
        app_code: appCode,
        enabled: !currentEnabled,
      });

      setApps((prev) =>
        prev.map((app) =>
          app.code === appCode ? { ...app, is_enabled: response.data.is_enabled } : app
        )
      );

      onUpdate?.();
    } catch (error) {
      console.error('Failed to toggle app:', error);
    } finally {
      setTogglingApp(null);
    }
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-20 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"
          />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      {apps.map((app) => (
        <button
          key={app.code}
          onClick={() => !app.coming_soon && toggleApp(app.code, app.is_enabled)}
          disabled={app.coming_soon || togglingApp === app.code}
          className={`relative flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all ${
            app.coming_soon
              ? 'opacity-50 cursor-not-allowed border-gray-200 dark:border-gray-700'
              : app.is_enabled
              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-400'
          }`}
        >
          {/* Logo or colored circle */}
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center mb-2"
            style={{ backgroundColor: app.color + '20' }}
          >
            {app.logo_url ? (
              <img
                src={app.logo_url}
                alt={app.name}
                className="w-8 h-8 object-contain"
                onError={(e) => {
                  // Fallback to initial if image fails
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            ) : (
              <span
                className="text-xl font-bold"
                style={{ color: app.color }}
              >
                {app.name.charAt(0)}
              </span>
            )}
          </div>

          {/* App name */}
          <span className="text-sm font-medium text-gray-900 dark:text-white">
            {app.name}
          </span>

          {/* Coming soon badge */}
          {app.coming_soon && (
            <span className="text-xs text-gray-500 mt-1">Coming Soon</span>
          )}

          {/* Enabled checkmark */}
          {app.is_enabled && !app.coming_soon && (
            <div className="absolute top-2 right-2 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
              <Check className="w-3 h-3 text-white" />
            </div>
          )}

          {/* Loading spinner */}
          {togglingApp === app.code && (
            <div className="absolute inset-0 bg-white/50 dark:bg-black/50 rounded-xl flex items-center justify-center">
              <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </button>
      ))}
    </div>
  );
}

export default DineoutApps;

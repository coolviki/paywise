import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import { useAuth } from './hooks/useAuth';
import { Loading } from './components/common/Loading';
import { AdminRoute } from './components/common/AdminRoute';

// Pages
import { Login } from './pages/Login';
import { Onboarding } from './pages/Onboarding';
import { Home } from './pages/Home';
import { Search } from './pages/Search';
import { Recommendation } from './pages/Recommendation';
import { MyCards } from './pages/MyCards';
import { Settings } from './pages/Settings';
import { AdminDashboard } from './pages/admin/AdminDashboard';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <Loading fullScreen text="Loading..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function AppRoutes() {
  // Initialize dark mode from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <Onboarding />
          </ProtectedRoute>
        }
      />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />
      <Route
        path="/search"
        element={
          <ProtectedRoute>
            <Search />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recommendation"
        element={
          <ProtectedRoute>
            <Recommendation />
          </ProtectedRoute>
        }
      />
      <Route
        path="/cards"
        element={
          <ProtectedRoute>
            <MyCards />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/*"
        element={
          <AdminRoute>
            <AdminDashboard />
          </AdminRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <div className="min-h-screen bg-white dark:bg-gray-900">
          <AppRoutes />
        </div>
      </BrowserRouter>
    </Provider>
  );
}

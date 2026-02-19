import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { GoogleAuthButton } from '../components/auth/GoogleAuthButton';
import { Loading } from '../components/common/Loading';

export function Login() {
  const { isAuthenticated, isLoading, error, login } = useAuth();

  if (isLoading) {
    return <Loading fullScreen text="Loading..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-800">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo */}
        <div className="text-center">
          <img src="/logo.svg" alt="PayWise" className="w-20 h-20 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">PayWise</h1>
          <p className="mt-2 text-gray-500 dark:text-gray-400">Pay Smart. Earn More.</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg text-sm text-center">
            {error}
          </div>
        )}

        {/* Auth buttons */}
        <div className="space-y-4">
          <GoogleAuthButton onClick={login} />

          <button className="w-full py-3 px-4 border-2 border-gray-200 dark:border-gray-700 rounded-lg text-gray-600 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            Other Sign-in Options
          </button>
        </div>

        {/* Terms */}
        <p className="text-center text-xs text-gray-500 dark:text-gray-400">
          By continuing, you agree to our{' '}
          <a href="#" className="text-primary-500 hover:underline">
            Terms of Service
          </a>{' '}
          &{' '}
          <a href="#" className="text-primary-500 hover:underline">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}

import React, { useState, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { GoogleAuthButton } from '../components/auth/GoogleAuthButton';
import { Loading } from '../components/common/Loading';

export function Login() {
  const { isAuthenticated, isLoading, error, login } = useAuth();
  const [isMuted, setIsMuted] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !isMuted;
      setIsMuted(!isMuted);
    }
  };

  if (isLoading) {
    return <Loading fullScreen text="Loading..." />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-800">
      {/* Video Section - Left on desktop, top on mobile */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-4 lg:p-8 bg-gray-900">
        <div className="relative w-full max-w-md lg:max-w-lg">
          <video
            ref={videoRef}
            className="w-full rounded-2xl shadow-2xl"
            autoPlay
            loop
            muted={isMuted}
            playsInline
            poster="/logo.svg"
          >
            <source src="/promo.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>

          {/* Mute/Unmute button with hint */}
          <button
            onClick={toggleMute}
            className={`absolute bottom-3 right-3 flex items-center gap-2 px-3 py-2 bg-black/60 hover:bg-black/80 rounded-full text-white transition-all ${isMuted ? 'animate-pulse' : ''}`}
            aria-label={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                </svg>
                <span className="text-sm font-medium">Tap for sound</span>
              </>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Login Section - Right on desktop, bottom on mobile */}
      <div className="w-full lg:w-1/2 flex flex-col items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-sm space-y-8">
          {/* Logo */}
          <div className="text-center">
            <img src="/logo.svg" alt="PayWise" className="w-20 h-20 mx-auto mb-4" />
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">PayWise</h1>
            <p className="mt-2 text-gray-500 dark:text-gray-400">Swipe Smarter. Save More.</p>
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
    </div>
  );
}

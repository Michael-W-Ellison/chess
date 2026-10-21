/**
 * ParentLogin Component
 * Password form shown before the parent dashboard when password protection is on
 */

import React, { useState } from 'react';
import { loginParent, ParentAuthError } from '../../services/parentAuth';

interface ParentLoginProps {
  onLogin: () => void;
  onNotConfigured: () => void;
  notice?: string | null; // e.g. "Your session expired"
}

export const ParentLogin: React.FC<ParentLoginProps> = ({ onLogin, onNotConfigured, notice }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!password || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    try {
      await loginParent(password);
      setPassword('');
      onLogin();
    } catch (err) {
      if (err instanceof ParentAuthError && err.status === 403) {
        onNotConfigured();
        return;
      }
      // 401 includes the attempts remaining, 429 the lockout time
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-full flex items-center justify-center bg-gray-50 p-6">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm bg-white border border-gray-200 rounded-lg shadow-sm p-6"
      >
        <h1 className="text-2xl font-bold text-gray-800">Parent Dashboard</h1>
        <p className="text-sm text-gray-600 mt-1 mb-4">Enter the parent password to continue.</p>

        {notice && (
          <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-sm text-yellow-800">
            {notice}
          </div>
        )}

        <label htmlFor="parent-password" className="block text-sm font-medium text-gray-700 mb-1">
          Password
        </label>
        <input
          id="parent-password"
          type="password"
          autoFocus
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />

        {error && (
          <p role="alert" className="mt-3 text-sm text-red-600">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={!password || isSubmitting}
          className="mt-4 w-full bg-blue-500 text-white font-medium rounded-lg px-4 py-2 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? 'Logging in...' : 'Log in'}
        </button>
      </form>
    </div>
  );
};

export default ParentLogin;

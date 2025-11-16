/**
 * useProfile Hook
 * Manages user profile and memory data
 */

import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import type { UserProfile, ProfileItem } from '../../shared/types';

export interface UseProfileState {
  // State
  profile: UserProfile | null;
  memories: ProfileItem[];
  isLoading: boolean;
  error: string | null;

  // Actions
  refreshProfile: () => Promise<void>;
  getMemories: (category?: string) => Promise<void>;
  updateProfile: (updates: { name?: string; age?: number; grade?: number }) => Promise<void>;
  clearError: () => void;
}

/**
 * Hook for managing user profile and memories
 */
export function useProfile(): UseProfileState {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [memories, setMemories] = useState<ProfileItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch user profile
   */
  const refreshProfile = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.profile.get();
      setProfile(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load profile';
      setError(errorMessage);
      console.error('Failed to fetch profile:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch memories (optionally filtered by category)
   */
  const getMemories = useCallback(async (category?: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.profile.getMemories(1, category);
      setMemories(data.memories);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load memories';
      setError(errorMessage);
      console.error('Failed to fetch memories:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Update user profile information
   */
  const updateProfile = useCallback(
    async (updates: { name?: string; age?: number; grade?: number }) => {
      try {
        setIsLoading(true);
        setError(null);

        const response = await api.profile.update(updates);

        if (response.success) {
          setProfile(response.user);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update profile';
        setError(errorMessage);
        console.error('Failed to update profile:', err);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Load profile on mount
   */
  useEffect(() => {
    refreshProfile();
    getMemories();
  }, [refreshProfile, getMemories]);

  return {
    // State
    profile,
    memories,
    isLoading,
    error,

    // Actions
    refreshProfile,
    getMemories,
    updateProfile,
    clearError,
  };
}

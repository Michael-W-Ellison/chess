/**
 * useAvatar Hook
 * Manages user avatar selection and persistence
 */

import { useState, useEffect, useCallback } from 'react';
import { DEFAULT_AVATAR } from '../../shared/avatars';
import { useAchievements } from './useAchievements';

const AVATAR_STORAGE_KEY = 'user_avatar_id';

export const useAvatar = () => {
  const [avatarId, setAvatarId] = useState<string>(DEFAULT_AVATAR.id);
  const [isLoading, setIsLoading] = useState(true);
  const { trackAvatarChange } = useAchievements();

  /**
   * Load avatar from localStorage on mount
   */
  useEffect(() => {
    try {
      const stored = localStorage.getItem(AVATAR_STORAGE_KEY);
      if (stored) {
        setAvatarId(stored);
      }
    } catch (error) {
      console.error('Failed to load avatar:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Update avatar and persist to localStorage
   */
  const updateAvatar = useCallback((newAvatarId: string) => {
    try {
      setAvatarId(newAvatarId);
      localStorage.setItem(AVATAR_STORAGE_KEY, newAvatarId);
      trackAvatarChange(newAvatarId);
    } catch (error) {
      console.error('Failed to save avatar:', error);
      throw error;
    }
  }, [trackAvatarChange]);

  /**
   * Reset avatar to default
   */
  const resetAvatar = useCallback(() => {
    updateAvatar(DEFAULT_AVATAR.id);
  }, [updateAvatar]);

  return {
    avatarId,
    updateAvatar,
    resetAvatar,
    isLoading,
  };
};

export default useAvatar;

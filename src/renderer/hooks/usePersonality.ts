/**
 * usePersonality Hook
 * Manages bot personality state and updates
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';
import type { PersonalityState } from '../../shared/types';
import { playLevelUpSound } from '../../shared/soundEffects';

export interface UsePersonalityState {
  // State
  personality: PersonalityState | null;
  description: {
    humor: string;
    energy: string;
    curiosity: string;
    formality: string;
  } | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  refreshPersonality: () => Promise<void>;
  getDescription: () => Promise<void>;
  clearError: () => void;
}

/**
 * Hook for managing bot personality
 */
export function usePersonality(): UsePersonalityState {
  const [personality, setPersonality] = useState<PersonalityState | null>(null);
  const [description, setDescription] = useState<{
    humor: string;
    energy: string;
    curiosity: string;
    formality: string;
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track previous friendship level to detect level-ups
  const previousLevelRef = useRef<number | null>(null);

  /**
   * Fetch current personality
   */
  const refreshPersonality = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.personality.get();

      // Check for level-up
      if (previousLevelRef.current !== null &&
          data.friendshipLevel > previousLevelRef.current) {
        // Play celebratory sound for level-up!
        playLevelUpSound();
        console.log(`🎉 Level up! ${previousLevelRef.current} → ${data.friendshipLevel}`);
      }

      // Update previous level
      previousLevelRef.current = data.friendshipLevel;

      setPersonality(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load personality';
      setError(errorMessage);
      console.error('Failed to fetch personality:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Fetch personality trait descriptions
   */
  const getDescription = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await api.personality.getDescription();
      setDescription(data);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to load personality description';
      setError(errorMessage);
      console.error('Failed to fetch description:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Load personality on mount
   */
  useEffect(() => {
    refreshPersonality();
  }, [refreshPersonality]);

  return {
    // State
    personality,
    description,
    isLoading,
    error,

    // Actions
    refreshPersonality,
    getDescription,
    clearError,
  };
}

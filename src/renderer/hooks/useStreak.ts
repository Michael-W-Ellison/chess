/**
 * useStreak Hook
 * Provides access to streak tracking functionality
 */

import { useContext } from 'react';
import { StreakContext } from '../contexts/StreakContext';

export function useStreak() {
  const context = useContext(StreakContext);
  if (!context) {
    throw new Error('useStreak must be used within a StreakProvider');
  }
  return context;
}

export default useStreak;

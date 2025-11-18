/**
 * useAchievements Hook
 * Access achievement tracking context
 */

import { useContext } from 'react';
import { AchievementContext } from '../contexts/AchievementContext';

export const useAchievements = () => {
  const context = useContext(AchievementContext);

  if (!context) {
    throw new Error('useAchievements must be used within an AchievementProvider');
  }

  return context;
};

export default useAchievements;

/**
 * StreakContext
 * Unified streak management for all activity types
 */

import React, { createContext, useState, useCallback, ReactNode } from 'react';
import {
  StreakRecord,
  StreakResult,
  StreakOptions,
  calculateStreakStats,
  isStreakAtRisk,
  getStreakMilestone,
  getProgressToNextMilestone,
  getTodayISO,
} from '../../shared/streakUtils';

const STREAK_STORAGE_KEY = 'streak_data';

export type StreakType = 'login' | 'chat' | 'exercise' | 'study' | 'custom';

export interface StreakData {
  type: StreakType;
  records: StreakRecord[];
  options: StreakOptions;
  stats: StreakResult;
}

export interface StreakMilestoneEvent {
  type: StreakType;
  milestone: number;
  timestamp: number;
}

interface StreakContextType {
  // Get streak data for a specific type
  getStreakData: (type: StreakType) => StreakData | null;

  // Record activity for a specific streak type
  recordActivity: (type: StreakType, customDate?: string) => void;

  // Get streak stats for a specific type
  getStats: (type: StreakType) => StreakResult;

  // Check if streak is at risk
  checkStreakRisk: (type: StreakType) => boolean;

  // Get milestone information
  getMilestoneInfo: (type: StreakType) => {
    current: number | null;
    next: number;
    progress: number;
    daysRemaining: number;
  };

  // Set options for a streak type
  setStreakOptions: (type: StreakType, options: StreakOptions) => void;

  // Recent milestone events
  recentMilestones: StreakMilestoneEvent[];

  // Reset all streaks (for testing/demo)
  resetAllStreaks: () => void;
}

export const StreakContext = createContext<StreakContextType | undefined>(undefined);

interface StreakProviderProps {
  children: ReactNode;
}

const DEFAULT_OPTIONS: StreakOptions = {
  allowWeekendGracePeriod: false,
  gracePeriodDays: 0,
  includeFutureDates: false,
};

/**
 * Streak data from localStorage, read when the provider is created so it is there on the
 * first render (App records the login activity on mount; loading it in an effect afterwards
 * let that write overwrite the stored records with only today's)
 */
function loadStoredStreakData(): Map<StreakType, StreakData> {
  const dataMap = new Map<StreakType, StreakData>();
  try {
    const stored = localStorage.getItem(STREAK_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      Object.entries(parsed).forEach(([type, data]) => {
        const streakType = type as StreakType;
        const streakInfo = data as StreakData;
        const stats = calculateStreakStats(streakInfo.records, streakInfo.options);
        dataMap.set(streakType, {
          ...streakInfo,
          stats,
        });
      });
    }
  } catch (error) {
    console.error('Failed to load streak data:', error);
  }
  return dataMap;
}

export const StreakProvider: React.FC<StreakProviderProps> = ({ children }) => {
  const [streakData, setStreakData] = useState<Map<StreakType, StreakData>>(loadStoredStreakData);
  const [recentMilestones, setRecentMilestones] = useState<StreakMilestoneEvent[]>([]);


  /**
   * Save streak data to localStorage
   */
  const saveStreakData = useCallback((data: Map<StreakType, StreakData>) => {
    try {
      const dataObject: Record<string, StreakData> = {};
      data.forEach((value, key) => {
        dataObject[key] = value;
      });
      localStorage.setItem(STREAK_STORAGE_KEY, JSON.stringify(dataObject));
    } catch (error) {
      console.error('Failed to save streak data:', error);
    }
  }, []);

  /**
   * Get streak data for a specific type
   */
  const getStreakData = useCallback(
    (type: StreakType): StreakData | null => {
      return streakData.get(type) || null;
    },
    [streakData]
  );

  /**
   * Get streak stats for a specific type
   */
  const getStats = useCallback(
    (type: StreakType): StreakResult => {
      const data = streakData.get(type);
      if (!data) {
        return {
          currentStreak: 0,
          longestStreak: 0,
          lastActivityDate: null,
          isActiveToday: false,
          streakHistory: [],
        };
      }
      return data.stats;
    },
    [streakData]
  );

  /**
   * Record activity for a specific streak type
   */
  const recordActivity = useCallback(
    (type: StreakType, customDate?: string) => {
      const today = customDate || getTodayISO();
      const existing = streakData.get(type);

      const records = existing ? [...existing.records] : [];
      const options = existing ? existing.options : DEFAULT_OPTIONS;

      // Check if already recorded today
      const alreadyRecorded = records.some((r) => r.date === today);

      if (!alreadyRecorded) {
        records.push({
          date: today,
          timestamp: Date.now(),
          type,
        });
      }

      // Recalculate stats
      const stats = calculateStreakStats(records, options);

      // Check for milestone
      const milestone = getStreakMilestone(stats.currentStreak);
      if (milestone && !alreadyRecorded) {
        setRecentMilestones((prev) => [
          {
            type,
            milestone,
            timestamp: Date.now(),
          },
          ...prev.slice(0, 9), // Keep last 10
        ]);
        console.log(`🎉 Milestone reached: ${type} streak ${milestone} days!`);
      }

      const newData = new Map(streakData);
      newData.set(type, {
        type,
        records,
        options,
        stats,
      });

      setStreakData(newData);
      saveStreakData(newData);

      console.log(`✅ ${type} activity recorded for ${today}. Current streak: ${stats.currentStreak}`);
    },
    [streakData, saveStreakData]
  );

  /**
   * Check if streak is at risk
   */
  const checkStreakRisk = useCallback(
    (type: StreakType): boolean => {
      const data = streakData.get(type);
      if (!data) return false;

      return isStreakAtRisk(data.records, data.options);
    },
    [streakData]
  );

  /**
   * Get milestone information
   */
  const getMilestoneInfo = useCallback(
    (type: StreakType) => {
      const stats = getStats(type);
      const current = getStreakMilestone(stats.currentStreak);
      const milestoneProgress = getProgressToNextMilestone(stats.currentStreak);

      return {
        current,
        next: milestoneProgress.nextMilestone,
        progress: milestoneProgress.progress,
        daysRemaining: milestoneProgress.daysRemaining,
      };
    },
    [getStats]
  );

  /**
   * Set options for a streak type
   */
  const setStreakOptions = useCallback(
    (type: StreakType, options: StreakOptions) => {
      const existing = streakData.get(type);
      const records = existing ? existing.records : [];

      // Recalculate stats with new options
      const stats = calculateStreakStats(records, options);

      const newData = new Map(streakData);
      newData.set(type, {
        type,
        records,
        options,
        stats,
      });

      setStreakData(newData);
      saveStreakData(newData);
    },
    [streakData, saveStreakData]
  );

  /**
   * Reset all streaks
   */
  const resetAllStreaks = useCallback(() => {
    setStreakData(new Map());
    setRecentMilestones([]);
    localStorage.removeItem(STREAK_STORAGE_KEY);
    console.log('🔄 All streaks reset');
  }, []);

  return (
    <StreakContext.Provider
      value={{
        getStreakData,
        recordActivity,
        getStats,
        checkStreakRisk,
        getMilestoneInfo,
        setStreakOptions,
        recentMilestones,
        resetAllStreaks,
      }}
    >
      {children}
    </StreakContext.Provider>
  );
};

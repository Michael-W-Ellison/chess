/**
 * AchievementContext
 * Manages achievement unlocking and progress tracking
 */

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { Achievement, ACHIEVEMENTS, getAchievementById } from '../../shared/achievements';

const ACHIEVEMENT_STORAGE_KEY = 'user_achievements';
const STATS_STORAGE_KEY = 'user_stats';

export interface UserStats {
  messageCount: number;
  conversationCount: number;
  dailyStreak: number;
  lastChatDate: string | null;
  longestSessionMinutes: number;
  wordCount: number;
  topicsDiversityCount: number;
  emojiUsageCount: number;
  questionsAskedCount: number;
  storiesSharedCount: number;
  avatarChangesCount: number;
  profileCompleteness: number;
  totalPoints: number;
  lastAchievementUnlocked: string | null;
  weekendDaysCount: number;
}

export interface RecentAchievement {
  achievement: Achievement;
  unlockedAt: string;
}

interface AchievementContextType {
  unlockedAchievements: string[];
  recentAchievements: RecentAchievement[];
  stats: UserStats;
  unlockAchievement: (achievementId: string) => boolean;
  checkAndUnlockAchievements: () => void;
  updateStats: (updates: Partial<UserStats>) => void;
  incrementStat: (stat: keyof UserStats, amount?: number) => void;
  resetAllProgress: () => void;
  isUnlocked: (achievementId: string) => boolean;
  getProgress: (achievementId: string) => number;
}

const DEFAULT_STATS: UserStats = {
  messageCount: 0,
  conversationCount: 0,
  dailyStreak: 0,
  lastChatDate: null,
  longestSessionMinutes: 0,
  wordCount: 0,
  topicsDiversityCount: 0,
  emojiUsageCount: 0,
  questionsAskedCount: 0,
  storiesSharedCount: 0,
  avatarChangesCount: 0,
  profileCompleteness: 0,
  totalPoints: 0,
  lastAchievementUnlocked: null,
  weekendDaysCount: 0,
};

export const AchievementContext = createContext<AchievementContextType | undefined>(undefined);

interface AchievementProviderProps {
  children: ReactNode;
}

export const AchievementProvider: React.FC<AchievementProviderProps> = ({ children }) => {
  const [unlockedAchievements, setUnlockedAchievements] = useState<string[]>([]);
  const [recentAchievements, setRecentAchievements] = useState<RecentAchievement[]>([]);
  const [stats, setStats] = useState<UserStats>(DEFAULT_STATS);

  /**
   * Load achievements and stats from localStorage
   */
  useEffect(() => {
    try {
      const storedAchievements = localStorage.getItem(ACHIEVEMENT_STORAGE_KEY);
      const storedStats = localStorage.getItem(STATS_STORAGE_KEY);

      if (storedAchievements) {
        setUnlockedAchievements(JSON.parse(storedAchievements));
      }

      if (storedStats) {
        setStats(JSON.parse(storedStats));
      } else {
        // Initialize stats
        setStats(DEFAULT_STATS);
      }
    } catch (error) {
      console.error('Failed to load achievement data:', error);
    }
  }, []);

  /**
   * Save achievements to localStorage
   */
  const saveAchievements = useCallback((achievements: string[]) => {
    try {
      localStorage.setItem(ACHIEVEMENT_STORAGE_KEY, JSON.stringify(achievements));
    } catch (error) {
      console.error('Failed to save achievements:', error);
    }
  }, []);

  /**
   * Save stats to localStorage
   */
  const saveStats = useCallback((updatedStats: UserStats) => {
    try {
      localStorage.setItem(STATS_STORAGE_KEY, JSON.stringify(updatedStats));
    } catch (error) {
      console.error('Failed to save stats:', error);
    }
  }, []);

  /**
   * Check if achievement is unlocked
   */
  const isUnlocked = useCallback(
    (achievementId: string): boolean => {
      return unlockedAchievements.includes(achievementId);
    },
    [unlockedAchievements]
  );

  /**
   * Get progress towards achievement (0-100)
   */
  const getProgress = useCallback(
    (achievementId: string): number => {
      const achievement = getAchievementById(achievementId);
      if (!achievement) return 0;
      if (isUnlocked(achievementId)) return 100;

      const { condition } = achievement;
      let currentValue = 0;

      switch (condition.type) {
        case 'message_count':
          currentValue = stats.messageCount;
          break;
        case 'conversation_count':
          currentValue = stats.conversationCount;
          break;
        case 'daily_streak':
          currentValue = stats.dailyStreak;
          break;
        case 'session_length':
          currentValue = stats.longestSessionMinutes;
          break;
        case 'word_count':
          currentValue = stats.wordCount;
          break;
        case 'topic_diversity':
          currentValue = stats.topicsDiversityCount;
          break;
        case 'emoji_usage':
          currentValue = stats.emojiUsageCount;
          break;
        case 'questions_asked':
          currentValue = stats.questionsAskedCount;
          break;
        case 'stories_shared':
          currentValue = stats.storiesSharedCount;
          break;
        case 'profile_complete':
          currentValue = stats.profileCompleteness;
          break;
        case 'avatar_changes':
          currentValue = stats.avatarChangesCount;
          break;
        default:
          currentValue = 0;
      }

      const progress = Math.min((currentValue / condition.value) * 100, 100);
      return Math.round(progress);
    },
    [stats, isUnlocked]
  );

  /**
   * Unlock a specific achievement
   */
  const unlockAchievement = useCallback(
    (achievementId: string): boolean => {
      if (isUnlocked(achievementId)) {
        return false; // Already unlocked
      }

      const achievement = getAchievementById(achievementId);
      if (!achievement) {
        return false; // Achievement not found
      }

      // Add to unlocked list
      const newUnlocked = [...unlockedAchievements, achievementId];
      setUnlockedAchievements(newUnlocked);
      saveAchievements(newUnlocked);

      // Add to recent achievements
      const recentAchievement: RecentAchievement = {
        achievement,
        unlockedAt: new Date().toISOString(),
      };
      setRecentAchievements((prev) => [recentAchievement, ...prev.slice(0, 9)]); // Keep last 10

      // Update total points
      const newStats = {
        ...stats,
        totalPoints: stats.totalPoints + achievement.points,
        lastAchievementUnlocked: achievementId,
      };
      setStats(newStats);
      saveStats(newStats);

      // Could trigger notification/toast here
      console.log(`🎉 Achievement Unlocked: ${achievement.name}`);

      return true;
    },
    [unlockedAchievements, stats, isUnlocked, saveAchievements, saveStats]
  );

  /**
   * Check conditions and auto-unlock achievements
   */
  const checkAndUnlockAchievements = useCallback(() => {
    ACHIEVEMENTS.forEach((achievement) => {
      if (isUnlocked(achievement.id)) return;

      const { condition } = achievement;
      let shouldUnlock = false;

      switch (condition.type) {
        case 'message_count':
          shouldUnlock = stats.messageCount >= condition.value;
          break;
        case 'conversation_count':
          shouldUnlock = stats.conversationCount >= condition.value;
          break;
        case 'daily_streak':
          shouldUnlock = stats.dailyStreak >= condition.value;
          break;
        case 'session_length':
          shouldUnlock = stats.longestSessionMinutes >= condition.value;
          break;
        case 'word_count':
          shouldUnlock = stats.wordCount >= condition.value;
          break;
        case 'topic_diversity':
          shouldUnlock = stats.topicsDiversityCount >= condition.value;
          break;
        case 'emoji_usage':
          shouldUnlock = stats.emojiUsageCount >= condition.value;
          break;
        case 'questions_asked':
          shouldUnlock = stats.questionsAskedCount >= condition.value;
          break;
        case 'stories_shared':
          shouldUnlock = stats.storiesSharedCount >= condition.value;
          break;
        case 'profile_complete':
          shouldUnlock = stats.profileCompleteness >= condition.value;
          break;
        case 'avatar_changes':
          shouldUnlock = stats.avatarChangesCount >= condition.value;
          break;
        case 'time_of_day':
          // Check current hour
          const hour = new Date().getHours();
          if (condition.description === 'before_8am') {
            shouldUnlock = hour < 8;
          } else if (condition.description === 'after_10pm') {
            shouldUnlock = hour >= 22;
          }
          break;
        case 'special_date':
          // Would need additional logic for birthday, etc.
          break;
        default:
          shouldUnlock = false;
      }

      if (shouldUnlock) {
        unlockAchievement(achievement.id);
      }
    });
  }, [stats, isUnlocked, unlockAchievement]);

  /**
   * Update stats
   */
  const updateStats = useCallback(
    (updates: Partial<UserStats>) => {
      const newStats = { ...stats, ...updates };
      setStats(newStats);
      saveStats(newStats);
    },
    [stats, saveStats]
  );

  /**
   * Increment a stat value
   */
  const incrementStat = useCallback(
    (stat: keyof UserStats, amount: number = 1) => {
      const currentValue = stats[stat];
      if (typeof currentValue === 'number') {
        updateStats({ [stat]: currentValue + amount } as Partial<UserStats>);
      }
    },
    [stats, updateStats]
  );

  /**
   * Reset all achievement progress (for testing/demo)
   */
  const resetAllProgress = useCallback(() => {
    setUnlockedAchievements([]);
    setRecentAchievements([]);
    setStats(DEFAULT_STATS);
    localStorage.removeItem(ACHIEVEMENT_STORAGE_KEY);
    localStorage.removeItem(STATS_STORAGE_KEY);
  }, []);

  return (
    <AchievementContext.Provider
      value={{
        unlockedAchievements,
        recentAchievements,
        stats,
        unlockAchievement,
        checkAndUnlockAchievements,
        updateStats,
        incrementStat,
        resetAllProgress,
        isUnlocked,
        getProgress,
      }}
    >
      {children}
    </AchievementContext.Provider>
  );
};

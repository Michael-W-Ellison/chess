/**
 * LoginContext
 * Manages daily login tracking and history
 */

import React, { createContext, useState, useCallback, ReactNode } from 'react';
import {
  calculateCurrentStreak,
  calculateLongestStreak,
  getTodayISO,
} from '../../shared/streakUtils';

const LOGIN_STORAGE_KEY = 'user_login_history';

export interface LoginRecord {
  date: string; // ISO date string (YYYY-MM-DD)
  timestamp: number; // Unix timestamp
  sessionCount: number; // Number of sessions that day
}

export interface LoginStats {
  totalLogins: number;
  currentStreak: number;
  longestStreak: number;
  lastLoginDate: string | null;
  loginHistory: LoginRecord[];
  thisWeekLogins: number;
  thisMonthLogins: number;
}

interface LoginContextType {
  stats: LoginStats;
  recordLogin: () => void;
  getLoginHistory: (days?: number) => LoginRecord[];
  hasLoggedInToday: () => boolean;
  getCalendarData: (month: number, year: number) => Map<string, LoginRecord>;
  resetLoginHistory: () => void;
}

const DEFAULT_STATS: LoginStats = {
  totalLogins: 0,
  currentStreak: 0,
  longestStreak: 0,
  lastLoginDate: null,
  loginHistory: [],
  thisWeekLogins: 0,
  thisMonthLogins: 0,
};

/**
 * Calculate statistics from login history
 */
function calculateStats(history: LoginRecord[]): LoginStats {
  if (history.length === 0) {
    return DEFAULT_STATS;
  }

  // Sort by date descending
  const sortedHistory = [...history].sort((a, b) => b.date.localeCompare(a.date));

  // Use centralized streak calculation utilities
  const currentStreak = calculateCurrentStreak(history);
  const longestStreak = calculateLongestStreak(history);

  // Calculate this week's logins
  const today = getTodayISO();
  const todayTime = new Date(today).getTime();
  const weekAgo = new Date(todayTime - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
  const thisWeekLogins = sortedHistory.filter((record) => record.date >= weekAgo).length;

  // Calculate this month's logins
  const monthStart = new Date();
  monthStart.setDate(1);
  const monthStartStr = monthStart.toISOString().split('T')[0];
  const thisMonthLogins = sortedHistory.filter((record) => record.date >= monthStartStr).length;

  return {
    totalLogins: history.length,
    currentStreak,
    longestStreak,
    lastLoginDate: sortedHistory[0].date,
    loginHistory: sortedHistory,
    thisWeekLogins,
    thisMonthLogins,
  };
}

/**
 * Login history from localStorage, read when the provider is created so it is there on the
 * first render (App records the login on mount; loading it in an effect afterwards let that
 * login overwrite the stored history with only today's entry)
 */
function loadStoredStats(): LoginStats {
  try {
    const stored = localStorage.getItem(LOGIN_STORAGE_KEY);
    if (stored) {
      return calculateStats(JSON.parse(stored) as LoginRecord[]);
    }
  } catch (error) {
    console.error('Failed to load login history:', error);
  }
  return DEFAULT_STATS;
}

export const LoginContext = createContext<LoginContextType | undefined>(undefined);

interface LoginProviderProps {
  children: ReactNode;
}

export const LoginProvider: React.FC<LoginProviderProps> = ({ children }) => {
  const [stats, setStats] = useState<LoginStats>(loadStoredStats);

  /**
   * Save login history to localStorage
   */
  const saveLoginHistory = useCallback((history: LoginRecord[]) => {
    try {
      localStorage.setItem(LOGIN_STORAGE_KEY, JSON.stringify(history));
    } catch (error) {
      console.error('Failed to save login history:', error);
    }
  }, []);


  /**
   * Check if user has logged in today
   */
  const hasLoggedInToday = useCallback((): boolean => {
    const today = getTodayISO();
    return stats.loginHistory.some((record) => record.date === today);
  }, [stats.loginHistory]);

  /**
   * Record a login for today
   */
  const recordLogin = useCallback(() => {
    const today = getTodayISO();
    const now = Date.now();

    let updatedHistory = [...stats.loginHistory];
    const existingIndex = updatedHistory.findIndex((record) => record.date === today);

    if (existingIndex >= 0) {
      // Update existing record
      updatedHistory[existingIndex] = {
        ...updatedHistory[existingIndex],
        timestamp: now,
        sessionCount: updatedHistory[existingIndex].sessionCount + 1,
      };
    } else {
      // Add new record
      updatedHistory.push({
        date: today,
        timestamp: now,
        sessionCount: 1,
      });
    }

    // Limit history to last 365 days
    const yearAgo = new Date(now - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    updatedHistory = updatedHistory.filter((record) => record.date >= yearAgo);

    saveLoginHistory(updatedHistory);
    const newStats = calculateStats(updatedHistory);
    setStats(newStats);

    console.log(`📅 Login recorded for ${today}. Current streak: ${newStats.currentStreak} days`);
  }, [stats.loginHistory, saveLoginHistory]);

  /**
   * Get login history for the last N days
   */
  const getLoginHistory = useCallback(
    (days: number = 30): LoginRecord[] => {
      const cutoffDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000)
        .toISOString()
        .split('T')[0];
      return stats.loginHistory.filter((record) => record.date >= cutoffDate);
    },
    [stats.loginHistory]
  );

  /**
   * Get calendar data for a specific month and year
   */
  const getCalendarData = useCallback(
    (month: number, year: number): Map<string, LoginRecord> => {
      const calendarMap = new Map<string, LoginRecord>();

      stats.loginHistory.forEach((record) => {
        const recordDate = new Date(record.date);
        if (recordDate.getMonth() === month && recordDate.getFullYear() === year) {
          calendarMap.set(record.date, record);
        }
      });

      return calendarMap;
    },
    [stats.loginHistory]
  );

  /**
   * Reset login history (for testing/demo)
   */
  const resetLoginHistory = useCallback(() => {
    setStats(DEFAULT_STATS);
    localStorage.removeItem(LOGIN_STORAGE_KEY);
    console.log('🔄 Login history reset');
  }, []);

  return (
    <LoginContext.Provider
      value={{
        stats,
        recordLogin,
        getLoginHistory,
        hasLoggedInToday,
        getCalendarData,
        resetLoginHistory,
      }}
    >
      {children}
    </LoginContext.Provider>
  );
};

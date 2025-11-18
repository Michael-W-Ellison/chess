/**
 * Streak Calculation Utilities
 * Centralized logic for calculating and managing streaks
 */

export interface StreakRecord {
  date: string; // ISO date string (YYYY-MM-DD)
  timestamp: number; // Unix timestamp
  type?: string; // Type of activity (login, chat, exercise, etc.)
}

export interface StreakResult {
  currentStreak: number;
  longestStreak: number;
  lastActivityDate: string | null;
  isActiveToday: boolean;
  streakHistory: StreakPeriod[];
}

export interface StreakPeriod {
  startDate: string;
  endDate: string;
  length: number;
}

export interface StreakOptions {
  allowWeekendGracePeriod?: boolean; // Allow skipping weekends
  gracePeriodDays?: number; // Allow missing N days (e.g., 1 = freeze)
  includeFutureDates?: boolean; // Whether to count dates in the future
  timezone?: string; // Timezone for date calculations
}

/**
 * Get today's date in ISO format (YYYY-MM-DD) in local timezone
 */
export function getTodayISO(): string {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

/**
 * Get yesterday's date in ISO format
 */
export function getYesterdayISO(): string {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return yesterday.toISOString().split('T')[0];
}

/**
 * Parse ISO date string to Date object
 */
export function parseISODate(dateStr: string): Date {
  return new Date(dateStr + 'T00:00:00');
}

/**
 * Get day difference between two ISO date strings
 */
export function getDayDifference(date1: string, date2: string): number {
  const d1 = parseISODate(date1);
  const d2 = parseISODate(date2);
  const diffTime = Math.abs(d2.getTime() - d1.getTime());
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Check if a date is a weekend (Saturday or Sunday)
 */
export function isWeekend(dateStr: string): boolean {
  const date = parseISODate(dateStr);
  const day = date.getDay();
  return day === 0 || day === 6; // Sunday or Saturday
}

/**
 * Check if dates are consecutive, considering options
 */
export function areConsecutive(
  date1: string,
  date2: string,
  options: StreakOptions = {}
): boolean {
  const dayDiff = getDayDifference(date1, date2);

  if (dayDiff === 1) {
    return true; // Perfectly consecutive
  }

  if (options.gracePeriodDays && dayDiff <= options.gracePeriodDays + 1) {
    return true; // Within grace period
  }

  if (options.allowWeekendGracePeriod && dayDiff <= 3) {
    // Check if the gap is only weekends
    const d1 = parseISODate(date1);
    const d2 = parseISODate(date2);
    const [earlier, later] = d1 < d2 ? [d1, d2] : [d2, d1];

    let hasNonWeekendGap = false;
    for (let i = 1; i < dayDiff; i++) {
      const checkDate = new Date(earlier);
      checkDate.setDate(earlier.getDate() + i);
      const checkDateStr = checkDate.toISOString().split('T')[0];
      if (!isWeekend(checkDateStr)) {
        hasNonWeekendGap = true;
        break;
      }
    }

    return !hasNonWeekendGap;
  }

  return false;
}

/**
 * Calculate current streak from a list of activity records
 */
export function calculateCurrentStreak(
  records: StreakRecord[],
  options: StreakOptions = {}
): number {
  if (records.length === 0) return 0;

  // Sort records by date descending (most recent first)
  const sortedRecords = [...records].sort((a, b) => b.date.localeCompare(a.date));

  const today = getTodayISO();
  let currentStreak = 0;

  // Check if there's activity today
  if (sortedRecords[0].date === today) {
    currentStreak = 1;
  } else if (areConsecutive(sortedRecords[0].date, today, options)) {
    // If yesterday or within grace period, start counting
    currentStreak = 1;
  } else {
    // Streak is broken
    return 0;
  }

  // Count consecutive days backwards
  for (let i = 1; i < sortedRecords.length; i++) {
    const prevDate = sortedRecords[i - 1].date;
    const currDate = sortedRecords[i].date;

    if (areConsecutive(currDate, prevDate, options)) {
      currentStreak++;
    } else {
      break;
    }
  }

  return currentStreak;
}

/**
 * Calculate longest streak from a list of activity records
 */
export function calculateLongestStreak(
  records: StreakRecord[],
  options: StreakOptions = {}
): number {
  if (records.length === 0) return 0;

  // Sort records by date ascending
  const sortedRecords = [...records].sort((a, b) => a.date.localeCompare(b.date));

  let longestStreak = 1;
  let currentStreak = 1;

  for (let i = 1; i < sortedRecords.length; i++) {
    const prevDate = sortedRecords[i - 1].date;
    const currDate = sortedRecords[i].date;

    if (areConsecutive(prevDate, currDate, options)) {
      currentStreak++;
      longestStreak = Math.max(longestStreak, currentStreak);
    } else {
      currentStreak = 1;
    }
  }

  return longestStreak;
}

/**
 * Find all streak periods from activity records
 */
export function findStreakPeriods(
  records: StreakRecord[],
  options: StreakOptions = {}
): StreakPeriod[] {
  if (records.length === 0) return [];

  const sortedRecords = [...records].sort((a, b) => a.date.localeCompare(b.date));
  const periods: StreakPeriod[] = [];

  let currentPeriod = {
    startDate: sortedRecords[0].date,
    endDate: sortedRecords[0].date,
    length: 1,
  };

  for (let i = 1; i < sortedRecords.length; i++) {
    const prevDate = sortedRecords[i - 1].date;
    const currDate = sortedRecords[i].date;

    if (areConsecutive(prevDate, currDate, options)) {
      currentPeriod.endDate = currDate;
      currentPeriod.length++;
    } else {
      periods.push({ ...currentPeriod });
      currentPeriod = {
        startDate: currDate,
        endDate: currDate,
        length: 1,
      };
    }
  }

  periods.push(currentPeriod);
  return periods;
}

/**
 * Calculate comprehensive streak statistics
 */
export function calculateStreakStats(
  records: StreakRecord[],
  options: StreakOptions = {}
): StreakResult {
  const currentStreak = calculateCurrentStreak(records, options);
  const longestStreak = calculateLongestStreak(records, options);
  const streakHistory = findStreakPeriods(records, options);
  const today = getTodayISO();

  const sortedRecords = [...records].sort((a, b) => b.date.localeCompare(a.date));
  const lastActivityDate = sortedRecords.length > 0 ? sortedRecords[0].date : null;
  const isActiveToday = lastActivityDate === today;

  return {
    currentStreak,
    longestStreak,
    lastActivityDate,
    isActiveToday,
    streakHistory,
  };
}

/**
 * Check if streak is at risk (last activity was yesterday or before with no grace left)
 */
export function isStreakAtRisk(
  records: StreakRecord[],
  options: StreakOptions = {}
): boolean {
  if (records.length === 0) return false;

  const sortedRecords = [...records].sort((a, b) => b.date.localeCompare(a.date));
  const lastActivityDate = sortedRecords[0].date;
  const today = getTodayISO();

  if (lastActivityDate === today) {
    return false; // Already active today, no risk
  }

  const yesterday = getYesterdayISO();
  if (lastActivityDate === yesterday) {
    return true; // Need to act today to maintain streak
  }

  // Check if within grace period
  if (options.gracePeriodDays) {
    const daysSinceActivity = getDayDifference(lastActivityDate, today);
    return daysSinceActivity === options.gracePeriodDays;
  }

  return false;
}

/**
 * Get streak milestone (e.g., 7, 30, 100 days)
 */
export function getStreakMilestone(streakLength: number): number | null {
  const milestones = [3, 5, 7, 10, 14, 21, 30, 50, 60, 75, 100, 150, 200, 250, 365, 500, 1000];

  for (const milestone of milestones) {
    if (streakLength === milestone) {
      return milestone;
    }
  }

  return null;
}

/**
 * Get next streak milestone
 */
export function getNextMilestone(streakLength: number): number {
  const milestones = [3, 5, 7, 10, 14, 21, 30, 50, 60, 75, 100, 150, 200, 250, 365, 500, 1000];

  for (const milestone of milestones) {
    if (streakLength < milestone) {
      return milestone;
    }
  }

  return streakLength + 100; // If beyond all milestones, add 100
}

/**
 * Get progress to next milestone (0-100)
 */
export function getProgressToNextMilestone(streakLength: number): {
  nextMilestone: number;
  progress: number;
  daysRemaining: number;
} {
  const nextMilestone = getNextMilestone(streakLength);
  const previousMilestone = getNextMilestone(0); // Start from first milestone

  let prev = 0;
  const milestones = [3, 5, 7, 10, 14, 21, 30, 50, 60, 75, 100, 150, 200, 250, 365, 500, 1000];
  for (const milestone of milestones) {
    if (milestone > streakLength) {
      break;
    }
    prev = milestone;
  }

  const range = nextMilestone - prev;
  const current = streakLength - prev;
  const progress = range > 0 ? Math.round((current / range) * 100) : 0;
  const daysRemaining = nextMilestone - streakLength;

  return {
    nextMilestone,
    progress,
    daysRemaining,
  };
}

/**
 * Format streak message
 */
export function getStreakMessage(streakLength: number): string {
  if (streakLength === 0) return "Start your streak today!";
  if (streakLength === 1) return "Great start! Come back tomorrow!";
  if (streakLength < 7) return `${streakLength} days strong! Keep it up!`;
  if (streakLength < 30) return `Amazing! ${streakLength}-day streak!`;
  if (streakLength < 100) return `Incredible! ${streakLength} days in a row!`;
  if (streakLength < 365) return `Legendary! ${streakLength}-day streak!`;
  return `🔥 UNSTOPPABLE! ${streakLength} days! 🔥`;
}

/**
 * Get streak emoji based on length
 */
export function getStreakEmoji(streakLength: number): string {
  if (streakLength === 0) return "💤";
  if (streakLength < 3) return "🔥";
  if (streakLength < 7) return "🔥🔥";
  if (streakLength < 30) return "🔥🔥🔥";
  if (streakLength < 100) return "⚡⚡⚡";
  if (streakLength < 365) return "💎💎💎";
  return "👑👑👑";
}

export default {
  getTodayISO,
  getYesterdayISO,
  parseISODate,
  getDayDifference,
  isWeekend,
  areConsecutive,
  calculateCurrentStreak,
  calculateLongestStreak,
  findStreakPeriods,
  calculateStreakStats,
  isStreakAtRisk,
  getStreakMilestone,
  getNextMilestone,
  getProgressToNextMilestone,
  getStreakMessage,
  getStreakEmoji,
};

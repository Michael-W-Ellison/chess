/**
 * Shared utility functions
 * Used by both main process and renderer process
 */

import { FriendshipLevelLabel, Mood } from './types';
import { FRIENDSHIP_LEVELS } from './constants';

// ============================================================================
// Date and Time Utilities
// ============================================================================

/**
 * Calculate hours between two dates
 */
export function getHoursBetween(date1: Date, date2: Date): number {
  const msPerHour = 1000 * 60 * 60;
  return Math.abs(date2.getTime() - date1.getTime()) / msPerHour;
}

/**
 * Calculate days between two dates
 */
export function getDaysBetween(date1: Date, date2: Date): number {
  return Math.floor(getHoursBetween(date1, date2) / 24);
}

/**
 * Format date to readable string
 */
export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format time to readable string
 */
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format duration in seconds to readable string
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} seconds`;
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? '' : 's'}`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours} hour${hours === 1 ? '' : 's'}${remainingMinutes > 0 ? ` ${remainingMinutes} min` : ''}`;
}

// ============================================================================
// Friendship Level Utilities
// ============================================================================

/**
 * Get friendship level label from level number
 */
export function getFriendshipLabel(level: number): FriendshipLevelLabel {
  if (level <= 2) return 'New Friends';
  if (level <= 4) return 'Good Friends';
  if (level <= 6) return 'Close Friends';
  if (level <= 8) return 'Best Friends';
  return 'Lifelong Friends';
}

/**
 * Get friendship level color
 */
export function getFriendshipColor(level: number): string {
  if (level <= 2) return '#fbbf24'; // yellow
  if (level <= 4) return '#fb923c'; // orange
  if (level <= 6) return '#f472b6'; // pink
  if (level <= 8) return '#ec4899'; // pink-600
  return '#dc2626'; // red
}

/**
 * Calculate friendship level from conversation count
 */
export function calculateFriendshipLevel(conversationCount: number): number {
  for (let i = FRIENDSHIP_LEVELS.length - 1; i >= 0; i--) {
    const levelData = FRIENDSHIP_LEVELS[i];
    if (conversationCount >= levelData.minConversations) {
      return levelData.level;
    }
  }
  return 1;
}

/**
 * Check if a feature is unlocked at current friendship level
 */
export function isFeatureUnlocked(feature: string, friendshipLevel: number): boolean {
  const levelData = FRIENDSHIP_LEVELS.find(l => l.level === friendshipLevel);
  return levelData?.unlockedFeatures.includes(feature) ?? false;
}

// ============================================================================
// Personality Utilities
// ============================================================================

/**
 * Get description for humor level
 */
export function getHumorDescription(humor: number): string {
  if (humor < 0.3) return 'rarely jokes';
  if (humor < 0.5) return 'occasional humor';
  if (humor < 0.7) return 'frequently funny';
  return 'very humorous';
}

/**
 * Get description for energy level
 */
export function getEnergyDescription(energy: number): string {
  if (energy < 0.4) return 'calm and relaxed';
  if (energy < 0.6) return 'moderately energetic';
  if (energy < 0.8) return 'very energetic';
  return 'extremely enthusiastic';
}

/**
 * Get description for curiosity level
 */
export function getCuriosityDescription(curiosity: number): string {
  if (curiosity < 0.3) return 'rarely asks questions';
  if (curiosity < 0.5) return 'somewhat curious';
  if (curiosity < 0.7) return 'very curious';
  return 'extremely inquisitive';
}

/**
 * Get description for formality level
 */
export function getFormalityDescription(formality: number): string {
  if (formality < 0.3) return 'very casual';
  if (formality < 0.5) return 'casual';
  if (formality < 0.7) return 'somewhat formal';
  return 'very formal';
}

// ============================================================================
// Text Processing Utilities
// ============================================================================

/**
 * Extract keywords from text (simple implementation)
 */
export function extractKeywords(text: string, stopWords?: string[]): string[] {
  const defaultStopWords = new Set([
    'i', 'me', 'my', 'we', 'you', 'the', 'a', 'an', 'and', 'or', 'but',
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did',
    'to', 'from', 'in', 'on', 'at', 'for', 'with', 'about',
  ]);

  const stops = stopWords ? new Set(stopWords) : defaultStopWords;

  const words = text
    .toLowerCase()
    .replace(/[^\w\s]/g, '') // Remove punctuation
    .split(/\s+/)
    .filter(word => word.length > 3 && !stops.has(word));

  // Remove duplicates and return top keywords
  return Array.from(new Set(words)).slice(0, 5);
}

/**
 * Truncate text to maximum length with ellipsis
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

/**
 * Count sentences in text
 */
export function countSentences(text: string): number {
  const sentences = text.match(/[^.!?]+[.!?]+/g);
  return sentences ? sentences.length : 0;
}

/**
 * Capitalize first letter of string
 */
export function capitalizeFirst(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// ============================================================================
// Validation Utilities
// ============================================================================

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate age is appropriate (9-13)
 */
export function isValidAge(age: number): boolean {
  return age >= 9 && age <= 13;
}

/**
 * Validate grade (typically 4-8 for ages 9-13)
 */
export function isValidGrade(grade: number): boolean {
  return grade >= 1 && grade <= 12;
}

// ============================================================================
// Random Utilities
// ============================================================================

/**
 * Get random integer between min and max (inclusive)
 */
export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/**
 * Get random float between min and max
 */
export function randomFloat(min: number, max: number): number {
  return Math.random() * (max - min) + min;
}

/**
 * Get random item from array
 */
export function randomItem<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)];
}

/**
 * Shuffle array (Fisher-Yates algorithm)
 */
export function shuffleArray<T>(array: T[]): T[] {
  const result = [...array];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}

// ============================================================================
// Object Utilities
// ============================================================================

/**
 * Deep clone an object
 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if object is empty
 */
export function isEmpty(obj: Record<string, any>): boolean {
  return Object.keys(obj).length === 0;
}

/**
 * Merge objects deeply
 */
export function deepMerge<T extends Record<string, any>>(
  target: T,
  source: Partial<T>
): T {
  const result = { ...target };

  for (const key in source) {
    if (source.hasOwnProperty(key)) {
      const sourceValue = source[key];
      const targetValue = result[key];

      if (
        sourceValue &&
        typeof sourceValue === 'object' &&
        !Array.isArray(sourceValue) &&
        targetValue &&
        typeof targetValue === 'object' &&
        !Array.isArray(targetValue)
      ) {
        result[key] = deepMerge(targetValue, sourceValue);
      } else {
        result[key] = sourceValue as T[Extract<keyof T, string>];
      }
    }
  }

  return result;
}

// ============================================================================
// Promise Utilities
// ============================================================================

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      const delay = baseDelay * Math.pow(2, i);
      await sleep(delay);
    }
  }
  throw new Error('Max retries exceeded');
}

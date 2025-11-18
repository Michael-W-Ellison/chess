/**
 * StreakDisplay Component
 * Visual display of streak information with animations
 */

import React, { useState, useEffect } from 'react';
import { StreakType } from '../contexts/StreakContext';
import { useStreak } from '../hooks/useStreak';
import { getStreakMessage, getStreakEmoji } from '../../shared/streakUtils';

interface StreakDisplayProps {
  type: StreakType;
  showProgress?: boolean;
  showRisk?: boolean;
  compact?: boolean;
  animated?: boolean;
}

export const StreakDisplay: React.FC<StreakDisplayProps> = ({
  type,
  showProgress = true,
  showRisk = true,
  compact = false,
  animated = true,
}) => {
  const { getStats, checkStreakRisk, getMilestoneInfo } = useStreak();
  const stats = getStats(type);
  const isAtRisk = showRisk && checkStreakRisk(type);
  const milestoneInfo = getMilestoneInfo(type);

  const [isAnimating, setIsAnimating] = useState(false);

  // Trigger animation on streak change
  useEffect(() => {
    if (animated && stats.currentStreak > 0) {
      setIsAnimating(true);
      const timer = setTimeout(() => setIsAnimating(false), 500);
      return () => clearTimeout(timer);
    }
  }, [stats.currentStreak, animated]);

  const getTypeLabel = (type: StreakType): string => {
    switch (type) {
      case 'login':
        return 'Login Streak';
      case 'chat':
        return 'Chat Streak';
      case 'exercise':
        return 'Exercise Streak';
      case 'study':
        return 'Study Streak';
      default:
        return 'Streak';
    }
  };

  const getTypeColor = (type: StreakType): string => {
    switch (type) {
      case 'login':
        return 'from-blue-500 to-purple-500';
      case 'chat':
        return 'from-green-500 to-teal-500';
      case 'exercise':
        return 'from-orange-500 to-red-500';
      case 'study':
        return 'from-indigo-500 to-blue-500';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <span className={`text-2xl ${isAnimating ? 'animate-bounce' : ''}`}>
          {getStreakEmoji(stats.currentStreak)}
        </span>
        <div>
          <div className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {stats.currentStreak} {stats.currentStreak === 1 ? 'day' : 'days'}
          </div>
          {isAtRisk && (
            <div className="text-xs text-red-600 dark:text-red-400 font-medium">
              ⚠️ Streak at risk!
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">
          {getTypeLabel(type)}
        </h3>
        <span className={`text-3xl ${isAnimating ? 'animate-bounce' : ''}`}>
          {getStreakEmoji(stats.currentStreak)}
        </span>
      </div>

      {/* Main Streak Display */}
      <div
        className={`relative bg-gradient-to-br ${getTypeColor(type)} rounded-lg p-6 text-white mb-4 overflow-hidden`}
      >
        {/* Animated background effect */}
        {stats.currentStreak > 0 && (
          <div className="absolute inset-0 bg-white opacity-10 animate-pulse" />
        )}

        <div className="relative z-10">
          <div className="text-5xl font-bold mb-2 flex items-baseline gap-2">
            {stats.currentStreak}
            <span className="text-2xl font-normal opacity-90">
              {stats.currentStreak === 1 ? 'day' : 'days'}
            </span>
          </div>
          <div className="text-sm opacity-90">{getStreakMessage(stats.currentStreak)}</div>
        </div>

        {/* Fire particles effect for high streaks */}
        {stats.currentStreak >= 7 && (
          <div className="absolute top-2 right-2 flex gap-1">
            {[...Array(Math.min(5, Math.floor(stats.currentStreak / 7)))].map((_, i) => (
              <span
                key={i}
                className="text-yellow-300 text-xl animate-pulse"
                style={{ animationDelay: `${i * 0.2}s` }}
              >
                ✨
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Longest Streak</div>
          <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {stats.longestStreak}
          </div>
        </div>
        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
          <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Total Periods</div>
          <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {stats.streakHistory.length}
          </div>
        </div>
      </div>

      {/* Progress to Next Milestone */}
      {showProgress && stats.currentStreak > 0 && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Next Milestone: {milestoneInfo.next} days
            </span>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              {milestoneInfo.daysRemaining} more
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full bg-gradient-to-r ${getTypeColor(type)} transition-all duration-500 rounded-full`}
              style={{ width: `${milestoneInfo.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Risk Warning */}
      {isAtRisk && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
          <span className="text-xl">⚠️</span>
          <div>
            <div className="text-sm font-semibold text-red-900 dark:text-red-200">
              Streak at Risk!
            </div>
            <div className="text-xs text-red-700 dark:text-red-300 mt-1">
              Complete your {type} activity today to keep your streak alive!
            </div>
          </div>
        </div>
      )}

      {/* Last Activity */}
      {stats.lastActivityDate && (
        <div className="mt-3 text-xs text-gray-500 dark:text-gray-400 text-center">
          Last activity: {new Date(stats.lastActivityDate).toLocaleDateString()}
        </div>
      )}
    </div>
  );
};

export default StreakDisplay;

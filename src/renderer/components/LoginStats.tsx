/**
 * LoginStats Component
 * Displays login statistics and streaks
 */

import React from 'react';
import { useLogin } from '../hooks/useLogin';

interface LoginStatsProps {
  compact?: boolean;
}

export const LoginStats: React.FC<LoginStatsProps> = ({ compact = false }) => {
  const { stats } = useLogin();

  if (compact) {
    return (
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {stats.currentStreak}
          </div>
          <div className="text-xs text-blue-700 dark:text-blue-300 font-medium">
            Day Streak 🔥
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-3 border border-purple-200 dark:border-purple-800">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {stats.totalLogins}
          </div>
          <div className="text-xs text-purple-700 dark:text-purple-300 font-medium">
            Total Logins 📅
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Main Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-xl p-4 border border-orange-200 dark:border-orange-800 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🔥</span>
            <span className="text-xs font-semibold text-orange-700 dark:text-orange-300">
              Current Streak
            </span>
          </div>
          <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">
            {stats.currentStreak}
          </div>
          <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
            {stats.currentStreak === 1 ? 'day' : 'days'}
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-xl p-4 border border-green-200 dark:border-green-800 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🏆</span>
            <span className="text-xs font-semibold text-green-700 dark:text-green-300">
              Longest Streak
            </span>
          </div>
          <div className="text-3xl font-bold text-green-600 dark:text-green-400">
            {stats.longestStreak}
          </div>
          <div className="text-xs text-green-600 dark:text-green-400 mt-1">
            {stats.longestStreak === 1 ? 'day' : 'days'}
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📅</span>
            <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
              Total Logins
            </span>
          </div>
          <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
            {stats.totalLogins}
          </div>
          <div className="text-xs text-blue-600 dark:text-blue-400 mt-1">
            all time
          </div>
        </div>

        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-xl p-4 border border-purple-200 dark:border-purple-800 shadow-sm">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">📊</span>
            <span className="text-xs font-semibold text-purple-700 dark:text-purple-300">
              This Week
            </span>
          </div>
          <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
            {stats.thisWeekLogins}
          </div>
          <div className="text-xs text-purple-600 dark:text-purple-400 mt-1">
            {stats.thisWeekLogins === 1 ? 'day' : 'days'}
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              This Month
            </span>
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {stats.thisMonthLogins} days
            </span>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Last Login
            </span>
            <span className="text-lg font-bold text-gray-900 dark:text-gray-100">
              {stats.lastLoginDate
                ? new Date(stats.lastLoginDate).toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                  })
                : 'Never'}
            </span>
          </div>
        </div>
      </div>

      {/* Motivational Message */}
      {stats.currentStreak > 0 && (
        <div className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg p-4 border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🎉</span>
            <div>
              <p className="text-sm font-semibold text-yellow-900 dark:text-yellow-200">
                {stats.currentStreak === 1 && "Great start! Come back tomorrow to build your streak!"}
                {stats.currentStreak >= 2 && stats.currentStreak < 7 && `Amazing! You're on a ${stats.currentStreak}-day streak!`}
                {stats.currentStreak >= 7 && stats.currentStreak < 30 && `Incredible! ${stats.currentStreak} days in a row! Keep it up!`}
                {stats.currentStreak >= 30 && `Wow! ${stats.currentStreak} days! You're a champion!`}
              </p>
              <p className="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
                Daily practice builds strong chess skills!
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginStats;

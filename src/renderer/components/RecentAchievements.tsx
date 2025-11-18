/**
 * RecentAchievements Component
 * Displays recently unlocked achievements
 */

import React from 'react';
import { useAchievements } from '../hooks/useAchievements';
import { TIER_COLORS } from '../../shared/achievements';

interface RecentAchievementsProps {
  limit?: number;
  compact?: boolean;
}

export const RecentAchievements: React.FC<RecentAchievementsProps> = ({
  limit = 5,
  compact = false,
}) => {
  const { recentAchievements } = useAchievements();
  const displayedAchievements = recentAchievements.slice(0, limit);

  if (displayedAchievements.length === 0) {
    return (
      <div className="text-center py-6 text-gray-500 dark:text-gray-400">
        <div className="text-4xl mb-2">🏆</div>
        <p className="text-sm">No achievements unlocked yet</p>
        <p className="text-xs mt-1">Start chatting to earn your first achievement!</p>
      </div>
    );
  }

  if (compact) {
    return (
      <div className="space-y-2">
        {displayedAchievements.map((recent, index) => {
          const tierColors = TIER_COLORS[recent.achievement.tier];
          const timeAgo = getTimeAgo(recent.unlockedAt);

          return (
            <div
              key={`${recent.achievement.id}-${index}`}
              className="flex items-center gap-3 p-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
            >
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center text-xl shadow-sm"
                style={{ backgroundColor: tierColors.bg }}
              >
                {recent.achievement.emoji}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold text-gray-800 dark:text-gray-200 truncate">
                  {recent.achievement.name}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">{timeAgo}</div>
              </div>
              <div
                className="text-xs font-bold px-2 py-1 rounded"
                style={{
                  backgroundColor: tierColors.border,
                  color: tierColors.text,
                }}
              >
                +{recent.achievement.points}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {displayedAchievements.map((recent, index) => {
        const tierColors = TIER_COLORS[recent.achievement.tier];
        const timeAgo = getTimeAgo(recent.unlockedAt);

        return (
          <div
            key={`${recent.achievement.id}-${index}`}
            className="flex items-start gap-4 p-4 rounded-lg bg-gradient-to-r from-white to-gray-50 dark:from-gray-800 dark:to-gray-750 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-all"
            style={{
              borderLeftWidth: '4px',
              borderLeftColor: tierColors.border,
            }}
          >
            <div
              className="w-16 h-16 rounded-xl flex items-center justify-center text-3xl shadow-md flex-shrink-0"
              style={{
                backgroundColor: tierColors.bg,
                boxShadow: `0 4px 12px ${tierColors.glow}`,
              }}
            >
              {recent.achievement.emoji}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className="text-base font-bold text-gray-800 dark:text-gray-200">
                  {recent.achievement.name}
                </h4>
                <div
                  className="text-sm font-bold px-2 py-1 rounded whitespace-nowrap"
                  style={{
                    backgroundColor: tierColors.border,
                    color: tierColors.text,
                  }}
                >
                  +{recent.achievement.points}
                </div>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                {recent.achievement.description}
              </p>
              <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1">
                  <span className="uppercase font-semibold" style={{ color: tierColors.border }}>
                    {recent.achievement.tier}
                  </span>
                </span>
                <span>•</span>
                <span>{timeAgo}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * Helper function to format time ago
 */
function getTimeAgo(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

export default RecentAchievements;

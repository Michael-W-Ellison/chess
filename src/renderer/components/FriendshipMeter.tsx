/**
 * FriendshipMeter Component
 * Visual display of friendship level progression
 */

import React from 'react';
import type { PersonalityStats } from '../../shared/types';

interface FriendshipMeterProps {
  friendshipLevel: number; // 1-10
  stats: PersonalityStats;
}

export const FriendshipMeter: React.FC<FriendshipMeterProps> = ({
  friendshipLevel,
  stats,
}) => {
  // Calculate progress to next level
  const getLevelProgress = (): { current: number; next: number; percentage: number } => {
    const levelThresholds = [
      { level: 1, conversations: 0 },
      { level: 2, conversations: 5 },
      { level: 3, conversations: 15 },
      { level: 4, conversations: 30 },
      { level: 5, conversations: 50 },
      { level: 6, conversations: 75 },
      { level: 7, conversations: 100 },
      { level: 8, conversations: 125 },
      { level: 9, conversations: 150 },
      { level: 10, conversations: 151 },
    ];

    const currentThreshold = levelThresholds.find((t) => t.level === friendshipLevel);
    const nextThreshold = levelThresholds.find((t) => t.level === friendshipLevel + 1);

    if (!currentThreshold || !nextThreshold) {
      return { current: stats.totalConversations, next: 151, percentage: 100 };
    }

    const conversationsNeeded = nextThreshold.conversations - currentThreshold.conversations;
    const conversationsProgress = stats.totalConversations - currentThreshold.conversations;
    const percentage = Math.min(100, (conversationsProgress / conversationsNeeded) * 100);

    return {
      current: stats.totalConversations,
      next: nextThreshold.conversations,
      percentage: Math.max(0, percentage),
    };
  };

  const progress = getLevelProgress();

  // Level emoji/icon
  const getLevelIcon = (level: number): string => {
    if (level <= 2) return '🌱';
    if (level <= 4) return '🌿';
    if (level <= 6) return '🌳';
    if (level <= 8) return '⭐';
    return '👑';
  };

  // Level name
  const getLevelName = (level: number): string => {
    if (level <= 2) return 'New Friend';
    if (level <= 4) return 'Good Friend';
    if (level <= 6) return 'Close Friend';
    if (level <= 8) return 'Best Friend';
    return 'Lifelong Friend';
  };

  // Generate heart icons for visual level display
  const renderHearts = () => {
    const hearts = [];
    const totalLevels = 10;

    for (let i = 1; i <= totalLevels; i++) {
      const isFilled = i <= friendshipLevel;
      hearts.push(
        <div
          key={i}
          className={`transition-all duration-300 hover:scale-125 ${
            isFilled ? 'scale-110' : 'scale-100 opacity-40'
          }`}
        >
          <span
            className={`text-2xl ${
              isFilled
                ? 'text-pink-500 drop-shadow-md'
                : 'text-gray-300'
            }`}
            title={`Level ${i}${isFilled ? ' - Achieved!' : ''}`}
          >
            {isFilled ? '❤️' : '🤍'}
          </span>
        </div>
      );
    }

    return hearts;
  };

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-4xl">{getLevelIcon(friendshipLevel)}</span>
          <div>
            <h3 className="text-lg font-semibold text-gray-800">
              {getLevelName(friendshipLevel)}
            </h3>
            <p className="text-sm text-gray-600">Level {friendshipLevel} of 10</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-purple-600">{friendshipLevel}</div>
          <div className="text-xs text-gray-500">Friendship Level</div>
        </div>
      </div>

      {/* Heart icons visualization */}
      <div className="mb-4 pb-4 border-b border-purple-200">
        <div className="flex items-center justify-center gap-2 flex-wrap">
          {renderHearts()}
        </div>
        <div className="text-xs text-gray-500 text-center mt-2">
          {friendshipLevel} {friendshipLevel === 1 ? 'heart' : 'hearts'} earned
        </div>
      </div>

      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2 text-sm text-gray-600">
          <span>Progress to next level</span>
          <span className="font-medium">{Math.round(progress.percentage)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-500 ease-out rounded-full"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        {friendshipLevel < 10 && (
          <div className="mt-2 text-xs text-gray-500 text-center">
            {progress.current} / {progress.next} conversations
          </div>
        )}
        {friendshipLevel === 10 && (
          <div className="mt-2 text-xs text-purple-600 text-center font-medium">
            🎉 Max level reached!
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-purple-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-purple-600">
            {stats.totalConversations}
          </div>
          <div className="text-xs text-gray-600">Total Chats</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.totalMessages}</div>
          <div className="text-xs text-gray-600">Messages</div>
        </div>
      </div>

      {/* Time stats */}
      {stats.lastInteraction && (
        <div className="mt-4 pt-4 border-t border-purple-200">
          <div className="text-xs text-gray-600 text-center">
            Last chat:{' '}
            {new Date(stats.lastInteraction).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default FriendshipMeter;

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

// Level information including labels and descriptions
interface LevelInfo {
  level: number;
  label: string;
  icon: string;
  description: string;
  color: string;
}

const LEVEL_INFO: Record<number, LevelInfo> = {
  1: {
    level: 1,
    label: 'New Friend',
    icon: '🌱',
    description: "We're just getting to know each other! Let's chat and discover what we have in common.",
    color: 'green',
  },
  2: {
    level: 2,
    label: 'New Friend',
    icon: '🌱',
    description: "Getting more comfortable! I'm starting to learn about what makes you unique.",
    color: 'green',
  },
  3: {
    level: 3,
    label: 'Good Friend',
    icon: '🌿',
    description: "We're becoming good friends! I'm learning about your interests and what matters to you.",
    color: 'teal',
  },
  4: {
    level: 4,
    label: 'Good Friend',
    icon: '🌿',
    description: "Our friendship is growing! I remember more about you and can give better advice.",
    color: 'teal',
  },
  5: {
    level: 5,
    label: 'Close Friend',
    icon: '🌳',
    description: "We're close friends now! I understand your personality and can support you better.",
    color: 'blue',
  },
  6: {
    level: 6,
    label: 'Close Friend',
    icon: '🌳',
    description: "Our bond is strong! I know your goals, favorite things, and the people important to you.",
    color: 'blue',
  },
  7: {
    level: 7,
    label: 'Best Friend',
    icon: '⭐',
    description: "You're one of my best friends! I can anticipate what you need and celebrate your wins.",
    color: 'yellow',
  },
  8: {
    level: 8,
    label: 'Best Friend',
    icon: '⭐',
    description: "Amazing friendship! I'm here for all your adventures, challenges, and achievements.",
    color: 'yellow',
  },
  9: {
    level: 9,
    label: 'Lifelong Friend',
    icon: '👑',
    description: "We're lifelong friends! Our connection is deep and I treasure every conversation we have.",
    color: 'purple',
  },
  10: {
    level: 10,
    label: 'Lifelong Friend',
    icon: '👑',
    description: "Maximum friendship achieved! We've shared so much together. Thank you for being amazing!",
    color: 'purple',
  },
};

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

  // Get current level information
  const currentLevelInfo = LEVEL_INFO[friendshipLevel] || LEVEL_INFO[1];

  // Level emoji/icon
  const getLevelIcon = (level: number): string => {
    return LEVEL_INFO[level]?.icon || '🌱';
  };

  // Level name
  const getLevelName = (level: number): string => {
    return LEVEL_INFO[level]?.label || 'New Friend';
  };

  // Level description
  const getLevelDescription = (level: number): string => {
    return LEVEL_INFO[level]?.description || '';
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

      {/* Level Description */}
      <div className="mb-4 bg-white/60 rounded-lg p-4 border border-purple-100">
        <p className="text-sm text-gray-700 leading-relaxed text-center italic">
          {getLevelDescription(friendshipLevel)}
        </p>
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

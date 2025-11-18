/**
 * AchievementBadge Component
 * Displays a single achievement with unlock status and progress
 */

import React from 'react';
import { Achievement, TIER_COLORS, RARITY_COLORS } from '../../shared/achievements';

interface AchievementBadgeProps {
  achievement: Achievement;
  isUnlocked: boolean;
  progress?: number;
  size?: 'small' | 'medium' | 'large';
  showProgress?: boolean;
  onClick?: () => void;
}

export const AchievementBadge: React.FC<AchievementBadgeProps> = ({
  achievement,
  isUnlocked,
  progress = 0,
  size = 'medium',
  showProgress = true,
  onClick,
}) => {
  const tierColors = TIER_COLORS[achievement.tier];
  const rarityColor = achievement.rarity ? RARITY_COLORS[achievement.rarity] : null;

  const sizeConfig = {
    small: { container: 'w-20 h-20', emoji: 'text-3xl', text: 'text-xs', padding: 'p-2' },
    medium: { container: 'w-28 h-28', emoji: 'text-4xl', text: 'text-sm', padding: 'p-3' },
    large: { container: 'w-36 h-36', emoji: 'text-5xl', text: 'text-base', padding: 'p-4' },
  };

  const config = sizeConfig[size];

  return (
    <div
      className={`${onClick ? 'cursor-pointer' : ''} transition-all hover:scale-105`}
      onClick={onClick}
    >
      {/* Badge container */}
      <div className="flex flex-col items-center gap-2">
        {/* Badge */}
        <div
          className={`
            ${config.container} ${config.padding}
            rounded-lg relative
            ${isUnlocked ? '' : 'opacity-40 grayscale'}
            transition-all duration-300
            flex flex-col items-center justify-center
            shadow-md
          `}
          style={{
            backgroundColor: tierColors.bg,
            borderColor: tierColors.border,
            borderWidth: '2px',
            borderStyle: 'solid',
            boxShadow: isUnlocked ? `0 0 20px ${tierColors.glow}` : 'none',
          }}
        >
          {/* Emoji */}
          <div className={`${config.emoji} mb-1`}>{achievement.emoji}</div>

          {/* Tier indicator */}
          <div
            className="absolute top-1 right-1 px-1.5 py-0.5 rounded text-xs font-bold uppercase"
            style={{
              backgroundColor: tierColors.border,
              color: tierColors.text,
              fontSize: size === 'small' ? '0.6rem' : '0.65rem',
            }}
          >
            {achievement.tier}
          </div>

          {/* Lock overlay for locked achievements */}
          {!isUnlocked && (
            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-30 rounded-lg">
              <span className="text-2xl">🔒</span>
            </div>
          )}

          {/* New/Recently unlocked indicator */}
          {isUnlocked && (
            <div className="absolute -top-2 -left-2 animate-pulse">
              <span className="text-xl">✨</span>
            </div>
          )}
        </div>

        {/* Achievement name */}
        <div className="text-center max-w-full">
          <div
            className={`${config.text} font-semibold text-gray-800 dark:text-gray-200 truncate max-w-full px-1`}
            title={achievement.name}
          >
            {achievement.name}
          </div>

          {/* Points */}
          <div className="text-xs text-gray-600 dark:text-gray-400">{achievement.points} pts</div>
        </div>

        {/* Progress bar */}
        {showProgress && !isUnlocked && progress > 0 && (
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{
                width: `${progress}%`,
                backgroundColor: tierColors.bg,
              }}
            />
          </div>
        )}

        {/* Progress text */}
        {showProgress && !isUnlocked && (
          <div className="text-xs text-gray-500 dark:text-gray-400">{progress}%</div>
        )}
      </div>
    </div>
  );
};

export default AchievementBadge;

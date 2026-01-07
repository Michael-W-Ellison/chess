/**
 * AchievementNotification Component
 * Toast notification when an achievement is unlocked
 */

import React, { useEffect, useState } from 'react';
import { Achievement, TIER_COLORS } from '../../shared/achievements';

interface AchievementNotificationProps {
  achievement: Achievement;
  onClose: () => void;
  duration?: number;
}

export const AchievementNotification: React.FC<AchievementNotificationProps> = ({
  achievement,
  onClose,
  duration = 3000,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const tierColors = TIER_COLORS[achievement.tier];

  useEffect(() => {
    // Trigger entrance animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto-close after duration
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Wait for exit animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div
      className={`
        fixed top-4 right-4 z-50
        transform transition-all duration-300 ease-out
        ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
      `}
    >
      <div
        className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl border-2 p-4 max-w-sm"
        style={{
          borderColor: tierColors.border,
          boxShadow: `0 10px 40px ${tierColors.glow}, 0 0 20px ${tierColors.glow}`,
        }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div className="text-4xl animate-bounce">{achievement.emoji}</div>
          <div className="flex-1">
            <div className="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Achievement Unlocked!
            </div>
            <div className="text-lg font-bold text-gray-800 dark:text-gray-200">
              {achievement.name}
            </div>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(onClose, 300);
            }}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Description */}
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
          {achievement.description}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between">
          <div
            className="px-3 py-1 rounded-full text-xs font-bold uppercase"
            style={{
              backgroundColor: tierColors.bg,
              color: tierColors.text,
            }}
          >
            {achievement.tier}
          </div>
          <div className="text-sm font-semibold" style={{ color: tierColors.border }}>
            +{achievement.points} points
          </div>
        </div>

        {/* Celebration particles */}
        <div className="absolute -top-2 -right-2 text-2xl animate-pulse">✨</div>
        <div className="absolute -bottom-2 -left-2 text-2xl animate-pulse" style={{ animationDelay: '0.5s' }}>
          🎉
        </div>
      </div>
    </div>
  );
};

export default AchievementNotification;

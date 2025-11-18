/**
 * StreakMilestoneNotification Component
 * Celebrates streak milestones with animated notifications
 */

import React, { useEffect, useState } from 'react';
import { StreakType } from '../contexts/StreakContext';

interface StreakMilestoneNotificationProps {
  type: StreakType;
  milestone: number;
  onClose: () => void;
  duration?: number;
}

export const StreakMilestoneNotification: React.FC<StreakMilestoneNotificationProps> = ({
  type,
  milestone,
  onClose,
  duration = 6000,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Slide in animation
    setTimeout(() => setIsVisible(true), 10);

    // Auto-dismiss
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getTypeLabel = (type: StreakType): string => {
    switch (type) {
      case 'login':
        return 'Login';
      case 'chat':
        return 'Chat';
      case 'exercise':
        return 'Exercise';
      case 'study':
        return 'Study';
      default:
        return type;
    }
  };

  const getTypeColor = (type: StreakType): string => {
    switch (type) {
      case 'login':
        return 'from-blue-500 to-purple-600';
      case 'chat':
        return 'from-green-500 to-teal-600';
      case 'exercise':
        return 'from-orange-500 to-red-600';
      case 'study':
        return 'from-indigo-500 to-blue-600';
      default:
        return 'from-gray-500 to-gray-700';
    }
  };

  const getMilestoneEmoji = (milestone: number): string => {
    if (milestone >= 365) return '👑';
    if (milestone >= 100) return '💎';
    if (milestone >= 50) return '🏆';
    if (milestone >= 30) return '🎖️';
    if (milestone >= 7) return '⭐';
    return '🎉';
  };

  const getMilestoneMessage = (milestone: number): string => {
    if (milestone >= 365) return 'LEGENDARY YEAR!';
    if (milestone >= 100) return 'CENTURY CLUB!';
    if (milestone >= 50) return 'HALF CENTURY!';
    if (milestone >= 30) return 'MONTH MASTERY!';
    if (milestone >= 7) return 'WEEK WARRIOR!';
    return 'MILESTONE REACHED!';
  };

  return (
    <div
      className={`fixed top-4 right-4 z-50 transition-all duration-300 transform ${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
    >
      <div
        className={`bg-gradient-to-br ${getTypeColor(type)} text-white rounded-xl shadow-2xl overflow-hidden max-w-sm`}
      >
        {/* Animated sparkles background */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          {[...Array(8)].map((_, i) => (
            <span
              key={i}
              className="absolute text-2xl animate-ping"
              style={{
                top: `${Math.random() * 100}%`,
                left: `${Math.random() * 100}%`,
                animationDelay: `${i * 0.2}s`,
                animationDuration: '2s',
              }}
            >
              ✨
            </span>
          ))}
        </div>

        {/* Content */}
        <div className="relative z-10 p-6">
          <div className="flex items-start justify-between mb-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wide opacity-90 mb-1">
                {getTypeLabel(type)} Streak
              </div>
              <div className="text-2xl font-bold">{getMilestoneMessage(milestone)}</div>
            </div>
            <button
              onClick={() => {
                setIsVisible(false);
                setTimeout(onClose, 300);
              }}
              className="text-white/80 hover:text-white transition-colors"
            >
              ✕
            </button>
          </div>

          <div className="flex items-center gap-4 bg-white/20 backdrop-blur-sm rounded-lg p-4">
            <span className="text-6xl animate-bounce">{getMilestoneEmoji(milestone)}</span>
            <div>
              <div className="text-4xl font-bold mb-1">{milestone}</div>
              <div className="text-sm opacity-90">Days in a row!</div>
            </div>
          </div>

          <div className="mt-3 text-sm text-center opacity-90">
            {milestone >= 100 && "You're absolutely incredible! 🌟"}
            {milestone >= 30 && milestone < 100 && "Outstanding dedication! Keep crushing it! 💪"}
            {milestone >= 7 && milestone < 30 && "Amazing work! You're on fire! 🔥"}
            {milestone < 7 && "Fantastic progress! Keep it up! 🎊"}
          </div>
        </div>

        {/* Progress bar */}
        <div className="h-1 bg-white/20">
          <div
            className="h-full bg-white transition-all duration-300 ease-linear"
            style={{
              width: `${100 - ((Date.now() % duration) / duration) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
};

export default StreakMilestoneNotification;

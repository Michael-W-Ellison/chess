/**
 * StreakPanel Component
 * Displays all active streaks in one place
 */

import React, { useState } from 'react';
import { useStreak } from '../hooks/useStreak';
import { StreakType } from '../contexts/StreakContext';
import { StreakDisplay } from './StreakDisplay';
import { StreakMilestoneNotification } from './StreakMilestoneNotification';

export const StreakPanel: React.FC = () => {
  const { recentMilestones, recordActivity } = useStreak();
  const [activeMilestone, setActiveMilestone] = useState<{ type: StreakType; milestone: number } | null>(null);

  // Show milestone notification for the most recent one
  React.useEffect(() => {
    if (recentMilestones.length > 0) {
      const latest = recentMilestones[0];
      setActiveMilestone({ type: latest.type, milestone: latest.milestone });
    }
  }, [recentMilestones]);

  const handleTestStreak = (type: StreakType) => {
    recordActivity(type);
  };

  return (
    <div className="p-6 space-y-6 pb-24">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Your Streaks 🔥
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Track your consistency across different activities
          </p>
        </div>

        {/* Streak Displays */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StreakDisplay type="login" showProgress showRisk animated />
          <StreakDisplay type="chat" showProgress showRisk animated />
        </div>

        {/* Development Tools (remove in production) */}
        {import.meta.env.DEV && (
          <div className="mt-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-200 mb-3">
              🛠️ Development Tools
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => handleTestStreak('login')}
                className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
              >
                Test Login Streak
              </button>
              <button
                onClick={() => handleTestStreak('chat')}
                className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600 transition-colors"
              >
                Test Chat Streak
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Milestone Notification */}
      {activeMilestone && (
        <StreakMilestoneNotification
          type={activeMilestone.type}
          milestone={activeMilestone.milestone}
          onClose={() => setActiveMilestone(null)}
        />
      )}
    </div>
  );
};

export default StreakPanel;

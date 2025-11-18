/**
 * SettingsPanel Component
 * App settings and preferences
 */

import React, { useState } from 'react';
import { useProfile } from '../hooks/useProfile';
import { useAvatar } from '../hooks/useAvatar';
import { useTheme } from '../hooks/useTheme';
import { useColor } from '../hooks/useColor';
import { useAchievements } from '../hooks/useAchievements';
import { useLogin } from '../hooks/useLogin';
import { useStreak } from '../hooks/useStreak';
import { AvatarSelector } from './AvatarSelector';
import { AvatarDisplay } from './AvatarDisplay';
import { ThemeToggle } from './ThemeToggle';
import { ColorSelector } from './ColorSelector';
import { RecentAchievements } from './RecentAchievements';
import { LoginStats } from './LoginStats';
import { LoginCalendar } from './LoginCalendar';
import { StreakDisplay } from './StreakDisplay';
import { calculateTotalPoints, getAchievementProgress } from '../../shared/achievements';

export const SettingsPanel: React.FC = () => {
  const { profile, updateProfile, isLoading } = useProfile();
  const { avatarId, updateAvatar } = useAvatar();
  const { theme } = useTheme();
  const { colorTheme } = useColor();
  const { unlockedAchievements, stats } = useAchievements();
  const loginStats = useLogin();

  // Local state for form
  const [formData, setFormData] = useState({
    name: profile?.name || '',
    age: profile?.age || '',
    grade: profile?.grade || '',
  });

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [showAvatarSelector, setShowAvatarSelector] = useState(false);

  /**
   * Handle form submission
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('saving');

    try {
      await updateProfile({
        name: formData.name || undefined,
        age: formData.age ? parseInt(formData.age as string) : undefined,
        grade: formData.grade ? parseInt(formData.grade as string) : undefined,
      });
      setSaveStatus('success');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    }
  };

  /**
   * Handle input change
   */
  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  /**
   * Handle avatar selection
   */
  const handleAvatarSelect = (newAvatarId: string) => {
    updateAvatar(newAvatarId);
    setShowAvatarSelector(false);
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900 pb-16">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200">Settings</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Manage your profile and preferences</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Avatar Selection */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>🎨</span>
              <span>Avatar</span>
            </h3>

            <div className="flex items-center gap-6">
              {/* Avatar preview */}
              <AvatarDisplay avatarId={avatarId} size="xlarge" showBorder />

              <div className="flex-1">
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  Choose an avatar to personalize your profile
                </p>
                <button
                  onClick={() => setShowAvatarSelector(!showAvatarSelector)}
                  className="px-4 py-2 text-white rounded-lg transition-colors text-sm font-medium"
                  style={{
                    backgroundColor: 'var(--color-primary)',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-hover)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--color-primary)';
                  }}
                >
                  {showAvatarSelector ? 'Hide Avatar Selector' : 'Change Avatar'}
                </button>
              </div>
            </div>

            {/* Avatar selector (expanded) */}
            {showAvatarSelector && (
              <div className="mt-6">
                <AvatarSelector
                  selectedAvatarId={avatarId}
                  onSelect={handleAvatarSelect}
                  onClose={() => setShowAvatarSelector(false)}
                />
              </div>
            )}
          </div>

          {/* Theme Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>🌓</span>
              <span>Appearance</span>
            </h3>

            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Theme
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Choose between light and dark mode
                </p>
              </div>
              <ThemeToggle showLabels={true} />
            </div>
          </div>

          {/* Color Customization */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>🎨</span>
              <span>Colors</span>
            </h3>

            <div className="space-y-3">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Personalize your experience with custom color themes
              </p>
              <ColorSelector />
            </div>
          </div>

          {/* Profile Information */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>👤</span>
              <span>Profile Information</span>
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Your Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 transition-shadow"
                  style={{
                    ['--tw-ring-color' as any]: 'var(--color-focus)',
                  }}
                  maxLength={50}
                />
              </div>

              {/* Age */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Age</label>
                <input
                  type="number"
                  value={formData.age}
                  onChange={(e) => handleChange('age', e.target.value)}
                  placeholder="Enter your age"
                  min={1}
                  max={120}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 transition-shadow"
                  style={{
                    ['--tw-ring-color' as any]: 'var(--color-focus)',
                  }}
                />
              </div>

              {/* Grade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Grade
                </label>
                <select
                  value={formData.grade}
                  onChange={(e) => handleChange('grade', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 transition-shadow"
                  style={{
                    ['--tw-ring-color' as any]: 'var(--color-focus)',
                  }}
                >
                  <option value="">Select grade</option>
                  <option value="1">1st Grade</option>
                  <option value="2">2nd Grade</option>
                  <option value="3">3rd Grade</option>
                  <option value="4">4th Grade</option>
                  <option value="5">5th Grade</option>
                  <option value="6">6th Grade</option>
                  <option value="7">7th Grade</option>
                  <option value="8">8th Grade</option>
                  <option value="9">9th Grade</option>
                  <option value="10">10th Grade</option>
                  <option value="11">11th Grade</option>
                  <option value="12">12th Grade</option>
                </select>
              </div>

              {/* Save button */}
              <div className="flex items-center justify-between pt-4">
                <button
                  type="submit"
                  disabled={isLoading || saveStatus === 'saving'}
                  className="px-6 py-2 text-white rounded-lg disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
                  style={{
                    backgroundColor: isLoading || saveStatus === 'saving' ? undefined : 'var(--color-primary)',
                  }}
                  onMouseEnter={(e) => {
                    if (!isLoading && saveStatus !== 'saving') {
                      e.currentTarget.style.backgroundColor = 'var(--color-hover)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isLoading && saveStatus !== 'saving') {
                      e.currentTarget.style.backgroundColor = 'var(--color-primary)';
                    }
                  }}
                >
                  {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
                </button>

                {/* Save status */}
                {saveStatus === 'success' && (
                  <span className="text-sm text-green-600 dark:text-green-400 flex items-center gap-1">
                    <span>✓</span>
                    <span>Saved successfully!</span>
                  </span>
                )}
                {saveStatus === 'error' && (
                  <span className="text-sm text-red-600 dark:text-red-400 flex items-center gap-1">
                    <span>✗</span>
                    <span>Failed to save</span>
                  </span>
                )}
              </div>
            </form>
          </div>

          {/* Achievements Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>🏆</span>
              <span>Achievements</span>
            </h3>

            <div className="space-y-4">
              {/* Stats grid */}
              <div className="grid grid-cols-3 gap-3">
                <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                    {unlockedAchievements.length}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Unlocked
                  </div>
                </div>
                <div className="text-center p-3 bg-gradient-to-br from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                    {calculateTotalPoints(unlockedAchievements)}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Points
                  </div>
                </div>
                <div className="text-center p-3 bg-gradient-to-br from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg border border-orange-200 dark:border-orange-800">
                  <div className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                    {getAchievementProgress(unlockedAchievements)}%
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    Progress
                  </div>
                </div>
              </div>

              {/* Recent stats */}
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Messages</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {stats.messageCount}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Streak</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {stats.dailyStreak} days
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Sessions</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {stats.conversationCount}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Total Points</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {stats.totalPoints}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                View all achievements in the Achievements tab
              </p>

              {/* Recent Achievements */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <span>✨</span>
                  <span>Recent Unlocks</span>
                </h4>
                <RecentAchievements limit={3} compact={true} />
              </div>
            </div>
          </div>

          {/* Login Tracking & Activity */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>📊</span>
              <span>Activity Tracking</span>
            </h3>

            <div className="space-y-6">
              {/* Streak Indicators */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <span>🔥</span>
                  <span>Active Streaks</span>
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <StreakDisplay type="login" compact={true} showProgress={false} showRisk={true} />
                  <StreakDisplay type="chat" compact={true} showProgress={false} showRisk={true} />
                </div>
              </div>

              {/* Login Stats */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <span>📈</span>
                  <span>Login Statistics</span>
                </h4>
                <LoginStats compact={true} />
              </div>

              {/* Login Calendar */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <span>📅</span>
                  <span>Login History (Last 90 Days)</span>
                </h4>
                <LoginCalendar months={3} />
              </div>

              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                Keep your login streak alive to unlock special achievements!
              </p>
            </div>
          </div>

          {/* Privacy & Data */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>🔒</span>
              <span>Privacy & Data</span>
            </h3>

            <div className="space-y-4">
              <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✓</span>
                  <div>
                    <div className="font-medium text-green-800 dark:text-green-300 mb-1">
                      All data stored locally
                    </div>
                    <p className="text-sm text-green-700 dark:text-green-400">
                      Your conversations and data are stored only on your computer. Nothing
                      is sent to the cloud or shared with third parties.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">🤖</span>
                  <div>
                    <div className="font-medium text-blue-800 dark:text-blue-300 mb-1">
                      Local AI processing
                    </div>
                    <p className="text-sm text-blue-700 dark:text-blue-400">
                      The AI model runs entirely on your device. No internet connection
                      required for chatting.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* About */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>ℹ️</span>
              <span>About</span>
            </h3>

            <div className="space-y-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center justify-between">
                <span>Version</span>
                <span className="font-medium text-gray-800 dark:text-gray-200">0.1.0</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Backend Status</span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 dark:bg-green-400 rounded-full"></span>
                  <span className="font-medium text-green-600 dark:text-green-400">Connected</span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Database</span>
                <span className="font-medium text-gray-800 dark:text-gray-200">SQLite (Local)</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                Chatbot Friend is a safe, private companion for preteens.
                <br />
                Designed with safety and privacy in mind.
              </p>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
              <span>⚙️</span>
              <span>Advanced</span>
            </h3>

            <div className="space-y-3">
              <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 transition-colors">
                View conversation history
              </button>
              <button className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg border border-gray-200 dark:border-gray-600 transition-colors">
                Export memory book (PDF)
              </button>
              <button className="w-full px-4 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 transition-colors">
                Clear all conversation data
              </button>
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400 mt-4">
              Note: Advanced features are coming soon!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;

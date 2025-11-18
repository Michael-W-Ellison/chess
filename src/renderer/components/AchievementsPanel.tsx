/**
 * AchievementsPanel Component
 * Displays all achievements organized by category
 */

import React, { useState } from 'react';
import { useAchievements } from '../hooks/useAchievements';
import {
  ACHIEVEMENTS,
  AchievementCategory,
  CATEGORY_NAMES,
  getAchievementsByCategory,
  getAchievementCategories,
  calculateTotalPoints,
  getAchievementProgress,
} from '../../shared/achievements';
import { AchievementBadge } from './AchievementBadge';

export const AchievementsPanel: React.FC = () => {
  const { unlockedAchievements, stats, isUnlocked, getProgress } = useAchievements();
  const [selectedCategory, setSelectedCategory] = useState<AchievementCategory | 'all'>('all');
  const [selectedAchievement, setSelectedAchievement] = useState<string | null>(null);

  const categories = getAchievementCategories();
  const totalPoints = calculateTotalPoints(unlockedAchievements);
  const progressPercent = getAchievementProgress(unlockedAchievements);

  // Filter achievements by category
  const displayedAchievements =
    selectedCategory === 'all'
      ? ACHIEVEMENTS.filter((a) => !a.hidden)
      : getAchievementsByCategory(selectedCategory).filter((a) => !a.hidden);

  // Get selected achievement details
  const selectedAch = selectedAchievement
    ? ACHIEVEMENTS.find((a) => a.id === selectedAchievement)
    : null;

  return (
    <div className="h-full flex flex-col bg-gray-50 dark:bg-gray-900 pb-16">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-gray-200">Achievements</h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Track your progress and earn rewards
        </p>

        {/* Progress summary */}
        <div className="mt-4 grid grid-cols-3 gap-4">
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
            <div className="text-xs text-gray-600 dark:text-gray-400">Unlocked</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-200">
              {unlockedAchievements.length} / {ACHIEVEMENTS.filter((a) => !a.hidden).length}
            </div>
          </div>
          <div className="bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-lg p-3 border border-green-200 dark:border-green-800">
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Points</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-200">
              {totalPoints}
            </div>
          </div>
          <div className="bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20 rounded-lg p-3 border border-orange-200 dark:border-orange-800">
            <div className="text-xs text-gray-600 dark:text-gray-400">Progress</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-200">
              {progressPercent}%
            </div>
          </div>
        </div>

        {/* Overall progress bar */}
        <div className="mt-3 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Category tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
        <div className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`px-4 py-3 font-medium text-sm whitespace-nowrap border-b-2 transition-colors ${
              selectedCategory === 'all'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-900'
                : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-white dark:hover:bg-gray-900'
            }`}
          >
            All Achievements
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-3 font-medium text-sm whitespace-nowrap border-b-2 transition-colors ${
                selectedCategory === category
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-900'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-white dark:hover:bg-gray-900'
              }`}
            >
              {CATEGORY_NAMES[category]}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-6xl mx-auto">
          {/* Achievement grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {displayedAchievements.map((achievement) => (
              <AchievementBadge
                key={achievement.id}
                achievement={achievement}
                isUnlocked={isUnlocked(achievement.id)}
                progress={getProgress(achievement.id)}
                size="medium"
                showProgress={true}
                onClick={() => setSelectedAchievement(achievement.id)}
              />
            ))}
          </div>

          {/* Empty state */}
          {displayedAchievements.length === 0 && (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <div className="text-4xl mb-2">🔍</div>
              <p>No achievements in this category</p>
            </div>
          )}
        </div>
      </div>

      {/* Achievement detail modal */}
      {selectedAch && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
          onClick={() => setSelectedAchievement(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-4">
              <AchievementBadge
                achievement={selectedAch}
                isUnlocked={isUnlocked(selectedAch.id)}
                progress={getProgress(selectedAch.id)}
                size="large"
                showProgress={false}
              />
              <div className="flex-1">
                <h3 className="text-xl font-bold text-gray-800 dark:text-gray-200 mb-2">
                  {selectedAch.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {selectedAch.description}
                </p>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Category</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {CATEGORY_NAMES[selectedAch.category]}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Points</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200">
                      {selectedAch.points}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Tier</span>
                    <span className="font-medium text-gray-800 dark:text-gray-200 uppercase">
                      {selectedAch.tier}
                    </span>
                  </div>
                  {selectedAch.rarity && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Rarity</span>
                      <span className="font-medium text-gray-800 dark:text-gray-200 capitalize">
                        {selectedAch.rarity}
                      </span>
                    </div>
                  )}
                  {!isUnlocked(selectedAch.id) && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Progress</span>
                      <span className="font-medium text-gray-800 dark:text-gray-200">
                        {getProgress(selectedAch.id)}%
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <button
              onClick={() => setSelectedAchievement(null)}
              className="mt-6 w-full px-4 py-2 text-white rounded-lg transition-colors"
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
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default AchievementsPanel;

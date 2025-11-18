/**
 * MemoryBook Component
 * Display and manage collected memories
 */

import React, { useState, useMemo } from 'react';
import { Memory, MemoryCategory } from '../../shared/types';
import {
  groupMemoriesByCategory,
  getCategoryEmoji,
  getCategoryDisplayName,
  formatMemoryForDisplay,
  createMemorySummary,
  searchMemories,
} from '../../shared/memoryUtils';

interface MemoryBookProps {
  memories: Memory[];
  onMemoryClick?: (memory: Memory) => void;
}

export const MemoryBook: React.FC<MemoryBookProps> = ({ memories, onMemoryClick }) => {
  const [selectedCategory, setSelectedCategory] = useState<MemoryCategory | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Group and filter memories
  const groupedMemories = useMemo(() => groupMemoriesByCategory(memories), [memories]);

  const summary = useMemo(() => createMemorySummary(memories), [memories]);

  const filteredMemories = useMemo(() => {
    let filtered = memories;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = groupedMemories[selectedCategory];
    }

    // Filter by search
    if (searchQuery.trim()) {
      filtered = searchMemories(filtered, searchQuery);
    }

    return filtered;
  }, [memories, selectedCategory, searchQuery, groupedMemories]);

  /**
   * Render empty state
   */
  if (memories.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📖</div>
        <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
          No Memories Yet
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mx-auto">
          Start chatting with your Chess Tutor! As you share your favorites, goals, and more,
          they'll be collected here in your personal memory book.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header & Summary */}
      <div>
        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          📖 Memory Book
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          All the things your Chess Tutor remembers about you
        </p>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
          {(['favorite', 'dislike', 'goal', 'person', 'achievement'] as MemoryCategory[]).map(
            (category) => (
              <div
                key={category}
                className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-3 text-center border border-blue-200 dark:border-blue-800"
              >
                <div className="text-2xl mb-1">{getCategoryEmoji(category)}</div>
                <div className="text-xl font-bold text-gray-900 dark:text-gray-100">
                  {summary.byCategory[category]}
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  {getCategoryDisplayName(category)}
                </div>
              </div>
            )
          )}
        </div>
      </div>

      {/* Search */}
      <div>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search memories..."
          className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Category Filter */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedCategory('all')}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            selectedCategory === 'all'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          All ({memories.length})
        </button>
        {(['favorite', 'dislike', 'goal', 'person', 'achievement'] as MemoryCategory[]).map(
          (category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                selectedCategory === category
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <span>{getCategoryEmoji(category)}</span>
              <span>
                {getCategoryDisplayName(category)} ({summary.byCategory[category]})
              </span>
            </button>
          )
        )}
      </div>

      {/* Memories List */}
      <div className="space-y-3">
        {filteredMemories.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No memories found matching your search.' : 'No memories in this category.'}
            </p>
          </div>
        ) : (
          filteredMemories.map((memory, index) => (
            <div
              key={index}
              onClick={() => onMemoryClick?.(memory)}
              className={`bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700 ${
                onMemoryClick ? 'cursor-pointer hover:border-blue-500 dark:hover:border-blue-500' : ''
              } transition-all`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{getCategoryEmoji(memory.category)}</span>
                    <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      {getCategoryDisplayName(memory.category)}
                    </span>
                    <span className="text-xs text-gray-400 dark:text-gray-500">•</span>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      Confidence: {Math.round(memory.confidence * 100)}%
                    </span>
                  </div>

                  <p className="text-gray-900 dark:text-gray-100 font-medium mb-2">
                    {formatMemoryForDisplay(memory)}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <span>
                      First mentioned:{' '}
                      {memory.firstMentioned instanceof Date
                        ? memory.firstMentioned.toLocaleDateString()
                        : new Date(memory.firstMentioned).toLocaleDateString()}
                    </span>
                    <span>
                      Last mentioned:{' '}
                      {memory.lastMentioned instanceof Date
                        ? memory.lastMentioned.toLocaleDateString()
                        : new Date(memory.lastMentioned).toLocaleDateString()}
                    </span>
                    <span>Mentioned {memory.mentionCount}x</span>
                  </div>
                </div>

                {/* Confidence indicator */}
                <div className="ml-4">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      memory.confidence >= 0.8
                        ? 'bg-green-500'
                        : memory.confidence >= 0.5
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                  ></div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Most Mentioned Section */}
      {summary.mostMentioned.length > 0 && selectedCategory === 'all' && !searchQuery && (
        <div className="mt-8">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
            <span>⭐</span>
            <span>Most Mentioned</span>
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {summary.mostMentioned.map((memory, index) => (
              <div
                key={index}
                className="bg-gradient-to-r from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-lg p-3 border border-yellow-200 dark:border-yellow-800"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">{getCategoryEmoji(memory.category)}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {formatMemoryForDisplay(memory)}
                  </span>
                </div>
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  Mentioned {memory.mentionCount} times
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Memories Section */}
      {summary.recent.length > 0 && selectedCategory === 'all' && !searchQuery && (
        <div className="mt-8">
          <h4 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
            <span>🕐</span>
            <span>Recently Updated</span>
          </h4>
          <div className="space-y-2">
            {summary.recent.map((memory, index) => (
              <div
                key={index}
                className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{getCategoryEmoji(memory.category)}</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {formatMemoryForDisplay(memory)}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {memory.lastMentioned instanceof Date
                      ? memory.lastMentioned.toLocaleDateString()
                      : new Date(memory.lastMentioned).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MemoryBook;

/**
 * ProfilePanel Component
 * Displays bot personality, user profile, and memories
 */

import React, { useState } from 'react';
import { usePersonality } from '../hooks/usePersonality';
import { useProfile } from '../hooks/useProfile';
import { useMemory } from '../contexts/MemoryContext';
import { FriendshipMeter } from './FriendshipMeter';
import { MemoryBook } from './MemoryBook';
import { ExportDialog } from './ExportDialog';

type TabType = 'personality' | 'profile' | 'memories';

export const ProfilePanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('personality');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const { personality, description, isLoading: personalityLoading } = usePersonality();
  const { profile, isLoading: profileLoading } = useProfile();
  const { memories } = useMemory();

  const isLoading = personalityLoading || profileLoading;

  /**
   * Render personality tab
   */
  const renderPersonalityTab = () => {
    if (!personality) {
      return (
        <div className="text-center py-12 text-gray-500">
          <div className="animate-pulse text-4xl mb-4">🤖</div>
          <p>Loading personality...</p>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        {/* Friendship meter */}
        <FriendshipMeter
          friendshipLevel={personality.friendshipLevel}
          stats={personality.stats}
        />

        {/* Personality traits */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Personality Traits</h3>

          <div className="space-y-4">
            {/* Humor */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">😄 Humor</span>
                <span className="text-sm text-gray-500">
                  {description?.humor || (personality.traits.humor * 100).toFixed(0)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-yellow-500 rounded-full transition-all"
                  style={{ width: `${personality.traits.humor * 100}%` }}
                />
              </div>
            </div>

            {/* Energy */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">⚡ Energy</span>
                <span className="text-sm text-gray-500">
                  {description?.energy || (personality.traits.energy * 100).toFixed(0)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-orange-500 rounded-full transition-all"
                  style={{ width: `${personality.traits.energy * 100}%` }}
                />
              </div>
            </div>

            {/* Curiosity */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">🔍 Curiosity</span>
                <span className="text-sm text-gray-500">
                  {description?.curiosity || (personality.traits.curiosity * 100).toFixed(0)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-blue-500 rounded-full transition-all"
                  style={{ width: `${personality.traits.curiosity * 100}%` }}
                />
              </div>
            </div>

            {/* Formality */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">💼 Formality</span>
                <span className="text-sm text-gray-500">
                  {description?.formality || (personality.traits.formality * 100).toFixed(0)}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="h-full bg-purple-500 rounded-full transition-all"
                  style={{ width: `${personality.traits.formality * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Mood & Info */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Current Mood</div>
            <div className="text-2xl font-semibold text-gray-800 capitalize">
              {personality.mood}
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Bot Name</div>
            <div className="text-2xl font-semibold text-gray-800">{personality.name}</div>
          </div>
        </div>

        {/* Quirks */}
        {personality.quirks.length > 0 && (
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Quirks</h3>
            <div className="flex flex-wrap gap-2">
              {personality.quirks.map((quirk, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                >
                  {quirk.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Interests */}
        {personality.interests.length > 0 && (
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Interests</h3>
            <div className="flex flex-wrap gap-2">
              {personality.interests.map((interest, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                >
                  {interest.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Catchphrase */}
        {personality.catchphrase && (
          <div className="bg-gradient-to-r from-purple-100 to-blue-100 rounded-lg p-4 border border-purple-200">
            <div className="text-xs text-gray-600 mb-1">Catchphrase</div>
            <div className="text-lg italic text-gray-800">"{personality.catchphrase}"</div>
          </div>
        )}
      </div>
    );
  };

  /**
   * Render user profile tab
   */
  const renderProfileTab = () => {
    if (!profile) {
      return (
        <div className="text-center py-12 text-gray-500">
          <div className="animate-pulse text-4xl mb-4">👤</div>
          <p>Loading profile...</p>
        </div>
      );
    }

    const sections = [
      { title: 'Favorites', items: profile.favorites, emoji: '⭐', color: 'yellow' },
      { title: 'Dislikes', items: profile.dislikes, emoji: '👎', color: 'red' },
      { title: 'Goals', items: profile.goals, emoji: '🎯', color: 'green' },
      { title: 'People', items: profile.people, emoji: '👥', color: 'blue' },
      { title: 'Achievements', items: profile.achievements, emoji: '🏆', color: 'purple' },
    ];

    return (
      <div className="space-y-6">
        {/* User info */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">About You</h3>
          <div className="space-y-2">
            {profile.name && (
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Name:</span>
                <span className="font-medium text-gray-800">{profile.name}</span>
              </div>
            )}
            {profile.age && (
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Age:</span>
                <span className="font-medium text-gray-800">{profile.age}</span>
              </div>
            )}
            {profile.grade && (
              <div className="flex items-center gap-2">
                <span className="text-gray-600">Grade:</span>
                <span className="font-medium text-gray-800">{profile.grade}</span>
              </div>
            )}
          </div>
        </div>

        {/* Profile sections */}
        {sections.map((section) => {
          if (!section.items || Object.keys(section.items).length === 0) {
            return null;
          }

          return (
            <div key={section.title} className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <span>{section.emoji}</span>
                <span>{section.title}</span>
              </h3>
              <div className="space-y-2">
                {Object.entries(section.items).map(([key, value]) => (
                  <div
                    key={key}
                    className="flex items-start justify-between p-2 bg-gray-50 rounded"
                  >
                    <div>
                      <div className="text-sm font-medium text-gray-700 capitalize">
                        {key.replace(/_/g, ' ')}
                      </div>
                      <div className="text-sm text-gray-600">{value}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}

        {/* Empty state */}
        {sections.every(
          (section) => !section.items || Object.keys(section.items).length === 0
        ) && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-4">💬</div>
            <p className="mb-2">Your profile is empty!</p>
            <p className="text-sm">
              Chat with me to help me learn about you
            </p>
          </div>
        )}
      </div>
    );
  };

  /**
   * Render memories tab
   */
  const renderMemoriesTab = () => {
    return <MemoryBook memories={memories} />;
  };

  return (
    <div className="h-full flex flex-col bg-gray-50 pb-16">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Profile</h2>
            <p className="text-sm text-gray-600 mt-1">
              View personality, profile, and memories
            </p>
          </div>
          <button
            onClick={() => setShowExportDialog(true)}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2 text-sm"
          >
            <span>📥</span>
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab('personality')}
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'personality'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            🤖 Personality
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'profile'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            👤 Your Profile
          </button>
          <button
            onClick={() => setActiveTab('memories')}
            className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors ${
              activeTab === 'memories'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            🧠 Memories ({memories.length})
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin text-4xl mb-4">⏳</div>
            <p className="text-gray-500">Loading...</p>
          </div>
        )}

        {!isLoading && (
          <>
            {activeTab === 'personality' && (
              <div className="tab-content-enter">
                {renderPersonalityTab()}
              </div>
            )}
            {activeTab === 'profile' && (
              <div className="tab-content-enter">
                {renderProfileTab()}
              </div>
            )}
            {activeTab === 'memories' && (
              <div className="tab-content-enter">
                {renderMemoriesTab()}
              </div>
            )}
          </>
        )}
      </div>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={showExportDialog}
        onClose={() => setShowExportDialog(false)}
        defaultType="memories"
        defaultFormat="markdown"
      />
    </div>
  );
};

export default ProfilePanel;

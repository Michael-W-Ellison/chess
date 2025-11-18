/**
 * SettingsPanel Component
 * App settings and preferences
 */

import React, { useState } from 'react';
import { useProfile } from '../hooks/useProfile';
import { useAvatar } from '../hooks/useAvatar';
import { AvatarSelector } from './AvatarSelector';
import { AvatarDisplay } from './AvatarDisplay';

export const SettingsPanel: React.FC = () => {
  const { profile, updateProfile, isLoading } = useProfile();
  const { avatarId, updateAvatar } = useAvatar();

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
    <div className="h-full flex flex-col bg-gray-50 pb-16">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h2 className="text-2xl font-bold text-gray-800">Settings</h2>
        <p className="text-sm text-gray-600 mt-1">Manage your profile and preferences</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Avatar Selection */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>🎨</span>
              <span>Avatar</span>
            </h3>

            <div className="flex items-center gap-6">
              {/* Avatar preview */}
              <AvatarDisplay avatarId={avatarId} size="xlarge" showBorder />

              <div className="flex-1">
                <p className="text-sm text-gray-600 mb-3">
                  Choose an avatar to personalize your profile
                </p>
                <button
                  onClick={() => setShowAvatarSelector(!showAvatarSelector)}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
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

          {/* Profile Information */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>👤</span>
              <span>Profile Information</span>
            </h3>

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  maxLength={50}
                />
              </div>

              {/* Age */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Age</label>
                <input
                  type="number"
                  value={formData.age}
                  onChange={(e) => handleChange('age', e.target.value)}
                  placeholder="Enter your age"
                  min={1}
                  max={120}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Grade */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Grade
                </label>
                <select
                  value={formData.grade}
                  onChange={(e) => handleChange('grade', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
                </button>

                {/* Save status */}
                {saveStatus === 'success' && (
                  <span className="text-sm text-green-600 flex items-center gap-1">
                    <span>✓</span>
                    <span>Saved successfully!</span>
                  </span>
                )}
                {saveStatus === 'error' && (
                  <span className="text-sm text-red-600 flex items-center gap-1">
                    <span>✗</span>
                    <span>Failed to save</span>
                  </span>
                )}
              </div>
            </form>
          </div>

          {/* Privacy & Data */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>🔒</span>
              <span>Privacy & Data</span>
            </h3>

            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✓</span>
                  <div>
                    <div className="font-medium text-green-800 mb-1">
                      All data stored locally
                    </div>
                    <p className="text-sm text-green-700">
                      Your conversations and data are stored only on your computer. Nothing
                      is sent to the cloud or shared with third parties.
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">🤖</span>
                  <div>
                    <div className="font-medium text-blue-800 mb-1">
                      Local AI processing
                    </div>
                    <p className="text-sm text-blue-700">
                      The AI model runs entirely on your device. No internet connection
                      required for chatting.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* About */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>ℹ️</span>
              <span>About</span>
            </h3>

            <div className="space-y-3 text-sm text-gray-600">
              <div className="flex items-center justify-between">
                <span>Version</span>
                <span className="font-medium text-gray-800">0.1.0</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Backend Status</span>
                <span className="flex items-center gap-1">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="font-medium text-green-600">Connected</span>
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span>Database</span>
                <span className="font-medium text-gray-800">SQLite (Local)</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500 text-center">
                Chatbot Friend is a safe, private companion for preteens.
                <br />
                Designed with safety and privacy in mind.
              </p>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span>⚙️</span>
              <span>Advanced</span>
            </h3>

            <div className="space-y-3">
              <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-200 transition-colors">
                View conversation history
              </button>
              <button className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded-lg border border-gray-200 transition-colors">
                Export memory book (PDF)
              </button>
              <button className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 rounded-lg border border-red-200 transition-colors">
                Clear all conversation data
              </button>
            </div>

            <p className="text-xs text-gray-500 mt-4">
              Note: Advanced features are coming soon!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;

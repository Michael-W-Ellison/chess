/**
 * NotificationPreferences Component
 * Configure parent notification settings
 */

import React, { useState } from 'react';
import { useNotificationPreferences } from '../../hooks/useNotificationPreferences';

interface NotificationPreferencesProps {
  userId: number;
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({ userId }) => {
  const { preferences, updatePreferences, isLoading, error, isSaving } = useNotificationPreferences(userId);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);

  const handleToggle = async (field: string, value: boolean) => {
    await updatePreferences({ [field]: value });
    setShowSaveSuccess(true);
    setTimeout(() => setShowSaveSuccess(false), 3000);
  };

  const handleUpdate = async (updates: any) => {
    await updatePreferences(updates);
    setShowSaveSuccess(true);
    setTimeout(() => setShowSaveSuccess(false), 3000);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading preferences...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading preferences: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Success Message */}
      {showSaveSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <span className="text-green-600">✓</span>
            <p className="text-green-800 font-medium">Preferences saved successfully!</p>
          </div>
        </div>
      )}

      {/* Master Switch */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-800">Email Notifications</h3>
            <p className="text-sm text-gray-600 mt-1">Receive email alerts for safety events</p>
          </div>
          <button
            onClick={() =>
              handleToggle('email_notifications_enabled', !preferences?.email_notifications_enabled)
            }
            disabled={isSaving}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences?.email_notifications_enabled ? 'bg-blue-600' : 'bg-gray-300'
            } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences?.email_notifications_enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Severity Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Severity Filters</h3>
        <p className="text-sm text-gray-600 mb-4">Choose which severity levels trigger instant notifications</p>
        <div className="space-y-3">
          {[
            { key: 'critical', label: 'Critical', color: 'red', icon: '🚨' },
            { key: 'high', label: 'High', color: 'orange', icon: '⚠️' },
            { key: 'medium', label: 'Medium', color: 'yellow', icon: '⚡' },
            { key: 'low', label: 'Low', color: 'blue', icon: 'ℹ️' },
          ].map(({ key, label, color, icon }) => (
            <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <div>
                  <div className="font-medium text-gray-800">{label}</div>
                  <div className="text-xs text-gray-600">Severity level</div>
                </div>
              </div>
              <button
                onClick={() =>
                  handleToggle(
                    `notify_on_${key}`,
                    !preferences?.severity_filters?.[key]
                  )
                }
                disabled={isSaving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences?.severity_filters?.[key] ? 'bg-blue-600' : 'bg-gray-300'
                } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    preferences?.severity_filters?.[key] ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Flag Type Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Flag Type Filters</h3>
        <p className="text-sm text-gray-600 mb-4">Choose which event types trigger notifications</p>
        <div className="space-y-3">
          {[
            { key: 'crisis', label: 'Crisis Events', icon: '⚠️', description: 'Self-harm, suicide, etc.' },
            { key: 'abuse', label: 'Abuse Reports', icon: '🛡️', description: 'Physical, emotional, sexual' },
            { key: 'bullying', label: 'Bullying', icon: '👊', description: 'Bullying behavior' },
            { key: 'profanity', label: 'Profanity', icon: '🤬', description: 'Inappropriate language' },
            { key: 'inappropriate', label: 'Inappropriate Content', icon: '🚫', description: 'Other inappropriate requests' },
          ].map(({ key, label, icon, description }) => (
            <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{icon}</span>
                <div>
                  <div className="font-medium text-gray-800">{label}</div>
                  <div className="text-xs text-gray-600">{description}</div>
                </div>
              </div>
              <button
                onClick={() =>
                  handleToggle(
                    `notify_on_${key}`,
                    !preferences?.flag_type_filters?.[key]
                  )
                }
                disabled={isSaving}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  preferences?.flag_type_filters?.[key] ? 'bg-blue-600' : 'bg-gray-300'
                } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    preferences?.flag_type_filters?.[key] ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Summary Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Summary Emails</h3>
        <p className="text-sm text-gray-600 mb-4">Receive periodic summaries of safety events</p>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Frequency</label>
            <select
              value={preferences?.summary_settings?.frequency || 'weekly'}
              onChange={(e) => handleUpdate({ summary_frequency: e.target.value })}
              disabled={isSaving}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="none">None - Disable summaries</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>

          {preferences?.summary_settings?.frequency === 'weekly' && (
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Day of Week</label>
              <select
                value={preferences?.summary_settings?.day_of_week || 0}
                onChange={(e) => handleUpdate({ summary_day_of_week: parseInt(e.target.value) })}
                disabled={isSaving}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="0">Monday</option>
                <option value="1">Tuesday</option>
                <option value="2">Wednesday</option>
                <option value="3">Thursday</option>
                <option value="4">Friday</option>
                <option value="5">Saturday</option>
                <option value="6">Sunday</option>
              </select>
            </div>
          )}

          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Time of Day</label>
            <input
              type="time"
              value={`${String(preferences?.summary_settings?.hour || 9).padStart(2, '0')}:00`}
              onChange={(e) => {
                const hour = parseInt(e.target.value.split(':')[0]);
                handleUpdate({ summary_hour: hour });
              }}
              disabled={isSaving}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-800">Quiet Hours</h3>
            <p className="text-sm text-gray-600 mt-1">Suppress notifications during specific hours</p>
          </div>
          <button
            onClick={() =>
              handleToggle('quiet_hours_enabled', !preferences?.quiet_hours?.enabled)
            }
            disabled={isSaving}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences?.quiet_hours?.enabled ? 'bg-blue-600' : 'bg-gray-300'
            } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences?.quiet_hours?.enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {preferences?.quiet_hours?.enabled && (
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Start Time</label>
              <input
                type="time"
                value={`${String(preferences?.quiet_hours?.start || 22).padStart(2, '0')}:00`}
                onChange={(e) => {
                  const hour = parseInt(e.target.value.split(':')[0]);
                  handleUpdate({ quiet_hours_start: hour });
                }}
                disabled={isSaving}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">End Time</label>
              <input
                type="time"
                value={`${String(preferences?.quiet_hours?.end || 7).padStart(2, '0')}:00`}
                onChange={(e) => {
                  const hour = parseInt(e.target.value.split(':')[0]);
                  handleUpdate({ quiet_hours_end: hour });
                }}
                disabled={isSaving}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleUpdate({ email_notifications_enabled: true, notify_on_critical: true, notify_on_high: true, notify_on_medium: true, notify_on_low: true })}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Enable All Notifications
          </button>
          <button
            onClick={() => handleUpdate({ email_notifications_enabled: false })}
            disabled={isSaving}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disable All Notifications
          </button>
          <button
            onClick={() => window.confirm('Reset all preferences to default values?') && handleUpdate({ reset: true })}
            disabled={isSaving}
            className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * NotificationPreferences Component
 * Configure parent notification settings
 */

import React, { useState } from 'react';
import { useNotificationPreferences } from '../../hooks/useNotificationPreferences';
import { SeverityBadge } from '../common/SeverityBadge';

interface NotificationPreferencesProps {
  userId: number;
}

export const NotificationPreferences: React.FC<NotificationPreferencesProps> = ({ userId }) => {
  const { preferences, updatePreferences, isLoading, error, isSaving } = useNotificationPreferences(userId);
  const [showSaveSuccess, setShowSaveSuccess] = useState(false);
  const [testingNotification, setTestingNotification] = useState(false);
  const [parentEmail, setParentEmail] = useState('');

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

  const handleTestNotification = async () => {
    setTestingNotification(true);
    try {
      const response = await fetch(`http://localhost:8000/api/parent/test-notification?user_id=${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send test notification');
      }

      const data = await response.json();
      alert(`✅ Test notification sent successfully to ${data.email}!\n\nCheck your email inbox (and spam folder) for the test notification.`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send test notification';
      alert(`❌ Error: ${errorMessage}\n\nPlease check your email configuration and try again.`);
      console.error('Failed to send test notification:', err);
    } finally {
      setTestingNotification(false);
    }
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
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 animate-fade-in">
          <div className="flex items-center gap-2">
            <span className="text-green-600 text-xl">✓</span>
            <p className="text-green-800 font-medium">Preferences saved successfully!</p>
          </div>
        </div>
      )}

      {/* Email Configuration */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Email Configuration</h3>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Parent Email Address</label>
            <div className="flex gap-2">
              <input
                type="email"
                value={parentEmail || preferences?.email || ''}
                onChange={(e) => setParentEmail(e.target.value)}
                placeholder="parent@example.com"
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <button
                onClick={() => handleUpdate({ email: parentEmail })}
                disabled={isSaving || !parentEmail}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Update
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">Safety notifications will be sent to this email address</p>
          </div>

          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div>
              <div className="font-medium text-gray-800">Enable Email Notifications</div>
              <p className="text-sm text-gray-600 mt-1">Receive instant email alerts for safety events</p>
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
      </div>

      {/* Severity Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-800">Severity Filters</h3>
            <p className="text-sm text-gray-600 mt-1">Choose which severity levels trigger instant notifications</p>
          </div>
          <button
            onClick={() => handleUpdate({
              notify_on_critical: true,
              notify_on_high: true,
              notify_on_medium: true,
              notify_on_low: true
            })}
            disabled={isSaving}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Enable All
          </button>
        </div>
        <div className="space-y-3">
          {[
            { key: 'critical', description: 'Immediate action required' },
            { key: 'high', description: 'Needs attention soon' },
            { key: 'medium', description: 'Should be reviewed' },
            { key: 'low', description: 'For your awareness' },
          ].map(({ key, description }) => {
            const fieldName = `notify_on_${key}` as keyof typeof preferences;
            const isEnabled = preferences?.[fieldName] as boolean;

            return (
              <div key={key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-center gap-3">
                  <SeverityBadge severity={key as 'critical' | 'high' | 'medium' | 'low'} size="md" />
                  <div>
                    <div className="text-xs text-gray-600">{description}</div>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle(fieldName, !isEnabled)}
                  disabled={isSaving}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isEnabled ? 'bg-blue-600' : 'bg-gray-300'
                  } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Flag Type Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-800">Event Type Filters</h3>
            <p className="text-sm text-gray-600 mt-1">Choose which event types trigger notifications</p>
          </div>
          <button
            onClick={() => handleUpdate({
              notify_on_crisis: true,
              notify_on_abuse: true,
              notify_on_bullying: true,
              notify_on_profanity: true,
              notify_on_inappropriate: true
            })}
            disabled={isSaving}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Enable All
          </button>
        </div>
        <div className="space-y-3">
          {[
            { key: 'crisis', label: 'Crisis Events', icon: '⚠️', description: 'Self-harm, suicide, mental health emergencies', priority: 'Always recommended' },
            { key: 'abuse', label: 'Abuse Reports', icon: '🛡️', description: 'Physical, emotional, or sexual abuse indicators', priority: 'Highly recommended' },
            { key: 'bullying', label: 'Bullying', icon: '👊', description: 'Bullying or harassment behavior', priority: 'Recommended' },
            { key: 'inappropriate', label: 'Inappropriate Content', icon: '🚫', description: 'Other inappropriate requests or behavior', priority: 'Recommended' },
            { key: 'profanity', label: 'Profanity', icon: '🤬', description: 'Inappropriate language', priority: 'Optional' },
          ].map(({ key, label, icon, description, priority }) => {
            const fieldName = `notify_on_${key}` as keyof typeof preferences;
            const isEnabled = preferences?.[fieldName] as boolean;
            const isCritical = key === 'crisis' || key === 'abuse';

            return (
              <div key={key} className={`flex items-center justify-between p-4 rounded-lg border ${
                isCritical ? 'bg-red-50 border-red-100' : 'bg-gray-50 border-gray-100'
              }`}>
                <div className="flex items-center gap-3 flex-1">
                  <span className="text-2xl">{icon}</span>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <div className="font-medium text-gray-800">{label}</div>
                      {isCritical && (
                        <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full font-semibold">
                          CRITICAL
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-600 mt-0.5">{description}</div>
                    <div className={`text-xs font-medium mt-1 ${
                      isCritical ? 'text-red-700' : 'text-gray-500'
                    }`}>
                      {priority}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleToggle(fieldName, !isEnabled)}
                  disabled={isSaving}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    isEnabled ? 'bg-blue-600' : 'bg-gray-300'
                  } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isEnabled ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary Settings */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Summary Emails</h3>
        <p className="text-sm text-gray-600 mb-4">Receive periodic summaries of all safety events</p>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-2 block">Frequency</label>
            <select
              value={preferences?.summary_frequency || 'weekly'}
              onChange={(e) => handleUpdate({ summary_frequency: e.target.value })}
              disabled={isSaving}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="none">None - Disable summaries</option>
              <option value="daily">Daily - Every day</option>
              <option value="weekly">Weekly - Once per week</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {preferences?.summary_frequency === 'daily' && 'You will receive a daily summary of all safety flags'}
              {preferences?.summary_frequency === 'weekly' && 'You will receive a weekly summary of all safety flags'}
              {preferences?.summary_frequency === 'none' && 'Summary emails are disabled'}
            </p>
          </div>

          {preferences?.summary_frequency === 'weekly' && (
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">Day of Week</label>
              <select
                value={preferences?.summary_day_of_week ?? 0}
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

          {preferences?.summary_frequency !== 'none' && (
            <div>
              <label className="text-sm font-medium text-gray-700 mb-2 block">
                Time of Day {preferences?.summary_frequency === 'daily' ? '(Daily)' : '(Weekly)'}
              </label>
              <input
                type="time"
                value={`${String(preferences?.summary_hour ?? 9).padStart(2, '0')}:00`}
                onChange={(e) => {
                  const hour = parseInt(e.target.value.split(':')[0]);
                  handleUpdate({ summary_hour: hour });
                }}
                disabled={isSaving}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">Summary will be sent around this time</p>
            </div>
          )}
        </div>
      </div>

      {/* Quiet Hours */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-800">Quiet Hours</h3>
            <p className="text-sm text-gray-600 mt-1">Suppress non-critical notifications during specific hours</p>
          </div>
          <button
            onClick={() =>
              handleToggle('quiet_hours_enabled', !preferences?.quiet_hours_enabled)
            }
            disabled={isSaving}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              preferences?.quiet_hours_enabled ? 'bg-blue-600' : 'bg-gray-300'
            } ${isSaving ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                preferences?.quiet_hours_enabled ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>

        {preferences?.quiet_hours_enabled && (
          <>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 mb-4">
              <p className="text-sm text-blue-800">
                ℹ️ <strong>Note:</strong> Critical safety flags (crisis/abuse) will always trigger notifications, even during quiet hours.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">Start Time</label>
                <input
                  type="time"
                  value={`${String(preferences?.quiet_hours_start ?? 22).padStart(2, '0')}:00`}
                  onChange={(e) => {
                    const hour = parseInt(e.target.value.split(':')[0]);
                    handleUpdate({ quiet_hours_start: hour });
                  }}
                  disabled={isSaving}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">When quiet hours begin</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">End Time</label>
                <input
                  type="time"
                  value={`${String(preferences?.quiet_hours_end ?? 7).padStart(2, '0')}:00`}
                  onChange={(e) => {
                    const hour = parseInt(e.target.value.split(':')[0]);
                    handleUpdate({ quiet_hours_end: hour });
                  }}
                  disabled={isSaving}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">When quiet hours end</p>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Quick Actions</h3>
        <p className="text-sm text-gray-600 mb-4">Quickly configure common notification settings</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button
            onClick={() => handleUpdate({
              email_notifications_enabled: true,
              notify_on_critical: true,
              notify_on_high: true,
              notify_on_medium: true,
              notify_on_low: true,
              notify_on_crisis: true,
              notify_on_abuse: true,
              notify_on_bullying: true,
              notify_on_inappropriate: true,
              notify_on_profanity: true
            })}
            disabled={isSaving}
            className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ✓ Enable All Notifications
          </button>
          <button
            onClick={() => {
              if (window.confirm('This will disable all email notifications. Critical safety flags will still be logged but not emailed. Continue?')) {
                handleUpdate({ email_notifications_enabled: false });
              }
            }}
            disabled={isSaving}
            className="px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ✕ Disable All Notifications
          </button>
          <button
            onClick={() => {
              if (window.confirm('Reset all notification preferences to their default values?')) {
                handleUpdate({
                  email_notifications_enabled: true,
                  notify_on_critical: true,
                  notify_on_high: true,
                  notify_on_medium: false,
                  notify_on_low: false,
                  notify_on_crisis: true,
                  notify_on_abuse: true,
                  notify_on_bullying: true,
                  notify_on_inappropriate: true,
                  notify_on_profanity: false,
                  summary_frequency: 'weekly',
                  summary_day_of_week: 0,
                  summary_hour: 9,
                  quiet_hours_enabled: false,
                });
              }
            }}
            disabled={isSaving}
            className="px-4 py-3 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ↻ Reset to Defaults
          </button>
          <button
            onClick={handleTestNotification}
            disabled={isSaving || testingNotification || !preferences?.email_notifications_enabled}
            className="px-4 py-3 border border-blue-200 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testingNotification ? '📧 Sending...' : '📧 Send Test Notification'}
          </button>
        </div>
        {!preferences?.email_notifications_enabled && (
          <p className="text-xs text-orange-600 mt-2">
            ⚠️ Email notifications are currently disabled. Enable them to send a test notification.
          </p>
        )}
      </div>

      {/* Notification Example */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">📧 Notification Example</h3>
        <p className="text-sm text-gray-600 mb-4">
          This is what you'll receive when a safety event is detected:
        </p>

        {/* Example Email Preview */}
        <div className="bg-gray-50 rounded-lg border-2 border-gray-200 p-5 space-y-4">
          {/* Email Header */}
          <div className="border-b border-gray-300 pb-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm text-gray-600">From:</div>
              <div className="text-sm font-medium text-gray-800">Chess Tutor Safety Monitor</div>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-600">Subject:</div>
              <div className="text-sm font-semibold text-gray-800">
                [Safety Alert] Critical Event Detected
              </div>
            </div>
          </div>

          {/* Email Body */}
          <div className="space-y-3">
            <div>
              <div className="text-sm text-gray-800 mb-2">
                <strong>Dear Parent,</strong>
              </div>
              <div className="text-sm text-gray-700">
                A safety event has been detected in your child's conversation with the Chess Tutor assistant.
              </div>
            </div>

            <div className="bg-red-50 border border-red-200 rounded p-3 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-red-800">Event Type:</span>
                <span className="text-sm text-red-700">Crisis Keywords Detected</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-red-800">Severity:</span>
                <SeverityBadge severity="critical" size="sm" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-red-800">Time:</span>
                <span className="text-sm text-red-700">Today at 2:45 PM</span>
              </div>
            </div>

            <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
              <div className="text-xs font-semibold text-yellow-800 mb-1">Recommended Action:</div>
              <div className="text-xs text-yellow-700">
                Talk to your child in a safe, non-judgmental environment. If this is a crisis situation, contact professional help immediately.
              </div>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded p-3">
              <div className="text-xs font-semibold text-blue-800 mb-1">Crisis Resources:</div>
              <div className="text-xs text-blue-700 space-y-1">
                <div>• National Suicide Prevention Lifeline: 988</div>
                <div>• Crisis Text Line: Text HOME to 741741</div>
              </div>
            </div>
          </div>
        </div>

        <p className="text-xs text-gray-500 mt-4 text-center">
          ℹ️ Actual notifications will include specific content details and timestamps
        </p>
      </div>

      {/* Current Configuration Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Current Configuration Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-white rounded-lg p-3">
            <div className="text-gray-600 text-xs mb-1">Email Notifications</div>
            <div className="font-semibold text-gray-800">
              {preferences?.email_notifications_enabled ? '✓ Enabled' : '✕ Disabled'}
            </div>
          </div>
          <div className="bg-white rounded-lg p-3">
            <div className="text-gray-600 text-xs mb-1">Active Severity Levels</div>
            <div className="font-semibold text-gray-800">
              {[
                preferences?.notify_on_critical && 'Critical',
                preferences?.notify_on_high && 'High',
                preferences?.notify_on_medium && 'Medium',
                preferences?.notify_on_low && 'Low'
              ].filter(Boolean).join(', ') || 'None'}
            </div>
          </div>
          <div className="bg-white rounded-lg p-3">
            <div className="text-gray-600 text-xs mb-1">Active Event Types</div>
            <div className="font-semibold text-gray-800">
              {[
                preferences?.notify_on_crisis && 'Crisis',
                preferences?.notify_on_abuse && 'Abuse',
                preferences?.notify_on_bullying && 'Bullying',
                preferences?.notify_on_inappropriate && 'Inappropriate',
                preferences?.notify_on_profanity && 'Profanity'
              ].filter(Boolean).join(', ') || 'None'}
            </div>
          </div>
          <div className="bg-white rounded-lg p-3">
            <div className="text-gray-600 text-xs mb-1">Summary Frequency</div>
            <div className="font-semibold text-gray-800 capitalize">
              {preferences?.summary_frequency === 'none' ? 'Disabled' : preferences?.summary_frequency || 'Weekly'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

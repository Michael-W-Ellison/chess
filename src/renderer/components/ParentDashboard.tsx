/**
 * ParentDashboard Component
 * Main parent dashboard for monitoring child's safety and activity
 */

import React, { useState } from 'react';
import { SafetyOverview } from './parent/SafetyOverview';
import { SafetyFlagsList } from './parent/SafetyFlagsList';
import { SafetyStatistics } from './parent/SafetyStatistics';
import { NotificationPreferences } from './parent/NotificationPreferences';
import { ConversationStatistics } from './parent/ConversationStatistics';

type DashboardTab = 'overview' | 'flags' | 'statistics' | 'conversations' | 'preferences';

export const ParentDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [userId] = useState<number>(1); // TODO: Get from context/props

  const tabs = [
    { id: 'overview' as DashboardTab, label: 'Overview', icon: '📊' },
    { id: 'flags' as DashboardTab, label: 'Safety Flags', icon: '🚩' },
    { id: 'statistics' as DashboardTab, label: 'Statistics', icon: '📈' },
    { id: 'conversations' as DashboardTab, label: 'Conversations', icon: '💬' },
    { id: 'preferences' as DashboardTab, label: 'Preferences', icon: '⚙️' },
  ];

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Parent Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">
              Monitor your child's safety and chatbot interactions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-700">Monitoring Active</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4 border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto pb-20">
        {activeTab === 'overview' && <SafetyOverview userId={userId} />}
        {activeTab === 'flags' && <SafetyFlagsList userId={userId} />}
        {activeTab === 'statistics' && <SafetyStatistics userId={userId} />}
        {activeTab === 'conversations' && <ConversationStatistics userId={userId} />}
        {activeTab === 'preferences' && <NotificationPreferences userId={userId} />}
      </div>
    </div>
  );
};

export default ParentDashboard;

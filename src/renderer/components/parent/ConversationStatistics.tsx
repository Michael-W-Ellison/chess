/**
 * ConversationStatistics Component
 * Display conversation activity and usage statistics
 */

import React, { useState } from 'react';
import { useConversationStats } from '../../hooks/useConversationStats';

interface ConversationStatisticsProps {
  userId: number;
}

export const ConversationStatistics: React.FC<ConversationStatisticsProps> = ({ userId }) => {
  const [timeRange, setTimeRange] = useState<number>(30); // days
  const { stats, isLoading, error } = useConversationStats(userId, timeRange);

  const timeRanges = [
    { value: 7, label: 'Last 7 Days' },
    { value: 30, label: 'Last 30 Days' },
    { value: 90, label: 'Last 90 Days' },
    { value: 365, label: 'Last Year' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading conversation statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading statistics: {error}</p>
        </div>
      </div>
    );
  }

  const totalConversations = stats?.total_conversations || 0;
  const totalMessages = stats?.total_messages || 0;
  const avgMessagesPerConversation = totalConversations > 0
    ? (totalMessages / totalConversations).toFixed(1)
    : '0';

  return (
    <div className="p-6 space-y-6">
      {/* Time Range Selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="font-semibold text-gray-800 mb-3">Time Range</h3>
        <div className="flex flex-wrap gap-2">
          {timeRanges.map((range) => (
            <button
              key={range.value}
              onClick={() => setTimeRange(range.value)}
              className={`px-4 py-2 rounded-lg border transition-colors ${
                timeRange === range.value
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span className="text-sm font-medium">{range.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Total Conversations */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Total Conversations</span>
            <span className="text-2xl">💬</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{totalConversations}</div>
          <p className="text-xs text-gray-500 mt-1">Chat sessions</p>
        </div>

        {/* Total Messages */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Total Messages</span>
            <span className="text-2xl">📝</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{totalMessages}</div>
          <p className="text-xs text-gray-500 mt-1">Messages exchanged</p>
        </div>

        {/* Avg Messages/Conversation */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Average Length</span>
            <span className="text-2xl">📊</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{avgMessagesPerConversation}</div>
          <p className="text-xs text-gray-500 mt-1">Messages per chat</p>
        </div>

        {/* Active Days */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Active Days</span>
            <span className="text-2xl">📅</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">{stats?.active_days || 0}</div>
          <p className="text-xs text-gray-500 mt-1">Days with activity</p>
        </div>
      </div>

      {/* Activity Trend */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Activity Trend</h3>
        <div className="space-y-4">
          {stats?.daily_activity && stats.daily_activity.length > 0 ? (
            <div className="space-y-2">
              {stats.daily_activity.slice(-7).map((day: any, index: number) => {
                const maxMessages = Math.max(...stats.daily_activity.map((d: any) => d.message_count));
                const percentage = maxMessages > 0 ? (day.message_count / maxMessages) * 100 : 0;

                return (
                  <div key={index}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">
                        {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}
                      </span>
                      <span className="text-sm text-gray-600">{day.message_count} messages</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No activity data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Most Active Hours */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Most Active Times</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats?.hourly_distribution && Object.keys(stats.hourly_distribution).length > 0 ? (
            Object.entries(stats.hourly_distribution)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .slice(0, 4)
              .map(([hour, count]) => (
                <div key={hour} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="text-2xl font-bold text-gray-900">
                    {parseInt(hour) === 0 ? '12' : parseInt(hour) > 12 ? parseInt(hour) - 12 : hour}
                    {parseInt(hour) >= 12 ? 'PM' : 'AM'}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">{count} messages</div>
                </div>
              ))
          ) : (
            <div className="col-span-4 text-center py-4 text-gray-500">
              <p>No hourly data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Conversation Topics */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Popular Topics</h3>
        <div className="space-y-3">
          {stats?.topics && stats.topics.length > 0 ? (
            stats.topics.slice(0, 5).map((topic: any, index: number) => (
              <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-lg">
                    {topic.category === 'school' && '📚'}
                    {topic.category === 'friendship' && '👥'}
                    {topic.category === 'family' && '👨‍👩‍👧'}
                    {topic.category === 'emotional' && '❤️'}
                    {topic.category === 'hobbies' && '🎨'}
                    {!['school', 'friendship', 'family', 'emotional', 'hobbies'].includes(topic.category) && '💬'}
                  </span>
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-800 capitalize">{topic.category.replace(/_/g, ' ')}</div>
                  <div className="text-sm text-gray-600">{topic.count} conversations</div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No topic data available</p>
            </div>
          )}
        </div>
      </div>

      {/* Usage Patterns */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Usage Patterns</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">🕐</span>
              <div className="font-medium text-gray-800">Average Session Length</div>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats?.avg_session_duration ? `${Math.floor(stats.avg_session_duration / 60)}m ${stats.avg_session_duration % 60}s` : 'N/A'}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">📆</span>
              <div className="font-medium text-gray-800">Sessions Per Week</div>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats?.sessions_per_week ? stats.sessions_per_week.toFixed(1) : 'N/A'}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">💭</span>
              <div className="font-medium text-gray-800">Longest Conversation</div>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats?.longest_conversation || 0} messages
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-2xl">⏱️</span>
              <div className="font-medium text-gray-800">Total Time Spent</div>
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {stats?.total_time_spent
                ? `${Math.floor(stats.total_time_spent / 3600)}h ${Math.floor((stats.total_time_spent % 3600) / 60)}m`
                : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-800 mb-3">💡 Insights</h3>
        <ul className="space-y-2 text-sm text-blue-700">
          {totalConversations > 0 && (
            <li>
              • Your child has had <strong>{totalConversations}</strong> conversation{totalConversations === 1 ? '' : 's'} in the last {timeRange} days
            </li>
          )}
          {stats?.most_active_day && (
            <li>
              • Most active on <strong>{stats.most_active_day}</strong>
            </li>
          )}
          {stats?.topics && stats.topics.length > 0 && (
            <li>
              • Most discussed topic: <strong>{stats.topics[0].category.replace(/_/g, ' ')}</strong>
            </li>
          )}
          {stats?.sessions_per_week && stats.sessions_per_week > 7 && (
            <li className="text-orange-700">
              • High activity detected - averaging <strong>{stats.sessions_per_week.toFixed(1)}</strong> sessions per week
            </li>
          )}
          {totalConversations === 0 && (
            <li className="text-gray-600">
              • No conversations recorded in the selected time period
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

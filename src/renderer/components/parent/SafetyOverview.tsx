/**
 * SafetyOverview Component
 * Dashboard overview with safety summary and attention indicators
 */

import React from 'react';
import { useSafetyOverview } from '../../hooks/useSafetyOverview';
import { SeverityDistribution } from './SeverityDistribution';
import { SeverityBadge } from '../common/SeverityBadge';

interface SafetyOverviewProps {
  userId: number;
}

export const SafetyOverview: React.FC<SafetyOverviewProps> = ({ userId }) => {
  const { overview, isLoading, error } = useSafetyOverview(userId);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading overview...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading overview: {error}</p>
        </div>
      </div>
    );
  }

  const requiresAttention = overview?.requires_attention || false;
  const criticalCount = overview?.critical_flags_count || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Attention Banner */}
      {requiresAttention && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg">
          <div className="flex items-start gap-3">
            <span className="text-2xl">⚠️</span>
            <div className="flex-1">
              <h3 className="font-semibold text-red-800">Attention Required</h3>
              <p className="text-sm text-red-700 mt-1">
                There are {criticalCount} critical safety {criticalCount === 1 ? 'flag' : 'flags'}{' '}
                that require your immediate attention.
              </p>
              <button className="mt-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium">
                View Critical Flags
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Flags */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">All-Time Flags</span>
            <span className="text-2xl">🚩</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {overview?.total_flags_all_time || 0}
          </div>
          <p className="text-xs text-gray-500 mt-1">Total safety events</p>
        </div>

        {/* Recent Flags */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Last 7 Days</span>
            <span className="text-2xl">📅</span>
          </div>
          <div className="text-3xl font-bold text-gray-900">
            {overview?.total_flags_last_7_days || 0}
          </div>
          <p className="text-xs text-gray-500 mt-1">Recent events</p>
        </div>

        {/* Critical Flags */}
        <div className={`bg-white rounded-lg border p-6 ${criticalCount > 0 ? 'border-red-300 bg-red-50' : 'border-gray-200'}`}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Critical</span>
            <span className="text-2xl">{criticalCount > 0 ? '🚨' : '✅'}</span>
          </div>
          <div className={`text-3xl font-bold ${criticalCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
            {criticalCount}
          </div>
          <div className="mt-2">
            {criticalCount > 0 ? (
              <SeverityBadge severity="critical" size="sm" />
            ) : (
              <p className="text-xs text-green-600 font-medium">All clear</p>
            )}
          </div>
        </div>

        {/* Most Common Type */}
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-600 text-sm font-medium">Most Common</span>
            <span className="text-2xl">📊</span>
          </div>
          <div className="text-lg font-bold text-gray-900 capitalize">
            {overview?.most_common_flag_type?.replace(/_/g, ' ') || 'None'}
          </div>
          <p className="text-xs text-gray-500 mt-1">Flag type</p>
        </div>
      </div>

      {/* Severity Distribution and Last Event */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Severity Distribution */}
        <SeverityDistribution userId={userId} sinceDays={30} />

        {/* Last Event */}
        {overview?.last_flag_timestamp && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-800 mb-3">Last Safety Event</h3>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-lg">🕐</span>
              </div>
              <div>
                <p className="text-sm text-gray-600">
                  {new Date(overview.last_flag_timestamp).toLocaleString()}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {(() => {
                    const diff = Date.now() - new Date(overview.last_flag_timestamp).getTime();
                    const hours = Math.floor(diff / (1000 * 60 * 60));
                    const days = Math.floor(hours / 24);
                    if (days > 0) return `${days} day${days === 1 ? '' : 's'} ago`;
                    if (hours > 0) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
                    return 'Less than an hour ago';
                  })()}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <button className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span className="text-2xl">🔔</span>
            <div className="text-left">
              <div className="font-medium text-gray-800 text-sm">View Unnotified Flags</div>
              <div className="text-xs text-gray-500">Flags requiring review</div>
            </div>
          </button>
          <button className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span className="text-2xl">📧</span>
            <div className="text-left">
              <div className="font-medium text-gray-800 text-sm">Email Settings</div>
              <div className="text-xs text-gray-500">Configure notifications</div>
            </div>
          </button>
          <button className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span className="text-2xl">📈</span>
            <div className="text-left">
              <div className="font-medium text-gray-800 text-sm">View Trends</div>
              <div className="text-xs text-gray-500">Activity over time</div>
            </div>
          </button>
          <button className="flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <span className="text-2xl">📋</span>
            <div className="text-left">
              <div className="font-medium text-gray-800 text-sm">Export Report</div>
              <div className="text-xs text-gray-500">Download activity log</div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

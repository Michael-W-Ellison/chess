/**
 * SafetyStatistics Component
 * Safety statistics and analytics
 */

import React, { useState } from 'react';
import { useSafetyStatistics } from '../../hooks/useSafetyStatistics';

interface SafetyStatisticsProps {
  userId: number;
}

export const SafetyStatistics: React.FC<SafetyStatisticsProps> = ({ userId }) => {
  const [timeRange, setTimeRange] = useState<number | null>(null); // null = all time
  const { statistics, isLoading, error } = useSafetyStatistics(userId, timeRange);

  const timeRanges = [
    { value: null, label: 'All Time' },
    { value: 7, label: 'Last 7 Days' },
    { value: 30, label: 'Last 30 Days' },
    { value: 90, label: 'Last 90 Days' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading statistics...</p>
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

  const bySeverity = statistics?.by_severity || {};
  const byType = statistics?.by_type || {};
  const total = statistics?.total_flags || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Time Range Selector */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="font-semibold text-gray-800 mb-3">Time Range</h3>
        <div className="flex flex-wrap gap-2">
          {timeRanges.map((range) => (
            <button
              key={range.label}
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm text-gray-600 mb-1">Total Events</div>
          <div className="text-3xl font-bold text-gray-900">{total}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm text-gray-600 mb-1">Reviewed</div>
          <div className="text-3xl font-bold text-green-600">{statistics?.parent_notified || 0}</div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="text-sm text-gray-600 mb-1">Pending Review</div>
          <div className="text-3xl font-bold text-orange-600">{statistics?.parent_unnotified || 0}</div>
        </div>
      </div>

      {/* By Severity */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Events by Severity</h3>
        <div className="space-y-3">
          {Object.entries(bySeverity).map(([severity, count]) => {
            const percentage = total > 0 ? ((count as number) / total) * 100 : 0;
            const colors: Record<string, string> = {
              critical: 'bg-red-500',
              high: 'bg-orange-500',
              medium: 'bg-yellow-500',
              low: 'bg-blue-500',
            };

            return (
              <div key={severity}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700 capitalize">{severity}</span>
                  <span className="text-sm text-gray-600">
                    {count} ({percentage.toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-full rounded-full transition-all ${colors[severity] || 'bg-gray-500'}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* By Type */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Events by Type</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(byType).map(([type, count]) => (
            <div
              key={type}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200"
            >
              <div>
                <div className="font-medium text-gray-800 capitalize">{type.replace(/_/g, ' ')}</div>
                <div className="text-sm text-gray-600 mt-1">{count} events</div>
              </div>
              <div className="text-2xl">
                {type === 'crisis' && '⚠️'}
                {type === 'abuse' && '🛡️'}
                {type === 'bullying' && '👊'}
                {type === 'profanity' && '🤬'}
                {type === 'inappropriate_request' && '🚫'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Last 24 Hours */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-3">Last 24 Hours Activity</h3>
        <div className="flex items-center gap-3">
          <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-2xl font-bold text-blue-600">{statistics?.last_24_hours || 0}</span>
          </div>
          <div>
            <div className="text-sm text-gray-600">Safety events in the last 24 hours</div>
            <div className="text-xs text-gray-500 mt-1">
              {statistics?.last_24_hours === 0
                ? 'No recent activity'
                : statistics?.last_24_hours === 1
                ? '1 event detected'
                : `${statistics?.last_24_hours} events detected`}
            </div>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-800 mb-3">📊 Insights</h3>
        <ul className="space-y-2 text-sm text-blue-700">
          {Object.entries(bySeverity).length > 0 && (
            <li>
              • Most flags are{' '}
              <strong>
                {
                  Object.entries(bySeverity).sort(
                    ([, a], [, b]) => (b as number) - (a as number)
                  )[0][0]
                }
              </strong>{' '}
              severity
            </li>
          )}
          {Object.entries(byType).length > 0 && (
            <li>
              • Most common type is{' '}
              <strong>
                {Object.entries(byType)
                  .sort(([, a], [, b]) => (b as number) - (a as number))[0][0]
                  .replace(/_/g, ' ')}
              </strong>
            </li>
          )}
          {statistics?.parent_unnotified && statistics.parent_unnotified > 0 && (
            <li className="text-orange-700">
              • <strong>{statistics.parent_unnotified}</strong> flag{statistics.parent_unnotified === 1 ? '' : 's'} pending your review
            </li>
          )}
        </ul>
      </div>
    </div>
  );
};

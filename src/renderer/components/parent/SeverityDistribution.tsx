/**
 * SeverityDistribution Component
 * Visual distribution of safety flags by severity level
 */

import React from 'react';
import { useSafetyStatistics } from '../../hooks/useSafetyStatistics';
import { SeverityBadge } from '../common/SeverityBadge';

interface SeverityDistributionProps {
  userId: number;
  sinceDays?: number | null;
}

export const SeverityDistribution: React.FC<SeverityDistributionProps> = ({
  userId,
  sinceDays = null,
}) => {
  const { statistics, isLoading, error } = useSafetyStatistics(userId, sinceDays);

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Severity Distribution</h3>
        <div className="flex items-center justify-center h-32">
          <div className="text-center">
            <div className="animate-spin text-2xl mb-2">⏳</div>
            <p className="text-sm text-gray-600">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !statistics) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Severity Distribution</h3>
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">Unable to load severity distribution</p>
        </div>
      </div>
    );
  }

  const { by_severity, total_flags } = statistics;

  const severityData = [
    { level: 'critical' as const, count: by_severity.critical || 0, color: 'bg-red-500' },
    { level: 'high' as const, count: by_severity.high || 0, color: 'bg-orange-500' },
    { level: 'medium' as const, count: by_severity.medium || 0, color: 'bg-yellow-500' },
    { level: 'low' as const, count: by_severity.low || 0, color: 'bg-blue-500' },
  ];

  const maxCount = Math.max(...severityData.map((d) => d.count), 1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-gray-800">Severity Distribution</h3>
        {sinceDays && (
          <span className="text-xs text-gray-500">Last {sinceDays} days</span>
        )}
      </div>

      {total_flags === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
          <div className="text-4xl mb-2">✅</div>
          <p className="text-sm text-green-800 font-medium">No safety flags</p>
          <p className="text-xs text-green-600 mt-1">All clear!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Bar Chart */}
          <div className="space-y-3">
            {severityData.map(({ level, count, color }) => {
              const percentage = total_flags > 0 ? (count / total_flags) * 100 : 0;
              const barWidth = total_flags > 0 ? (count / maxCount) * 100 : 0;

              return (
                <div key={level} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <SeverityBadge severity={level} size="sm" />
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900">{count}</span>
                      <span className="text-gray-500">({percentage.toFixed(0)}%)</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${color} transition-all duration-300`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Total Flags</span>
              <span className="font-bold text-gray-900">{total_flags}</span>
            </div>
          </div>

          {/* Critical Alert */}
          {by_severity.critical > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-start gap-2">
                <span className="text-lg">⚠️</span>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-800">
                    {by_severity.critical} Critical {by_severity.critical === 1 ? 'Flag' : 'Flags'}
                  </p>
                  <p className="text-xs text-red-700 mt-1">
                    These require immediate attention
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

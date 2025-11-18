/**
 * SafetyFlagsList Component
 * List of safety flags with filtering and details
 */

import React, { useState } from 'react';
import { useSafetyFlags } from '../../hooks/useSafetyFlags';

interface SafetyFlagsListProps {
  userId: number;
}

type FilterType = 'all' | 'critical' | 'unnotified' | 'crisis' | 'abuse' | 'bullying' | 'profanity';

export const SafetyFlagsList: React.FC<SafetyFlagsListProps> = ({ userId }) => {
  const [filter, setFilter] = useState<FilterType>('all');
  const [selectedFlag, setSelectedFlag] = useState<number | null>(null);
  const { flags, isLoading, error } = useSafetyFlags(userId, filter);

  const filters = [
    { id: 'all' as FilterType, label: 'All Flags', icon: '📋' },
    { id: 'critical' as FilterType, label: 'Critical', icon: '🚨' },
    { id: 'unnotified' as FilterType, label: 'Unnotified', icon: '🔔' },
    { id: 'crisis' as FilterType, label: 'Crisis', icon: '⚠️' },
    { id: 'abuse' as FilterType, label: 'Abuse', icon: '🛡️' },
    { id: 'bullying' as FilterType, label: 'Bullying', icon: '👊' },
    { id: 'profanity' as FilterType, label: 'Profanity', icon: '🤬' },
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⏳</div>
          <p className="text-gray-600">Loading safety flags...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">Error loading flags: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Filters */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="font-semibold text-gray-800 mb-3">Filter Flags</h3>
        <div className="flex flex-wrap gap-2">
          {filters.map((f) => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                filter === f.id
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{f.icon}</span>
              <span className="text-sm font-medium">{f.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Flags List */}
      <div className="space-y-3">
        {flags && flags.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">✅</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No Flags Found</h3>
            <p className="text-gray-600">
              {filter === 'all' ? 'No safety flags have been recorded.' : `No ${filter} flags found.`}
            </p>
          </div>
        ) : (
          flags?.map((flag: any) => (
            <div
              key={flag.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedFlag(selectedFlag === flag.id ? null : flag.id)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Header */}
                  <div className="flex items-center gap-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(
                        flag.severity
                      )}`}
                    >
                      {flag.severity.toUpperCase()}
                    </span>
                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                      {flag.flag_type.replace(/_/g, ' ')}
                    </span>
                    {!flag.parent_notified && (
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
                        Not Reviewed
                      </span>
                    )}
                  </div>

                  {/* Timestamp */}
                  <div className="text-sm text-gray-600 mb-2">
                    {new Date(flag.timestamp).toLocaleString()}
                  </div>

                  {/* Content Snippet */}
                  {flag.content_snippet && (
                    <div className="bg-gray-50 rounded-lg p-3 mb-2">
                      <p className="text-sm text-gray-700 italic">&quot;{flag.content_snippet}&quot;</p>
                    </div>
                  )}

                  {/* Expanded Details */}
                  {selectedFlag === flag.id && (
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-600">Flag ID:</span>
                          <span className="ml-2 font-mono text-gray-800">{flag.id}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">Message ID:</span>
                          <span className="ml-2 font-mono text-gray-800">{flag.message_id || 'N/A'}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-gray-600">Action Taken:</span>
                          <span className="ml-2 text-gray-800">{flag.action_taken || 'None'}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 mt-3">
                        <button className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
                          Mark as Reviewed
                        </button>
                        <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
                          View Message
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                <button
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFlag(selectedFlag === flag.id ? null : flag.id);
                  }}
                >
                  {selectedFlag === flag.id ? '▲' : '▼'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Load More */}
      {flags && flags.length > 0 && flags.length % 20 === 0 && (
        <div className="flex justify-center">
          <button className="px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
            Load More Flags
          </button>
        </div>
      )}
    </div>
  );
};

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
type SortType = 'newest' | 'oldest' | 'severity';

export const SafetyFlagsList: React.FC<SafetyFlagsListProps> = ({ userId }) => {
  const [filter, setFilter] = useState<FilterType>('all');
  const [sort, setSort] = useState<SortType>('newest');
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

  const handleMarkAsReviewed = async (flagId: number) => {
    try {
      // TODO: Replace with actual API call
      // await fetch(`http://localhost:8000/api/parent/safety-flags/${flagId}/mark-notified`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      // });
      console.log(`Marked flag ${flagId} as reviewed`);
      // Refresh flags list
    } catch (err) {
      console.error('Failed to mark flag as reviewed:', err);
    }
  };

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

  const getFlagTypeGuidance = (flagType: string, severity: string) => {
    const isUrgent = severity.toLowerCase() === 'critical' || flagType.includes('crisis');

    const guidance: Record<string, { title: string; action: string; resources?: string[] }> = {
      crisis_suicide: {
        title: 'Suicide-Related Content',
        action: 'URGENT: Talk to your child immediately. Contact mental health professionals.',
        resources: [
          'National Suicide Prevention Lifeline: 988',
          'Crisis Text Line: Text HOME to 741741',
          'International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/',
        ],
      },
      crisis_self_harm: {
        title: 'Self-Harm Content',
        action: 'URGENT: Have a calm conversation with your child. Seek professional help.',
        resources: [
          'National Suicide Prevention Lifeline: 988',
          'SAMHSA National Helpline: 1-800-662-4357',
        ],
      },
      abuse: {
        title: 'Potential Abuse',
        action: 'Talk to your child in a safe, non-judgmental environment. Consider contacting authorities.',
        resources: [
          'Childhelp National Child Abuse Hotline: 1-800-422-4453',
          'RAINN National Sexual Assault Hotline: 1-800-656-4673',
        ],
      },
      bullying: {
        title: 'Bullying Content',
        action: 'Discuss with your child. Contact school if needed.',
        resources: ['StopBullying.gov: https://www.stopbullying.gov/'],
      },
      inappropriate_request: {
        title: 'Inappropriate Request',
        action: 'Review the content and discuss appropriate boundaries with your child.',
      },
      profanity: {
        title: 'Profanity Detected',
        action: 'Consider discussing language and communication with your child.',
      },
    };

    return guidance[flagType] || {
      title: flagType.replace(/_/g, ' '),
      action: 'Review this flag and take appropriate action.',
    };
  };

  const sortedFlags = [...(flags || [])].sort((a, b) => {
    switch (sort) {
      case 'newest':
        return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
      case 'oldest':
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      case 'severity': {
        const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
        return (severityOrder[a.severity.toLowerCase()] || 4) - (severityOrder[b.severity.toLowerCase()] || 4);
      }
      default:
        return 0;
    }
  });

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

  const criticalCount = flags?.filter((f: any) => f.severity.toLowerCase() === 'critical').length || 0;
  const unreviewedCount = flags?.filter((f: any) => !f.parent_notified).length || 0;

  return (
    <div className="p-6 space-y-6">
      {/* Statistics Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">📋</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-gray-900">{flags?.length || 0}</div>
              <div className="text-sm text-gray-600">Total Flags</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">🚨</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{criticalCount}</div>
              <div className="text-sm text-gray-600">Critical Flags</div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">🔔</span>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600">{unreviewedCount}</div>
              <div className="text-sm text-gray-600">Need Review</div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Sort */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
        <div>
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

        <div>
          <h3 className="font-semibold text-gray-800 mb-3">Sort By</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setSort('newest')}
              className={`px-4 py-2 rounded-lg border transition-colors text-sm font-medium ${
                sort === 'newest'
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              Newest First
            </button>
            <button
              onClick={() => setSort('oldest')}
              className={`px-4 py-2 rounded-lg border transition-colors text-sm font-medium ${
                sort === 'oldest'
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              Oldest First
            </button>
            <button
              onClick={() => setSort('severity')}
              className={`px-4 py-2 rounded-lg border transition-colors text-sm font-medium ${
                sort === 'severity'
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
              }`}
            >
              By Severity
            </button>
          </div>
        </div>
      </div>

      {/* Flags List */}
      <div className="space-y-3">
        {sortedFlags.length === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4">✅</div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No Flags Found</h3>
            <p className="text-gray-600">
              {filter === 'all' ? 'No safety flags have been recorded.' : `No ${filter} flags found.`}
            </p>
          </div>
        ) : (
          sortedFlags.map((flag: any) => {
            const guidance = getFlagTypeGuidance(flag.flag_type, flag.severity);
            const isCritical = flag.severity.toLowerCase() === 'critical' || flag.flag_type.includes('crisis');

            return (
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
                    <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
                      {/* Guidance Section */}
                      <div className={`rounded-lg p-4 ${isCritical ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
                        <h4 className={`font-semibold mb-2 ${isCritical ? 'text-red-800' : 'text-blue-800'}`}>
                          {isCritical && '⚠️ '}{guidance.title}
                        </h4>
                        <p className={`text-sm mb-2 ${isCritical ? 'text-red-700' : 'text-blue-700'}`}>
                          <strong>Recommended Action:</strong> {guidance.action}
                        </p>
                        {guidance.resources && guidance.resources.length > 0 && (
                          <div className="mt-2">
                            <p className={`text-sm font-semibold mb-1 ${isCritical ? 'text-red-800' : 'text-blue-800'}`}>
                              Crisis Resources:
                            </p>
                            <ul className={`text-xs space-y-1 ${isCritical ? 'text-red-700' : 'text-blue-700'}`}>
                              {guidance.resources.map((resource, idx) => (
                                <li key={idx}>• {resource}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Flag Details */}
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
                        <div className="col-span-2">
                          <span className="text-gray-600">Conversation ID:</span>
                          <span className="ml-2 font-mono text-gray-800">{flag.conversation_id || 'N/A'}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2 mt-3">
                        {!flag.parent_notified && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleMarkAsReviewed(flag.id);
                            }}
                            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
                          >
                            Mark as Reviewed
                          </button>
                        )}
                        {flag.parent_notified && (
                          <div className="flex-1 px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded-lg text-sm font-medium text-center">
                            ✓ Reviewed
                          </div>
                        )}
                        <button
                          onClick={(e) => e.stopPropagation()}
                          className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
                        >
                          View Conversation
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
            );
          })
        )}
      </div>

      {/* Load More */}
      {sortedFlags.length > 0 && sortedFlags.length >= 20 && (
        <div className="flex justify-center">
          <button className="px-6 py-3 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium">
            Load More Flags
          </button>
        </div>
      )}

      {/* Export Options */}
      {sortedFlags.length > 0 && (
        <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-gray-800">Export Flags</h3>
              <p className="text-sm text-gray-600 mt-1">Download safety flags for your records</p>
            </div>
            <button className="px-4 py-2 bg-white border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
              Download CSV
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

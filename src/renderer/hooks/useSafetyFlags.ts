/**
 * useSafetyFlags Hook
 * Fetches safety flags with filtering
 */

import { useState, useEffect } from 'react';

interface SafetyFlag {
  id: number;
  user_id: number;
  message_id: number | null;
  flag_type: string;
  severity: string;
  content_snippet: string | null;
  action_taken: string | null;
  timestamp: string;
  parent_notified: boolean;
}

export const useSafetyFlags = (userId: number, filter: string) => {
  const [flags, setFlags] = useState<SafetyFlag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const refetch = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  useEffect(() => {
    const fetchFlags = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Determine API endpoint based on filter type
        let endpoint = '';
        const baseUrl = 'http://localhost:8000/api/parent';

        switch (filter) {
          case 'all':
            endpoint = `${baseUrl}/safety-flags/all?user_id=${userId}&limit=100`;
            break;
          case 'critical':
            endpoint = `${baseUrl}/safety-flags/critical?user_id=${userId}`;
            break;
          case 'unnotified':
            endpoint = `${baseUrl}/safety-flags/unnotified?user_id=${userId}`;
            break;
          case 'crisis':
          case 'abuse':
          case 'bullying':
          case 'profanity':
            endpoint = `${baseUrl}/safety-flags/by-type/${filter}?user_id=${userId}`;
            break;
          default:
            endpoint = `${baseUrl}/safety-flags/all?user_id=${userId}&limit=100`;
        }

        const response = await fetch(endpoint);

        if (!response.ok) {
          throw new Error(`Failed to fetch safety flags: ${response.statusText}`);
        }

        const data = await response.json();
        setFlags(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch flags');
        setFlags([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFlags();
  }, [userId, filter, refreshTrigger]);

  return { flags, isLoading, error, refetch };
};

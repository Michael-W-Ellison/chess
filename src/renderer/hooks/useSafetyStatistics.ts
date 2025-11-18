/**
 * useSafetyStatistics Hook
 * Fetches safety statistics with time range filtering
 */

import { useState, useEffect } from 'react';

interface Statistics {
  total_flags: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  parent_notified: number;
  parent_unnotified: number;
  last_24_hours: number;
}

export const useSafetyStatistics = (userId: number, sinceDays: number | null) => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStatistics = async () => {
      try:
        setIsLoading(true);
        setError(null);

        const baseUrl = 'http://localhost:8000/api/parent/safety-flags/stats';
        const url = sinceDays
          ? `${baseUrl}?user_id=${userId}&since_days=${sinceDays}`
          : `${baseUrl}?user_id=${userId}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch statistics: ${response.statusText}`);
        }

        const data = await response.json();
        setStatistics(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
        // Set default statistics on error
        setStatistics({
          total_flags: 0,
          by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
          by_type: {},
          parent_notified: 0,
          parent_unnotified: 0,
          last_24_hours: 0,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatistics();
  }, [userId, sinceDays]);

  return { statistics, isLoading, error };
};

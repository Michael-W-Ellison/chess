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
      try {
        setIsLoading(true);
        setError(null);

        // TODO: Replace with actual API call
        // const url = sinceDays
        //   ? `http://localhost:8000/api/parent/statistics?user_id=${userId}&since_days=${sinceDays}`
        //   : `http://localhost:8000/api/parent/statistics?user_id=${userId}`;
        // const response = await fetch(url);
        // const data = await response.json();

        // Mock data for now
        const mockData: Statistics = {
          total_flags: 0,
          by_severity: { critical: 0, high: 0, medium: 0, low: 0 },
          by_type: {},
          parent_notified: 0,
          parent_unnotified: 0,
          last_24_hours: 0,
        };

        setStatistics(mockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStatistics();
  }, [userId, sinceDays]);

  return { statistics, isLoading, error };
};

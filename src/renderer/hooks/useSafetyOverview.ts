/**
 * useSafetyOverview Hook
 * Fetches parent dashboard safety overview data
 */

import { useState, useEffect } from 'react';

interface SafetyOverview {
  user_id: number;
  user_name: string;
  total_flags_all_time: number;
  total_flags_last_7_days: number;
  critical_flags_count: number;
  last_flag_timestamp: string | null;
  most_common_flag_type: string | null;
  requires_attention: boolean;
}

export const useSafetyOverview = (userId: number) => {
  const [overview, setOverview] = useState<SafetyOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // TODO: Replace with actual API call
        // const response = await fetch(`http://localhost:8000/api/parent/dashboard/overview?user_id=${userId}`);
        // const data = await response.json();

        // Mock data for now
        const mockData: SafetyOverview = {
          user_id: userId,
          user_name: 'Test Child',
          total_flags_all_time: 0,
          total_flags_last_7_days: 0,
          critical_flags_count: 0,
          last_flag_timestamp: null,
          most_common_flag_type: null,
          requires_attention: false,
        };

        setOverview(mockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch overview');
      } finally {
        setIsLoading(false);
      }
    };

    fetchOverview();
  }, [userId]);

  return { overview, isLoading, error };
};

/**
 * useConversationStats Hook
 * Fetches conversation statistics and usage patterns
 */

import { useState, useEffect } from 'react';

interface DailyActivity {
  date: string;
  message_count: number;
}

interface Topic {
  category: string;
  count: number;
}

interface ConversationStats {
  total_conversations: number;
  total_messages: number;
  active_days: number;
  daily_activity: DailyActivity[];
  hourly_distribution: Record<number, number>;
  topics: Topic[];
  avg_session_duration: number; // in seconds
  sessions_per_week: number;
  longest_conversation: number;
  total_time_spent: number; // in seconds
  most_active_day: string;
}

export const useConversationStats = (userId: number, timeRange: number) => {
  const [stats, setStats] = useState<ConversationStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // TODO: Replace with actual API call
        // const response = await fetch(
        //   `http://localhost:8000/api/parent/conversation-stats?user_id=${userId}&time_range_days=${timeRange}`
        // );
        // const data = await response.json();

        // Mock data for now
        const mockData: ConversationStats = {
          total_conversations: 0,
          total_messages: 0,
          active_days: 0,
          daily_activity: [],
          hourly_distribution: {},
          topics: [],
          avg_session_duration: 0,
          sessions_per_week: 0,
          longest_conversation: 0,
          total_time_spent: 0,
          most_active_day: '',
        };

        setStats(mockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch conversation stats');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, [userId, timeRange]);

  return { stats, isLoading, error };
};

/**
 * useNotificationPreferences Hook
 * Manages notification preferences
 */

import { useState, useEffect, useCallback } from 'react';

interface Preferences {
  id: number;
  user_id: number;
  email_notifications_enabled: boolean;
  instant_notification_min_severity: string;
  severity_filters: {
    critical: boolean;
    high: boolean;
    medium: boolean;
    low: boolean;
  };
  flag_type_filters: {
    crisis: boolean;
    abuse: boolean;
    bullying: boolean;
    profanity: boolean;
    inappropriate: boolean;
  };
  summary_settings: {
    frequency: string;
    day_of_week: number | null;
    hour: number;
  };
  content_settings: {
    include_snippets: boolean;
    max_snippet_length: number;
  };
  quiet_hours: {
    enabled: boolean;
    start: number | null;
    end: number | null;
  };
  created_at: string;
  updated_at: string;
}

export const useNotificationPreferences = (userId: number) => {
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPreferences = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // TODO: Replace with actual API call
      // const response = await fetch(`http://localhost:8000/api/parent/preferences?user_id=${userId}`);
      // const data = await response.json();

      // Mock default preferences
      const mockData: Preferences = {
        id: 1,
        user_id: userId,
        email_notifications_enabled: true,
        instant_notification_min_severity: 'high',
        severity_filters: {
          critical: true,
          high: true,
          medium: false,
          low: false,
        },
        flag_type_filters: {
          crisis: true,
          abuse: true,
          bullying: true,
          profanity: false,
          inappropriate: true,
        },
        summary_settings: {
          frequency: 'weekly',
          day_of_week: 0,
          hour: 9,
        },
        content_settings: {
          include_snippets: true,
          max_snippet_length: 100,
        },
        quiet_hours: {
          enabled: false,
          start: 22,
          end: 7,
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      setPreferences(mockData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch preferences');
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const updatePreferences = useCallback(async (updates: any) => {
    try {
      setIsSaving(true);

      // TODO: Replace with actual API call
      // const response = await fetch(`http://localhost:8000/api/parent/preferences?user_id=${userId}`, {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updates),
      // });
      // const data = await response.json();

      // Mock update for now - merge updates with current preferences
      setPreferences((prev) => {
        if (!prev) return prev;

        const updated = { ...prev };

        // Handle top-level updates
        Object.keys(updates).forEach((key) => {
          if (key in updated) {
            (updated as any)[key] = updates[key];
          }
        });

        updated.updated_at = new Date().toISOString();
        return updated;
      });

      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 500));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      throw err;
    } finally {
      setIsSaving(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  return { preferences, updatePreferences, isLoading, isSaving, error };
};

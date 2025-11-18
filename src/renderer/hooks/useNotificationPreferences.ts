/**
 * useNotificationPreferences Hook
 * Manages notification preferences
 */

import { useState, useEffect, useCallback } from 'react';

interface Preferences {
  id: number;
  user_id: number;
  email: string | null;
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
  // Flattened fields for component compatibility
  notify_on_critical?: boolean;
  notify_on_high?: boolean;
  notify_on_medium?: boolean;
  notify_on_low?: boolean;
  notify_on_crisis?: boolean;
  notify_on_abuse?: boolean;
  notify_on_bullying?: boolean;
  notify_on_profanity?: boolean;
  notify_on_inappropriate?: boolean;
  summary_frequency?: string;
  summary_day_of_week?: number | null;
  summary_hour?: number;
  quiet_hours_enabled?: boolean;
  quiet_hours_start?: number | null;
  quiet_hours_end?: number | null;
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

      const response = await fetch(`http://localhost:8000/api/parent/preferences?user_id=${userId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch preferences: ${response.statusText}`);
      }

      const data = await response.json();

      // Flatten nested structure for component compatibility
      const flattenedData: Preferences = {
        ...data,
        // Add flattened severity filters
        notify_on_critical: data.severity_filters.critical,
        notify_on_high: data.severity_filters.high,
        notify_on_medium: data.severity_filters.medium,
        notify_on_low: data.severity_filters.low,
        // Add flattened flag type filters
        notify_on_crisis: data.flag_type_filters.crisis,
        notify_on_abuse: data.flag_type_filters.abuse,
        notify_on_bullying: data.flag_type_filters.bullying,
        notify_on_profanity: data.flag_type_filters.profanity,
        notify_on_inappropriate: data.flag_type_filters.inappropriate,
        // Add flattened summary settings
        summary_frequency: data.summary_settings.frequency,
        summary_day_of_week: data.summary_settings.day_of_week,
        summary_hour: data.summary_settings.hour,
        // Add flattened quiet hours
        quiet_hours_enabled: data.quiet_hours.enabled,
        quiet_hours_start: data.quiet_hours.start,
        quiet_hours_end: data.quiet_hours.end,
      };

      setPreferences(flattenedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch preferences');
      console.error('Failed to fetch preferences:', err);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  const updatePreferences = useCallback(async (updates: any) => {
    try {
      setIsSaving(true);

      const response = await fetch(`http://localhost:8000/api/parent/preferences?user_id=${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update preferences');
      }

      const data = await response.json();

      // Flatten nested structure for component compatibility
      const flattenedData: Preferences = {
        ...data,
        // Add flattened severity filters
        notify_on_critical: data.severity_filters.critical,
        notify_on_high: data.severity_filters.high,
        notify_on_medium: data.severity_filters.medium,
        notify_on_low: data.severity_filters.low,
        // Add flattened flag type filters
        notify_on_crisis: data.flag_type_filters.crisis,
        notify_on_abuse: data.flag_type_filters.abuse,
        notify_on_bullying: data.flag_type_filters.bullying,
        notify_on_profanity: data.flag_type_filters.profanity,
        notify_on_inappropriate: data.flag_type_filters.inappropriate,
        // Add flattened summary settings
        summary_frequency: data.summary_settings.frequency,
        summary_day_of_week: data.summary_settings.day_of_week,
        summary_hour: data.summary_settings.hour,
        // Add flattened quiet hours
        quiet_hours_enabled: data.quiet_hours.enabled,
        quiet_hours_start: data.quiet_hours.start,
        quiet_hours_end: data.quiet_hours.end,
      };

      setPreferences(flattenedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      console.error('Failed to update preferences:', err);
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

/**
 * useLanguageModelSetting Hook
 * Whether replies may come from the language model (off by default)
 */

import { useState, useEffect, useCallback } from 'react';
import { parentFetch } from '../services/parentAuth';

export interface LanguageModelStatus {
  enabled: boolean;
  enabled_by_config: boolean;
  warning: string;
  warning_accepted_at: string | null;
  model_available: boolean;
  model_file: string;
  bundled_model: boolean;
}

export const useLanguageModelSetting = () => {
  const [status, setStatus] = useState<LanguageModelStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await parentFetch('/language-model');
      if (!response.ok) {
        throw new Error(`Failed to fetch the language model setting: ${response.statusText}`);
      }
      setStatus(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  }, []);

  /** Turning the model on requires warningAccepted: the parent confirmed they read the warning */
  const setEnabled = useCallback(async (enabled: boolean, warningAccepted = false) => {
    try {
      setIsSaving(true);
      setError(null);
      const response = await parentFetch('/language-model', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled, warning_accepted: warningAccepted }),
      });
      if (!response.ok) {
        throw new Error(`Failed to save the language model setting: ${response.statusText}`);
      }
      setStatus(await response.json());
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return false;
    } finally {
      setIsSaving(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  return { status, isLoading, isSaving, error, setEnabled };
};

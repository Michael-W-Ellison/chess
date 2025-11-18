/**
 * useElectronStore Hook
 * React hook for accessing electron-store from the renderer process
 *
 * This provides a typed, reactive way to interact with persistent electron-store
 * which is stored on the user's filesystem (not browser localStorage).
 *
 * Benefits over localStorage:
 * - Persistent across app reinstalls (stored in OS app data directory)
 * - Type-safe with schema validation
 * - Works in main process and renderer process
 * - Better performance for large data sets
 * - Cross-platform file location handling
 */

import { useState, useEffect, useCallback } from 'react';

/**
 * Hook for reading a single value from electron-store
 * Automatically updates when the value changes
 *
 * @param key - The store key to read
 * @param defaultValue - Default value if key doesn't exist
 * @returns [value, setValue, isLoading, error]
 *
 * @example
 * const [theme, setTheme, isLoading] = useElectronStore('settings.theme', 'light');
 *
 * // Update theme
 * await setTheme('dark');
 */
export function useElectronStore<T = any>(
  key: string,
  defaultValue?: T
): [T | undefined, (value: T) => Promise<void>, boolean, Error | null] {
  const [value, setValue] = useState<T | undefined>(defaultValue);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  /**
   * Load initial value from store
   */
  useEffect(() => {
    const loadValue = async () => {
      try {
        setIsLoading(true);
        const storedValue = await window.electron.store.get(key, defaultValue);
        setValue(storedValue);
        setError(null);
      } catch (err) {
        console.error(`Failed to load store value for key "${key}":`, err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
        setValue(defaultValue);
      } finally {
        setIsLoading(false);
      }
    };

    loadValue();
  }, [key, defaultValue]);

  /**
   * Update value in store
   */
  const updateValue = useCallback(
    async (newValue: T) => {
      try {
        await window.electron.store.set(key, newValue);
        setValue(newValue);
        setError(null);
      } catch (err) {
        console.error(`Failed to update store value for key "${key}":`, err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
        throw err;
      }
    },
    [key]
  );

  return [value, updateValue, isLoading, error];
}

/**
 * Hook for accessing the entire electron-store
 * Provides methods for all store operations
 *
 * @returns Store API methods
 *
 * @example
 * const store = useElectronStoreAPI();
 *
 * // Get value
 * const theme = await store.get('settings.theme', 'light');
 *
 * // Set value
 * await store.set('settings.theme', 'dark');
 *
 * // Check if key exists
 * const exists = await store.has('settings.theme');
 *
 * // Delete key
 * await store.delete('settings.theme');
 *
 * // Get all data
 * const allData = await store.getAll();
 *
 * // Clear all data
 * await store.clear();
 *
 * // Get store file path
 * const path = await store.getPath();
 */
export function useElectronStoreAPI() {
  return {
    /**
     * Get value from store
     */
    get: async (key: string, defaultValue?: any): Promise<any> => {
      try {
        return await window.electron.store.get(key, defaultValue);
      } catch (error) {
        console.error('Store get error:', error);
        throw error;
      }
    },

    /**
     * Set value in store
     */
    set: async (key: string, value: any): Promise<void> => {
      try {
        await window.electron.store.set(key, value);
      } catch (error) {
        console.error('Store set error:', error);
        throw error;
      }
    },

    /**
     * Delete key from store
     */
    delete: async (key: string): Promise<void> => {
      try {
        await window.electron.store.delete(key);
      } catch (error) {
        console.error('Store delete error:', error);
        throw error;
      }
    },

    /**
     * Check if key exists in store
     */
    has: async (key: string): Promise<boolean> => {
      try {
        return await window.electron.store.has(key);
      } catch (error) {
        console.error('Store has error:', error);
        throw error;
      }
    },

    /**
     * Get all store data
     */
    getAll: async (): Promise<any> => {
      try {
        return await window.electron.store.getAll();
      } catch (error) {
        console.error('Store getAll error:', error);
        throw error;
      }
    },

    /**
     * Clear all store data (reset to defaults)
     */
    clear: async (): Promise<void> => {
      try {
        await window.electron.store.clear();
      } catch (error) {
        console.error('Store clear error:', error);
        throw error;
      }
    },

    /**
     * Get store file path
     */
    getPath: async (): Promise<string> => {
      try {
        return await window.electron.store.getPath();
      } catch (error) {
        console.error('Store getPath error:', error);
        throw error;
      }
    },
  };
}

/**
 * Hook for multiple store values
 * Efficiently loads multiple values in parallel
 *
 * @param keys - Array of [key, defaultValue] tuples
 * @returns [values, isLoading, error]
 *
 * @example
 * const [values, isLoading] = useElectronStoreMultiple([
 *   ['settings.theme', 'light'],
 *   ['settings.soundEnabled', true],
 *   ['user.name', 'Guest'],
 * ]);
 *
 * // Access values
 * const theme = values['settings.theme'];
 * const soundEnabled = values['settings.soundEnabled'];
 * const userName = values['user.name'];
 */
export function useElectronStoreMultiple(
  keys: Array<[string, any]>
): [Record<string, any>, boolean, Error | null] {
  const [values, setValues] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const loadValues = async () => {
      try {
        setIsLoading(true);
        const promises = keys.map(([key, defaultValue]) =>
          window.electron.store.get(key, defaultValue).then((value) => ({ key, value }))
        );

        const results = await Promise.all(promises);
        const valuesMap = results.reduce(
          (acc, { key, value }) => {
            acc[key] = value;
            return acc;
          },
          {} as Record<string, any>
        );

        setValues(valuesMap);
        setError(null);
      } catch (err) {
        console.error('Failed to load multiple store values:', err);
        setError(err instanceof Error ? err : new Error('Unknown error'));
      } finally {
        setIsLoading(false);
      }
    };

    loadValues();
  }, [JSON.stringify(keys)]); // eslint-disable-line react-hooks/exhaustive-deps

  return [values, isLoading, error];
}

export default useElectronStore;

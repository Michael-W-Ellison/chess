/**
 * Electron Store Configuration
 * Persistent storage for application settings and user preferences
 *
 * This replaces localStorage for Electron-specific features and provides:
 * - Type-safe storage with schema validation
 * - Automatic file persistence
 * - Default values
 * - Cross-platform storage location
 */

import Store from 'electron-store';

/**
 * Store Schema Definition
 * Defines the structure and types of all stored data
 */
export interface StoreSchema {
  // User Settings
  user: {
    id: number;
    name?: string;
    age?: number;
    grade?: number;
  };

  // Application Settings
  settings: {
    theme: 'light' | 'dark';
    colorTheme: string;
    soundEnabled: boolean;
    notificationsEnabled: boolean;
    autoStartConversation: boolean;
    maxMessageHistory: number;
  };

  // UI State
  ui: {
    windowBounds?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
    sidebarCollapsed: boolean;
    lastOpenedTab: string;
  };

  // Privacy & Safety
  privacy: {
    dataCollectionEnabled: boolean;
    parentPassword?: string;
    safetyLevel: 'low' | 'medium' | 'high';
  };

  // App Metadata
  app: {
    firstLaunchDate?: string;
    lastLaunchDate?: string;
    launchCount: number;
    version: string;
  };
}

/**
 * Default Store Values
 * These values are used when the store is first initialized
 */
const defaults: StoreSchema = {
  user: {
    id: 1,
    name: undefined,
    age: undefined,
    grade: undefined,
  },

  settings: {
    theme: 'light',
    colorTheme: 'purple',
    soundEnabled: true,
    notificationsEnabled: true,
    autoStartConversation: false,
    maxMessageHistory: 100,
  },

  ui: {
    windowBounds: undefined,
    sidebarCollapsed: false,
    lastOpenedTab: 'chat',
  },

  privacy: {
    dataCollectionEnabled: true,
    parentPassword: undefined,
    safetyLevel: 'medium',
  },

  app: {
    firstLaunchDate: undefined,
    lastLaunchDate: undefined,
    launchCount: 0,
    version: '0.1.0',
  },
};

/**
 * Store Instance
 * Singleton instance of the electron-store
 */
export const store = new Store<StoreSchema>({
  name: 'chatbot-friend-config',
  defaults,

  // File location:
  // - Windows: %APPDATA%/chatbot-friend-config/config.json
  // - macOS: ~/Library/Application Support/chatbot-friend-config/config.json
  // - Linux: ~/.config/chatbot-friend-config/config.json

  // Schema validation (optional, for development)
  // schema: { ... } // Can add JSON Schema for validation

  // Migrations for version changes
  migrations: {
    '0.1.0': (store) => {
      // Initial version, no migrations needed
    },
  },

  // Clear invalid data
  clearInvalidConfig: true,
});

/**
 * Store Helper Functions
 * Type-safe wrappers for common operations
 */

/**
 * Get a value from the store
 */
export function getStoreValue<K extends keyof StoreSchema>(key: K): StoreSchema[K] {
  return store.get(key);
}

/**
 * Get a nested value from the store
 */
export function getStoreNestedValue<
  K extends keyof StoreSchema,
  NK extends keyof StoreSchema[K]
>(key: K, nestedKey: NK): StoreSchema[K][NK] {
  return store.get(`${key}.${String(nestedKey)}` as any);
}

/**
 * Set a value in the store
 */
export function setStoreValue<K extends keyof StoreSchema>(
  key: K,
  value: StoreSchema[K]
): void {
  store.set(key, value);
}

/**
 * Set a nested value in the store
 */
export function setStoreNestedValue<
  K extends keyof StoreSchema,
  NK extends keyof StoreSchema[K]
>(key: K, nestedKey: NK, value: StoreSchema[K][NK]): void {
  store.set(`${key}.${String(nestedKey)}` as any, value);
}

/**
 * Delete a value from the store
 */
export function deleteStoreValue<K extends keyof StoreSchema>(key: K): void {
  store.delete(key);
}

/**
 * Reset store to defaults
 */
export function resetStore(): void {
  store.clear();
}

/**
 * Check if a key exists
 */
export function hasStoreKey<K extends keyof StoreSchema>(key: K): boolean {
  return store.has(key);
}

/**
 * Get entire store as object
 */
export function getAllStoreData(): StoreSchema {
  return store.store;
}

/**
 * Track app launch
 * Updates launch metadata
 */
export function trackAppLaunch(): void {
  const now = new Date().toISOString();
  const currentCount = store.get('app.launchCount');
  const firstLaunch = store.get('app.firstLaunchDate');

  if (!firstLaunch) {
    store.set('app.firstLaunchDate', now);
  }

  store.set('app.lastLaunchDate', now);
  store.set('app.launchCount', currentCount + 1);

  console.log(`App launched ${currentCount + 1} times (First: ${firstLaunch || now})`);
}

/**
 * Get store file path
 */
export function getStorePath(): string {
  return store.path;
}

/**
 * Watch for changes to a key
 */
export function watchStoreKey<K extends keyof StoreSchema>(
  key: K,
  callback: (newValue: StoreSchema[K] | undefined, oldValue: StoreSchema[K] | undefined) => void
): () => void {
  return store.onDidChange(key, callback);
}

// Export the store instance as default
export default store;

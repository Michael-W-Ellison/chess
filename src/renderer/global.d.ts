/**
 * Global type definitions for the renderer process
 * Defines the window.electron API exposed via preload script
 */

interface ElectronStoreAPI {
  get: (key: string, defaultValue?: any) => Promise<any>;
  set: (key: string, value: any) => Promise<void>;
  delete: (key: string) => Promise<void>;
  clear: () => Promise<void>;
  has: (key: string) => Promise<boolean>;
  getAll: () => Promise<any>;
  getPath: () => Promise<string>;
}

interface ElectronAPI {
  // Platform information
  platform: string;

  // Send message to main process (one-way)
  send: (channel: string, ...args: any[]) => void;

  // Receive message from main process (one-way)
  on: (channel: string, callback: (...args: any[]) => void) => () => void;

  // Invoke (request-response pattern)
  invoke: (channel: string, ...args: any[]) => Promise<any>;

  // Remove all listeners for a channel
  removeAllListeners: (channel: string) => void;

  // Electron Store API
  store: ElectronStoreAPI;
}

declare global {
  interface Window {
    electron: ElectronAPI;
  }
}

export {};

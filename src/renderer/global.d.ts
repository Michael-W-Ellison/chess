/**
 * Global type definitions for the renderer process
 * Defines the window.electron API exposed via preload script
 */

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
}

declare global {
  interface Window {
    electron: ElectronAPI;
  }
}

export {};

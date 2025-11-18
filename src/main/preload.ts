import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';

/**
 * Preload script - runs in a secure context before the renderer process loads.
 * Exposes a safe, limited API to the renderer process via contextBridge.
 *
 * Security: This prevents the renderer from directly accessing Node.js APIs
 * while still allowing controlled IPC communication.
 */

// Define the API that will be available in the renderer
const electronAPI = {
  // Platform information
  platform: process.platform,

  // Send message to main process (one-way)
  send: (channel: string, ...args: any[]) => {
    // Whitelist of allowed channels
    const validChannels = [
      'start-conversation',
      'send-message',
      'end-conversation',
      'get-personality',
      'get-profile',
      'update-settings',
    ];

    if (validChannels.includes(channel)) {
      ipcRenderer.send(channel, ...args);
    } else {
      console.error(`Invalid IPC channel: ${channel}`);
    }
  },

  // Receive message from main process (one-way)
  on: (channel: string, callback: (...args: any[]) => void) => {
    const validChannels = [
      'conversation-started',
      'message-received',
      'conversation-ended',
      'personality-updated',
      'profile-updated',
      'error',
    ];

    if (validChannels.includes(channel)) {
      const subscription = (_event: IpcRendererEvent, ...args: any[]) => callback(...args);
      ipcRenderer.on(channel, subscription);

      // Return unsubscribe function
      return () => {
        ipcRenderer.removeListener(channel, subscription);
      };
    } else {
      console.error(`Invalid IPC channel: ${channel}`);
      return () => {};
    }
  },

  // Invoke (request-response pattern)
  invoke: async (channel: string, ...args: any[]): Promise<any> => {
    const validChannels = [
      'backend-status',
      'backend-health',
      'start-conversation',
      'send-message',
      'end-conversation',
      'get-personality',
      'get-profile',
      'get-parent-dashboard',
      'update-settings',
      'export-memory-book',
      'store-get',
      'store-set',
      'store-delete',
      'store-clear',
      'store-has',
      'store-get-all',
      'store-get-path',
    ];

    if (validChannels.includes(channel)) {
      return await ipcRenderer.invoke(channel, ...args);
    } else {
      console.error(`Invalid IPC invoke channel: ${channel}`);
      throw new Error(`Invalid channel: ${channel}`);
    }
  },

  // Electron Store API
  store: {
    get: async (key: string, defaultValue?: any): Promise<any> => {
      const result = await ipcRenderer.invoke('store-get', key, defaultValue);
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.error);
      }
    },

    set: async (key: string, value: any): Promise<void> => {
      const result = await ipcRenderer.invoke('store-set', key, value);
      if (!result.success) {
        throw new Error(result.error);
      }
    },

    delete: async (key: string): Promise<void> => {
      const result = await ipcRenderer.invoke('store-delete', key);
      if (!result.success) {
        throw new Error(result.error);
      }
    },

    clear: async (): Promise<void> => {
      const result = await ipcRenderer.invoke('store-clear');
      if (!result.success) {
        throw new Error(result.error);
      }
    },

    has: async (key: string): Promise<boolean> => {
      const result = await ipcRenderer.invoke('store-has', key);
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.error);
      }
    },

    getAll: async (): Promise<any> => {
      const result = await ipcRenderer.invoke('store-get-all');
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.error);
      }
    },

    getPath: async (): Promise<string> => {
      const result = await ipcRenderer.invoke('store-get-path');
      if (result.success) {
        return result.data;
      } else {
        throw new Error(result.error);
      }
    },
  },

  // Remove all listeners for a channel
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  },
};

// Expose the API to the renderer process
contextBridge.exposeInMainWorld('electron', electronAPI);

// Type definition for TypeScript (to be added to shared types)
export type ElectronAPI = typeof electronAPI;

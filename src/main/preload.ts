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
      'start-conversation',
      'send-message',
      'end-conversation',
      'get-personality',
      'get-profile',
      'get-parent-dashboard',
      'update-settings',
      'export-memory-book',
    ];

    if (validChannels.includes(channel)) {
      return await ipcRenderer.invoke(channel, ...args);
    } else {
      console.error(`Invalid IPC invoke channel: ${channel}`);
      throw new Error(`Invalid channel: ${channel}`);
    }
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

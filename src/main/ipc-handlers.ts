import { app, BrowserWindow, dialog, ipcMain, IpcMainInvokeEvent } from 'electron';
import { promises as fs } from 'fs';
import * as path from 'path';
import { backendManager } from './backend-manager';
import { store, defaults as storeDefaults, getAllStoreData, getStorePath, StoreSchema } from './store';

const IPC_CHANNELS = [
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

/**
 * The message from a failed backendManager.request(), whose error reads
 * "Backend request failed: <status> <body>"; FastAPI bodies are {"detail": ...}
 */
function backendErrorMessage(error: unknown): string {
  const message = error instanceof Error ? error.message : 'Unknown error';
  const match = message.match(/^Backend request failed: \d+ (.*)$/s);
  if (match) {
    try {
      const detail = JSON.parse(match[1]).detail;
      if (typeof detail === 'string') return detail;
      if (detail?.message) return detail.message;
    } catch {
      // Not JSON: use the whole message
    }
  }
  return message;
}

/**
 * IPC Handlers - Handle all communication from renderer to main process
 * These handlers communicate with the Python backend via HTTP requests
 */

/**
 * Initialize all IPC handlers
 */
export function setupIpcHandlers(): void {
  console.log('Setting up IPC handlers...');

  // Backend Status
  ipcMain.handle('backend-status', handleBackendStatus);
  ipcMain.handle('backend-health', handleBackendHealth);

  // Conversation Management
  ipcMain.handle('start-conversation', handleStartConversation);
  ipcMain.handle('send-message', handleSendMessage);
  ipcMain.handle('end-conversation', handleEndConversation);

  // Data Retrieval
  ipcMain.handle('get-personality', handleGetPersonality);
  ipcMain.handle('get-profile', handleGetProfile);
  ipcMain.handle('get-parent-dashboard', handleGetParentDashboard);

  // Settings
  ipcMain.handle('update-settings', handleUpdateSettings);

  // Export
  ipcMain.handle('export-memory-book', handleExportMemoryBook);

  // Electron Store
  ipcMain.handle('store-get', handleStoreGet);
  ipcMain.handle('store-set', handleStoreSet);
  ipcMain.handle('store-delete', handleStoreDelete);
  ipcMain.handle('store-clear', handleStoreClear);
  ipcMain.handle('store-has', handleStoreHas);
  ipcMain.handle('store-get-all', handleStoreGetAll);
  ipcMain.handle('store-get-path', handleStoreGetPath);

  console.log('IPC handlers ready');
}

/**
 * Get backend status
 */
async function handleBackendStatus(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    const status = backendManager.getStatus();
    return {
      success: true,
      data: status,
    };
  } catch (error) {
    console.error('Error getting backend status:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Check backend health
 */
async function handleBackendHealth(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    if (!backendManager.isBackendRunning()) {
      return {
        success: true,
        data: { healthy: false, message: 'Backend is not running' },
      };
    }

    const healthy = await backendManager.checkHealth();

    return {
      success: true,
      data: {
        healthy,
        message: healthy ? 'Backend is healthy' : 'Backend health check failed'
      },
    };
  } catch (error) {
    console.error('Error checking backend health:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Start a new conversation session
 */
async function handleStartConversation(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    console.log('IPC: Starting conversation...');

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }

    const response = await backendManager.request('POST', '/api/conversation/start?user_id=1');

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Error starting conversation:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Send a message and get bot response
 */
async function handleSendMessage(
  _event: IpcMainInvokeEvent,
  conversationId: number,
  message: string
): Promise<any> {
  try {
    console.log('IPC: Sending message:', message.substring(0, 50) + '...');

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }

    const response = await backendManager.request('POST', '/api/message', {
      content: message,
      conversation_id: conversationId,
      user_id: 1,
    });

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Error sending message:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * End current conversation
 */
async function handleEndConversation(
  _event: IpcMainInvokeEvent,
  conversationId: number
): Promise<any> {
  try {
    console.log('IPC: Ending conversation:', conversationId);

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }

    await backendManager.request('POST', `/api/conversation/end/${conversationId}`);

    return {
      success: true,
    };
  } catch (error) {
    console.error('Error ending conversation:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Get current personality state
 */
async function handleGetPersonality(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    console.log('IPC: Getting personality...');

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }

    const response = await backendManager.request('GET', '/api/personality?user_id=1');

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Error getting personality:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Get user profile data
 */
async function handleGetProfile(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    console.log('IPC: Getting profile...');

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }

    const response = await backendManager.request('GET', '/api/profile?user_id=1');

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Error getting profile:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Get parent dashboard data (password protected)
 *
 * Logs in to the backend with the parent password (POST /api/parent/auth/login) and
 * returns GET /api/parent/dashboard for the child. When password protection is off,
 * the backend accepts any password.
 */
async function handleGetParentDashboard(
  _event: IpcMainInvokeEvent,
  password: string,
  userId: number = 1
): Promise<any> {
  try {
    console.log('IPC: Getting parent dashboard...');

    if (!backendManager.isBackendRunning()) {
      throw new Error('Backend is not running');
    }
    if (typeof password !== 'string') {
      throw new Error('Password is required');
    }

    const login = await backendManager.request<{ access_token: string }>(
      'POST',
      '/api/parent/auth/login',
      { password }
    );
    const response = await backendManager.request(
      'GET',
      `/api/parent/dashboard?user_id=${encodeURIComponent(String(userId))}`,
      undefined,
      { Authorization: `Bearer ${login.access_token}` }
    );

    return {
      success: true,
      data: response,
    };
  } catch (error) {
    console.error('Error getting parent dashboard:', error);
    return {
      success: false,
      error: backendErrorMessage(error),
    };
  }
}

/**
 * Check settings updates against the stored settings' types; returns the problems found
 */
function validateSettingsUpdate(updates: Record<string, unknown>): string[] {
  const errors: string[] = [];
  const known = storeDefaults.settings as Record<string, unknown>;
  for (const [key, value] of Object.entries(updates)) {
    if (!(key in known)) {
      errors.push(`Unknown setting: ${key}`);
    } else if (typeof value !== typeof known[key]) {
      errors.push(`${key} must be a ${typeof known[key]}`);
    } else if (key === 'theme' && value !== 'light' && value !== 'dark') {
      errors.push('theme must be "light" or "dark"');
    } else if (key === 'maxMessageHistory' && !(Number.isInteger(value) && (value as number) > 0)) {
      errors.push('maxMessageHistory must be a positive integer');
    }
  }
  return errors;
}

/**
 * Update application settings
 *
 * Merges the given settings into the stored settings (electron-store key "settings")
 * and returns the saved settings. Nothing is saved if any value is invalid.
 */
async function handleUpdateSettings(
  _event: IpcMainInvokeEvent,
  updates: Partial<StoreSchema['settings']>
): Promise<any> {
  try {
    console.log('IPC: Updating settings...');

    if (!updates || typeof updates !== 'object' || Array.isArray(updates)) {
      throw new Error('Settings must be an object');
    }
    const errors = validateSettingsUpdate(updates as Record<string, unknown>);
    if (errors.length > 0) {
      throw new Error(errors.join('; '));
    }

    const settings = { ...store.get('settings'), ...updates };
    store.set('settings', settings);

    return {
      success: true,
      data: settings,
    };
  } catch (error) {
    console.error('Error updating settings:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Save an exported memory book to a file the user chooses
 *
 * The renderer generates the content (see src/shared/exportUtils.ts); this shows a save
 * dialog and writes it. Returns { canceled: true } if the dialog was closed.
 */
async function handleExportMemoryBook(
  event: IpcMainInvokeEvent,
  content: string,
  defaultFileName: string = 'memory-book.txt'
): Promise<any> {
  try {
    console.log('IPC: Exporting memory book...');

    if (typeof content !== 'string') {
      throw new Error('Export content must be text');
    }

    const extension = path.extname(defaultFileName).slice(1).toLowerCase();
    const filters = extension
      ? [{ name: `${extension.toUpperCase()} files`, extensions: [extension] }, { name: 'All files', extensions: ['*'] }]
      : [{ name: 'All files', extensions: ['*'] }];
    const options = {
      title: 'Save Memory Book',
      defaultPath: path.join(app.getPath('documents'), path.basename(defaultFileName)),
      filters,
    };
    const window = BrowserWindow.fromWebContents(event.sender);
    const result = window
      ? await dialog.showSaveDialog(window, options)
      : await dialog.showSaveDialog(options);

    if (result.canceled || !result.filePath) {
      return {
        success: true,
        canceled: true,
      };
    }

    await fs.writeFile(result.filePath, content, 'utf-8');

    return {
      success: true,
      filePath: result.filePath,
    };
  } catch (error) {
    console.error('Error exporting memory book:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Get value
 */
async function handleStoreGet(
  _event: IpcMainInvokeEvent,
  key: string,
  defaultValue?: any
): Promise<any> {
  try {
    const value = store.get(key, defaultValue);
    return {
      success: true,
      data: value,
    };
  } catch (error) {
    console.error('Error getting store value:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Set value
 */
async function handleStoreSet(
  _event: IpcMainInvokeEvent,
  key: string,
  value: any
): Promise<any> {
  try {
    store.set(key, value);
    return {
      success: true,
    };
  } catch (error) {
    console.error('Error setting store value:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Delete value
 */
async function handleStoreDelete(
  _event: IpcMainInvokeEvent,
  key: string
): Promise<any> {
  try {
    // electron-store also accepts dot-notation paths at runtime
    store.delete(key as keyof StoreSchema);
    return {
      success: true,
    };
  } catch (error) {
    console.error('Error deleting store value:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Clear all data
 */
async function handleStoreClear(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    store.clear();
    return {
      success: true,
    };
  } catch (error) {
    console.error('Error clearing store:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Check if key exists
 */
async function handleStoreHas(
  _event: IpcMainInvokeEvent,
  key: string
): Promise<any> {
  try {
    const exists = store.has(key);
    return {
      success: true,
      data: exists,
    };
  } catch (error) {
    console.error('Error checking store key:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Get all data
 */
async function handleStoreGetAll(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    const allData = getAllStoreData();
    return {
      success: true,
      data: allData,
    };
  } catch (error) {
    console.error('Error getting all store data:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Electron Store: Get store file path
 */
async function handleStoreGetPath(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    const path = getStorePath();
    return {
      success: true,
      data: path,
    };
  } catch (error) {
    console.error('Error getting store path:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Clean up IPC handlers
 */
export function cleanupIpcHandlers(): void {
  console.log('Cleaning up IPC handlers...');
  // Handlers registered with ipcMain.handle() are removed with removeHandler()
  for (const channel of IPC_CHANNELS) {
    ipcMain.removeHandler(channel);
  }
}

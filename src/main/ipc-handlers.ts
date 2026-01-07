import { ipcMain, IpcMainInvokeEvent } from 'electron';
import { backendManager } from './backend-manager';

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
      user_message: message,
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
 */
async function handleGetParentDashboard(
  _event: IpcMainInvokeEvent,
  _password: string
): Promise<any> {
  try {
    console.log('IPC: Getting parent dashboard...');

    // TODO: Call Python backend API with authentication
    // const response = await backendManager.request('GET', '/api/parent/dashboard', {
    //   headers: { 'X-Parent-Password': password }
    // });

    // Mock response for now
    const mockResponse = {
      conversationSummaries: [],
      safetyFlags: [],
      stats: {
        totalConversations: 0,
        currentStreak: 0,
        averageSessionLength: '0 minutes',
      },
    };

    return {
      success: true,
      data: mockResponse,
    };
  } catch (error) {
    console.error('Error getting parent dashboard:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unauthorized',
    };
  }
}

/**
 * Update application settings
 */
async function handleUpdateSettings(
  _event: IpcMainInvokeEvent,
  _settings: any
): Promise<any> {
  try {
    console.log('IPC: Updating settings...');

    // TODO: Save to electron-store
    // Store.set('settings', settings);

    return {
      success: true,
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
 * Export memory book as PDF/text
 */
async function handleExportMemoryBook(
  _event: IpcMainInvokeEvent
): Promise<any> {
  try {
    console.log('IPC: Exporting memory book...');

    // TODO: Generate memory book and show save dialog
    // const { dialog } = require('electron');
    // const result = await dialog.showSaveDialog({...});

    return {
      success: true,
      filePath: '/path/to/memory-book.pdf',
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
 * Clean up IPC handlers
 */
export function cleanupIpcHandlers(): void {
  console.log('Cleaning up IPC handlers...');
  ipcMain.removeAllListeners('backend-status');
  ipcMain.removeAllListeners('backend-health');
  ipcMain.removeAllListeners('start-conversation');
  ipcMain.removeAllListeners('send-message');
  ipcMain.removeAllListeners('end-conversation');
  ipcMain.removeAllListeners('get-personality');
  ipcMain.removeAllListeners('get-profile');
  ipcMain.removeAllListeners('get-parent-dashboard');
  ipcMain.removeAllListeners('update-settings');
  ipcMain.removeAllListeners('export-memory-book');
}

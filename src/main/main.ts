import { app, BrowserWindow, Menu } from 'electron';
import * as path from 'path';
import { setupIpcHandlers, cleanupIpcHandlers } from './ipc-handlers';
import { backendManager } from './backend-manager';
import { trackAppLaunch, getStorePath } from './store';
import { DEV_SERVER_URL, isAppUrl, isDev } from './security';

// Global reference to the main window
let mainWindow: BrowserWindow | null = null;

/**
 * Create the main application window
 */
function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    title: 'Chatbot Friend',
    backgroundColor: '#ffffff',
    show: false, // Don't show until ready-to-show
    webPreferences: {
      nodeIntegration: false, // Security: disable node integration in renderer
      contextIsolation: true,  // Security: enable context isolation
      sandbox: true,           // Security: enable sandbox
      preload: path.join(__dirname, 'preload.js'),
      devTools: isDev,         // Security: no DevTools for the child outside development
    },
  });

  // Load the app
  if (isDev) {
    // Development: load from Vite dev server
    mainWindow.loadURL(DEV_SERVER_URL);
    // Open DevTools in development
    mainWindow.webContents.openDevTools();
  } else {
    // Production: load from built files
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  // Show window when ready
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    mainWindow?.focus();
  });

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Prevent navigation away from the app, by a link or a redirect
  const keepInApp = (event: Electron.Event, url: string) => {
    if (!isAppUrl(url)) {
      event.preventDefault();
    }
  };
  mainWindow.webContents.on('will-navigate', keepInApp);
  mainWindow.webContents.on('will-redirect', keepInApp);

  // Prevent new window creation (security)
  mainWindow.webContents.setWindowOpenHandler(() => {
    return { action: 'deny' };
  });
}

/**
 * App lifecycle: Ready
 */
app.whenReady().then(async () => {
  // Outside development, a menu without View > Toggle Developer Tools (and its shortcut)
  if (!isDev) {
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      ...(process.platform === 'darwin' ? [{ role: 'appMenu' as const }] : []),
      { role: 'editMenu' },
      { role: 'windowMenu' },
    ]));
  }

  // Initialize electron-store and track app launch
  console.log('Initializing electron-store...');
  trackAppLaunch();
  console.log(`Store location: ${getStorePath()}`);

  // Set up IPC communication handlers
  setupIpcHandlers();

  // Start Python backend
  console.log('Starting Python backend...');
  try {
    await backendManager.start();
    console.log('✓ Backend started successfully');
  } catch (error) {
    console.error('Failed to start backend:', error);
    console.error('The application will run with limited functionality');
    // Continue anyway - app can still show UI, just without backend functionality
  }

  createMainWindow();

  // macOS: Re-create window when dock icon is clicked and no windows are open
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

/**
 * App lifecycle: All windows closed
 */
app.on('window-all-closed', () => {
  // On macOS, keep app active until user explicitly quits (Cmd+Q)
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * App lifecycle: Before quit
 * Clean up resources here
 */
app.on('before-quit', async (event) => {
  console.log('Application shutting down...');

  // Prevent default to allow async cleanup
  event.preventDefault();

  try {
    // Cleanup IPC handlers
    cleanupIpcHandlers();

    // Shutdown Python backend gracefully
    console.log('Stopping Python backend...');
    await backendManager.stop();
    console.log('✓ Backend stopped');
  } catch (error) {
    console.error('Error during cleanup:', error);
  } finally {
    // Now actually quit
    app.exit(0);
  }
});

/**
 * Security: the remote module and its 'remote-*' app events were removed in Electron 14,
 * so there is nothing to disable here on Electron 28.
 */

// Export for testing
export { mainWindow };

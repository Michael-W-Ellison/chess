import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider } from './contexts/ThemeContext';
import { ColorProvider } from './contexts/ColorContext';
import { AchievementProvider } from './contexts/AchievementContext';
import { LoginProvider } from './contexts/LoginContext';
import { StreakProvider } from './contexts/StreakContext';
import { MemoryProvider } from './contexts/MemoryContext';
import { ChatProvider } from './contexts/ChatContext';
import { loadApiToken } from './services/apiToken';
import './styles/index.css';

// Ask the main process for the backend's API token now, so even a request sent while the
// window closes has it
loadApiToken();

// Load IPC integration tests in development mode
if (import.meta.env.DEV) {
  import('./test-ipc-integration').then(() => {
    console.log('💡 IPC integration tests loaded! Run testIPC() in console.');
  });
}

// Mount the React application
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <ColorProvider>
        <MemoryProvider>
          <StreakProvider>
            <LoginProvider>
              <AchievementProvider>
                <ChatProvider>
                  <App />
                </ChatProvider>
              </AchievementProvider>
            </LoginProvider>
          </StreakProvider>
        </MemoryProvider>
      </ColorProvider>
    </ThemeProvider>
  </React.StrictMode>
);

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider } from './contexts/ThemeContext';
import { ColorProvider } from './contexts/ColorContext';
import { AchievementProvider } from './contexts/AchievementContext';
import { LoginProvider } from './contexts/LoginContext';
import { StreakProvider } from './contexts/StreakContext';
import { MemoryProvider } from './contexts/MemoryContext';
import './styles/index.css';

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
                <App />
              </AchievementProvider>
            </LoginProvider>
          </StreakProvider>
        </MemoryProvider>
      </ColorProvider>
    </ThemeProvider>
  </React.StrictMode>
);

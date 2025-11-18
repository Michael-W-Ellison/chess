import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { ThemeProvider } from './contexts/ThemeContext';
import { ColorProvider } from './contexts/ColorContext';
import { AchievementProvider } from './contexts/AchievementContext';
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
        <AchievementProvider>
          <App />
        </AchievementProvider>
      </ColorProvider>
    </ThemeProvider>
  </React.StrictMode>
);

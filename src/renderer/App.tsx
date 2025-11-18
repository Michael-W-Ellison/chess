import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import ProfilePanel from './components/ProfilePanel';
import SettingsPanel from './components/SettingsPanel';
import ParentDashboard from './components/ParentDashboard';
import AchievementsPanel from './components/AchievementsPanel';

/**
 * Main application component
 * This is the root component that manages the overall app state and layout
 */
function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'profile' | 'achievements' | 'settings' | 'parent'>('chat');

  return (
    <div className="app h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Render appropriate view */}
      {currentView === 'chat' && <ChatWindow />}
      {currentView === 'profile' && <ProfilePanel />}
      {currentView === 'achievements' && <AchievementsPanel />}
      {currentView === 'settings' && <SettingsPanel />}
      {currentView === 'parent' && <ParentDashboard />}

      {/* Global navigation overlay (bottom) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg transition-colors">
        <nav className="flex items-center justify-around max-w-2xl mx-auto px-4 py-3">
          <button
            onClick={() => setCurrentView('chat')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'chat'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'chat' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">💬</span>
            <span className="text-xs font-medium">Chat</span>
          </button>
          <button
            onClick={() => setCurrentView('profile')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'profile'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'profile' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">🤖</span>
            <span className="text-xs font-medium">Profile</span>
          </button>
          <button
            onClick={() => setCurrentView('achievements')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'achievements'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'achievements' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">🏆</span>
            <span className="text-xs font-medium">Achieve</span>
          </button>
          <button
            onClick={() => setCurrentView('settings')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'settings'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'settings' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">⚙️</span>
            <span className="text-xs font-medium">Settings</span>
          </button>
          <button
            onClick={() => setCurrentView('parent')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'parent'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'parent' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">👨‍👩‍👧</span>
            <span className="text-xs font-medium">Parent</span>
          </button>
        </nav>
      </div>
    </div>
  );
}

export default App;

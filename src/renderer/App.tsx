import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import ProfilePanel from './components/ProfilePanel';
import SettingsPanel from './components/SettingsPanel';
import ParentDashboard from './components/ParentDashboard';

/**
 * Main application component
 * This is the root component that manages the overall app state and layout
 */
function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'profile' | 'settings' | 'parent'>('chat');

  return (
    <div className="app h-screen flex flex-col bg-gray-50">
      {/* Render appropriate view */}
      {currentView === 'chat' && <ChatWindow />}
      {currentView === 'profile' && <ProfilePanel />}
      {currentView === 'settings' && <SettingsPanel />}
      {currentView === 'parent' && <ParentDashboard />}

      {/* Global navigation overlay (bottom) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
        <nav className="flex items-center justify-around max-w-2xl mx-auto px-4 py-3">
          <button
            onClick={() => setCurrentView('chat')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'chat'
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <span className="text-2xl">💬</span>
            <span className="text-xs font-medium">Chat</span>
          </button>
          <button
            onClick={() => setCurrentView('profile')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'profile'
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <span className="text-2xl">🤖</span>
            <span className="text-xs font-medium">Profile</span>
          </button>
          <button
            onClick={() => setCurrentView('settings')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'settings'
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <span className="text-2xl">⚙️</span>
            <span className="text-xs font-medium">Settings</span>
          </button>
          <button
            onClick={() => setCurrentView('parent')}
            className={`flex flex-col items-center gap-1 px-4 py-2 rounded-lg transition-colors ${
              currentView === 'parent'
                ? 'text-blue-600 bg-blue-50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
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

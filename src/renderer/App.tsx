import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import ProfilePanel from './components/ProfilePanel';
import SettingsPanel from './components/SettingsPanel';

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
      {currentView === 'parent' && (
        <div className="h-full flex flex-col">
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <h2 className="text-2xl font-bold text-gray-800">Parent Dashboard</h2>
            <p className="text-sm text-gray-600 mt-1">
              Monitor your child's chatbot interactions
            </p>
          </div>
          <div className="flex-1 flex items-center justify-center p-6">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">👨‍👩‍👧‍👦</div>
              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                Parent Dashboard Coming Soon
              </h3>
              <p className="text-gray-600 mb-4">
                The parent dashboard will provide insights into your child's conversations,
                safety alerts, and activity monitoring.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                <h4 className="font-medium text-blue-800 mb-2">Planned Features:</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Conversation summaries</li>
                  <li>• Safety event notifications</li>
                  <li>• Activity trends and analytics</li>
                  <li>• Time usage reports</li>
                  <li>• Password-protected access</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

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

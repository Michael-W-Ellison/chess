import React, { useState } from 'react';

/**
 * Main application component
 * This is the root component that manages the overall app state and layout
 */
function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'profile' | 'settings' | 'parent'>('chat');

  return (
    <div className="app min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Chatbot Friend</h1>

            {/* Navigation */}
            <nav className="flex space-x-4">
              <button
                onClick={() => setCurrentView('chat')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  currentView === 'chat'
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setCurrentView('profile')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  currentView === 'profile'
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Profile
              </button>
              <button
                onClick={() => setCurrentView('settings')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  currentView === 'settings'
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Settings
              </button>
              <button
                onClick={() => setCurrentView('parent')}
                className={`px-4 py-2 rounded-md font-medium transition-colors ${
                  currentView === 'parent'
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-700 hover:bg-gray-100'
                }`}
              >
                Parent
              </button>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {currentView === 'chat' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Chat View</h2>
            <p className="text-gray-600">Chat component will be added here</p>
          </div>
        )}

        {currentView === 'profile' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Profile View</h2>
            <p className="text-gray-600">Profile component will be added here</p>
          </div>
        )}

        {currentView === 'settings' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Settings View</h2>
            <p className="text-gray-600">Settings component will be added here</p>
          </div>
        )}

        {currentView === 'parent' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Parent Dashboard</h2>
            <p className="text-gray-600">Parent dashboard will be added here</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2">
        <div className="max-w-7xl mx-auto px-4">
          <p className="text-sm text-gray-500 text-center">
            Chatbot Friend v0.1.0 - All data stored locally
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;

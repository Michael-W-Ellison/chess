import React, { useState, useEffect, useRef } from 'react';
import ChatWindow from './components/ChatWindow';
import ProfilePanel from './components/ProfilePanel';
import SettingsPanel from './components/SettingsPanel';
import ParentDashboard from './components/ParentDashboard';
import AchievementsPanel from './components/AchievementsPanel';
import StreakPanel from './components/StreakPanel';
import { useAchievements } from './hooks/useAchievements';
import { useLogin } from './hooks/useLogin';
import { useStreak } from './hooks/useStreak';

/**
 * Main application component
 * This is the root component that manages the overall app state and layout
 */
function App() {
  const [currentView, setCurrentView] = useState<'chat' | 'profile' | 'achievements' | 'streaks' | 'settings' | 'parent'>('chat');
  const { trackSessionStart, trackSessionEnd, recentAchievements } = useAchievements();
  const { recordLogin } = useLogin();
  const { recordActivity, getStats } = useStreak();

  // Count unseen achievements (within last hour)
  const unseenCount = recentAchievements.filter((recent) => {
    const unlockTime = new Date(recent.unlockedAt).getTime();
    const now = Date.now();
    return now - unlockTime < 3600000; // 1 hour
  }).length;

  // Track if we've done initial login recording
  const hasRecordedLogin = useRef(false);

  // Track session and login on mount only (empty deps to run once)
  useEffect(() => {
    if (!hasRecordedLogin.current) {
      hasRecordedLogin.current = true;
      recordLogin();
      recordActivity('login'); // Also record in StreakContext
      trackSessionStart();
    }

    return () => {
      trackSessionEnd();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps - only run once on mount

  // Get current login streak for display
  const loginStreakStats = getStats('login');

  return (
    <div className="app h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Render appropriate view */}
      {currentView === 'chat' && (
        <div className="view-enter h-full">
          <ChatWindow />
        </div>
      )}
      {currentView === 'profile' && (
        <div className="view-enter h-full">
          <ProfilePanel />
        </div>
      )}
      {currentView === 'achievements' && (
        <div className="view-enter h-full">
          <AchievementsPanel />
        </div>
      )}
      {currentView === 'streaks' && (
        <div className="view-enter h-full">
          <StreakPanel />
        </div>
      )}
      {currentView === 'settings' && (
        <div className="view-enter h-full">
          <SettingsPanel />
        </div>
      )}
      {currentView === 'parent' && (
        <div className="view-enter h-full">
          <ParentDashboard />
        </div>
      )}

      {/* Global navigation overlay (bottom) */}
      <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg transition-colors">
        <nav className="flex items-center justify-around max-w-3xl mx-auto px-2 py-3">
          <button
            onClick={() => setCurrentView('chat')}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
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
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
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
            className={`relative flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
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
            {unseenCount > 0 && (
              <span
                className="absolute top-1 right-1 min-w-[18px] h-[18px] flex items-center justify-center text-white text-xs font-bold rounded-full animate-pulse"
                style={{ backgroundColor: 'var(--color-primary)' }}
              >
                {unseenCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setCurrentView('streaks')}
            className={`relative flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
              currentView === 'streaks'
                ? ''
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
            style={currentView === 'streaks' ? {
              color: 'var(--color-text)',
              backgroundColor: 'var(--color-primary-lighter)',
            } : {}}
          >
            <span className="text-2xl">🔥</span>
            <span className="text-xs font-medium">Streaks</span>
            {loginStreakStats.currentStreak > 0 && (
              <span className="absolute -top-1 -right-1 text-xs font-bold text-orange-600 dark:text-orange-400">
                {loginStreakStats.currentStreak}
              </span>
            )}
          </button>
          <button
            onClick={() => setCurrentView('settings')}
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
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
            className={`flex flex-col items-center gap-1 px-2 py-2 rounded-lg transition-colors ${
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

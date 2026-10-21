/**
 * ParentDashboard Component
 * Main parent dashboard for monitoring child's safety and activity
 *
 * When the backend requires a parent password, the dashboard is shown only after
 * logging in (see services/parentAuth.ts); a rejected token returns to the login form.
 */

import React, { useCallback, useEffect, useState } from 'react';
import { SafetyOverview } from './parent/SafetyOverview';
import { SafetyFlagsList } from './parent/SafetyFlagsList';
import { SafetyStatistics } from './parent/SafetyStatistics';
import { NotificationPreferences } from './parent/NotificationPreferences';
import { ConversationStatistics } from './parent/ConversationStatistics';
import { ParentLogin } from './parent/ParentLogin';
import {
  getParentAuthStatus,
  logoutParent,
  PARENT_AUTH_EXPIRED_EVENT,
  verifyParentToken,
} from '../services/parentAuth';

type DashboardTab = 'overview' | 'flags' | 'statistics' | 'conversations' | 'preferences';

// checking: asking the backend; login: password needed; ready: dashboard shown;
// unconfigured: password required but none set up; unreachable: backend not responding
type AuthState = 'checking' | 'login' | 'ready' | 'unconfigured' | 'unreachable';

export const ParentDashboard: React.FC = () => {
  const [authState, setAuthState] = useState<AuthState>('checking');
  const [passwordRequired, setPasswordRequired] = useState(false);
  const [loginNotice, setLoginNotice] = useState<string | null>(null);

  const checkAuth = useCallback(async () => {
    setAuthState('checking');
    try {
      const status = await getParentAuthStatus();
      setPasswordRequired(status.required);
      if (!status.required) {
        setAuthState('ready');
      } else if (!status.configured) {
        setAuthState('unconfigured');
      } else {
        setAuthState((await verifyParentToken()) ? 'ready' : 'login');
      }
    } catch {
      setAuthState('unreachable');
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // A request rejected with 401 (e.g. the token expired) returns to the login form
  useEffect(() => {
    const handleExpired = () => {
      setLoginNotice('Your session has expired. Please log in again.');
      setAuthState('login');
    };
    window.addEventListener(PARENT_AUTH_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(PARENT_AUTH_EXPIRED_EVENT, handleExpired);
  }, []);

  const handleLogout = () => {
    logoutParent();
    setLoginNotice(null);
    setAuthState('login');
  };

  if (authState === 'checking') {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <p className="text-gray-600">Checking access...</p>
      </div>
    );
  }

  if (authState === 'login') {
    return (
      <ParentLogin
        notice={loginNotice}
        onLogin={() => {
          setLoginNotice(null);
          setAuthState('ready');
        }}
        onNotConfigured={() => setAuthState('unconfigured')}
      />
    );
  }

  if (authState === 'unconfigured' || authState === 'unreachable') {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 p-6">
        <div className="w-full max-w-md bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-800">Parent Dashboard</h1>
          {authState === 'unconfigured' ? (
            <p className="text-sm text-gray-700 mt-3">
              The parent dashboard requires a password, but none has been set up. Set
              PARENT_DASHBOARD_PASSWORD and JWT_SECRET_KEY in the backend's .env file
              (POST /api/parent/auth/setup-password generates both values), then restart
              the app.
            </p>
          ) : (
            <p className="text-sm text-gray-700 mt-3">
              The backend is not responding, so the dashboard cannot be loaded.
            </p>
          )}
          <button
            onClick={checkAuth}
            className="mt-4 bg-blue-500 text-white font-medium rounded-lg px-4 py-2 hover:bg-blue-600"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return <DashboardContent onLogout={passwordRequired ? handleLogout : undefined} />;
};

const DashboardContent: React.FC<{ onLogout?: () => void }> = ({ onLogout }) => {
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');
  const [userId] = useState<number>(1); // TODO: Get from context/props

  const tabs = [
    { id: 'overview' as DashboardTab, label: 'Overview', icon: '📊' },
    { id: 'flags' as DashboardTab, label: 'Safety Flags', icon: '🚩' },
    { id: 'statistics' as DashboardTab, label: 'Statistics', icon: '📈' },
    { id: 'conversations' as DashboardTab, label: 'Conversations', icon: '💬' },
    { id: 'preferences' as DashboardTab, label: 'Preferences', icon: '⚙️' },
  ];

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Parent Dashboard</h1>
            <p className="text-sm text-gray-600 mt-1">
              Monitor your child's safety and chatbot interactions
            </p>
          </div>
          <div className="flex items-center gap-2">
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-sm font-medium text-green-700">Monitoring Active</span>
              </div>
            </div>
            {onLogout && (
              <button
                onClick={onLogout}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Log out
              </button>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mt-4 border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <span className="text-lg">{tab.icon}</span>
              <span className="font-medium">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto pb-20">
        {activeTab === 'overview' && <SafetyOverview userId={userId} />}
        {activeTab === 'flags' && <SafetyFlagsList userId={userId} />}
        {activeTab === 'statistics' && <SafetyStatistics userId={userId} />}
        {activeTab === 'conversations' && <ConversationStatistics userId={userId} />}
        {activeTab === 'preferences' && <NotificationPreferences userId={userId} />}
      </div>
    </div>
  );
};

export default ParentDashboard;

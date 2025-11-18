/**
 * ThemeToggle Component
 * Interactive toggle switch for light/dark theme
 */

import React from 'react';
import { useTheme } from '../hooks/useTheme';

interface ThemeToggleProps {
  showLabels?: boolean;
  className?: string;
}

export const ThemeToggle: React.FC<ThemeToggleProps> = ({
  showLabels = true,
  className = '',
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {showLabels && (
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {isDark ? '🌙 Dark' : '☀️ Light'}
        </span>
      )}

      <button
        onClick={toggleTheme}
        className={`
          relative inline-flex items-center h-8 w-16 rounded-full
          transition-colors duration-300 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
          dark:focus:ring-offset-gray-800
          ${isDark ? 'bg-blue-600' : 'bg-gray-300'}
        `}
        aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        role="switch"
        aria-checked={isDark}
      >
        {/* Toggle circle */}
        <span
          className={`
            inline-block w-6 h-6 rounded-full bg-white
            transform transition-transform duration-300 ease-in-out
            shadow-lg flex items-center justify-center text-xs
            ${isDark ? 'translate-x-9' : 'translate-x-1'}
          `}
        >
          {isDark ? '🌙' : '☀️'}
        </span>
      </button>
    </div>
  );
};

/**
 * ThemeToggleButton Component
 * Simple icon button for theme toggle (for compact spaces)
 */
export const ThemeToggleButton: React.FC<{ className?: string }> = ({
  className = '',
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className={`
        p-2 rounded-lg
        bg-gray-100 hover:bg-gray-200
        dark:bg-gray-700 dark:hover:bg-gray-600
        transition-colors
        ${className}
      `}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
    >
      <span className="text-2xl">{isDark ? '☀️' : '🌙'}</span>
    </button>
  );
};

export default ThemeToggle;

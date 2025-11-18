/**
 * TypingIndicator Component
 * Shows animated dots when bot is typing
 */

import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex w-full mb-4 justify-start typing-indicator-container">
      <div className="flex flex-col max-w-[75%] items-start">
        {/* Typing bubble with enhanced animations */}
        <div className="relative px-4 py-3 rounded-2xl shadow-sm bg-gray-200 dark:bg-gray-700 rounded-bl-sm typing-bubble">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-gray-600 dark:bg-gray-300 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-gray-600 dark:bg-gray-300 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-gray-600 dark:bg-gray-300 rounded-full typing-dot"></div>
          </div>
        </div>

        {/* Optional label with fade-in */}
        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1 px-2 italic animate-fade-in">
          typing...
        </span>
      </div>
    </div>
  );
};

export default TypingIndicator;

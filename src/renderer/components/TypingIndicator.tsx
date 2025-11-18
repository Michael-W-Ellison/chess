/**
 * TypingIndicator Component
 * Shows animated dots when bot is typing
 */

import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex w-full mb-4 justify-start animate-message-left">
      <div className="flex flex-col max-w-[75%] items-start">
        {/* Typing bubble */}
        <div className="relative px-4 py-3 rounded-2xl shadow-sm bg-gray-200 dark:bg-gray-700 rounded-bl-sm">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-gray-500 dark:bg-gray-400 rounded-full typing-dot"></div>
          </div>
        </div>

        {/* Optional label */}
        <span className="text-xs text-gray-500 dark:text-gray-400 mt-1 px-2 italic">
          typing...
        </span>
      </div>
    </div>
  );
};

export default TypingIndicator;

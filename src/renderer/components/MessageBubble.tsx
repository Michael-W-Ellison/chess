/**
 * MessageBubble Component
 * Displays a single message in the chat
 */

import React from 'react';
import type { ChatMessage } from '../../shared/types';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  // Format timestamp
  const timestamp = new Date(message.timestamp);
  const timeString = timestamp.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });

  // Safety flag warning
  const hasSafetyFlag = message.metadata?.safety_flag || false;

  return (
    <div
      className={`flex w-full mb-4 ${
        isUser ? 'justify-end' : 'justify-start'
      } ${isUser ? 'animate-message-right' : 'animate-message-left'}`}
    >
      <div
        className={`flex flex-col max-w-[75%] ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        {/* Message bubble */}
        <div
          className={`
            relative px-4 py-3 rounded-2xl shadow-sm
            ${
              isUser
                ? 'bg-blue-500 text-white rounded-br-sm'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-bl-sm'
            }
            ${hasSafetyFlag ? 'border-2 border-yellow-500' : ''}
          `}
        >
          {/* Safety flag indicator */}
          {hasSafetyFlag && (
            <div className="flex items-center gap-1 mb-1 text-xs text-yellow-700">
              <span>⚠️</span>
              <span>Message reviewed for safety</span>
            </div>
          )}

          {/* Message content */}
          <p className="text-sm whitespace-pre-wrap break-words">
            {message.content}
          </p>

          {/* Mood indicator (if assistant and mood detected) */}
          {isAssistant && message.metadata?.mood_detected && (
            <div className="mt-2 text-xs text-gray-600">
              <span className="italic">
                Detected mood: {message.metadata.mood_detected}
              </span>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span className="text-xs text-gray-500 mt-1 px-2">
          {timeString}
        </span>

        {/* Topics extracted (for debugging, optional) */}
        {message.metadata?.topics_extracted &&
          message.metadata.topics_extracted.length > 0 && (
            <div className="text-xs text-gray-400 mt-1 px-2">
              Topics: {message.metadata.topics_extracted.join(', ')}
            </div>
          )}
      </div>
    </div>
  );
};

export default MessageBubble;

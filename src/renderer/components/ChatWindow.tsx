/**
 * ChatWindow Component
 * Main chat interface with messages and input
 */

import React, { useEffect, useRef } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';

export const ChatWindow: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    conversationId,
    personality,
    sendMessage,
    startConversation,
    clearError,
  } = useChat();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new messages arrive
   */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /**
   * Handle sending a message
   */
  const handleSendMessage = (content: string) => {
    sendMessage(content);
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          {/* Bot avatar/status */}
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              {personality?.name ? personality.name.charAt(0) : '🤖'}
            </div>
            {/* Online status indicator */}
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"></div>
          </div>

          {/* Bot info */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              {personality?.name || 'Loading...'}
            </h2>
            {personality && (
              <p className="text-xs text-gray-500">
                Mood: {personality.mood} • Level {personality.friendshipLevel}
              </p>
            )}
          </div>
        </div>

        {/* Conversation status */}
        <div className="flex items-center gap-2">
          {conversationId && (
            <span className="text-xs text-gray-500">
              ID: {conversationId}
            </span>
          )}
          {isLoading && (
            <div className="flex items-center gap-1 text-xs text-blue-600">
              <div className="animate-pulse">●</div>
              <span>Thinking...</span>
            </div>
          )}
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-6 py-3 bg-red-50 border-b border-red-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-red-800">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-xs text-red-600 hover:text-red-800 underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-6 py-4"
        style={{ scrollBehavior: 'smooth' }}
      >
        {/* Loading state */}
        {messages.length === 0 && !error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-500">
              <div className="animate-pulse text-4xl mb-4">💭</div>
              <p className="text-sm">Starting conversation...</p>
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />

        {/* Typing indicator */}
        {isLoading && messages.length > 0 && (
          <div className="flex items-center gap-2 mb-4 text-gray-500">
            <div className="flex gap-1">
              <span className="animate-bounce delay-0">●</span>
              <span className="animate-bounce delay-75">●</span>
              <span className="animate-bounce delay-150">●</span>
            </div>
            <span className="text-sm italic">{personality?.name || 'Bot'} is typing...</span>
          </div>
        )}
      </div>

      {/* Input area */}
      <InputArea
        onSend={handleSendMessage}
        disabled={isLoading || !conversationId}
        placeholder={
          conversationId
            ? 'Type a message...'
            : 'Connecting...'
        }
      />

      {/* Reconnect button (if no conversation) */}
      {!conversationId && !isLoading && (
        <div className="p-4 text-center bg-gray-50 border-t">
          <button
            onClick={startConversation}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Start New Conversation
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatWindow;

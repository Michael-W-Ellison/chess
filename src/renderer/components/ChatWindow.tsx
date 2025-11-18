/**
 * ChatWindow Component
 * Main chat interface with messages and input
 */

import React, { useEffect, useRef, useState } from 'react';
import { useChat } from '../hooks/useChat';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';
import { TwentyQuestionsGame } from './TwentyQuestionsGame';
import { WordAssociationGame } from './WordAssociationGame';

type GameMode = 'twenty-questions' | 'word-association' | null;

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
  const [gameMode, setGameMode] = useState<GameMode>(null);
  const [showGameMenu, setShowGameMenu] = useState(false);

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
    <div className="flex flex-col h-screen bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800 pb-16">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="flex items-center gap-3">
          {/* Bot avatar/status */}
          <div className="relative">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold shadow-md">
              {personality?.name ? personality.name.charAt(0) : '🤖'}
            </div>
            {/* Online status indicator */}
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white dark:border-gray-800"></div>
          </div>

          {/* Bot info */}
          <div>
            <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
              {gameMode === 'twenty-questions' && '20 Questions ♟️'}
              {gameMode === 'word-association' && 'Word Association 🧠'}
              {!gameMode && (personality?.name || 'Loading...')}
            </h2>
            {personality && !gameMode && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Mood: {personality.mood} • Level {personality.friendshipLevel}
              </p>
            )}
            {gameMode && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {gameMode === 'twenty-questions' && 'Chess guessing game'}
                {gameMode === 'word-association' && 'Type related words quickly'}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 relative">
          <button
            onClick={() => {
              if (gameMode) {
                setGameMode(null);
                setShowGameMenu(false);
              } else {
                setShowGameMenu(!showGameMenu);
              }
            }}
            className="px-3 py-1.5 bg-purple-500 hover:bg-purple-600 text-white text-sm rounded-lg font-medium transition-colors shadow-sm"
          >
            {gameMode ? '💬 Back to Chat' : '🎮 Games'}
          </button>

          {/* Game Selection Menu */}
          {showGameMenu && !gameMode && (
            <div className="absolute top-full right-0 mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 min-w-[200px]">
              <button
                onClick={() => {
                  setGameMode('twenty-questions');
                  setShowGameMenu(false);
                }}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-3 border-b border-gray-200 dark:border-gray-700"
              >
                <span className="text-2xl">♟️</span>
                <div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    20 Questions
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Guess the chess item
                  </div>
                </div>
              </button>
              <button
                onClick={() => {
                  setGameMode('word-association');
                  setShowGameMenu(false);
                }}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center gap-3"
              >
                <span className="text-2xl">🧠</span>
                <div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    Word Association
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Type related words
                  </div>
                </div>
              </button>
            </div>
          )}

          {!gameMode && conversationId && (
            <span className="text-xs text-gray-500 dark:text-gray-400">
              ID: {conversationId}
            </span>
          )}
          {!gameMode && isLoading && (
            <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
              <div className="animate-pulse">●</div>
              <span>Thinking...</span>
            </div>
          )}
        </div>
      </div>

      {/* Game Mode */}
      {gameMode ? (
        <div className="flex-1 overflow-y-auto">
          {gameMode === 'twenty-questions' && <TwentyQuestionsGame />}
          {gameMode === 'word-association' && <WordAssociationGame />}
        </div>
      ) : (
        <>
          {/* Error banner */}
          {error && (
            <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-red-800 dark:text-red-200">
                  <span>⚠️</span>
                  <span>{error}</span>
                </div>
                <button
                  onClick={clearError}
                  className="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 underline"
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
                <div className="text-center text-gray-500 dark:text-gray-400">
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
              <div className="flex items-center gap-2 mb-4 text-gray-500 dark:text-gray-400">
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
            <div className="p-4 text-center bg-gray-50 dark:bg-gray-800 border-t dark:border-gray-700">
              <button
                onClick={startConversation}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Start New Conversation
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default ChatWindow;

/**
 * InputArea Component
 * Text input area for typing and sending messages
 */

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { playMessageSendSound } from '../../shared/soundEffects';

interface InputAreaProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

export const InputArea: React.FC<InputAreaProps> = ({
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
  maxLength = 500,
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Handle sending message
   */
  const handleSend = () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || disabled) {
      return;
    }

    // Play send sound effect
    playMessageSendSound();

    onSend(trimmedMessage);
    setMessage('');

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  /**
   * Handle Enter key (send) and Shift+Enter (new line)
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  /**
   * Auto-resize textarea based on content
   */
  const handleInput = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';

    // Set height to scrollHeight (but max 150px)
    const newHeight = Math.min(textarea.scrollHeight, 150);
    textarea.style.height = `${newHeight}px`;
  };

  /**
   * Auto-focus on mount
   */
  useEffect(() => {
    if (textareaRef.current && !disabled) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  const charactersRemaining = maxLength - message.length;
  const isNearLimit = charactersRemaining < 50;

  return (
    <div className="flex flex-col gap-2 p-4 bg-white border-t border-gray-200">
      {/* Character counter (when near limit) */}
      {isNearLimit && (
        <div className="text-xs text-right text-gray-500">
          {charactersRemaining} characters remaining
        </div>
      )}

      {/* Input area */}
      <div className="flex gap-2 items-end">
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          maxLength={maxLength}
          rows={1}
          className="
            flex-1 resize-none rounded-lg border border-gray-300
            px-4 py-3 text-sm
            focus:outline-none focus:ring-2 focus:ring-blue-500
            disabled:bg-gray-100 disabled:cursor-not-allowed
            transition-all duration-200
          "
          style={{
            minHeight: '44px',
            maxHeight: '150px',
          }}
        />

        {/* Send button */}
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="
            flex items-center justify-center
            w-12 h-11 rounded-lg
            bg-blue-500 text-white
            hover:bg-blue-600
            disabled:bg-gray-300 disabled:cursor-not-allowed
            transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-blue-500
          "
          aria-label="Send message"
        >
          {/* Send icon (paper plane) */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-5 h-5"
          >
            <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
          </svg>
        </button>
      </div>

      {/* Helper text */}
      <div className="text-xs text-gray-500">
        Press <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded">Enter</kbd> to send,{' '}
        <kbd className="px-1 py-0.5 bg-gray-100 border border-gray-300 rounded">Shift+Enter</kbd> for new line
      </div>
    </div>
  );
};

export default InputArea;

/**
 * useChat Hook
 * Manages conversation state and message exchange
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { api } from '../services/api';
import type { ChatMessage, PersonalityState } from '../../shared/types';
import { playMessageReceiveSound } from '../../shared/soundEffects';

export interface UseChatState {
  // State
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationId: number | null;
  isConversationActive: boolean;
  personality: PersonalityState | null;

  // Actions
  startConversation: () => Promise<void>;
  sendMessage: (message: string) => Promise<void>;
  endConversation: () => Promise<void>;
  clearError: () => void;
}

/**
 * Hook for managing chat conversations
 */
export function useChat(): UseChatState {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [personality, setPersonality] = useState<PersonalityState | null>(null);

  // Ref to track if conversation is active
  const isConversationActiveRef = useRef(false);

  /**
   * Start a new conversation
   */
  const startConversation = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      setMessages([]);

      const response = await api.conversation.start();

      setConversationId(response.conversation_id);
      setPersonality(response.personality);
      isConversationActiveRef.current = true;

      // Add greeting message
      const greetingMessage: ChatMessage = {
        id: `greeting-${Date.now()}`,
        content: response.greeting,
        role: 'assistant',
        timestamp: new Date().toISOString(),
        metadata: {
          safetyFlag: false,
        },
      };

      setMessages([greetingMessage]);

      // Play receive sound for greeting
      playMessageReceiveSound();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start conversation';
      setError(errorMessage);
      console.error('Failed to start conversation:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Send a message and get response
   */
  const sendMessage = useCallback(
    async (content: string) => {
      if (!conversationId) {
        setError('No active conversation. Please start a conversation first.');
        return;
      }

      if (!content.trim()) {
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Add user message immediately (optimistic update)
        const userMessage: ChatMessage = {
          id: `user-${Date.now()}`,
          content: content.trim(),
          role: 'user',
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, userMessage]);

        // Send to backend
        const response = await api.conversation.sendMessage(conversationId, content.trim());

        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: `assistant-${Date.now()}`,
          content: response.content,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          metadata: response.metadata,
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Play receive sound for bot response
        playMessageReceiveSound();

        // Show safety warning if flagged
        if (response.metadata?.safety_flag) {
          console.warn('Message flagged by safety filter:', response.metadata);
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);
        console.error('Failed to send message:', err);

        // Remove the optimistic user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId]
  );

  /**
   * End the current conversation
   */
  const endConversation = useCallback(async () => {
    if (!conversationId) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      await api.conversation.end(conversationId);

      // Reset state
      setConversationId(null);
      setPersonality(null);
      isConversationActiveRef.current = false;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to end conversation';
      setError(errorMessage);
      console.error('Failed to end conversation:', err);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Auto-start conversation on mount
   */
  useEffect(() => {
    startConversation();

    // Cleanup: end conversation on unmount
    return () => {
      if (isConversationActiveRef.current && conversationId) {
        api.conversation.end(conversationId).catch(console.error);
      }
    };
  }, []); // Only run on mount/unmount

  return {
    // State
    messages,
    isLoading,
    error,
    conversationId,
    isConversationActive: isConversationActiveRef.current,
    personality,

    // Actions
    startConversation,
    sendMessage,
    endConversation,
    clearError,
  };
}

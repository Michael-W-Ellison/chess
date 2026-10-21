/**
 * Chat Context
 * One conversation for the whole app, shared by the chat window and the export views
 *
 * useChat() starts a conversation when it mounts and ends it when it unmounts, so it is
 * called once here, above the views. Components that need the chat (ChatWindow,
 * ExportDialog, MemoryExport) read it with useChatContext() instead of calling useChat()
 * themselves, which would start a separate, empty conversation. The conversation also
 * stays open while the child switches to another view.
 */

import React, { createContext, useContext } from 'react';
import { useChat, UseChatState } from '../hooks/useChat';

const ChatContext = createContext<UseChatState | undefined>(undefined);

export const ChatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const chat = useChat();
  return <ChatContext.Provider value={chat}>{children}</ChatContext.Provider>;
};

export function useChatContext(): UseChatState {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}

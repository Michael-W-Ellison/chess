/**
 * MemoryContext
 * Manages collected memories from conversations
 */

import React, { createContext, useCallback, useEffect, useState } from 'react';
import { Memory, MemoryCategory } from '../../shared/types';
import { extractMemoriesFromText, mergeDuplicateMemories } from '../../shared/memoryUtils';

interface MemoryContextValue {
  memories: Memory[];
  addMemoryFromText: (text: string) => void;
  addMemory: (memory: Omit<Memory, 'id' | 'userId'>) => void;
  updateMemory: (id: number, updates: Partial<Memory>) => void;
  deleteMemory: (id: number) => void;
  clearAllMemories: () => void;
  getMemoriesByCategory: (category: MemoryCategory) => Memory[];
}

const MemoryContext = createContext<MemoryContextValue | undefined>(undefined);

const STORAGE_KEY = 'chess_tutor_memories';

export const MemoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [nextId, setNextId] = useState(1);

  /**
   * Load memories from localStorage on mount
   */
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        setMemories(parsed.memories || []);
        setNextId(parsed.nextId || 1);
      }
    } catch (error) {
      console.error('Failed to load memories:', error);
    }
  }, []);

  /**
   * Save memories to localStorage whenever they change
   */
  useEffect(() => {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          memories,
          nextId,
        })
      );
    } catch (error) {
      console.error('Failed to save memories:', error);
    }
  }, [memories, nextId]);

  /**
   * Extract and add memories from text
   */
  const addMemoryFromText = useCallback(
    (text: string) => {
      const extracted = extractMemoriesFromText(text);

      if (extracted.length === 0) {
        return;
      }

      const newMemories: Memory[] = extracted.map((extracted) => ({
        id: nextId + memories.length,
        userId: 1, // Default user ID
        category: extracted.category,
        key: extracted.key,
        value: extracted.value,
        confidence: extracted.confidence,
        firstMentioned: new Date(),
        lastMentioned: new Date(),
        mentionCount: 1,
      }));

      setMemories((prev) => {
        const combined = [...prev, ...newMemories];
        return mergeDuplicateMemories(combined);
      });

      setNextId((prev) => prev + newMemories.length);
    },
    [nextId, memories.length]
  );

  /**
   * Add a single memory
   */
  const addMemory = useCallback(
    (memory: Omit<Memory, 'id' | 'userId'>) => {
      const newMemory: Memory = {
        ...memory,
        id: nextId,
        userId: 1,
      };

      setMemories((prev) => {
        const combined = [...prev, newMemory];
        return mergeDuplicateMemories(combined);
      });

      setNextId((prev) => prev + 1);
    },
    [nextId]
  );

  /**
   * Update a memory
   */
  const updateMemory = useCallback((id: number, updates: Partial<Memory>) => {
    setMemories((prev) =>
      prev.map((memory) =>
        memory.id === id
          ? {
              ...memory,
              ...updates,
              lastMentioned: new Date(),
            }
          : memory
      )
    );
  }, []);

  /**
   * Delete a memory
   */
  const deleteMemory = useCallback((id: number) => {
    setMemories((prev) => prev.filter((memory) => memory.id !== id));
  }, []);

  /**
   * Clear all memories
   */
  const clearAllMemories = useCallback(() => {
    setMemories([]);
    setNextId(1);
  }, []);

  /**
   * Get memories by category
   */
  const getMemoriesByCategory = useCallback(
    (category: MemoryCategory) => {
      return memories.filter((memory) => memory.category === category);
    },
    [memories]
  );

  const value: MemoryContextValue = {
    memories,
    addMemoryFromText,
    addMemory,
    updateMemory,
    deleteMemory,
    clearAllMemories,
    getMemoriesByCategory,
  };

  return <MemoryContext.Provider value={value}>{children}</MemoryContext.Provider>;
};

export const useMemory = () => {
  const context = React.useContext(MemoryContext);
  if (!context) {
    throw new Error('useMemory must be used within MemoryProvider');
  }
  return context;
};

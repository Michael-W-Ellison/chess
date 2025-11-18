/**
 * Memory Utilities
 * Functions for extracting, formatting, and managing memories
 */

import { Memory, MemoryCategory } from './types';

export interface ExtractedMemory {
  category: MemoryCategory;
  key: string;
  value: string;
  confidence: number;
}

/**
 * Common patterns for extracting memories from text
 */
const MEMORY_PATTERNS = {
  favorite: [
    /my favorite (\w+) is (.+)/i,
    /i (?:really )?love (.+)/i,
    /i (?:really )?like (.+)/i,
    /(.+) is my favorite/i,
  ],
  dislike: [
    /i (?:really )?hate (.+)/i,
    /i (?:really )?dislike (.+)/i,
    /i don't like (.+)/i,
    /(.+) (?:is|are) (?:not )?my least favorite/i,
  ],
  goal: [
    /i want to (.+)/i,
    /my goal is to (.+)/i,
    /i'm (?:trying|planning|hoping) to (.+)/i,
    /i would like to (.+)/i,
  ],
  person: [
    /my (\w+) (?:is |named |called )?(.+)/i,
    /(.+) is my (\w+)/i,
  ],
};

/**
 * Extract memories from a text string
 */
export function extractMemoriesFromText(text: string): ExtractedMemory[] {
  const memories: ExtractedMemory[] = [];
  const lowerText = text.toLowerCase();

  // Check for favorites
  MEMORY_PATTERNS.favorite.forEach((pattern) => {
    const match = lowerText.match(pattern);
    if (match) {
      let key = 'favorite';
      let value = '';

      if (match.length === 3) {
        key = `favorite_${match[1]}`;
        value = match[2];
      } else {
        value = match[1];
      }

      memories.push({
        category: 'favorite',
        key,
        value: value.trim(),
        confidence: 0.8,
      });
    }
  });

  // Check for dislikes
  MEMORY_PATTERNS.dislike.forEach((pattern) => {
    const match = lowerText.match(pattern);
    if (match) {
      memories.push({
        category: 'dislike',
        key: 'dislike',
        value: match[1].trim(),
        confidence: 0.8,
      });
    }
  });

  // Check for goals
  MEMORY_PATTERNS.goal.forEach((pattern) => {
    const match = lowerText.match(pattern);
    if (match) {
      memories.push({
        category: 'goal',
        key: 'goal',
        value: match[1].trim(),
        confidence: 0.7,
      });
    }
  });

  // Check for people
  MEMORY_PATTERNS.person.forEach((pattern) => {
    const match = lowerText.match(pattern);
    if (match) {
      if (match.length === 3) {
        const relationship = match[1];
        const name = match[2];

        // Filter out common false positives
        const commonWords = ['name', 'turn', 'move', 'favorite'];
        if (!commonWords.includes(relationship)) {
          memories.push({
            category: 'person',
            key: relationship,
            value: name.trim(),
            confidence: 0.7,
          });
        }
      }
    }
  });

  return memories;
}

/**
 * Format a memory for display
 */
export function formatMemoryForDisplay(memory: Memory): string {
  const { category, key, value } = memory;

  switch (category) {
    case 'favorite':
      if (key.startsWith('favorite_')) {
        const item = key.replace('favorite_', '');
        return `Favorite ${item}: ${value}`;
      }
      return `Likes: ${value}`;

    case 'dislike':
      return `Dislikes: ${value}`;

    case 'goal':
      return `Goal: ${value}`;

    case 'person':
      return `${key.charAt(0).toUpperCase() + key.slice(1)}: ${value}`;

    case 'achievement':
      return `Achievement: ${value}`;

    default:
      return `${key}: ${value}`;
  }
}

/**
 * Group memories by category
 */
export function groupMemoriesByCategory(memories: Memory[]): Record<MemoryCategory, Memory[]> {
  const grouped: Record<MemoryCategory, Memory[]> = {
    favorite: [],
    dislike: [],
    goal: [],
    person: [],
    achievement: [],
  };

  memories.forEach((memory) => {
    grouped[memory.category].push(memory);
  });

  return grouped;
}

/**
 * Get category emoji
 */
export function getCategoryEmoji(category: MemoryCategory): string {
  const emojis: Record<MemoryCategory, string> = {
    favorite: '❤️',
    dislike: '👎',
    goal: '🎯',
    person: '👤',
    achievement: '🏆',
  };
  return emojis[category];
}

/**
 * Get category display name
 */
export function getCategoryDisplayName(category: MemoryCategory): string {
  const names: Record<MemoryCategory, string> = {
    favorite: 'Favorites',
    dislike: 'Dislikes',
    goal: 'Goals',
    person: 'Important People',
    achievement: 'Achievements',
  };
  return names[category];
}

/**
 * Sort memories by relevance (confidence and recency)
 */
export function sortMemoriesByRelevance(memories: Memory[]): Memory[] {
  return [...memories].sort((a, b) => {
    // First sort by confidence
    if (a.confidence !== b.confidence) {
      return b.confidence - a.confidence;
    }

    // Then by last mentioned date (most recent first)
    const aDate = a.lastMentioned instanceof Date ? a.lastMentioned : new Date(a.lastMentioned);
    const bDate = b.lastMentioned instanceof Date ? b.lastMentioned : new Date(b.lastMentioned);
    return bDate.getTime() - aDate.getTime();
  });
}

/**
 * Create a memory summary for display
 */
export function createMemorySummary(memories: Memory[]): {
  totalMemories: number;
  byCategory: Record<MemoryCategory, number>;
  mostMentioned: Memory[];
  recent: Memory[];
} {
  const byCategory: Record<MemoryCategory, number> = {
    favorite: 0,
    dislike: 0,
    goal: 0,
    person: 0,
    achievement: 0,
  };

  memories.forEach((memory) => {
    byCategory[memory.category]++;
  });

  // Get most mentioned (top 5)
  const mostMentioned = [...memories]
    .sort((a, b) => b.mentionCount - a.mentionCount)
    .slice(0, 5);

  // Get most recent (top 5)
  const recent = [...memories]
    .sort((a, b) => {
      const aDate = a.lastMentioned instanceof Date ? a.lastMentioned : new Date(a.lastMentioned);
      const bDate = b.lastMentioned instanceof Date ? b.lastMentioned : new Date(b.lastMentioned);
      return bDate.getTime() - aDate.getTime();
    })
    .slice(0, 5);

  return {
    totalMemories: memories.length,
    byCategory,
    mostMentioned,
    recent,
  };
}

/**
 * Build memory context string for AI
 */
export function buildMemoryContext(memories: Memory[], maxItems: number = 10): string {
  const sorted = sortMemoriesByRelevance(memories).slice(0, maxItems);

  if (sorted.length === 0) {
    return 'No previous memories.';
  }

  const lines = sorted.map((memory) => `- ${formatMemoryForDisplay(memory)}`);

  return `Previous memories about the user:\n${lines.join('\n')}`;
}

/**
 * Merge duplicate memories
 */
export function mergeDuplicateMemories(memories: Memory[]): Memory[] {
  const merged = new Map<string, Memory>();

  memories.forEach((memory) => {
    const key = `${memory.category}:${memory.key}`;

    if (merged.has(key)) {
      const existing = merged.get(key)!;

      // Update with higher confidence
      if (memory.confidence > existing.confidence) {
        existing.value = memory.value;
        existing.confidence = memory.confidence;
      }

      // Update mention count and dates
      existing.mentionCount += memory.mentionCount;

      const existingLastDate =
        existing.lastMentioned instanceof Date
          ? existing.lastMentioned
          : new Date(existing.lastMentioned);

      const memoryLastDate =
        memory.lastMentioned instanceof Date ? memory.lastMentioned : new Date(memory.lastMentioned);

      if (memoryLastDate > existingLastDate) {
        existing.lastMentioned = memory.lastMentioned;
      }
    } else {
      merged.set(key, { ...memory });
    }
  });

  return Array.from(merged.values());
}

/**
 * Search memories by text
 */
export function searchMemories(memories: Memory[], query: string): Memory[] {
  const lowerQuery = query.toLowerCase();

  return memories.filter((memory) => {
    const lowerValue = memory.value.toLowerCase();
    const lowerKey = memory.key.toLowerCase();

    return lowerValue.includes(lowerQuery) || lowerKey.includes(lowerQuery);
  });
}

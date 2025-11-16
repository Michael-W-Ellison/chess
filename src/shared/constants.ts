/**
 * Shared constants and configuration
 * Used by both main process and renderer process
 */

import { FriendshipLevel, Interest, Quirk, Mood } from './types';

// ============================================================================
// Friendship Levels
// ============================================================================

export const FRIENDSHIP_LEVELS: FriendshipLevel[] = [
  {
    level: 1,
    label: 'New Friends',
    color: '#fbbf24', // yellow
    minConversations: 0,
    maxConversations: 5,
    unlockedFeatures: ['basic_conversation', 'emoji_basic'],
  },
  {
    level: 2,
    label: 'New Friends',
    color: '#fbbf24',
    minConversations: 6,
    maxConversations: 10,
    unlockedFeatures: ['basic_conversation', 'emoji_basic', 'name_memory'],
  },
  {
    level: 3,
    label: 'Good Friends',
    color: '#fb923c', // orange
    minConversations: 11,
    maxConversations: 20,
    unlockedFeatures: [
      'past_references',
      'catchphrase',
      'emoji_enhanced',
      'inside_jokes',
    ],
  },
  {
    level: 4,
    label: 'Good Friends',
    color: '#fb923c',
    minConversations: 21,
    maxConversations: 30,
    unlockedFeatures: [
      'past_references',
      'catchphrase',
      'emoji_enhanced',
      'inside_jokes',
      'favorite_topics',
    ],
  },
  {
    level: 5,
    label: 'Close Friends',
    color: '#f472b6', // pink
    minConversations: 31,
    maxConversations: 45,
    unlockedFeatures: [
      'proactive_checkins',
      'personalized_advice',
      'story_mode',
      'emotional_support',
    ],
  },
  {
    level: 6,
    label: 'Close Friends',
    color: '#f472b6',
    minConversations: 46,
    maxConversations: 60,
    unlockedFeatures: [
      'proactive_checkins',
      'personalized_advice',
      'story_mode',
      'emotional_support',
      'shared_stories',
    ],
  },
  {
    level: 7,
    label: 'Best Friends',
    color: '#ec4899', // pink-600
    minConversations: 61,
    maxConversations: 80,
    unlockedFeatures: [
      'complex_memory',
      'growth_celebration',
      'sophisticated_advice',
      'goal_tracking',
    ],
  },
  {
    level: 8,
    label: 'Best Friends',
    color: '#ec4899',
    minConversations: 81,
    maxConversations: 100,
    unlockedFeatures: [
      'complex_memory',
      'growth_celebration',
      'sophisticated_advice',
      'goal_tracking',
      'achievement_celebrations',
    ],
  },
  {
    level: 9,
    label: 'Lifelong Friends',
    color: '#dc2626', // red
    minConversations: 101,
    maxConversations: 150,
    unlockedFeatures: [
      'deep_emotional_intelligence',
      'mentor_guidance',
      'rich_personality',
      'memory_book',
      'special_games',
    ],
  },
  {
    level: 10,
    label: 'Lifelong Friends',
    color: '#dc2626',
    minConversations: 151,
    maxConversations: Infinity,
    unlockedFeatures: [
      'deep_emotional_intelligence',
      'mentor_guidance',
      'rich_personality',
      'memory_book',
      'special_games',
      'all_features',
    ],
  },
];

// ============================================================================
// Personality Configuration
// ============================================================================

export const PERSONALITY_TRAIT_RANGES = {
  humor: { min: 0.3, max: 0.8 },
  energy: { min: 0.4, max: 0.9 },
  curiosity: { min: 0.3, max: 0.8 },
  formality: { min: 0.2, max: 0.6 },
} as const;

export const PERSONALITY_DRIFT_LIMITS = {
  maxChangePerConversation: 0.02,
  maxChangePerMonth: 0.15,
} as const;

// ============================================================================
// Available Quirks
// ============================================================================

export const AVAILABLE_QUIRKS: Quirk[] = [
  'uses_emojis',
  'tells_puns',
  'shares_facts',
  'storyteller',
];

export const QUIRK_DESCRIPTIONS: Record<Quirk, string> = {
  uses_emojis: 'Adds appropriate emojis to messages',
  tells_puns: 'Frequently makes puns and wordplay',
  shares_facts: 'Shares fun facts related to topics',
  catchphrase: 'Has a signature phrase (developed after level 3)',
  storyteller: 'Likes to share short stories',
};

// ============================================================================
// Available Interests
// ============================================================================

export const AVAILABLE_INTERESTS: Interest[] = [
  'sports',
  'music',
  'art',
  'science',
  'reading',
  'gaming',
  'nature',
  'cooking',
  'technology',
  'history',
  'animals',
];

// ============================================================================
// Mood Configuration
// ============================================================================

export const MOOD_DESCRIPTIONS: Record<Mood, string> = {
  happy: 'Default, upbeat and friendly',
  excited: 'High energy, lots of enthusiasm',
  calm: 'Gentle, soothing responses',
  concerned: 'Serious, supportive when user seems upset',
  playful: 'Extra jokes and fun suggestions',
  thoughtful: 'Reflective, asks deeper questions',
};

export const MOOD_EMOJIS: Record<Mood, string[]> = {
  happy: ['😊', '🙂', '😄'],
  excited: ['🎉', '😃', '🤩'],
  concerned: ['💙', '🫂'],
  playful: ['😄', '😆', '🎮'],
  thoughtful: ['🤔', '💭'],
  calm: ['😌', '🌸', '✨'],
};

// ============================================================================
// Safety Configuration
// ============================================================================

export const CRISIS_KEYWORDS = [
  'kill myself',
  'suicide',
  'want to die',
  'self harm',
  'cut myself',
  'hurt myself',
  'end it all',
];

export const BULLYING_KEYWORDS = [
  'bully',
  'bullied',
  'teasing me',
  'making fun of me',
  'spreading rumors',
  'left me out',
];

export const ABUSE_KEYWORDS = [
  'hit me',
  'hurt me',
  'touched me inappropriately',
  'makes me scared',
  'threatens me',
];

export const CRISIS_RESOURCES = {
  suicidePreventionLifeline: {
    name: 'National Suicide Prevention Lifeline',
    number: '988',
    description: 'Call or text anytime',
  },
  crisisTextLine: {
    name: 'Crisis Text Line',
    shortCode: 'HOME',
    number: '741741',
    description: 'Text HOME to 741741',
  },
};

// ============================================================================
// Advice Categories
// ============================================================================

export const ADVICE_CATEGORY_KEYWORDS: Record<string, string[]> = {
  school_stress: ['test', 'homework', 'grade', 'study', 'exam', 'project'],
  friend_conflict: ['friend', 'argument', 'fight', 'mad at me', 'ignoring'],
  performance_anxiety: ['nervous', 'scared', 'worried', 'anxious', 'presentation'],
  family_issues: ['parent', 'sibling', 'mom', 'dad', 'brother', 'sister'],
  boredom: ['bored', 'nothing to do', 'no fun'],
  self_confidence: ['not good at', 'bad at', 'everyone else', "I can't"],
};

// ============================================================================
// Memory Configuration
// ============================================================================

export const MEMORY_CATEGORIES = [
  'favorite',
  'dislike',
  'goal',
  'person',
  'achievement',
] as const;

export const SHORT_TERM_MEMORY_LIMIT = 3; // Last 3 conversations
export const RECENT_MESSAGES_LIMIT = 10;  // Last 10 messages in context
export const RELEVANT_MEMORIES_LIMIT = 5; // Top 5 memories to include

// ============================================================================
// Response Configuration
// ============================================================================

export const RESPONSE_LENGTH_GUIDELINES = {
  min_sentences: 2,
  max_sentences: 4,
  target_length: 'concise', // Preteen attention span
};

// ============================================================================
// Time Constants
// ============================================================================

export const TIME_THRESHOLDS = {
  CONTINUING_CONVERSATION: 1,   // hours
  NEW_DAY_GREETING: 24,         // hours
  MISSED_YOU_GREETING: 48,      // hours
};

// ============================================================================
// API Configuration
// ============================================================================

export const API_ENDPOINTS = {
  CONVERSATION_START: '/api/conversation/start',
  MESSAGE: '/api/message',
  CONVERSATION_END: '/api/conversation/end',
  PERSONALITY: '/api/personality',
  PROFILE: '/api/profile',
  PARENT_DASHBOARD: '/api/parent/dashboard',
} as const;

export const BACKEND_PORT = 8000;
export const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get friendship level data from conversation count
 */
export function getFriendshipLevelFromCount(conversationCount: number): FriendshipLevel {
  for (let i = FRIENDSHIP_LEVELS.length - 1; i >= 0; i--) {
    const level = FRIENDSHIP_LEVELS[i];
    if (conversationCount >= level.minConversations) {
      return level;
    }
  }
  return FRIENDSHIP_LEVELS[0];
}

/**
 * Get random items from an array
 */
export function getRandomItems<T>(array: T[], count: number): T[] {
  const shuffled = [...array].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
}

/**
 * Generate random trait value within allowed range
 */
export function generateRandomTrait(traitName: keyof typeof PERSONALITY_TRAIT_RANGES): number {
  const range = PERSONALITY_TRAIT_RANGES[traitName];
  return range.min + Math.random() * (range.max - range.min);
}

/**
 * Clamp a number between min and max
 */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

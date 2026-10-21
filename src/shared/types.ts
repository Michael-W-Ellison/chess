/**
 * Shared TypeScript types and interfaces
 * Used by both main process and renderer process
 *
 * Types for backend API responses use the field names the backend sends (mostly
 * snake_case, e.g. friendship_level), so they describe the data actually received.
 */

// ============================================================================
// Personality Types
// ============================================================================

export type Mood = 'happy' | 'excited' | 'calm' | 'concerned' | 'playful' | 'thoughtful';

export type Quirk =
  | 'uses_emojis'
  | 'tells_puns'
  | 'shares_facts'
  | 'catchphrase'
  | 'storyteller';

export type Interest =
  | 'sports'
  | 'music'
  | 'art'
  | 'science'
  | 'reading'
  | 'gaming'
  | 'nature'
  | 'cooking'
  | 'technology'
  | 'history'
  | 'animals';

export interface PersonalityTraits {
  humor: number;        // 0.0-1.0
  energy: number;       // 0.0-1.0
  curiosity: number;    // 0.0-1.0
  formality: number;    // 0.0-1.0
}

// The backend sends these stats in camelCase
export interface PersonalityStats {
  totalConversations: number;
  totalMessages: number;
  daysSinceMet: number;
  currentStreak: number;
  lastInteraction?: string | null;  // ISO date string
}

/** GET /api/personality */
export interface PersonalityState {
  name: string;
  traits: PersonalityTraits;
  friendship_level: number;  // 1-10
  total_conversations: number;
  mood: Mood;
  interests: Interest[];
  quirks: Quirk[];
  catchphrase?: string | null;
  stats: PersonalityStats;
}

/** The personality summary in POST /api/conversation/start */
export interface ConversationPersonality {
  name: string;
  mood: Mood;
  friendship_level: number;
  friendship_points: number;
}

// ============================================================================
// User Profile Types
// ============================================================================

/** A person in the profile: name is the memory key (e.g. "best_friend_maya"), notes its value */
export interface ImportantPerson {
  name: string;
  notes?: string;
}

/** GET /api/profile */
export interface UserProfile {
  name: string;
  age?: number | null;
  grade?: number | null;
  favorites: Record<string, string>;  // color, food, subject, hobby, animal, etc.
  dislikes: Record<string, string>;
  importantPeople: ImportantPerson[];
  goals: string[];
  achievements: string[];
}

/** A stored memory from GET /api/profile/memories */
export interface ProfileItem {
  id: number;
  user_id: number;
  category: string;
  key: string;
  value: string;
  confidence: number;
  first_mentioned: string | null;
  last_mentioned: string | null;
  mention_count: number;
}

// ============================================================================
// Chat Message Types
// ============================================================================

export type MessageRole = 'user' | 'assistant';

/** Metadata of a bot reply from POST /api/message */
export interface MessageMetadata {
  safety_flag?: boolean;
  severity?: string;
  crisis_response?: boolean;
  flags?: unknown[];
  notify_parent?: boolean;
  mood_change?: string;
  mood_detected?: string | null;
  topics_extracted?: string[];
  points_awarded?: unknown[];
  activities_detected?: unknown[];
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;  // ISO date string
  metadata?: MessageMetadata;
}

// ============================================================================
// Conversation Types
// ============================================================================

export interface ConversationSummary {
  date: string;
  messageCount: number;
  topics: string[];
  moodDetected: string;
  flagsRaised: number;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/** POST /api/conversation/start */
export interface StartConversationResponse {
  conversation_id: number;
  greeting: string;
  personality: ConversationPersonality;
}

export interface SendMessageResponse {
  message_id: number;
  content: string;
  timestamp: string;
  metadata: MessageMetadata;
}

// ============================================================================
// Memory Types
// ============================================================================

export type MemoryCategory = 'favorite' | 'dislike' | 'goal' | 'person' | 'achievement';

export interface Memory {
  id: number;
  userId: number;
  category: MemoryCategory;
  key: string;           // e.g., 'favorite_color', 'friend_name'
  value: string;
  confidence: number;    // 0.0-1.0
  firstMentioned: Date;
  lastMentioned: Date;
  mentionCount: number;
}

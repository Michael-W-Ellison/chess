/**
 * Shared TypeScript types and interfaces
 * Used by both main process and renderer process
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

export interface PersonalityStats {
  totalConversations: number;
  totalMessages: number;
  daysSinceMet: number;
  currentStreak: number;
  lastInteraction?: string;  // ISO date string
}

export interface PersonalityState {
  name: string;
  traits: PersonalityTraits;
  friendshipLevel: number;  // 1-10
  mood: Mood;
  interests: Interest[];
  quirks: Quirk[];
  catchphrase?: string;
  stats: PersonalityStats;
}

// ============================================================================
// User Profile Types
// ============================================================================

export interface ImportantPerson {
  name: string;
  relationship: string;  // 'friend', 'sibling', 'pet', 'teacher', etc.
  notes?: string;
}

export interface Goal {
  description: string;
  category: string;
  dateSet: Date;
  achieved?: boolean;
}

export interface Achievement {
  description: string;
  date: Date;
}

export interface UserProfile {
  name: string;
  age?: number;
  grade?: number;
  favorites: Record<string, string>;  // color, food, subject, hobby, animal, etc.
  dislikes: Record<string, string>;
  importantPeople: ImportantPerson[];
  goals: Goal[];
  achievements: Achievement[];
}

// ============================================================================
// Chat Message Types
// ============================================================================

export type MessageRole = 'user' | 'assistant';

export interface MessageMetadata {
  moodDetected?: string;
  topicsExtracted?: string[];
  memoryTriggered?: string[];
  adviceCategory?: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  metadata?: MessageMetadata;
}

// ============================================================================
// Conversation Types
// ============================================================================

export type ConversationGoal = 'casual' | 'advice' | 'storytelling' | 'game';

export interface ConversationContext {
  personality: PersonalityState;
  userProfile: UserProfile;
  recentMessages: ChatMessage[];  // Last 10 messages
  relevantMemories: string[];     // Retrieved from long-term memory
  currentTopic?: string;
  conversationGoal?: ConversationGoal;
  timeSinceLastChat?: number;     // Hours
}

export interface ConversationSummary {
  date: string;
  messageCount: number;
  topics: string[];
  moodDetected: string;
  flagsRaised: number;
}

// ============================================================================
// Safety Types
// ============================================================================

export type FlagType = 'profanity' | 'crisis' | 'bullying' | 'inappropriate';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export interface SafetyFlag {
  id: number;
  userId: number;
  messageId?: number;
  flagType: FlagType;
  severity: Severity;
  contentSnippet?: string;
  actionTaken: string;
  timestamp: Date;
  parentNotified: boolean;
}

// ============================================================================
// Advice Types
// ============================================================================

export type AdviceCategory =
  | 'school_stress'
  | 'friend_conflict'
  | 'performance_anxiety'
  | 'family_issues'
  | 'boredom'
  | 'self_confidence';

export interface AdviceTemplate {
  id: number;
  category: AdviceCategory;
  keywords: string[];
  template: string;
  minFriendshipLevel: number;
  expertReviewed: boolean;
}

// ============================================================================
// API Request/Response Types
// ============================================================================

export interface StartConversationResponse {
  conversationId: string;
  greeting: string;
  personality: {
    name: string;
    mood: Mood;
    friendshipLevel: number;
  };
}

export interface SendMessageRequest {
  content: string;
}

export interface SendMessageResponse {
  messageId: string;
  content: string;
  timestamp: string;
  metadata: MessageMetadata;
}

export interface EndConversationRequest {
  conversationId: string;
}

export interface GetPersonalityResponse {
  name: string;
  traits: PersonalityTraits;
  friendshipLevel: number;
  mood: Mood;
  interests: Interest[];
  quirks: Quirk[];
  stats: PersonalityStats;
}

export interface GetProfileResponse {
  name: string;
  age?: number;
  grade?: number;
  favorites: Record<string, string>;
  importantPeople: ImportantPerson[];
  goals: Goal[];
}

export interface ParentDashboardData {
  conversationSummaries: ConversationSummary[];
  safetyFlags: SafetyFlag[];
  stats: {
    totalConversations: number;
    currentStreak: number;
    averageSessionLength: string;
  };
}

export interface GetParentDashboardRequest {
  password: string;
}

export interface GetParentDashboardResponse {
  data: ParentDashboardData;
}

// ============================================================================
// Settings Types
// ============================================================================

// Comprehensive settings schema - re-export from settings modules
export type {
  AppSettings,
  AppearanceSettings,
  SoundSettings,
  NotificationSettings,
  PrivacySettings,
  ChatSettings,
  PersonalitySettings,
  AccessibilitySettings,
  ParentalSettings,
  AdvancedSettings,
  WindowSettings,
  AppMetadata,
  Theme,
  ColorTheme,
  SafetyLevel,
  FontSize,
  SettingsPath,
  SettingsCategory,
  SettingsValidationError,
  SettingsValidationResult,
} from './settings-schema';

export { DEFAULT_SETTINGS, DEFAULT_USER_ID } from './settings-defaults';
export { validateSettings, sanitizeSettings } from './settings-validation';

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

// ============================================================================
// Database Model Types (for reference)
// ============================================================================

export interface User {
  id: number;
  name: string;
  age?: number;
  grade?: number;
  createdAt: Date;
  lastActive: Date;
  parentEmail?: string;
}

export interface BotPersonality {
  id: number;
  userId: number;
  name: string;
  humor: number;
  energy: number;
  curiosity: number;
  formality: number;
  friendshipLevel: number;
  totalConversations: number;
  mood: Mood;
  quirks: string;        // JSON array
  interests: string;     // JSON array
  catchphrase?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Conversation {
  id: number;
  userId: number;
  timestamp: Date;
  conversationSummary?: string;
  moodDetected?: string;
  topics?: string;       // JSON array
  durationSeconds?: number;
  messageCount?: number;
}

export interface Message {
  id: number;
  conversationId: number;
  role: MessageRole;
  content: string;
  timestamp: Date;
  flagged: boolean;
  metadata?: string;     // JSON
}

// ============================================================================
// IPC Response Wrapper
// ============================================================================

export interface IPCResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// ============================================================================
// Utility Types
// ============================================================================

export type FriendshipLevelLabel =
  | 'New Friends'
  | 'Good Friends'
  | 'Close Friends'
  | 'Best Friends'
  | 'Lifelong Friends';

export interface FriendshipLevel {
  level: number;
  label: FriendshipLevelLabel;
  color: string;
  minConversations: number;
  maxConversations: number;
  unlockedFeatures: string[];
}

// ============================================================================
// Export all types
// ============================================================================

export type {
  // Re-export commonly used types for convenience
};

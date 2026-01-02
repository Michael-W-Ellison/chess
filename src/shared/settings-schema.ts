/**
 * Settings Schema and Types
 * Comprehensive type definitions for all application settings
 *
 * This file defines the complete structure of application settings,
 * organized into logical categories for easy management.
 */

// ============================================================================
// Base Setting Types
// ============================================================================

/**
 * Theme options for the application
 */
export type Theme = 'light' | 'dark' | 'auto';

/**
 * Color theme options (primary accent color)
 */
export type ColorTheme =
  | 'purple'
  | 'blue'
  | 'green'
  | 'pink'
  | 'orange'
  | 'red'
  | 'teal'
  | 'indigo';

/**
 * Safety level for content filtering
 */
export type SafetyLevel = 'low' | 'medium' | 'high' | 'strict';

/**
 * Language options
 */
export type Language = 'en' | 'es' | 'fr' | 'de' | 'zh' | 'ja';

/**
 * Font size options
 */
export type FontSize = 'small' | 'medium' | 'large' | 'x-large';

/**
 * Avatar style options
 */
export type AvatarStyle =
  | 'robot'
  | 'animal'
  | 'monster'
  | 'space'
  | 'fantasy'
  | 'custom';

// ============================================================================
// Settings Categories
// ============================================================================

/**
 * Appearance Settings
 * Visual customization options
 */
export interface AppearanceSettings {
  // Theme
  theme: Theme;
  colorTheme: ColorTheme;

  // Layout
  fontSize: FontSize;
  compactMode: boolean;
  showSidebar: boolean;
  sidebarCollapsed: boolean;

  // Visual Effects
  enableAnimations: boolean;
  enableParticles: boolean;
  reduceMotion: boolean;

  // Avatar
  avatarId?: string;
  avatarStyle: AvatarStyle;
  showAvatarInChat: boolean;
}

/**
 * Sound Settings
 * Audio and notification sounds
 */
export interface SoundSettings {
  // Master Controls
  soundEnabled: boolean;
  masterVolume: number; // 0.0 - 1.0

  // Individual Sounds
  messageSound: boolean;
  achievementSound: boolean;
  levelUpSound: boolean;
  clickSound: boolean;
  errorSound: boolean;

  // Volume Levels
  messageSoundVolume: number;
  achievementSoundVolume: number;
  levelUpSoundVolume: number;
  clickSoundVolume: number;
  errorSoundVolume: number;
}

/**
 * Notification Settings
 * System notifications and alerts
 */
export interface NotificationSettings {
  // Desktop Notifications
  notificationsEnabled: boolean;
  showDesktopNotifications: boolean;

  // Email Notifications (for parents)
  emailNotificationsEnabled: boolean;
  parentEmail?: string;

  // Notification Types
  notifyOnNewMessage: boolean;
  notifyOnAchievement: boolean;
  notifyOnLevelUp: boolean;
  notifyOnStreak: boolean;

  // Weekly Reports
  weeklyReportEnabled: boolean;
  weeklyReportDay: number; // 0-6 (Sunday-Saturday)
}

/**
 * Privacy Settings
 * Data collection and safety settings
 */
export interface PrivacySettings {
  // Data Collection
  dataCollectionEnabled: boolean;
  analyticsEnabled: boolean;
  crashReportsEnabled: boolean;

  // Safety
  safetyLevel: SafetyLevel;
  parentalControlsEnabled: boolean;
  parentPassword?: string;
  requireParentApproval: boolean;

  // Content Filters
  profanityFilterEnabled: boolean;
  bullying DetectionEnabled: boolean;
  crisisDetectionEnabled: boolean;
  inappropriateContentFilterEnabled: boolean;

  // Data Retention
  retainChatHistory: boolean;
  chatHistoryDays: number; // How many days to keep
  autoDeleteOldChats: boolean;
}

/**
 * Chat Settings
 * Conversation and interaction preferences
 */
export interface ChatSettings {
  // Conversation
  autoStartConversation: boolean;
  showTypingIndicator: boolean;
  enableAutoCorrect: boolean;

  // Message History
  maxMessageHistory: number;
  saveConversations: boolean;
  exportConversationsEnabled: boolean;

  // Response Behavior
  responseSpeed: 'slow' | 'medium' | 'fast';
  responseLength: 'short' | 'medium' | 'long';
  useCasualLanguage: boolean;
  useEmojis: boolean;

  // Time Limits
  dailyChatTimeLimit?: number; // minutes, undefined = no limit
  chatSessionTimeout: number; // minutes of inactivity
  reminderInterval: number; // minutes before reminder
}

/**
 * Personality Settings
 * Bot personality customization
 */
export interface PersonalitySettings {
  // Name
  botName: string;
  allowNameChange: boolean;

  // Traits (0.0 - 1.0)
  humorLevel: number;
  energyLevel: number;
  curiosityLevel: number;
  formalityLevel: number;

  // Behavior
  enableQuirks: boolean;
  enableCatchphrases: boolean;
  enableStorytelling: boolean;
  enableJokes: boolean;

  // Learning
  adaptToUserStyle: boolean;
  rememberConversations: boolean;
  evolveOverTime: boolean;
}

/**
 * Accessibility Settings
 * Features for improved accessibility
 */
export interface AccessibilitySettings {
  // Screen Reader
  screenReaderEnabled: boolean;

  // Visual
  highContrast: boolean;
  largeText: boolean;
  reduceMotion: boolean;

  // Reading
  dyslexicFont: boolean;
  increaseLineSpacing: boolean;

  // Interaction
  keyboardNavigationEnabled: boolean;
  focusIndicatorsEnabled: boolean;
  slowAnimations: boolean;
}

/**
 * Parental Settings
 * Settings that can only be changed by parents
 */
export interface ParentalSettings {
  // Access Control
  parentalControlsActive: boolean;
  requirePasswordForSettings: boolean;
  requirePasswordForExport: boolean;

  // Time Management
  dailyTimeLimitEnabled: boolean;
  dailyTimeLimitMinutes: number;
  quietHoursEnabled: boolean;
  quietHoursStart: string; // HH:MM format
  quietHoursEnd: string;

  // Content Restrictions
  restrictTopics: string[];
  allowedTopics: string[];
  blockExternalLinks: boolean;

  // Monitoring
  parentDashboardEnabled: boolean;
  conversationReviewEnabled: boolean;
  safetyAlertThreshold: SafetyLevel;
}

/**
 * Advanced Settings
 * Developer and advanced user options
 */
export interface AdvancedSettings {
  // Performance
  enableCaching: boolean;
  cacheSize: number; // MB
  preloadMessages: boolean;

  // Debug
  debugMode: boolean;
  showDebugInfo: boolean;
  logLevel: 'error' | 'warn' | 'info' | 'debug';

  // Experimental
  enableExperimentalFeatures: boolean;
  betaFeaturesEnabled: boolean;

  // Data
  exportFormat: 'json' | 'csv' | 'pdf';
  autoBackupEnabled: boolean;
  backupFrequency: number; // days
}

/**
 * Window Settings
 * Window and layout preferences (Electron-specific)
 */
export interface WindowSettings {
  // Window State
  windowBounds?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  windowMaximized: boolean;
  windowFullscreen: boolean;

  // Startup
  openOnStartup: boolean;
  startMinimized: boolean;
  rememberWindowPosition: boolean;

  // Behavior
  closeToTray: boolean;
  minimizeToTray: boolean;
  showInTaskbar: boolean;
  alwaysOnTop: boolean;
}

/**
 * App Metadata
 * Internal app settings and metadata
 */
export interface AppMetadata {
  // Version
  version: string;
  buildNumber?: number;

  // Installation
  firstLaunchDate?: string; // ISO string
  lastLaunchDate?: string;
  launchCount: number;

  // Updates
  lastUpdateCheck?: string;
  updateChannel: 'stable' | 'beta' | 'dev';
  autoUpdateEnabled: boolean;

  // Migration
  migrationVersion: number;
  migratedFromLocalStorage: boolean;

  // User
  userId: number;
  installId: string; // Unique installation identifier
}

// ============================================================================
// Complete Settings Schema
// ============================================================================

/**
 * Complete Application Settings
 * This is the master settings object that contains all categories
 */
export interface AppSettings {
  appearance: AppearanceSettings;
  sound: SoundSettings;
  notifications: NotificationSettings;
  privacy: PrivacySettings;
  chat: ChatSettings;
  personality: PersonalitySettings;
  accessibility: AccessibilitySettings;
  parental: ParentalSettings;
  advanced: AdvancedSettings;
  window: WindowSettings;
  metadata: AppMetadata;
}

// ============================================================================
// Settings Validation Types
// ============================================================================

/**
 * Settings validation error
 */
export interface SettingsValidationError {
  path: string;
  message: string;
  value: any;
  expected?: string;
}

/**
 * Settings validation result
 */
export interface SettingsValidationResult {
  valid: boolean;
  errors: SettingsValidationError[];
}

// ============================================================================
// Settings Change Events
// ============================================================================

/**
 * Setting change event
 */
export interface SettingChangeEvent<T = any> {
  path: string;
  oldValue: T;
  newValue: T;
  timestamp: Date;
}

/**
 * Setting change callback
 */
export type SettingChangeCallback<T = any> = (event: SettingChangeEvent<T>) => void;

// ============================================================================
// Settings Import/Export Types
// ============================================================================

/**
 * Settings export format
 */
export interface SettingsExport {
  version: string;
  exportDate: string;
  settings: Partial<AppSettings>;
  checksum?: string;
}

/**
 * Settings import result
 */
export interface SettingsImportResult {
  success: boolean;
  imported: number;
  skipped: number;
  errors: string[];
}

// ============================================================================
// Utility Types
// ============================================================================

/**
 * Deep partial type for settings updates
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

/**
 * Settings path type (dot notation)
 */
export type SettingsPath =
  | keyof AppSettings
  | `${keyof AppSettings}.${string}`;

/**
 * Settings category names
 */
export type SettingsCategory = keyof AppSettings;

/**
 * Readonly settings (for display purposes)
 */
export type ReadonlySettings = Readonly<AppSettings>;

// ============================================================================
// Type Guards
// ============================================================================

/**
 * Check if value is a valid Theme
 */
export function isTheme(value: any): value is Theme {
  return ['light', 'dark', 'auto'].includes(value);
}

/**
 * Check if value is a valid ColorTheme
 */
export function isColorTheme(value: any): value is ColorTheme {
  return ['purple', 'blue', 'green', 'pink', 'orange', 'red', 'teal', 'indigo'].includes(value);
}

/**
 * Check if value is a valid SafetyLevel
 */
export function isSafetyLevel(value: any): value is SafetyLevel {
  return ['low', 'medium', 'high', 'strict'].includes(value);
}

/**
 * Check if value is a valid FontSize
 */
export function isFontSize(value: any): value is FontSize {
  return ['small', 'medium', 'large', 'x-large'].includes(value);
}

/**
 * Check if value is in range 0-1
 */
export function isNormalizedValue(value: any): value is number {
  return typeof value === 'number' && value >= 0 && value <= 1;
}

// ============================================================================
// Constants
// ============================================================================

/**
 * Default user ID (single user app)
 */
export const DEFAULT_USER_ID = 1;

/**
 * Settings file name
 */
export const SETTINGS_FILE_NAME = 'chatbot-friend-config';

/**
 * Current settings schema version
 */
export const SETTINGS_SCHEMA_VERSION = 1;

/**
 * Maximum allowed values
 */
export const MAX_CHAT_HISTORY_DAYS = 365;
export const MAX_MESSAGE_HISTORY = 1000;
export const MAX_CACHE_SIZE_MB = 500;
export const MAX_DAILY_TIME_LIMIT_MINUTES = 1440; // 24 hours

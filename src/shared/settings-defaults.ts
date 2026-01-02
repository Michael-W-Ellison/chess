/**
 * Settings Defaults
 * Default values for all application settings
 *
 * These defaults are used when:
 * - The app is first launched
 * - Settings are reset
 * - A setting value is missing or invalid
 */

import type {
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
} from './settings-schema';
import { DEFAULT_USER_ID, SETTINGS_SCHEMA_VERSION } from './settings-schema';

/**
 * Generate a simple unique ID
 */
function generateUniqueId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 15)}`;
}

// ============================================================================
// Default Settings by Category
// ============================================================================

/**
 * Default Appearance Settings
 * Visual customization defaults
 */
export const DEFAULT_APPEARANCE: AppearanceSettings = {
  // Theme
  theme: 'auto', // Respect system preference
  colorTheme: 'purple', // Brand color

  // Layout
  fontSize: 'medium',
  compactMode: false,
  showSidebar: true,
  sidebarCollapsed: false,

  // Visual Effects
  enableAnimations: true,
  enableParticles: true,
  reduceMotion: false,

  // Avatar
  avatarId: undefined, // User selects on first run
  avatarStyle: 'robot',
  showAvatarInChat: true,
};

/**
 * Default Sound Settings
 * Audio defaults optimized for preteen users
 */
export const DEFAULT_SOUND: SoundSettings = {
  // Master Controls
  soundEnabled: true,
  masterVolume: 0.7, // 70% volume

  // Individual Sounds
  messageSound: true,
  achievementSound: true,
  levelUpSound: true,
  clickSound: true,
  errorSound: true,

  // Volume Levels (relative to master volume)
  messageSoundVolume: 0.6,
  achievementSoundVolume: 0.8,
  levelUpSoundVolume: 1.0,
  clickSoundVolume: 0.3,
  errorSoundVolume: 0.5,
};

/**
 * Default Notification Settings
 * Conservative defaults to avoid notification overload
 */
export const DEFAULT_NOTIFICATIONS: NotificationSettings = {
  // Desktop Notifications
  notificationsEnabled: true,
  showDesktopNotifications: false, // Opt-in

  // Email Notifications
  emailNotificationsEnabled: false,
  parentEmail: undefined,

  // Notification Types
  notifyOnNewMessage: false, // User is already in app
  notifyOnAchievement: true,
  notifyOnLevelUp: true,
  notifyOnStreak: true,

  // Weekly Reports
  weeklyReportEnabled: true,
  weeklyReportDay: 0, // Sunday
};

/**
 * Default Privacy Settings
 * Privacy-first defaults with medium safety
 */
export const DEFAULT_PRIVACY: PrivacySettings = {
  // Data Collection
  dataCollectionEnabled: true, // For improving experience
  analyticsEnabled: false, // Opt-in
  crashReportsEnabled: true, // For bug fixes

  // Safety
  safetyLevel: 'medium',
  parentalControlsEnabled: false,
  parentPassword: undefined,
  requireParentApproval: false,

  // Content Filters
  profanityFilterEnabled: true,
  bullyingDetectionEnabled: true,
  crisisDetectionEnabled: true,
  inappropriateContentFilterEnabled: true,

  // Data Retention
  retainChatHistory: true,
  chatHistoryDays: 90, // 3 months
  autoDeleteOldChats: false,
};

/**
 * Default Chat Settings
 * Balanced for engaging conversations
 */
export const DEFAULT_CHAT: ChatSettings = {
  // Conversation
  autoStartConversation: false,
  showTypingIndicator: true,
  enableAutoCorrect: true,

  // Message History
  maxMessageHistory: 100,
  saveConversations: true,
  exportConversationsEnabled: true,

  // Response Behavior
  responseSpeed: 'medium',
  responseLength: 'medium',
  useCasualLanguage: true,
  useEmojis: true,

  // Time Limits
  dailyChatTimeLimit: undefined, // No limit by default
  chatSessionTimeout: 30, // 30 minutes
  reminderInterval: 60, // 1 hour
};

/**
 * Default Personality Settings
 * Friendly, balanced bot personality
 */
export const DEFAULT_PERSONALITY: PersonalitySettings = {
  // Name
  botName: 'Buddy',
  allowNameChange: true,

  // Traits (0.0 - 1.0)
  humorLevel: 0.7, // Quite humorous
  energyLevel: 0.6, // Moderately energetic
  curiosityLevel: 0.8, // Very curious
  formalityLevel: 0.3, // Casual and friendly

  // Behavior
  enableQuirks: true,
  enableCatchphrases: true,
  enableStorytelling: true,
  enableJokes: true,

  // Learning
  adaptToUserStyle: true,
  rememberConversations: true,
  evolveOverTime: true,
};

/**
 * Default Accessibility Settings
 * Standard accessibility (users opt-in to specialized features)
 */
export const DEFAULT_ACCESSIBILITY: AccessibilitySettings = {
  // Screen Reader
  screenReaderEnabled: false,

  // Visual
  highContrast: false,
  largeText: false,
  reduceMotion: false,

  // Reading
  dyslexicFont: false,
  increaseLineSpacing: false,

  // Interaction
  keyboardNavigationEnabled: true,
  focusIndicatorsEnabled: true,
  slowAnimations: false,
};

/**
 * Default Parental Settings
 * Parental controls disabled by default (opt-in)
 */
export const DEFAULT_PARENTAL: ParentalSettings = {
  // Access Control
  parentalControlsActive: false,
  requirePasswordForSettings: false,
  requirePasswordForExport: false,

  // Time Management
  dailyTimeLimitEnabled: false,
  dailyTimeLimitMinutes: 120, // 2 hours if enabled
  quietHoursEnabled: false,
  quietHoursStart: '21:00',
  quietHoursEnd: '07:00',

  // Content Restrictions
  restrictTopics: [],
  allowedTopics: [],
  blockExternalLinks: true,

  // Monitoring
  parentDashboardEnabled: false,
  conversationReviewEnabled: false,
  safetyAlertThreshold: 'medium',
};

/**
 * Default Advanced Settings
 * Optimized for performance and stability
 */
export const DEFAULT_ADVANCED: AdvancedSettings = {
  // Performance
  enableCaching: true,
  cacheSize: 100, // 100 MB
  preloadMessages: true,

  // Debug
  debugMode: false,
  showDebugInfo: false,
  logLevel: 'warn',

  // Experimental
  enableExperimentalFeatures: false,
  betaFeaturesEnabled: false,

  // Data
  exportFormat: 'json',
  autoBackupEnabled: false,
  backupFrequency: 7, // Weekly
};

/**
 * Default Window Settings
 * Sensible window defaults for desktop app
 */
export const DEFAULT_WINDOW: WindowSettings = {
  // Window State
  windowBounds: {
    x: 100,
    y: 100,
    width: 1200,
    height: 800,
  },
  windowMaximized: false,
  windowFullscreen: false,

  // Startup
  openOnStartup: false,
  startMinimized: false,
  rememberWindowPosition: true,

  // Behavior
  closeToTray: false,
  minimizeToTray: false,
  showInTaskbar: true,
  alwaysOnTop: false,
};

/**
 * Default App Metadata
 * Initial metadata values
 */
export const DEFAULT_METADATA: AppMetadata = {
  // Version
  version: '0.1.0',
  buildNumber: undefined,

  // Installation
  firstLaunchDate: undefined, // Set on first launch
  lastLaunchDate: undefined,
  launchCount: 0,

  // Updates
  lastUpdateCheck: undefined,
  updateChannel: 'stable',
  autoUpdateEnabled: true,

  // Migration
  migrationVersion: SETTINGS_SCHEMA_VERSION,
  migratedFromLocalStorage: false,

  // User
  userId: DEFAULT_USER_ID,
  installId: generateUniqueId(), // Generate unique ID
};

// ============================================================================
// Complete Default Settings
// ============================================================================

/**
 * Complete Default Application Settings
 * This is the master default object used for initialization
 */
export const DEFAULT_SETTINGS: AppSettings = {
  appearance: DEFAULT_APPEARANCE,
  sound: DEFAULT_SOUND,
  notifications: DEFAULT_NOTIFICATIONS,
  privacy: DEFAULT_PRIVACY,
  chat: DEFAULT_CHAT,
  personality: DEFAULT_PERSONALITY,
  accessibility: DEFAULT_ACCESSIBILITY,
  parental: DEFAULT_PARENTAL,
  advanced: DEFAULT_ADVANCED,
  window: DEFAULT_WINDOW,
  metadata: DEFAULT_METADATA,
};

// ============================================================================
// Preset Configurations
// ============================================================================

/**
 * Kid-Friendly Preset
 * Enhanced safety and parental controls
 */
export const KID_FRIENDLY_PRESET: Partial<AppSettings> = {
  privacy: {
    ...DEFAULT_PRIVACY,
    safetyLevel: 'high',
    parentalControlsEnabled: true,
  },
  chat: {
    ...DEFAULT_CHAT,
    dailyChatTimeLimit: 60, // 1 hour
  },
  parental: {
    ...DEFAULT_PARENTAL,
    parentalControlsActive: true,
    dailyTimeLimitEnabled: true,
    dailyTimeLimitMinutes: 60,
    quietHoursEnabled: true,
    parentDashboardEnabled: true,
  },
};

/**
 * Teen Preset
 * More freedom with moderate safety
 */
export const TEEN_PRESET: Partial<AppSettings> = {
  privacy: {
    ...DEFAULT_PRIVACY,
    safetyLevel: 'medium',
  },
  chat: {
    ...DEFAULT_CHAT,
    dailyChatTimeLimit: undefined, // No limit
    responseLength: 'long',
  },
  personality: {
    ...DEFAULT_PERSONALITY,
    humorLevel: 0.8,
    formalityLevel: 0.2,
  },
};

/**
 * Minimal Preset
 * Performance-focused, minimal features
 */
export const MINIMAL_PRESET: Partial<AppSettings> = {
  appearance: {
    ...DEFAULT_APPEARANCE,
    enableAnimations: false,
    enableParticles: false,
    compactMode: true,
  },
  sound: {
    ...DEFAULT_SOUND,
    soundEnabled: false,
  },
  advanced: {
    ...DEFAULT_ADVANCED,
    enableCaching: false,
    preloadMessages: false,
  },
};

/**
 * Accessibility Preset
 * Enhanced accessibility features
 */
export const ACCESSIBILITY_PRESET: Partial<AppSettings> = {
  appearance: {
    ...DEFAULT_APPEARANCE,
    fontSize: 'large',
    reduceMotion: true,
  },
  accessibility: {
    ...DEFAULT_ACCESSIBILITY,
    highContrast: true,
    largeText: true,
    reduceMotion: true,
    increaseLineSpacing: true,
    slowAnimations: true,
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get default value for a specific setting category
 */
export function getDefaultCategory(category: keyof AppSettings): any {
  return DEFAULT_SETTINGS[category];
}

/**
 * Get all preset names
 */
export function getPresetNames(): string[] {
  return ['default', 'kid-friendly', 'teen', 'minimal', 'accessibility'];
}

/**
 * Get preset configuration by name
 */
export function getPreset(name: string): Partial<AppSettings> {
  switch (name.toLowerCase()) {
    case 'kid-friendly':
      return KID_FRIENDLY_PRESET;
    case 'teen':
      return TEEN_PRESET;
    case 'minimal':
      return MINIMAL_PRESET;
    case 'accessibility':
      return ACCESSIBILITY_PRESET;
    case 'default':
    default:
      return DEFAULT_SETTINGS;
  }
}

/**
 * Merge preset with default settings
 */
export function mergeWithDefaults(preset: Partial<AppSettings>): AppSettings {
  return {
    appearance: { ...DEFAULT_APPEARANCE, ...preset.appearance },
    sound: { ...DEFAULT_SOUND, ...preset.sound },
    notifications: { ...DEFAULT_NOTIFICATIONS, ...preset.notifications },
    privacy: { ...DEFAULT_PRIVACY, ...preset.privacy },
    chat: { ...DEFAULT_CHAT, ...preset.chat },
    personality: { ...DEFAULT_PERSONALITY, ...preset.personality },
    accessibility: { ...DEFAULT_ACCESSIBILITY, ...preset.accessibility },
    parental: { ...DEFAULT_PARENTAL, ...preset.parental },
    advanced: { ...DEFAULT_ADVANCED, ...preset.advanced },
    window: { ...DEFAULT_WINDOW, ...preset.window },
    metadata: { ...DEFAULT_METADATA, ...preset.metadata },
  };
}

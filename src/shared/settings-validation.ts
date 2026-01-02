/**
 * Settings Validation
 * Validation functions and type guards for settings
 *
 * This module provides comprehensive validation for all settings
 * to ensure data integrity and prevent invalid configurations.
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
  SettingsValidationError,
  SettingsValidationResult,
  Theme,
  ColorTheme,
  SafetyLevel,
  FontSize,
} from './settings-schema';
import {
  isTheme,
  isColorTheme,
  isSafetyLevel,
  isFontSize,
  isNormalizedValue,
  MAX_CHAT_HISTORY_DAYS,
  MAX_MESSAGE_HISTORY,
  MAX_CACHE_SIZE_MB,
  MAX_DAILY_TIME_LIMIT_MINUTES,
} from './settings-schema';

// ============================================================================
// Validation Helpers
// ============================================================================

/**
 * Create a validation error
 */
function createError(
  path: string,
  message: string,
  value: any,
  expected?: string
): SettingsValidationError {
  return { path, message, value, expected };
}

/**
 * Validate a boolean value
 */
function validateBoolean(
  value: any,
  path: string,
  errors: SettingsValidationError[]
): boolean {
  if (typeof value !== 'boolean') {
    errors.push(createError(path, 'Must be a boolean', value, 'boolean'));
    return false;
  }
  return true;
}

/**
 * Validate a number value
 */
function validateNumber(
  value: any,
  path: string,
  errors: SettingsValidationError[],
  min?: number,
  max?: number
): boolean {
  if (typeof value !== 'number' || isNaN(value)) {
    errors.push(createError(path, 'Must be a number', value, 'number'));
    return false;
  }

  if (min !== undefined && value < min) {
    errors.push(createError(path, `Must be at least ${min}`, value, `>= ${min}`));
    return false;
  }

  if (max !== undefined && value > max) {
    errors.push(createError(path, `Must be at most ${max}`, value, `<= ${max}`));
    return false;
  }

  return true;
}

/**
 * Validate a string value
 */
function validateString(
  value: any,
  path: string,
  errors: SettingsValidationError[],
  minLength?: number,
  maxLength?: number
): boolean {
  if (typeof value !== 'string') {
    errors.push(createError(path, 'Must be a string', value, 'string'));
    return false;
  }

  if (minLength !== undefined && value.length < minLength) {
    errors.push(createError(path, `Must be at least ${minLength} characters`, value));
    return false;
  }

  if (maxLength !== undefined && value.length > maxLength) {
    errors.push(createError(path, `Must be at most ${maxLength} characters`, value));
    return false;
  }

  return true;
}

/**
 * Validate an optional value
 */
function validateOptional<T>(
  value: T | undefined,
  path: string,
  validator: (val: T, path: string, errors: SettingsValidationError[]) => boolean,
  errors: SettingsValidationError[]
): boolean {
  if (value === undefined) {
    return true; // Optional, so undefined is valid
  }
  return validator(value, path, errors);
}

/**
 * Validate an enum value
 */
function validateEnum<T>(
  value: any,
  path: string,
  validValues: readonly T[],
  errors: SettingsValidationError[]
): boolean {
  if (!validValues.includes(value)) {
    errors.push(
      createError(
        path,
        `Invalid value`,
        value,
        validValues.map(String).join(' | ')
      )
    );
    return false;
  }
  return true;
}

/**
 * Validate time format (HH:MM)
 */
function validateTimeFormat(
  value: any,
  path: string,
  errors: SettingsValidationError[]
): boolean {
  if (typeof value !== 'string') {
    errors.push(createError(path, 'Must be a string', value, 'HH:MM'));
    return false;
  }

  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;
  if (!timeRegex.test(value)) {
    errors.push(createError(path, 'Invalid time format', value, 'HH:MM (24-hour)'));
    return false;
  }

  return true;
}

// ============================================================================
// Category Validators
// ============================================================================

/**
 * Validate Appearance Settings
 */
export function validateAppearance(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'appearance';
  let valid = true;

  // Theme
  if (!validateEnum(settings.theme, `${base}.theme`, ['light', 'dark', 'auto'], errors)) {
    valid = false;
  }

  // ColorTheme
  if (!validateEnum(
    settings.colorTheme,
    `${base}.colorTheme`,
    ['purple', 'blue', 'green', 'pink', 'orange', 'red', 'teal', 'indigo'],
    errors
  )) {
    valid = false;
  }

  // FontSize
  if (!validateEnum(
    settings.fontSize,
    `${base}.fontSize`,
    ['small', 'medium', 'large', 'x-large'],
    errors
  )) {
    valid = false;
  }

  // Booleans
  valid = validateBoolean(settings.compactMode, `${base}.compactMode`, errors) && valid;
  valid = validateBoolean(settings.showSidebar, `${base}.showSidebar`, errors) && valid;
  valid = validateBoolean(settings.sidebarCollapsed, `${base}.sidebarCollapsed`, errors) && valid;
  valid = validateBoolean(settings.enableAnimations, `${base}.enableAnimations`, errors) && valid;
  valid = validateBoolean(settings.enableParticles, `${base}.enableParticles`, errors) && valid;
  valid = validateBoolean(settings.reduceMotion, `${base}.reduceMotion`, errors) && valid;
  valid = validateBoolean(settings.showAvatarInChat, `${base}.showAvatarInChat`, errors) && valid;

  // Optional strings
  if (settings.avatarId !== undefined) {
    valid = validateString(settings.avatarId, `${base}.avatarId`, errors) && valid;
  }

  return valid;
}

/**
 * Validate Sound Settings
 */
export function validateSound(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'sound';
  let valid = true;

  // Booleans
  valid = validateBoolean(settings.soundEnabled, `${base}.soundEnabled`, errors) && valid;
  valid = validateBoolean(settings.messageSound, `${base}.messageSound`, errors) && valid;
  valid = validateBoolean(settings.achievementSound, `${base}.achievementSound`, errors) && valid;
  valid = validateBoolean(settings.levelUpSound, `${base}.levelUpSound`, errors) && valid;
  valid = validateBoolean(settings.clickSound, `${base}.clickSound`, errors) && valid;
  valid = validateBoolean(settings.errorSound, `${base}.errorSound`, errors) && valid;

  // Volume levels (0.0 - 1.0)
  valid = validateNumber(settings.masterVolume, `${base}.masterVolume`, errors, 0, 1) && valid;
  valid = validateNumber(settings.messageSoundVolume, `${base}.messageSoundVolume`, errors, 0, 1) && valid;
  valid = validateNumber(settings.achievementSoundVolume, `${base}.achievementSoundVolume`, errors, 0, 1) && valid;
  valid = validateNumber(settings.levelUpSoundVolume, `${base}.levelUpSoundVolume`, errors, 0, 1) && valid;
  valid = validateNumber(settings.clickSoundVolume, `${base}.clickSoundVolume`, errors, 0, 1) && valid;
  valid = validateNumber(settings.errorSoundVolume, `${base}.errorSoundVolume`, errors, 0, 1) && valid;

  return valid;
}

/**
 * Validate Notification Settings
 */
export function validateNotifications(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'notifications';
  let valid = true;

  // Booleans
  valid = validateBoolean(settings.notificationsEnabled, `${base}.notificationsEnabled`, errors) && valid;
  valid = validateBoolean(settings.showDesktopNotifications, `${base}.showDesktopNotifications`, errors) && valid;
  valid = validateBoolean(settings.emailNotificationsEnabled, `${base}.emailNotificationsEnabled`, errors) && valid;
  valid = validateBoolean(settings.notifyOnNewMessage, `${base}.notifyOnNewMessage`, errors) && valid;
  valid = validateBoolean(settings.notifyOnAchievement, `${base}.notifyOnAchievement`, errors) && valid;
  valid = validateBoolean(settings.notifyOnLevelUp, `${base}.notifyOnLevelUp`, errors) && valid;
  valid = validateBoolean(settings.notifyOnStreak, `${base}.notifyOnStreak`, errors) && valid;
  valid = validateBoolean(settings.weeklyReportEnabled, `${base}.weeklyReportEnabled`, errors) && valid;

  // Numbers
  valid = validateNumber(settings.weeklyReportDay, `${base}.weeklyReportDay`, errors, 0, 6) && valid;

  // Optional email
  if (settings.parentEmail !== undefined) {
    valid = validateString(settings.parentEmail, `${base}.parentEmail`, errors, 5, 254) && valid;
    // Basic email validation
    if (typeof settings.parentEmail === 'string' && !settings.parentEmail.includes('@')) {
      errors.push(createError(`${base}.parentEmail`, 'Invalid email format', settings.parentEmail));
      valid = false;
    }
  }

  return valid;
}

/**
 * Validate Privacy Settings
 */
export function validatePrivacy(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'privacy';
  let valid = true;

  // Booleans
  valid = validateBoolean(settings.dataCollectionEnabled, `${base}.dataCollectionEnabled`, errors) && valid;
  valid = validateBoolean(settings.analyticsEnabled, `${base}.analyticsEnabled`, errors) && valid;
  valid = validateBoolean(settings.crashReportsEnabled, `${base}.crashReportsEnabled`, errors) && valid;
  valid = validateBoolean(settings.parentalControlsEnabled, `${base}.parentalControlsEnabled`, errors) && valid;
  valid = validateBoolean(settings.requireParentApproval, `${base}.requireParentApproval`, errors) && valid;
  valid = validateBoolean(settings.profanityFilterEnabled, `${base}.profanityFilterEnabled`, errors) && valid;
  valid = validateBoolean(settings.bullyingDetectionEnabled, `${base}.bullyingDetectionEnabled`, errors) && valid;
  valid = validateBoolean(settings.crisisDetectionEnabled, `${base}.crisisDetectionEnabled`, errors) && valid;
  valid = validateBoolean(settings.inappropriateContentFilterEnabled, `${base}.inappropriateContentFilterEnabled`, errors) && valid;
  valid = validateBoolean(settings.retainChatHistory, `${base}.retainChatHistory`, errors) && valid;
  valid = validateBoolean(settings.autoDeleteOldChats, `${base}.autoDeleteOldChats`, errors) && valid;

  // SafetyLevel
  if (!validateEnum(
    settings.safetyLevel,
    `${base}.safetyLevel`,
    ['low', 'medium', 'high', 'strict'],
    errors
  )) {
    valid = false;
  }

  // Numbers
  valid = validateNumber(settings.chatHistoryDays, `${base}.chatHistoryDays`, errors, 1, MAX_CHAT_HISTORY_DAYS) && valid;

  return valid;
}

/**
 * Validate Chat Settings
 */
export function validateChat(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'chat';
  let valid = true;

  // Booleans
  valid = validateBoolean(settings.autoStartConversation, `${base}.autoStartConversation`, errors) && valid;
  valid = validateBoolean(settings.showTypingIndicator, `${base}.showTypingIndicator`, errors) && valid;
  valid = validateBoolean(settings.enableAutoCorrect, `${base}.enableAutoCorrect`, errors) && valid;
  valid = validateBoolean(settings.saveConversations, `${base}.saveConversations`, errors) && valid;
  valid = validateBoolean(settings.exportConversationsEnabled, `${base}.exportConversationsEnabled`, errors) && valid;
  valid = validateBoolean(settings.useCasualLanguage, `${base}.useCasualLanguage`, errors) && valid;
  valid = validateBoolean(settings.useEmojis, `${base}.useEmojis`, errors) && valid;

  // Numbers
  valid = validateNumber(settings.maxMessageHistory, `${base}.maxMessageHistory`, errors, 10, MAX_MESSAGE_HISTORY) && valid;
  valid = validateNumber(settings.chatSessionTimeout, `${base}.chatSessionTimeout`, errors, 5, 1440) && valid;
  valid = validateNumber(settings.reminderInterval, `${base}.reminderInterval`, errors, 5, 1440) && valid;

  // Optional time limit
  if (settings.dailyChatTimeLimit !== undefined) {
    valid = validateNumber(settings.dailyChatTimeLimit, `${base}.dailyChatTimeLimit`, errors, 10, MAX_DAILY_TIME_LIMIT_MINUTES) && valid;
  }

  // Enums
  if (!validateEnum(
    settings.responseSpeed,
    `${base}.responseSpeed`,
    ['slow', 'medium', 'fast'],
    errors
  )) {
    valid = false;
  }

  if (!validateEnum(
    settings.responseLength,
    `${base}.responseLength`,
    ['short', 'medium', 'long'],
    errors
  )) {
    valid = false;
  }

  return valid;
}

/**
 * Validate Personality Settings
 */
export function validatePersonality(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'personality';
  let valid = true;

  // Strings
  valid = validateString(settings.botName, `${base}.botName`, errors, 1, 50) && valid;

  // Booleans
  valid = validateBoolean(settings.allowNameChange, `${base}.allowNameChange`, errors) && valid;
  valid = validateBoolean(settings.enableQuirks, `${base}.enableQuirks`, errors) && valid;
  valid = validateBoolean(settings.enableCatchphrases, `${base}.enableCatchphrases`, errors) && valid;
  valid = validateBoolean(settings.enableStorytelling, `${base}.enableStorytelling`, errors) && valid;
  valid = validateBoolean(settings.enableJokes, `${base}.enableJokes`, errors) && valid;
  valid = validateBoolean(settings.adaptToUserStyle, `${base}.adaptToUserStyle`, errors) && valid;
  valid = validateBoolean(settings.rememberConversations, `${base}.rememberConversations`, errors) && valid;
  valid = validateBoolean(settings.evolveOverTime, `${base}.evolveOverTime`, errors) && valid;

  // Trait levels (0.0 - 1.0)
  valid = validateNumber(settings.humorLevel, `${base}.humorLevel`, errors, 0, 1) && valid;
  valid = validateNumber(settings.energyLevel, `${base}.energyLevel`, errors, 0, 1) && valid;
  valid = validateNumber(settings.curiosityLevel, `${base}.curiosityLevel`, errors, 0, 1) && valid;
  valid = validateNumber(settings.formalityLevel, `${base}.formalityLevel`, errors, 0, 1) && valid;

  return valid;
}

/**
 * Validate Parental Settings
 */
export function validateParental(
  settings: any,
  errors: SettingsValidationError[] = []
): boolean {
  const base = 'parental';
  let valid = true;

  // Booleans
  valid = validateBoolean(settings.parentalControlsActive, `${base}.parentalControlsActive`, errors) && valid;
  valid = validateBoolean(settings.requirePasswordForSettings, `${base}.requirePasswordForSettings`, errors) && valid;
  valid = validateBoolean(settings.requirePasswordForExport, `${base}.requirePasswordForExport`, errors) && valid;
  valid = validateBoolean(settings.dailyTimeLimitEnabled, `${base}.dailyTimeLimitEnabled`, errors) && valid;
  valid = validateBoolean(settings.quietHoursEnabled, `${base}.quietHoursEnabled`, errors) && valid;
  valid = validateBoolean(settings.blockExternalLinks, `${base}.blockExternalLinks`, errors) && valid;
  valid = validateBoolean(settings.parentDashboardEnabled, `${base}.parentDashboardEnabled`, errors) && valid;
  valid = validateBoolean(settings.conversationReviewEnabled, `${base}.conversationReviewEnabled`, errors) && valid;

  // Numbers
  valid = validateNumber(settings.dailyTimeLimitMinutes, `${base}.dailyTimeLimitMinutes`, errors, 10, MAX_DAILY_TIME_LIMIT_MINUTES) && valid;

  // Time formats
  valid = validateTimeFormat(settings.quietHoursStart, `${base}.quietHoursStart`, errors) && valid;
  valid = validateTimeFormat(settings.quietHoursEnd, `${base}.quietHoursEnd`, errors) && valid;

  // SafetyLevel
  if (!validateEnum(
    settings.safetyAlertThreshold,
    `${base}.safetyAlertThreshold`,
    ['low', 'medium', 'high', 'strict'],
    errors
  )) {
    valid = false;
  }

  return valid;
}

/**
 * Validate complete AppSettings
 */
export function validateSettings(settings: any): SettingsValidationResult {
  const errors: SettingsValidationError[] = [];

  if (!settings || typeof settings !== 'object') {
    errors.push(createError('', 'Settings must be an object', settings));
    return { valid: false, errors };
  }

  let valid = true;

  // Validate each category
  if (settings.appearance) {
    valid = validateAppearance(settings.appearance, errors) && valid;
  }

  if (settings.sound) {
    valid = validateSound(settings.sound, errors) && valid;
  }

  if (settings.notifications) {
    valid = validateNotifications(settings.notifications, errors) && valid;
  }

  if (settings.privacy) {
    valid = validatePrivacy(settings.privacy, errors) && valid;
  }

  if (settings.chat) {
    valid = validateChat(settings.chat, errors) && valid;
  }

  if (settings.personality) {
    valid = validatePersonality(settings.personality, errors) && valid;
  }

  if (settings.parental) {
    valid = validateParental(settings.parental, errors) && valid;
  }

  return { valid, errors };
}

/**
 * Sanitize settings by removing invalid values
 * Invalid values are replaced with defaults
 */
export function sanitizeSettings(settings: Partial<AppSettings>, defaults: AppSettings): AppSettings {
  const result = { ...defaults };

  // Merge each category, validating as we go
  if (settings.appearance) {
    const errors: SettingsValidationError[] = [];
    if (validateAppearance(settings.appearance, errors)) {
      result.appearance = { ...defaults.appearance, ...settings.appearance };
    }
  }

  if (settings.sound) {
    const errors: SettingsValidationError[] = [];
    if (validateSound(settings.sound, errors)) {
      result.sound = { ...defaults.sound, ...settings.sound };
    }
  }

  if (settings.notifications) {
    const errors: SettingsValidationError[] = [];
    if (validateNotifications(settings.notifications, errors)) {
      result.notifications = { ...defaults.notifications, ...settings.notifications };
    }
  }

  if (settings.privacy) {
    const errors: SettingsValidationError[] = [];
    if (validatePrivacy(settings.privacy, errors)) {
      result.privacy = { ...defaults.privacy, ...settings.privacy };
    }
  }

  if (settings.chat) {
    const errors: SettingsValidationError[] = [];
    if (validateChat(settings.chat, errors)) {
      result.chat = { ...defaults.chat, ...settings.chat };
    }
  }

  if (settings.personality) {
    const errors: SettingsValidationError[] = [];
    if (validatePersonality(settings.personality, errors)) {
      result.personality = { ...defaults.personality, ...settings.personality };
    }
  }

  if (settings.parental) {
    const errors: SettingsValidationError[] = [];
    if (validateParental(settings.parental, errors)) {
      result.parental = { ...defaults.parental, ...settings.parental };
    }
  }

  return result;
}

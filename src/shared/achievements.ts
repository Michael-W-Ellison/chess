/**
 * Achievement System
 * Defines achievements, badges, and unlock conditions
 */

export type AchievementCategory =
  | 'conversation'
  | 'friendship'
  | 'learning'
  | 'creativity'
  | 'milestones'
  | 'special';

export type AchievementTier = 'bronze' | 'silver' | 'gold' | 'platinum' | 'diamond';

export interface UnlockCondition {
  type:
    | 'message_count' // Total messages sent
    | 'conversation_count' // Total conversations
    | 'daily_streak' // Consecutive days chatting
    | 'session_length' // Minutes in a single session
    | 'word_count' // Total words exchanged
    | 'topic_diversity' // Number of different topics discussed
    | 'emoji_usage' // Number of emojis used
    | 'questions_asked' // Number of questions asked
    | 'stories_shared' // Number of stories shared
    | 'profile_complete' // Profile completeness percentage
    | 'avatar_changes' // Number of avatar changes
    | 'time_of_day' // Chat at specific time
    | 'special_date' // Achievement on special date
    | 'custom'; // Custom condition

  value: number;
  description?: string;
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  emoji: string;
  category: AchievementCategory;
  tier: AchievementTier;
  condition: UnlockCondition;
  points: number;
  hidden?: boolean; // Secret achievements
  rarity?: 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary';
}

export const ACHIEVEMENTS: Achievement[] = [
  // CONVERSATION ACHIEVEMENTS
  {
    id: 'first_chat',
    name: 'First Words',
    description: 'Send your first message',
    emoji: '💬',
    category: 'conversation',
    tier: 'bronze',
    condition: { type: 'message_count', value: 1 },
    points: 10,
    rarity: 'common',
  },
  {
    id: 'chatty_10',
    name: 'Getting Chatty',
    description: 'Send 10 messages',
    emoji: '🗨️',
    category: 'conversation',
    tier: 'bronze',
    condition: { type: 'message_count', value: 10 },
    points: 25,
    rarity: 'common',
  },
  {
    id: 'chatty_50',
    name: 'Conversationalist',
    description: 'Send 50 messages',
    emoji: '💭',
    category: 'conversation',
    tier: 'silver',
    condition: { type: 'message_count', value: 50 },
    points: 50,
    rarity: 'uncommon',
  },
  {
    id: 'chatty_100',
    name: 'Chatterbox',
    description: 'Send 100 messages',
    emoji: '🎭',
    category: 'conversation',
    tier: 'gold',
    condition: { type: 'message_count', value: 100 },
    points: 100,
    rarity: 'rare',
  },
  {
    id: 'chatty_500',
    name: 'Master Communicator',
    description: 'Send 500 messages',
    emoji: '🎪',
    category: 'conversation',
    tier: 'platinum',
    condition: { type: 'message_count', value: 500 },
    points: 250,
    rarity: 'epic',
  },
  {
    id: 'chatty_1000',
    name: 'Legendary Talker',
    description: 'Send 1000 messages',
    emoji: '👑',
    category: 'conversation',
    tier: 'diamond',
    condition: { type: 'message_count', value: 1000 },
    points: 500,
    rarity: 'legendary',
  },

  // FRIENDSHIP ACHIEVEMENTS
  {
    id: 'first_session',
    name: 'New Friend',
    description: 'Complete your first chat session',
    emoji: '🤝',
    category: 'friendship',
    tier: 'bronze',
    condition: { type: 'conversation_count', value: 1 },
    points: 15,
    rarity: 'common',
  },
  {
    id: 'daily_streak_3',
    name: 'Regular Visitor',
    description: 'Chat for 3 days in a row',
    emoji: '🔥',
    category: 'friendship',
    tier: 'bronze',
    condition: { type: 'daily_streak', value: 3 },
    points: 30,
    rarity: 'uncommon',
  },
  {
    id: 'daily_streak_7',
    name: 'Week Warrior',
    description: 'Chat for 7 days in a row',
    emoji: '⭐',
    category: 'friendship',
    tier: 'silver',
    condition: { type: 'daily_streak', value: 7 },
    points: 75,
    rarity: 'rare',
  },
  {
    id: 'daily_streak_30',
    name: 'Monthly Marvel',
    description: 'Chat for 30 days in a row',
    emoji: '🌟',
    category: 'friendship',
    tier: 'gold',
    condition: { type: 'daily_streak', value: 30 },
    points: 200,
    rarity: 'epic',
  },
  {
    id: 'daily_streak_100',
    name: 'Dedicated Friend',
    description: 'Chat for 100 days in a row',
    emoji: '💎',
    category: 'friendship',
    tier: 'diamond',
    condition: { type: 'daily_streak', value: 100 },
    points: 500,
    rarity: 'legendary',
  },
  {
    id: 'long_session_30',
    name: 'Deep Conversation',
    description: 'Chat for 30 minutes straight',
    emoji: '⏰',
    category: 'friendship',
    tier: 'silver',
    condition: { type: 'session_length', value: 30 },
    points: 40,
    rarity: 'uncommon',
  },
  {
    id: 'long_session_60',
    name: 'Marathon Chatter',
    description: 'Chat for 1 hour straight',
    emoji: '⏳',
    category: 'friendship',
    tier: 'gold',
    condition: { type: 'session_length', value: 60 },
    points: 100,
    rarity: 'rare',
  },

  // LEARNING ACHIEVEMENTS
  {
    id: 'curious_10',
    name: 'Curious Mind',
    description: 'Ask 10 questions',
    emoji: '🤔',
    category: 'learning',
    tier: 'bronze',
    condition: { type: 'questions_asked', value: 10 },
    points: 25,
    rarity: 'common',
  },
  {
    id: 'curious_50',
    name: 'Inquisitive',
    description: 'Ask 50 questions',
    emoji: '❓',
    category: 'learning',
    tier: 'silver',
    condition: { type: 'questions_asked', value: 50 },
    points: 60,
    rarity: 'uncommon',
  },
  {
    id: 'curious_100',
    name: 'Question Master',
    description: 'Ask 100 questions',
    emoji: '🎓',
    category: 'learning',
    tier: 'gold',
    condition: { type: 'questions_asked', value: 100 },
    points: 150,
    rarity: 'rare',
  },
  {
    id: 'diverse_topics_5',
    name: 'Well Rounded',
    description: 'Discuss 5 different topics',
    emoji: '🌈',
    category: 'learning',
    tier: 'bronze',
    condition: { type: 'topic_diversity', value: 5 },
    points: 30,
    rarity: 'uncommon',
  },
  {
    id: 'diverse_topics_15',
    name: 'Renaissance Kid',
    description: 'Discuss 15 different topics',
    emoji: '🎨',
    category: 'learning',
    tier: 'silver',
    condition: { type: 'topic_diversity', value: 15 },
    points: 80,
    rarity: 'rare',
  },
  {
    id: 'diverse_topics_30',
    name: 'Universal Scholar',
    description: 'Discuss 30 different topics',
    emoji: '🌍',
    category: 'learning',
    tier: 'gold',
    condition: { type: 'topic_diversity', value: 30 },
    points: 200,
    rarity: 'epic',
  },

  // CREATIVITY ACHIEVEMENTS
  {
    id: 'storyteller_1',
    name: 'Once Upon a Time',
    description: 'Share your first story',
    emoji: '📖',
    category: 'creativity',
    tier: 'bronze',
    condition: { type: 'stories_shared', value: 1 },
    points: 20,
    rarity: 'common',
  },
  {
    id: 'storyteller_10',
    name: 'Story Weaver',
    description: 'Share 10 stories',
    emoji: '📚',
    category: 'creativity',
    tier: 'silver',
    condition: { type: 'stories_shared', value: 10 },
    points: 70,
    rarity: 'uncommon',
  },
  {
    id: 'storyteller_50',
    name: 'Master Narrator',
    description: 'Share 50 stories',
    emoji: '🎬',
    category: 'creativity',
    tier: 'gold',
    condition: { type: 'stories_shared', value: 50 },
    points: 180,
    rarity: 'rare',
  },
  {
    id: 'emoji_artist_50',
    name: 'Emoji Enthusiast',
    description: 'Use 50 emojis',
    emoji: '😊',
    category: 'creativity',
    tier: 'bronze',
    condition: { type: 'emoji_usage', value: 50 },
    points: 20,
    rarity: 'common',
  },
  {
    id: 'emoji_artist_200',
    name: 'Emoji Master',
    description: 'Use 200 emojis',
    emoji: '🎉',
    category: 'creativity',
    tier: 'silver',
    condition: { type: 'emoji_usage', value: 200 },
    points: 50,
    rarity: 'uncommon',
  },
  {
    id: 'wordsmith_1000',
    name: 'Wordsmith',
    description: 'Exchange 1,000 words',
    emoji: '✍️',
    category: 'creativity',
    tier: 'bronze',
    condition: { type: 'word_count', value: 1000 },
    points: 30,
    rarity: 'common',
  },
  {
    id: 'wordsmith_10000',
    name: 'Verbose Virtuoso',
    description: 'Exchange 10,000 words',
    emoji: '📝',
    category: 'creativity',
    tier: 'silver',
    condition: { type: 'word_count', value: 10000 },
    points: 100,
    rarity: 'uncommon',
  },
  {
    id: 'wordsmith_50000',
    name: 'Literary Legend',
    description: 'Exchange 50,000 words',
    emoji: '📜',
    category: 'creativity',
    tier: 'gold',
    condition: { type: 'word_count', value: 50000 },
    points: 250,
    rarity: 'rare',
  },

  // MILESTONE ACHIEVEMENTS
  {
    id: 'profile_complete',
    name: 'All Set Up',
    description: 'Complete your profile',
    emoji: '✅',
    category: 'milestones',
    tier: 'bronze',
    condition: { type: 'profile_complete', value: 100 },
    points: 25,
    rarity: 'common',
  },
  {
    id: 'avatar_collector_5',
    name: 'Style Explorer',
    description: 'Try 5 different avatars',
    emoji: '🎭',
    category: 'milestones',
    tier: 'bronze',
    condition: { type: 'avatar_changes', value: 5 },
    points: 15,
    rarity: 'common',
  },
  {
    id: 'avatar_collector_20',
    name: 'Avatar Connoisseur',
    description: 'Try 20 different avatars',
    emoji: '🎨',
    category: 'milestones',
    tier: 'silver',
    condition: { type: 'avatar_changes', value: 20 },
    points: 40,
    rarity: 'uncommon',
  },
  {
    id: 'sessions_10',
    name: 'Regular Chatter',
    description: 'Complete 10 chat sessions',
    emoji: '🗓️',
    category: 'milestones',
    tier: 'bronze',
    condition: { type: 'conversation_count', value: 10 },
    points: 35,
    rarity: 'common',
  },
  {
    id: 'sessions_50',
    name: 'Veteran Chatter',
    description: 'Complete 50 chat sessions',
    emoji: '📅',
    category: 'milestones',
    tier: 'silver',
    condition: { type: 'conversation_count', value: 50 },
    points: 100,
    rarity: 'uncommon',
  },
  {
    id: 'sessions_100',
    name: 'Chat Champion',
    description: 'Complete 100 chat sessions',
    emoji: '🏆',
    category: 'milestones',
    tier: 'gold',
    condition: { type: 'conversation_count', value: 100 },
    points: 250,
    rarity: 'rare',
  },

  // SPECIAL ACHIEVEMENTS
  {
    id: 'early_bird',
    name: 'Early Bird',
    description: 'Chat before 8 AM',
    emoji: '🌅',
    category: 'special',
    tier: 'silver',
    condition: { type: 'time_of_day', value: 8, description: 'before_8am' },
    points: 30,
    rarity: 'uncommon',
    hidden: true,
  },
  {
    id: 'night_owl',
    name: 'Night Owl',
    description: 'Chat after 10 PM',
    emoji: '🦉',
    category: 'special',
    tier: 'silver',
    condition: { type: 'time_of_day', value: 22, description: 'after_10pm' },
    points: 30,
    rarity: 'uncommon',
    hidden: true,
  },
  {
    id: 'weekend_warrior',
    name: 'Weekend Warrior',
    description: 'Chat on both Saturday and Sunday',
    emoji: '🎮',
    category: 'special',
    tier: 'bronze',
    condition: { type: 'custom', value: 1, description: 'weekend_both_days' },
    points: 25,
    rarity: 'common',
  },
  {
    id: 'birthday_chat',
    name: 'Birthday Buddy',
    description: 'Chat on your birthday',
    emoji: '🎂',
    category: 'special',
    tier: 'gold',
    condition: { type: 'special_date', value: 1, description: 'birthday' },
    points: 100,
    rarity: 'epic',
    hidden: true,
  },
  {
    id: 'new_year',
    name: 'New Year, New Chat',
    description: 'Chat on New Year\'s Day',
    emoji: '🎊',
    category: 'special',
    tier: 'gold',
    condition: { type: 'special_date', value: 1, description: 'new_year' },
    points: 50,
    rarity: 'rare',
    hidden: true,
  },
  {
    id: 'perfect_week',
    name: 'Perfect Week',
    description: 'Chat every day for a week',
    emoji: '🌟',
    category: 'special',
    tier: 'platinum',
    condition: { type: 'daily_streak', value: 7 },
    points: 100,
    rarity: 'epic',
  },
];

/**
 * Tier colors for visual representation
 */
export const TIER_COLORS: Record<AchievementTier, { bg: string; text: string; border: string; glow: string }> = {
  bronze: {
    bg: '#CD7F32',
    text: '#FFFFFF',
    border: '#A0522D',
    glow: 'rgba(205, 127, 50, 0.3)',
  },
  silver: {
    bg: '#C0C0C0',
    text: '#1F2937',
    border: '#A9A9A9',
    glow: 'rgba(192, 192, 192, 0.3)',
  },
  gold: {
    bg: '#FFD700',
    text: '#1F2937',
    border: '#DAA520',
    glow: 'rgba(255, 215, 0, 0.3)',
  },
  platinum: {
    bg: '#E5E4E2',
    text: '#1F2937',
    border: '#BCC6CC',
    glow: 'rgba(229, 228, 226, 0.3)',
  },
  diamond: {
    bg: '#B9F2FF',
    text: '#1F2937',
    border: '#87CEEB',
    glow: 'rgba(185, 242, 255, 0.3)',
  },
};

/**
 * Rarity colors for visual representation
 */
export const RARITY_COLORS: Record<string, { bg: string; text: string }> = {
  common: { bg: '#9CA3AF', text: '#FFFFFF' },
  uncommon: { bg: '#10B981', text: '#FFFFFF' },
  rare: { bg: '#3B82F6', text: '#FFFFFF' },
  epic: { bg: '#8B5CF6', text: '#FFFFFF' },
  legendary: { bg: '#F59E0B', text: '#FFFFFF' },
};

/**
 * Category names for display
 */
export const CATEGORY_NAMES: Record<AchievementCategory, string> = {
  conversation: 'Conversation',
  friendship: 'Friendship',
  learning: 'Learning',
  creativity: 'Creativity',
  milestones: 'Milestones',
  special: 'Special',
};

/**
 * Get achievement by ID
 */
export const getAchievementById = (id: string): Achievement | undefined => {
  return ACHIEVEMENTS.find((achievement) => achievement.id === id);
};

/**
 * Get achievements by category
 */
export const getAchievementsByCategory = (category: AchievementCategory): Achievement[] => {
  return ACHIEVEMENTS.filter((achievement) => achievement.category === category);
};

/**
 * Get all achievement categories
 */
export const getAchievementCategories = (): AchievementCategory[] => {
  return Array.from(new Set(ACHIEVEMENTS.map((a) => a.category)));
};

/**
 * Calculate total points from achievements
 */
export const calculateTotalPoints = (unlockedIds: string[]): number => {
  return unlockedIds.reduce((total, id) => {
    const achievement = getAchievementById(id);
    return total + (achievement?.points || 0);
  }, 0);
};

/**
 * Get achievement progress percentage
 */
export const getAchievementProgress = (unlockedIds: string[]): number => {
  const visibleAchievements = ACHIEVEMENTS.filter((a) => !a.hidden);
  return Math.round((unlockedIds.length / visibleAchievements.length) * 100);
};

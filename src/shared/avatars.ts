/**
 * Avatar Data
 * Emoji-based avatars for user personalization
 */

export interface Avatar {
  id: string;
  emoji: string;
  name: string;
  category: AvatarCategory;
  color: string;  // Background color for avatar display
}

export type AvatarCategory = 'animals' | 'fantasy' | 'nature' | 'space' | 'food' | 'sports';

/**
 * Available avatars grouped by category
 */
export const AVATARS: Avatar[] = [
  // Animals
  { id: 'cat', emoji: '🐱', name: 'Cat', category: 'animals', color: '#FFF3CD' },
  { id: 'dog', emoji: '🐶', name: 'Dog', category: 'animals', color: '#FFDAB9' },
  { id: 'panda', emoji: '🐼', name: 'Panda', category: 'animals', color: '#E8F4F8' },
  { id: 'fox', emoji: '🦊', name: 'Fox', category: 'animals', color: '#FFE4CC' },
  { id: 'koala', emoji: '🐨', name: 'Koala', category: 'animals', color: '#E8E8E8' },
  { id: 'penguin', emoji: '🐧', name: 'Penguin', category: 'animals', color: '#E3F2FD' },
  { id: 'owl', emoji: '🦉', name: 'Owl', category: 'animals', color: '#F5E6D3' },
  { id: 'bunny', emoji: '🐰', name: 'Bunny', category: 'animals', color: '#FFE4E4' },
  { id: 'tiger', emoji: '🐯', name: 'Tiger', category: 'animals', color: '#FFE4B5' },
  { id: 'monkey', emoji: '🐵', name: 'Monkey', category: 'animals', color: '#F4D4A8' },
  { id: 'lion', emoji: '🦁', name: 'Lion', category: 'animals', color: '#FFEAA7' },
  { id: 'bear', emoji: '🐻', name: 'Bear', category: 'animals', color: '#D4A373' },

  // Fantasy
  { id: 'unicorn', emoji: '🦄', name: 'Unicorn', category: 'fantasy', color: '#F8EDFF' },
  { id: 'dragon', emoji: '🐉', name: 'Dragon', category: 'fantasy', color: '#FFE5E5' },
  { id: 'wizard', emoji: '🧙', name: 'Wizard', category: 'fantasy', color: '#E6E6FA' },
  { id: 'fairy', emoji: '🧚', name: 'Fairy', category: 'fantasy', color: '#FFF0F5' },
  { id: 'mermaid', emoji: '🧜', name: 'Mermaid', category: 'fantasy', color: '#E0F7FA' },
  { id: 'vampire', emoji: '🧛', name: 'Vampire', category: 'fantasy', color: '#FFE4E1' },
  { id: 'zombie', emoji: '🧟', name: 'Zombie', category: 'fantasy', color: '#E8F5E9' },
  { id: 'robot', emoji: '🤖', name: 'Robot', category: 'fantasy', color: '#E3F2FD' },
  { id: 'alien', emoji: '👽', name: 'Alien', category: 'fantasy', color: '#E8F5E9' },
  { id: 'ghost', emoji: '👻', name: 'Ghost', category: 'fantasy', color: '#F5F5F5' },

  // Nature
  { id: 'flower', emoji: '🌸', name: 'Flower', category: 'nature', color: '#FFE4F0' },
  { id: 'tree', emoji: '🌳', name: 'Tree', category: 'nature', color: '#E8F5E9' },
  { id: 'cactus', emoji: '🌵', name: 'Cactus', category: 'nature', color: '#E0F2E9' },
  { id: 'mushroom', emoji: '🍄', name: 'Mushroom', category: 'nature', color: '#FFE4E4' },
  { id: 'leaf', emoji: '🍃', name: 'Leaf', category: 'nature', color: '#E8F5E9' },
  { id: 'sunflower', emoji: '🌻', name: 'Sunflower', category: 'nature', color: '#FFF8DC' },
  { id: 'rose', emoji: '🌹', name: 'Rose', category: 'nature', color: '#FFE4E8' },
  { id: 'tulip', emoji: '🌷', name: 'Tulip', category: 'nature', color: '#FFE4F5' },

  // Space
  { id: 'rocket', emoji: '🚀', name: 'Rocket', category: 'space', color: '#E3F2FD' },
  { id: 'planet', emoji: '🪐', name: 'Planet', category: 'space', color: '#FFE4CC' },
  { id: 'star', emoji: '⭐', name: 'Star', category: 'space', color: '#FFF9C4' },
  { id: 'moon', emoji: '🌙', name: 'Moon', category: 'space', color: '#FFF8DC' },
  { id: 'sun', emoji: '☀️', name: 'Sun', category: 'space', color: '#FFFACD' },
  { id: 'comet', emoji: '☄️', name: 'Comet', category: 'space', color: '#FFE4B5' },
  { id: 'satellite', emoji: '🛰️', name: 'Satellite', category: 'space', color: '#E0E0E0' },
  { id: 'ufo', emoji: '🛸', name: 'UFO', category: 'space', color: '#E8F5E9' },

  // Food
  { id: 'pizza', emoji: '🍕', name: 'Pizza', category: 'food', color: '#FFE4CC' },
  { id: 'donut', emoji: '🍩', name: 'Donut', category: 'food', color: '#FFE4F0' },
  { id: 'ice-cream', emoji: '🍦', name: 'Ice Cream', category: 'food', color: '#FFF0F5' },
  { id: 'cookie', emoji: '🍪', name: 'Cookie', category: 'food', color: '#F5DEB3' },
  { id: 'cupcake', emoji: '🧁', name: 'Cupcake', category: 'food', color: '#FFE4F5' },
  { id: 'burger', emoji: '🍔', name: 'Burger', category: 'food', color: '#FFEAA7' },
  { id: 'taco', emoji: '🌮', name: 'Taco', category: 'food', color: '#FFF8DC' },
  { id: 'sushi', emoji: '🍣', name: 'Sushi', category: 'food', color: '#FFE4E4' },

  // Sports
  { id: 'soccer', emoji: '⚽', name: 'Soccer', category: 'sports', color: '#E8F5E9' },
  { id: 'basketball', emoji: '🏀', name: 'Basketball', category: 'sports', color: '#FFE4CC' },
  { id: 'football', emoji: '🏈', name: 'Football', category: 'sports', color: '#F5E6D3' },
  { id: 'baseball', emoji: '⚾', name: 'Baseball', category: 'sports', color: '#FFFFFF' },
  { id: 'tennis', emoji: '🎾', name: 'Tennis', category: 'sports', color: '#FFFACD' },
  { id: 'skateboard', emoji: '🛹', name: 'Skateboard', category: 'sports', color: '#FFE4B5' },
  { id: 'trophy', emoji: '🏆', name: 'Trophy', category: 'sports', color: '#FFEAA7' },
  { id: 'medal', emoji: '🏅', name: 'Medal', category: 'sports', color: '#FFD700' },
];

/**
 * Get avatar by ID
 */
export const getAvatarById = (id: string): Avatar | undefined => {
  return AVATARS.find(avatar => avatar.id === id);
};

/**
 * Get avatars by category
 */
export const getAvatarsByCategory = (category: AvatarCategory): Avatar[] => {
  return AVATARS.filter(avatar => avatar.category === category);
};

/**
 * Get all categories
 */
export const getCategories = (): AvatarCategory[] => {
  return ['animals', 'fantasy', 'nature', 'space', 'food', 'sports'];
};

/**
 * Get category display name
 */
export const getCategoryName = (category: AvatarCategory): string => {
  const names: Record<AvatarCategory, string> = {
    animals: '🐾 Animals',
    fantasy: '✨ Fantasy',
    nature: '🌿 Nature',
    space: '🌌 Space',
    food: '🍕 Food',
    sports: '⚽ Sports',
  };
  return names[category];
};

/**
 * Default avatar (used when no avatar is selected)
 */
export const DEFAULT_AVATAR: Avatar = AVATARS[0]; // Cat

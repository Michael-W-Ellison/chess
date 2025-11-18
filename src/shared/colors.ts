/**
 * Color System
 * Preset color themes for UI customization
 */

export type ColorTheme = {
  id: string;
  name: string;
  emoji: string;
  primary: string;
  primaryDark: string;
  primaryLight: string;
  primaryLighter: string;
  hover: string;
  hoverDark: string;
  focus: string;
  focusDark: string;
  text: string;
  textDark: string;
};

export const COLOR_THEMES: ColorTheme[] = [
  {
    id: 'blue',
    name: 'Ocean Blue',
    emoji: '🌊',
    primary: '#3B82F6',
    primaryDark: '#2563EB',
    primaryLight: '#60A5FA',
    primaryLighter: '#DBEAFE',
    hover: '#2563EB',
    hoverDark: '#1D4ED8',
    focus: '#3B82F6',
    focusDark: '#2563EB',
    text: '#1E40AF',
    textDark: '#93C5FD',
  },
  {
    id: 'purple',
    name: 'Royal Purple',
    emoji: '💜',
    primary: '#9333EA',
    primaryDark: '#7C3AED',
    primaryLight: '#A855F7',
    primaryLighter: '#F3E8FF',
    hover: '#7C3AED',
    hoverDark: '#6B21A8',
    focus: '#9333EA',
    focusDark: '#7C3AED',
    text: '#6B21A8',
    textDark: '#C084FC',
  },
  {
    id: 'green',
    name: 'Forest Green',
    emoji: '🌲',
    primary: '#10B981',
    primaryDark: '#059669',
    primaryLight: '#34D399',
    primaryLighter: '#D1FAE5',
    hover: '#059669',
    hoverDark: '#047857',
    focus: '#10B981',
    focusDark: '#059669',
    text: '#047857',
    textDark: '#6EE7B7',
  },
  {
    id: 'orange',
    name: 'Sunset Orange',
    emoji: '🌅',
    primary: '#F59E0B',
    primaryDark: '#D97706',
    primaryLight: '#FBBF24',
    primaryLighter: '#FEF3C7',
    hover: '#D97706',
    hoverDark: '#B45309',
    focus: '#F59E0B',
    focusDark: '#D97706',
    text: '#B45309',
    textDark: '#FCD34D',
  },
  {
    id: 'pink',
    name: 'Cherry Pink',
    emoji: '🌸',
    primary: '#EC4899',
    primaryDark: '#DB2777',
    primaryLight: '#F472B6',
    primaryLighter: '#FCE7F3',
    hover: '#DB2777',
    hoverDark: '#BE185D',
    focus: '#EC4899',
    focusDark: '#DB2777',
    text: '#BE185D',
    textDark: '#F9A8D4',
  },
  {
    id: 'teal',
    name: 'Ocean Teal',
    emoji: '🏝️',
    primary: '#14B8A6',
    primaryDark: '#0D9488',
    primaryLight: '#2DD4BF',
    primaryLighter: '#CCFBF1',
    hover: '#0D9488',
    hoverDark: '#0F766E',
    focus: '#14B8A6',
    focusDark: '#0D9488',
    text: '#0F766E',
    textDark: '#5EEAD4',
  },
  {
    id: 'red',
    name: 'Ruby Red',
    emoji: '💎',
    primary: '#EF4444',
    primaryDark: '#DC2626',
    primaryLight: '#F87171',
    primaryLighter: '#FEE2E2',
    hover: '#DC2626',
    hoverDark: '#B91C1C',
    focus: '#EF4444',
    focusDark: '#DC2626',
    text: '#B91C1C',
    textDark: '#FCA5A5',
  },
  {
    id: 'indigo',
    name: 'Midnight Indigo',
    emoji: '🌙',
    primary: '#6366F1',
    primaryDark: '#4F46E5',
    primaryLight: '#818CF8',
    primaryLighter: '#E0E7FF',
    hover: '#4F46E5',
    hoverDark: '#4338CA',
    focus: '#6366F1',
    focusDark: '#4F46E5',
    text: '#4338CA',
    textDark: '#A5B4FC',
  },
];

export const DEFAULT_COLOR_THEME = COLOR_THEMES[0]; // Blue

/**
 * Get color theme by ID
 */
export const getColorThemeById = (id: string): ColorTheme | undefined => {
  return COLOR_THEMES.find((theme) => theme.id === id);
};

/**
 * Get color theme by ID or return default
 */
export const getColorThemeByIdOrDefault = (id: string): ColorTheme => {
  return getColorThemeById(id) || DEFAULT_COLOR_THEME;
};

/**
 * ColorContext
 * Manages color theme selection and applies CSS custom properties
 */

import React, { createContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
  ColorTheme,
  DEFAULT_COLOR_THEME,
  getColorThemeByIdOrDefault,
} from '../../shared/colors';

const COLOR_STORAGE_KEY = 'app_color_theme';

interface ColorContextType {
  colorTheme: ColorTheme;
  setColorTheme: (themeId: string) => void;
}

export const ColorContext = createContext<ColorContextType | undefined>(undefined);

interface ColorProviderProps {
  children: ReactNode;
}

export const ColorProvider: React.FC<ColorProviderProps> = ({ children }) => {
  const [colorTheme, setColorThemeState] = useState<ColorTheme>(DEFAULT_COLOR_THEME);

  /**
   * Apply color theme to document root as CSS custom properties
   */
  const applyColorTheme = useCallback((theme: ColorTheme) => {
    const root = document.documentElement;
    root.style.setProperty('--color-primary', theme.primary);
    root.style.setProperty('--color-primary-dark', theme.primaryDark);
    root.style.setProperty('--color-primary-light', theme.primaryLight);
    root.style.setProperty('--color-primary-lighter', theme.primaryLighter);
    root.style.setProperty('--color-hover', theme.hover);
    root.style.setProperty('--color-hover-dark', theme.hoverDark);
    root.style.setProperty('--color-focus', theme.focus);
    root.style.setProperty('--color-focus-dark', theme.focusDark);
    root.style.setProperty('--color-text', theme.text);
    root.style.setProperty('--color-text-dark', theme.textDark);
  }, []);

  /**
   * Initialize color theme from localStorage
   */
  useEffect(() => {
    try {
      const stored = localStorage.getItem(COLOR_STORAGE_KEY);
      if (stored) {
        const theme = getColorThemeByIdOrDefault(stored);
        setColorThemeState(theme);
        applyColorTheme(theme);
      } else {
        applyColorTheme(DEFAULT_COLOR_THEME);
      }
    } catch (error) {
      console.error('Failed to load color theme:', error);
      applyColorTheme(DEFAULT_COLOR_THEME);
    }
  }, [applyColorTheme]);

  /**
   * Set color theme and persist to localStorage
   */
  const setColorTheme = useCallback(
    (themeId: string) => {
      try {
        const theme = getColorThemeByIdOrDefault(themeId);
        setColorThemeState(theme);
        applyColorTheme(theme);
        localStorage.setItem(COLOR_STORAGE_KEY, theme.id);
      } catch (error) {
        console.error('Failed to save color theme:', error);
      }
    },
    [applyColorTheme]
  );

  return (
    <ColorContext.Provider value={{ colorTheme, setColorTheme }}>
      {children}
    </ColorContext.Provider>
  );
};

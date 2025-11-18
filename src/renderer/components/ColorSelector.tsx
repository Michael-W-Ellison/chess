/**
 * ColorSelector Component
 * Interactive color theme selection with preview
 */

import React, { useState } from 'react';
import { COLOR_THEMES, ColorTheme } from '../../shared/colors';
import { useColor } from '../hooks/useColor';

interface ColorSelectorProps {
  compact?: boolean;
}

export const ColorSelector: React.FC<ColorSelectorProps> = ({ compact = false }) => {
  const { colorTheme, setColorTheme } = useColor();
  const [hoveredTheme, setHoveredTheme] = useState<string | null>(null);

  /**
   * Handle color theme selection
   */
  const handleSelect = (themeId: string) => {
    setColorTheme(themeId);
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {COLOR_THEMES.map((theme) => {
          const isSelected = theme.id === colorTheme.id;
          return (
            <button
              key={theme.id}
              onClick={() => handleSelect(theme.id)}
              onMouseEnter={() => setHoveredTheme(theme.id)}
              onMouseLeave={() => setHoveredTheme(null)}
              className={`
                relative w-10 h-10 rounded-full transition-all cursor-pointer
                ${
                  isSelected
                    ? 'ring-4 ring-offset-2 ring-gray-400 dark:ring-gray-500 scale-110'
                    : 'hover:scale-105 hover:ring-2 hover:ring-gray-300 dark:hover:ring-gray-600 hover:ring-offset-1'
                }
              `}
              style={{ backgroundColor: theme.primary }}
              title={theme.name}
              aria-label={`Select ${theme.name} color theme`}
            >
              {isSelected && (
                <div className="absolute inset-0 flex items-center justify-center text-white text-lg">
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Current selection preview */}
      <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-lg border border-gray-200 dark:border-gray-600">
        <div
          className="w-16 h-16 rounded-full flex items-center justify-center text-2xl transition-all shadow-lg"
          style={{ backgroundColor: colorTheme.primary }}
        >
          {colorTheme.emoji}
        </div>
        <div>
          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
            Current Color
          </div>
          <div className="text-lg font-semibold text-gray-800 dark:text-gray-200">
            {colorTheme.name}
          </div>
        </div>
      </div>

      {/* Color grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {COLOR_THEMES.map((theme) => {
          const isSelected = theme.id === colorTheme.id;
          const isHovered = hoveredTheme === theme.id;

          return (
            <button
              key={theme.id}
              onClick={() => handleSelect(theme.id)}
              onMouseEnter={() => setHoveredTheme(theme.id)}
              onMouseLeave={() => setHoveredTheme(null)}
              className={`
                group relative p-4 rounded-lg border-2 transition-all cursor-pointer
                ${
                  isSelected
                    ? 'border-gray-400 dark:border-gray-500 bg-white dark:bg-gray-800 shadow-lg scale-105'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 hover:scale-102'
                }
              `}
            >
              {/* Color circle */}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center text-xl transition-all shadow-md
                    ${isHovered ? 'scale-110' : ''}
                  `}
                  style={{ backgroundColor: theme.primary }}
                >
                  {theme.emoji}
                </div>
                <div className="text-sm font-medium text-gray-700 dark:text-gray-300 text-center">
                  {theme.name}
                </div>
              </div>

              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-white text-xs shadow-md"
                  style={{ backgroundColor: theme.primary }}
                >
                  ✓
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Info text */}
      <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
        {COLOR_THEMES.length} color themes available
      </p>
    </div>
  );
};

export default ColorSelector;

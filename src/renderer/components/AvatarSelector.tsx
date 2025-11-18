/**
 * AvatarSelector Component
 * Interactive avatar selection with categories and preview
 */

import React, { useState } from 'react';
import {
  Avatar,
  AvatarCategory,
  AVATARS,
  getCategories,
  getCategoryName,
  getAvatarsByCategory,
  DEFAULT_AVATAR,
} from '../../shared/avatars';

interface AvatarSelectorProps {
  selectedAvatarId?: string;
  onSelect: (avatarId: string) => void;
  onClose?: () => void;
}

export const AvatarSelector: React.FC<AvatarSelectorProps> = ({
  selectedAvatarId,
  onSelect,
  onClose,
}) => {
  const [activeCategory, setActiveCategory] = useState<AvatarCategory>('animals');
  const [hoveredAvatar, setHoveredAvatar] = useState<string | null>(null);

  const categories = getCategories();
  const avatarsInCategory = getAvatarsByCategory(activeCategory);

  /**
   * Handle avatar selection
   */
  const handleSelect = (avatarId: string) => {
    onSelect(avatarId);
    if (onClose) {
      onClose();
    }
  };

  /**
   * Get selected avatar object
   */
  const selectedAvatar = AVATARS.find(a => a.id === selectedAvatarId) || DEFAULT_AVATAR;

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-800">Choose Your Avatar</h3>
            <p className="text-sm text-gray-600 mt-1">
              Select an avatar to personalize your profile
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>

        {/* Current Selection Preview */}
        <div className="flex items-center gap-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-100">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center text-4xl transition-all"
            style={{ backgroundColor: selectedAvatar.color }}
          >
            {selectedAvatar.emoji}
          </div>
          <div>
            <div className="text-sm font-medium text-gray-600">Current Avatar</div>
            <div className="text-lg font-semibold text-gray-800">
              {selectedAvatar.name}
            </div>
          </div>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setActiveCategory(category)}
              className={`px-6 py-3 font-medium text-sm whitespace-nowrap border-b-2 transition-colors ${
                activeCategory === category
                  ? 'border-blue-500 text-blue-600 bg-white'
                  : 'border-transparent text-gray-600 hover:text-gray-800 hover:bg-white'
              }`}
            >
              {getCategoryName(category)}
            </button>
          ))}
        </div>
      </div>

      {/* Avatar Grid */}
      <div className="p-6 max-h-96 overflow-y-auto">
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-3">
          {avatarsInCategory.map((avatar) => {
            const isSelected = avatar.id === selectedAvatarId;
            const isHovered = hoveredAvatar === avatar.id;

            return (
              <button
                key={avatar.id}
                onClick={() => handleSelect(avatar.id)}
                onMouseEnter={() => setHoveredAvatar(avatar.id)}
                onMouseLeave={() => setHoveredAvatar(null)}
                className={`
                  group relative aspect-square rounded-lg flex items-center justify-center
                  text-4xl transition-all cursor-pointer
                  ${
                    isSelected
                      ? 'ring-4 ring-blue-500 ring-offset-2 scale-105'
                      : 'hover:scale-110 hover:ring-2 hover:ring-gray-300 hover:ring-offset-1'
                  }
                `}
                style={{ backgroundColor: avatar.color }}
                title={avatar.name}
              >
                {avatar.emoji}

                {/* Selection checkmark */}
                {isSelected && (
                  <div className="absolute -top-2 -right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-xs">
                    ✓
                  </div>
                )}

                {/* Hover tooltip */}
                {isHovered && !isSelected && (
                  <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 px-2 py-1 bg-gray-800 text-white text-xs rounded whitespace-nowrap z-10">
                    {avatar.name}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Empty state (shouldn't happen) */}
        {avatarsInCategory.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-2">🔍</div>
            <p>No avatars in this category</p>
          </div>
        )}
      </div>

      {/* Footer with stats */}
      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <span>{AVATARS.length} avatars available</span>
          <span>{avatarsInCategory.length} in {getCategoryName(activeCategory)}</span>
        </div>
      </div>
    </div>
  );
};

export default AvatarSelector;

/**
 * AvatarDisplay Component
 * Displays user's selected avatar in various sizes
 */

import React from 'react';
import { getAvatarById, DEFAULT_AVATAR } from '../../shared/avatars';

interface AvatarDisplayProps {
  avatarId?: string;
  size?: 'small' | 'medium' | 'large' | 'xlarge';
  showBorder?: boolean;
  className?: string;
}

const sizeConfig = {
  small: {
    container: 'w-8 h-8',
    emoji: 'text-2xl',
  },
  medium: {
    container: 'w-12 h-12',
    emoji: 'text-3xl',
  },
  large: {
    container: 'w-16 h-16',
    emoji: 'text-4xl',
  },
  xlarge: {
    container: 'w-24 h-24',
    emoji: 'text-6xl',
  },
};

export const AvatarDisplay: React.FC<AvatarDisplayProps> = ({
  avatarId,
  size = 'medium',
  showBorder = false,
  className = '',
}) => {
  const avatar = getAvatarById(avatarId || '') || DEFAULT_AVATAR;
  const config = sizeConfig[size];

  return (
    <div
      className={`
        ${config.container}
        rounded-full flex items-center justify-center
        transition-all
        ${showBorder ? 'ring-2 ring-gray-200 ring-offset-2' : ''}
        ${className}
      `}
      style={{ backgroundColor: avatar.color }}
      title={avatar.name}
    >
      <span className={config.emoji}>{avatar.emoji}</span>
    </div>
  );
};

export default AvatarDisplay;

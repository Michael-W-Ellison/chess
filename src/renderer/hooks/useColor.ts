/**
 * useColor Hook
 * Access color theme context
 */

import { useContext } from 'react';
import { ColorContext } from '../contexts/ColorContext';

export const useColor = () => {
  const context = useContext(ColorContext);

  if (!context) {
    throw new Error('useColor must be used within a ColorProvider');
  }

  return context;
};

export default useColor;

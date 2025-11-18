/**
 * useLogin Hook
 * Provides access to login tracking functionality
 */

import { useContext } from 'react';
import { LoginContext } from '../contexts/LoginContext';

export function useLogin() {
  const context = useContext(LoginContext);
  if (!context) {
    throw new Error('useLogin must be used within a LoginProvider');
  }
  return context;
}

export default useLogin;

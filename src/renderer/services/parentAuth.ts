/**
 * Parent Authentication
 * Logs the parent in to the parent dashboard API and adds the token to its requests
 *
 * When the backend has password protection on, every /api/parent/* endpoint except
 * /api/parent/auth/* requires "Authorization: Bearer <token>". The token is kept in
 * sessionStorage, so it lasts until the app window closes or the token expires, and it
 * is dropped as soon as the backend rejects it (401).
 */

import { BACKEND_URL } from '../../shared/constants';
import { apiTokenHeaders } from './apiToken';

export const PARENT_API_URL = `${BACKEND_URL}/api/parent`;

/** Dispatched on window when the backend rejects the token, so the dashboard asks to log in again */
export const PARENT_AUTH_EXPIRED_EVENT = 'parent-auth-expired';

const TOKEN_KEY = 'parentAuthToken';

export interface ParentAuthStatus {
  required: boolean; // password protection is on
  configured: boolean; // a parent password and JWT secret are set on the backend
}

export class ParentAuthError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'ParentAuthError';
  }
}

// Fallback when sessionStorage is unavailable
let memoryToken: string | null = null;

export function getParentToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? memoryToken;
  } catch {
    return memoryToken;
  }
}

function setParentToken(token: string | null): void {
  memoryToken = token;
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token);
    } else {
      sessionStorage.removeItem(TOKEN_KEY);
    }
  } catch {
    // sessionStorage unavailable: the in-memory token is used
  }
}

/** The error message from a FastAPI error response ({"detail": "..."} or {"detail": {"message": "..."}}) */
async function errorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === 'string') return data.detail;
    if (data.detail?.message) return data.detail.message;
  } catch {
    // Not JSON
  }
  return response.statusText || `Request failed (${response.status})`;
}

/** Whether the backend requires a parent password, and whether one is set up */
export async function getParentAuthStatus(): Promise<ParentAuthStatus> {
  const response = await fetch(`${PARENT_API_URL}/auth/status`, { headers: await apiTokenHeaders() });
  if (!response.ok) {
    throw new ParentAuthError(await errorDetail(response), response.status);
  }
  const data = await response.json();
  return { required: data.required, configured: data.configured };
}

/**
 * Log in with the parent password and store the token
 *
 * Throws ParentAuthError with the backend's message: 401 wrong password (with the
 * attempts remaining), 429 locked out after too many attempts, 403 not configured.
 */
export async function loginParent(password: string): Promise<void> {
  const response = await fetch(`${PARENT_API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(await apiTokenHeaders()) },
    body: JSON.stringify({ password }),
  });
  if (!response.ok) {
    throw new ParentAuthError(await errorDetail(response), response.status);
  }
  const data = await response.json();
  setParentToken(data.access_token);
}

export function logoutParent(): void {
  setParentToken(null);
}

/** True if the stored token is still accepted; an expired or invalid token is dropped */
export async function verifyParentToken(): Promise<boolean> {
  const token = getParentToken();
  if (!token) return false;
  const response = await fetch(`${PARENT_API_URL}/auth/verify`, {
    headers: { Authorization: `Bearer ${token}`, ...(await apiTokenHeaders()) },
  });
  if (!response.ok) {
    setParentToken(null);
    return false;
  }
  return true;
}

/**
 * fetch() for parent API endpoints: adds the Authorization header, and on 401 drops the
 * token and dispatches PARENT_AUTH_EXPIRED_EVENT
 *
 * @param url A full URL or a path under /api/parent (e.g. "/preferences?user_id=1")
 */
export async function parentFetch(url: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  for (const [name, value] of Object.entries(await apiTokenHeaders())) {
    headers.set(name, value);
  }
  const token = getParentToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  const response = await fetch(url.startsWith('http') ? url : `${PARENT_API_URL}${url}`, {
    ...init,
    headers,
  });
  if (response.status === 401) {
    setParentToken(null);
    window.dispatchEvent(new Event(PARENT_AUTH_EXPIRED_EVENT));
  }
  return response;
}

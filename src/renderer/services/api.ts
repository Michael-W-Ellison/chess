/**
 * API Client Service
 * Handles all HTTP communication with the FastAPI backend
 */

import type {
  StartConversationResponse,
  SendMessageResponse,
  PersonalityState,
  UserProfile,
  SafetyFlag,
  ConversationSummary,
  ProfileItem,
} from '../../shared/types';

const API_BASE_URL = 'http://localhost:8000';

/**
 * API Client Configuration
 */
interface ApiConfig {
  baseURL: string;
  timeout: number;
  userId: number; // Default user ID for single-user app
}

const defaultConfig: ApiConfig = {
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes - LLM model loading can take 30-60s on first request
  userId: 1, // Single user app
};

/**
 * API Error class for better error handling
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchWithErrorHandling<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), defaultConfig.timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.error || `HTTP ${response.status}: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new ApiError('Request timeout - backend may be offline');
      }
      throw new ApiError(`Network error: ${error.message}`);
    }

    throw new ApiError('Unknown error occurred');
  }
}

/**
 * Conversation API
 */
export const conversationApi = {
  /**
   * Start a new conversation session
   */
  async start(userId: number = defaultConfig.userId): Promise<StartConversationResponse> {
    return fetchWithErrorHandling<StartConversationResponse>(
      `${defaultConfig.baseURL}/api/conversation/start?user_id=${userId}`,
      { method: 'POST' }
    );
  },

  /**
   * Send a message and get response
   */
  async sendMessage(
    conversationId: number,
    message: string,
    userId: number = defaultConfig.userId
  ): Promise<SendMessageResponse> {
    return fetchWithErrorHandling<SendMessageResponse>(
      `${defaultConfig.baseURL}/api/message`,
      {
        method: 'POST',
        body: JSON.stringify({
          content: message,
          conversation_id: conversationId,
          user_id: userId,
        }),
      }
    );
  },

  /**
   * End the current conversation
   */
  async end(conversationId: number): Promise<{ success: boolean; message: string }> {
    return fetchWithErrorHandling<{ success: boolean; message: string }>(
      `${defaultConfig.baseURL}/api/conversation/end/${conversationId}`,
      { method: 'POST' }
    );
  },

  /**
   * Get conversation details
   */
  async getConversation(conversationId: number): Promise<ConversationSummary> {
    return fetchWithErrorHandling<ConversationSummary>(
      `${defaultConfig.baseURL}/api/conversation/${conversationId}`
    );
  },
};

/**
 * Personality API
 */
export const personalityApi = {
  /**
   * Get current bot personality
   */
  async get(userId: number = defaultConfig.userId): Promise<PersonalityState> {
    return fetchWithErrorHandling<PersonalityState>(
      `${defaultConfig.baseURL}/api/personality?user_id=${userId}`
    );
  },

  /**
   * Get personality trait descriptions
   */
  async getDescription(
    userId: number = defaultConfig.userId
  ): Promise<{
    humor: string;
    energy: string;
    curiosity: string;
    formality: string;
  }> {
    return fetchWithErrorHandling<{
      humor: string;
      energy: string;
      curiosity: string;
      formality: string;
    }>(`${defaultConfig.baseURL}/api/personality/description?user_id=${userId}`);
  },
};

/**
 * Profile & Memory API
 */
export const profileApi = {
  /**
   * Get user profile summary
   */
  async get(userId: number = defaultConfig.userId): Promise<UserProfile> {
    return fetchWithErrorHandling<UserProfile>(
      `${defaultConfig.baseURL}/api/profile?user_id=${userId}`
    );
  },

  /**
   * Get memory items
   */
  async getMemories(
    userId: number = defaultConfig.userId,
    category?: string
  ): Promise<{ memories: ProfileItem[] }> {
    const url = category
      ? `${defaultConfig.baseURL}/api/profile/memories?user_id=${userId}&category=${category}`
      : `${defaultConfig.baseURL}/api/profile/memories?user_id=${userId}`;

    return fetchWithErrorHandling<{ memories: ProfileItem[] }>(url);
  },

  /**
   * Update user profile
   */
  async update(
    updates: {
      name?: string;
      age?: number;
      grade?: number;
    },
    userId: number = defaultConfig.userId
  ): Promise<{ success: boolean; user: UserProfile }> {
    return fetchWithErrorHandling<{ success: boolean; user: UserProfile }>(
      `${defaultConfig.baseURL}/api/profile/update`,
      {
        method: 'PUT',
        body: JSON.stringify({
          user_id: userId,
          ...updates,
        }),
      }
    );
  },
};

/**
 * Health & Status API
 */
export const healthApi = {
  /**
   * Check if backend is running
   */
  async check(): Promise<{
    status: string;
    database: string;
    llm: string;
    model_info: {
      loaded: boolean;
      model_path: string | null;
      context_length: number;
      max_tokens: number;
      temperature: number;
      gpu_layers: number;
    };
  }> {
    return fetchWithErrorHandling(`${defaultConfig.baseURL}/health`);
  },

  /**
   * Get API info
   */
  async getInfo(): Promise<{
    message: string;
    version: string;
    status: string;
  }> {
    return fetchWithErrorHandling(`${defaultConfig.baseURL}/`);
  },
};

/**
 * Combined API object for easy importing
 */
export const api = {
  conversation: conversationApi,
  personality: personalityApi,
  profile: profileApi,
  health: healthApi,
};

export default api;

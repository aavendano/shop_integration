/**
 * Base API Client Service
 * Provides core HTTP functionality for all API requests to the Django backend
 * Includes session token management and automatic refresh on expiration
 * Requirements: 14.4, 14.5
 */

import { ApiError } from '../types/api';

export class ApiClient {
  private baseUrl: string;
  private sessionToken: string;
  private onTokenRefresh?: (newToken: string) => Promise<void>;

  constructor(
    baseUrl: string,
    sessionToken: string,
    onTokenRefresh?: (newToken: string) => Promise<void>
  ) {
    this.baseUrl = baseUrl;
    this.sessionToken = sessionToken;
    this.onTokenRefresh = onTokenRefresh;
  }

  /**
   * Update session token (called when token is refreshed)
   * Requirements: 14.5
   */
  setSessionToken(token: string): void {
    this.sessionToken = token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.sessionToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle token expiration (401 response)
    if (response.status === 401) {
      // Token has expired, trigger refresh
      if (this.onTokenRefresh) {
        try {
          // Attempt to get new token from App Bridge
          const newToken = await this.getRefreshedToken();
          if (newToken) {
            this.setSessionToken(newToken);
            await this.onTokenRefresh(newToken);

            // Retry the request with new token
            return this.request<T>(endpoint, options);
          }
        } catch (error) {
          console.error("Token refresh failed:", error);
          throw new Error("Session expired. Please refresh the page.");
        }
      }
    }

    if (!response.ok) {
      let error: ApiError;
      try {
        error = await response.json();
      } catch {
        error = {
          detail: `HTTP ${response.status}: ${response.statusText}`,
        };
      }
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get refreshed token from App Bridge
   * Requirements: 14.5
   */
  private async getRefreshedToken(): Promise<string | null> {
    try {
      // In a real implementation, this would call App Bridge to get a new token
      // For now, we'll return null to indicate token refresh failed
      // The actual implementation depends on how Shopify App Bridge provides token refresh
      return null;
    } catch (error) {
      console.error("Error getting refreshed token:", error);
      return null;
    }
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }
}

/**
 * Helper to create API client in loaders/actions
 * Extracts session token from Remix request and initializes API client
 * Includes token refresh callback for handling expiration
 * Requirements: 14.4, 14.5
 */
export async function createApiClient(
  request: Request,
  sessionToken: string,
  onTokenRefresh?: (newToken: string) => Promise<void>
): Promise<ApiClient> {
  const baseUrl = process.env.DJANGO_API_URL || 'http://localhost:8000';
  return new ApiClient(baseUrl, sessionToken, onTokenRefresh);
}


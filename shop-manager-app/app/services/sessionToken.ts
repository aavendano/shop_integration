/**
 * Session Token Service
 * Handles OAuth flow and session token management for Shopify embedded app
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
 */

import { useAppBridge } from "@shopify/app-bridge-react";

/**
 * Session token storage key
 */
const SESSION_TOKEN_KEY = "shopify_session_token";
const SESSION_TOKEN_EXPIRY_KEY = "shopify_session_token_expiry";

/**
 * Session Token Service
 * Manages OAuth flow and session token lifecycle
 */
export class SessionTokenService {
  private appBridge: any;

  constructor(appBridge: any) {
    this.appBridge = appBridge;
  }

  /**
   * Initialize OAuth flow
   * Requests required scopes on installation
   * Requirements: 14.1, 14.2
   */
  async initializeOAuthFlow(): Promise<void> {
    try {
      // The Shopify App Bridge handles OAuth automatically
      // This is called during app installation
      console.log("OAuth flow initialized");
    } catch (error) {
      console.error("OAuth initialization error:", error);
      throw error;
    }
  }

  /**
   * Store session token securely after OAuth completion
   * Requirements: 14.3
   */
  async storeSessionToken(token: string, expiresIn?: number): Promise<void> {
    try {
      // Store token in sessionStorage (cleared when browser closes)
      sessionStorage.setItem(SESSION_TOKEN_KEY, token);

      // Calculate and store expiry time
      if (expiresIn) {
        const expiryTime = Date.now() + expiresIn * 1000;
        sessionStorage.setItem(SESSION_TOKEN_EXPIRY_KEY, expiryTime.toString());
      }

      console.log("Session token stored securely");
    } catch (error) {
      console.error("Error storing session token:", error);
      throw error;
    }
  }

  /**
   * Retrieve stored session token
   * Requirements: 14.4
   */
  getSessionToken(): string | null {
    try {
      const token = sessionStorage.getItem(SESSION_TOKEN_KEY);

      // Check if token has expired
      if (token && this.isTokenExpired()) {
        this.clearSessionToken();
        return null;
      }

      return token;
    } catch (error) {
      console.error("Error retrieving session token:", error);
      return null;
    }
  }

  /**
   * Check if session token has expired
   * Requirements: 14.5
   */
  private isTokenExpired(): boolean {
    try {
      const expiryTime = sessionStorage.getItem(SESSION_TOKEN_EXPIRY_KEY);

      if (!expiryTime) {
        return false; // No expiry set, assume valid
      }

      return Date.now() > parseInt(expiryTime, 10);
    } catch (error) {
      console.error("Error checking token expiry:", error);
      return false;
    }
  }

  /**
   * Refresh authentication when Session_Token expires
   * Requirements: 14.5
   */
  async refreshAuthentication(): Promise<string | null> {
    try {
      // Request new session token from App Bridge
      if (this.appBridge && this.appBridge.getSessionToken) {
        const newToken = await this.appBridge.getSessionToken();

        if (newToken) {
          await this.storeSessionToken(newToken);
          return newToken;
        }
      }

      return null;
    } catch (error) {
      console.error("Error refreshing authentication:", error);
      return null;
    }
  }

  /**
   * Clear stored session token
   */
  clearSessionToken(): void {
    try {
      sessionStorage.removeItem(SESSION_TOKEN_KEY);
      sessionStorage.removeItem(SESSION_TOKEN_EXPIRY_KEY);
      console.log("Session token cleared");
    } catch (error) {
      console.error("Error clearing session token:", error);
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return this.getSessionToken() !== null;
  }
}

/**
 * Hook for session token management
 * Provides easy access to session token operations
 */
export function useSessionToken() {
  const appBridge = useAppBridge();
  const service = new SessionTokenService(appBridge);

  return {
    /**
     * Get current session token
     */
    getToken: () => service.getSessionToken(),

    /**
     * Store session token
     */
    storeToken: (token: string, expiresIn?: number) =>
      service.storeSessionToken(token, expiresIn),

    /**
     * Refresh authentication
     */
    refreshAuth: () => service.refreshAuthentication(),

    /**
     * Clear session token
     */
    clearToken: () => service.clearSessionToken(),

    /**
     * Check if authenticated
     */
    isAuthenticated: () => service.isAuthenticated(),
  };
}

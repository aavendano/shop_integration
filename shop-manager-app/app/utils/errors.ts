/**
 * Error Handling Utilities
 * Provides functions for consistent error handling across the application
 * Requirements: 16.2, 16.3, 16.4, 16.5, 16.6, 16.7
 */

import { ApiError } from '../types/api';

/**
 * Extracts user-friendly error message from various error types
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object' && 'detail' in error) {
    const apiError = error as ApiError;
    return apiError.detail;
  }

  return 'An unexpected error occurred. Please try again.';
}

/**
 * Extracts field-level validation errors from API response
 * Requirements: 16.4
 */
export function getFieldErrors(error: unknown): Record<string, string[]> {
  if (error && typeof error === 'object' && 'field_errors' in error) {
    const apiError = error as ApiError;
    return apiError.field_errors || {};
  }

  return {};
}

/**
 * Determines if an error is a network error
 * Requirements: 16.3
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof TypeError) {
    return error.message.includes('fetch') || error.message.includes('network');
  }

  if (error instanceof Error) {
    return error.message.includes('Failed to fetch') || 
           error.message.includes('NetworkError') ||
           error.message.includes('timeout');
  }

  return false;
}

/**
 * Determines if an error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  if (error && typeof error === 'object' && 'field_errors' in error) {
    const apiError = error as ApiError;
    return Object.keys(apiError.field_errors || {}).length > 0;
  }

  return false;
}

/**
 * Determines if an error is an authentication error
 */
export function isAuthenticationError(error: unknown): boolean {
  if (error instanceof Error) {
    return error.message.includes('401') || 
           error.message.includes('Unauthorized') ||
           error.message.includes('authentication');
  }

  return false;
}

/**
 * Logs error to console for debugging
 * Requirements: 16.5
 */
export function logError(error: unknown, context?: string): void {
  const message = getErrorMessage(error);
  const prefix = context ? `[${context}]` : '[Error]';
  const timestamp = new Date().toISOString();

  console.error(`${timestamp} ${prefix} ${message}`, error);

  // Log additional context for debugging
  if (error instanceof Error && error.stack) {
    console.error('Stack trace:', error.stack);
  }
}

/**
 * Logs warning to console
 */
export function logWarning(message: string, context?: string): void {
  const prefix = context ? `[${context}]` : '[Warning]';
  const timestamp = new Date().toISOString();

  console.warn(`${timestamp} ${prefix} ${message}`);
}

/**
 * Logs info to console
 */
export function logInfo(message: string, context?: string): void {
  const prefix = context ? `[${context}]` : '[Info]';
  const timestamp = new Date().toISOString();

  console.log(`${timestamp} ${prefix} ${message}`);
}

/**
 * Formats error for display in UI
 * Requirements: 16.2, 16.7
 */
export function formatErrorForDisplay(error: unknown): {
  title: string;
  message: string;
  isNetworkError: boolean;
  isValidationError: boolean;
  isAuthError: boolean;
} {
  const message = getErrorMessage(error);
  const networkError = isNetworkError(error);
  const validationError = isValidationError(error);
  const authError = isAuthenticationError(error);

  let title = 'Error';
  let displayMessage = message;

  if (networkError) {
    title = 'Connection Error';
    displayMessage = 'Unable to connect to the server. Please check your connection and try again.';
  } else if (authError) {
    title = 'Authentication Error';
    displayMessage = 'Your session has expired. Please refresh and try again.';
  } else if (validationError) {
    title = 'Validation Error';
    displayMessage = 'Please check your input and try again.';
  } else if (!message || message.includes('unexpected')) {
    title = 'Unexpected Error';
    displayMessage = 'An unexpected error occurred. Please try again or contact support if the problem persists.';
  }

  return {
    title,
    message: displayMessage,
    isNetworkError: networkError,
    isValidationError: validationError,
    isAuthError: authError,
  };
}

/**
 * Creates a retry handler with exponential backoff
 * Requirements: 16.6
 */
export function createRetryHandler(
  fn: () => Promise<any>,
  maxRetries: number = 3,
  delayMs: number = 1000
) {
  return async function retry(attempt: number = 0): Promise<any> {
    try {
      return await fn();
    } catch (error) {
      if (attempt < maxRetries) {
        const delay = delayMs * Math.pow(2, attempt);
        logWarning(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`, 'RetryHandler');
        await new Promise(resolve => setTimeout(resolve, delay));
        return retry(attempt + 1);
      }

      logError(error, 'RetryHandler');
      throw error;
    }
  };
}

/**
 * Sanitizes error message to avoid exposing technical details
 * Requirements: 16.7
 */
export function sanitizeErrorMessage(error: unknown): string {
  const message = getErrorMessage(error);

  // Remove sensitive information patterns
  const sanitized = message
    .replace(/\/api\/[^\s]*/g, '[API endpoint]')
    .replace(/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/g, '[IP address]')
    .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[email]')
    .replace(/Bearer\s+[^\s]*/g, '[token]');

  return sanitized;
}

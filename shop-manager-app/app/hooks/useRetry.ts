import { useState, useCallback } from 'react';
import { logger } from '../utils/logger';

/**
 * useRetry Hook
 * Provides retry functionality for failed operations
 * Requirements: 16.6
 */

export interface RetryOptions {
  maxRetries?: number;
  delayMs?: number;
  backoffMultiplier?: number;
  onRetry?: (attempt: number, error: Error) => void;
  onSuccess?: (result: any) => void;
  onError?: (error: Error) => void;
}

export function useRetry(context: string = 'useRetry') {
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<Error | null>(null);

  const retry = useCallback(
    async <T,>(
      fn: () => Promise<T>,
      options: RetryOptions = {}
    ): Promise<T> => {
      const {
        maxRetries = 3,
        delayMs = 1000,
        backoffMultiplier = 2,
        onRetry,
        onSuccess,
        onError,
      } = options;

      setIsRetrying(true);
      setRetryCount(0);
      setLastError(null);

      const attemptRetry = async (attempt: number = 0): Promise<T> => {
        try {
          const result = await fn();
          onSuccess?.(result);
          setIsRetrying(false);
          return result;
        } catch (error) {
          const err = error instanceof Error ? error : new Error(String(error));
          setLastError(err);

          if (attempt < maxRetries) {
            const delay = delayMs * Math.pow(backoffMultiplier, attempt);
            setRetryCount(attempt + 1);

            logger.warn(
              context,
              `Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`,
              { error: err.message }
            );

            onRetry?.(attempt + 1, err);

            await new Promise((resolve) => setTimeout(resolve, delay));
            return attemptRetry(attempt + 1);
          }

          logger.error(context, `Failed after ${maxRetries} retries`, err);
          onError?.(err);
          setIsRetrying(false);
          throw err;
        }
      };

      return attemptRetry();
    },
    [context]
  );

  const reset = useCallback(() => {
    setIsRetrying(false);
    setRetryCount(0);
    setLastError(null);
  }, []);

  return {
    retry,
    isRetrying,
    retryCount,
    lastError,
    reset,
  };
}

/**
 * useAsyncWithRetry Hook
 * Combines async operation with automatic retry
 */
export function useAsyncWithRetry<T>(
  fn: () => Promise<T>,
  context: string = 'useAsyncWithRetry',
  options: RetryOptions = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { retry, isRetrying, retryCount, lastError, reset } = useRetry(context);

  const execute = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await retry(fn, {
        ...options,
        onSuccess: (result) => {
          setData(result);
          options.onSuccess?.(result);
        },
        onError: (err) => {
          setError(err);
          options.onError?.(err);
        },
      });
      return result;
    } finally {
      setIsLoading(false);
    }
  }, [fn, retry, options]);

  return {
    data,
    error,
    isLoading,
    isRetrying,
    retryCount,
    lastError,
    execute,
    reset,
  };
}

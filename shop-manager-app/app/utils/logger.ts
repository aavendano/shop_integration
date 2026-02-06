/**
 * Logger Utility
 * Provides structured logging for debugging and monitoring
 * Requirements: 16.5
 */

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARN = 'WARN',
  ERROR = 'ERROR',
}

export interface LogEntry {
  timestamp: string;
  level: LogLevel;
  context: string;
  message: string;
  data?: any;
  stack?: string;
}

/**
 * Logger class for structured logging
 */
class Logger {
  private logs: LogEntry[] = [];
  private maxLogs = 100;
  private isDevelopment = process.env.NODE_ENV === 'development';

  /**
   * Log a message at the specified level
   */
  private log(level: LogLevel, context: string, message: string, data?: any): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      context,
      message,
      data,
    };

    // Add to in-memory log
    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    // Log to console in development
    if (this.isDevelopment) {
      const prefix = `[${entry.timestamp}] [${level}] [${context}]`;
      switch (level) {
        case LogLevel.DEBUG:
          console.debug(prefix, message, data);
          break;
        case LogLevel.INFO:
          console.info(prefix, message, data);
          break;
        case LogLevel.WARN:
          console.warn(prefix, message, data);
          break;
        case LogLevel.ERROR:
          console.error(prefix, message, data);
          break;
      }
    }
  }

  /**
   * Log debug message
   */
  debug(context: string, message: string, data?: any): void {
    this.log(LogLevel.DEBUG, context, message, data);
  }

  /**
   * Log info message
   */
  info(context: string, message: string, data?: any): void {
    this.log(LogLevel.INFO, context, message, data);
  }

  /**
   * Log warning message
   */
  warn(context: string, message: string, data?: any): void {
    this.log(LogLevel.WARN, context, message, data);
  }

  /**
   * Log error message
   */
  error(context: string, message: string, error?: Error | unknown, data?: any): void {
    let stack: string | undefined;
    let errorData = data;

    if (error instanceof Error) {
      stack = error.stack;
      errorData = { ...data, errorMessage: error.message };
    } else if (error) {
      errorData = { ...data, error };
    }

    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level: LogLevel.ERROR,
      context,
      message,
      data: errorData,
      stack,
    };

    this.logs.push(entry);
    if (this.logs.length > this.maxLogs) {
      this.logs.shift();
    }

    if (this.isDevelopment) {
      const prefix = `[${entry.timestamp}] [ERROR] [${context}]`;
      console.error(prefix, message, errorData);
      if (stack) {
        console.error('Stack trace:', stack);
      }
    }
  }

  /**
   * Get all logs
   */
  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  /**
   * Get logs filtered by level
   */
  getLogsByLevel(level: LogLevel): LogEntry[] {
    return this.logs.filter((log) => log.level === level);
  }

  /**
   * Get logs filtered by context
   */
  getLogsByContext(context: string): LogEntry[] {
    return this.logs.filter((log) => log.context === context);
  }

  /**
   * Clear all logs
   */
  clearLogs(): void {
    this.logs = [];
  }

  /**
   * Export logs as JSON
   */
  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  /**
   * Export logs as CSV
   */
  exportLogsAsCSV(): string {
    const headers = ['Timestamp', 'Level', 'Context', 'Message', 'Data'];
    const rows = this.logs.map((log) => [
      log.timestamp,
      log.level,
      log.context,
      log.message,
      JSON.stringify(log.data || {}),
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    return csv;
  }
}

// Create singleton instance
export const logger = new Logger();

/**
 * Hook for using logger in React components
 */
export function useLogger(context: string) {
  return {
    debug: (message: string, data?: any) => logger.debug(context, message, data),
    info: (message: string, data?: any) => logger.info(context, message, data),
    warn: (message: string, data?: any) => logger.warn(context, message, data),
    error: (message: string, error?: Error | unknown, data?: any) =>
      logger.error(context, message, error, data),
  };
}

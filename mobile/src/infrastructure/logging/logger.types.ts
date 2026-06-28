/**
 * Logger types — shared between logger implementation and consumers.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export type LogContext = Record<string, unknown>;

export interface LogEntry {
  readonly level: LogLevel;
  readonly message: string;
  readonly context: LogContext;
  readonly timestamp: string; // ISO 8601
}

export interface LogTransport {
  write(entry: LogEntry): void;
}

export interface Logger {
  child(extra: LogContext): Logger;
  debug(message: string, context?: LogContext): void;
  info(message: string, context?: LogContext): void;
  warn(message: string, context?: LogContext): void;
  error(message: string, context?: LogContext): void;
  fatal(message: string, context?: LogContext): void;
}

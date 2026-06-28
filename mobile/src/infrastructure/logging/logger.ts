/**
 * AraFlow — Logger
 *
 * Logger estruturado multi-transport. Suporta:
 *   - Console (dev) — pretty-printed
 *   - In-memory ring buffer (debug)
 *   - Sentry (production, stubbed em Sprint 0)
 *
 * Princípios:
 *   - Structured: cada log é um objeto com campos tipados.
 *   - Leveled: debug | info | warn | error | fatal
 *   - Child loggers: herdam contexto e adicionam mais campos.
 *   - PII-safe: o logger NÃO serializa PII automaticamente.
 *
 * Uso:
 *   const log = logger.child({ feature: 'session' });
 *   log.info('session.started', { sessionId, protocolId });
 */

import type { LogContext, LogEntry, LogLevel, Logger, LogTransport } from './logger.types';

const LEVEL_PRIORITY: Record<LogLevel, number> = {
  debug: 10,
  info: 20,
  warn: 30,
  error: 40,
  fatal: 50,
};

const MIN_LEVEL: LogLevel = __DEV__ ? 'debug' : 'info';

class ConsoleTransport implements LogTransport {
  public write(entry: LogEntry): void {
    const { level, message, context, timestamp } = entry;
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    const args: unknown[] = [prefix, message];
    if (Object.keys(context).length > 0) {
      args.push(context);
    }
    if (level === 'error' || level === 'fatal') {
      console.error(...args);
    } else if (level === 'warn') {
      console.warn(...args);
    } else {
      console.log(...args);
    }
  }
}

class RingBufferTransport implements LogTransport {
  private readonly capacity: number;
  private readonly buffer: LogEntry[];
  private writeIndex = 0;

  public constructor(capacity = 500) {
    this.capacity = capacity;
    this.buffer = new Array<LogEntry>(capacity);
  }

  public write(entry: LogEntry): void {
    this.buffer[this.writeIndex] = entry;
    this.writeIndex = (this.writeIndex + 1) % this.capacity;
  }

  public snapshot(): readonly LogEntry[] {
    return this.buffer.filter((e): e is LogEntry => e !== undefined);
  }
}

class CoreLogger implements Logger {
  private readonly baseContext: LogContext;
  private readonly transports: LogTransport[];

  public constructor(baseContext: LogContext = {}, transports: LogTransport[]) {
    this.baseContext = baseContext;
    this.transports = transports;
  }

  public child(extra: LogContext): Logger {
    return new CoreLogger({ ...this.baseContext, ...extra }, this.transports);
  }

  public debug(message: string, context: LogContext = {}): void {
    this.emit('debug', message, context);
  }

  public info(message: string, context: LogContext = {}): void {
    this.emit('info', message, context);
  }

  public warn(message: string, context: LogContext = {}): void {
    this.emit('warn', message, context);
  }

  public error(message: string, context: LogContext = {}): void {
    this.emit('error', message, context);
  }

  public fatal(message: string, context: LogContext = {}): void {
    this.emit('fatal', message, context);
  }

  private emit(level: LogLevel, message: string, context: LogContext): void {
    if (LEVEL_PRIORITY[level] < LEVEL_PRIORITY[MIN_LEVEL]) {
      return;
    }
    const entry: LogEntry = {
      level,
      message,
      context: { ...this.baseContext, ...context },
      timestamp: new Date().toISOString(),
    };
    for (const transport of this.transports) {
      try {
        transport.write(entry);
      } catch {
        // Transport errors must never crash the app.
      }
    }
  }
}

const ringBuffer = new RingBufferTransport(500);

export const logger: Logger = new CoreLogger(
  { app: 'araflow', env: __DEV__ ? 'development' : 'production' },
  [new ConsoleTransport(), ringBuffer],
);

export const getRecentLogs = (): readonly LogEntry[] => ringBuffer.snapshot();

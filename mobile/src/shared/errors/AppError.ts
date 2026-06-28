/**
 * AraFlow — AppError
 *
 * Classe base para todos os erros de domínio/infraestrutura do app.
 * Subclasses devem fornecer `code` estável (usado para telemetria) e
 * opcionalmente `userMessage` localizada.
 *
 * Princípios:
 *   - Nunca expor stack em produção via UI.
 *   - `code` é o identificador para i18n, logs, analytics, e mapping.
 *   - Erros são serializáveis (sem funções, sem refs circulares).
 */

export type ErrorSeverity = 'info' | 'warn' | 'error' | 'fatal';

export interface AppErrorOptions {
  readonly code: string;
  readonly severity?: ErrorSeverity;
  readonly cause?: unknown;
  readonly userMessage?: string;
  readonly context?: Record<string, unknown>;
}

export class AppError extends Error {
  public readonly code: string;
  public readonly severity: ErrorSeverity;
  public readonly userMessage: string | undefined;
  public readonly context: Readonly<Record<string, unknown>>;
  public readonly cause: unknown;

  public constructor(message: string, options: AppErrorOptions) {
    super(message);
    this.name = 'AppError';
    this.code = options.code;
    this.severity = options.severity ?? 'error';
    this.userMessage = options.userMessage;
    this.context = options.context ?? {};
    this.cause = options.cause;
    Object.setPrototypeOf(this, new.target.prototype);
  }

  public toJSON(): Record<string, unknown> {
    return {
      name: this.name,
      code: this.code,
      message: this.message,
      severity: this.severity,
      userMessage: this.userMessage,
      context: this.context,
      cause: this.cause instanceof Error ? { name: this.cause.name, message: this.cause.message } : this.cause,
      stack: this.stack,
    };
  }
}

/**
 * Error thrown when a precondition (age, condition, consent) is violated.
 */
export class PreconditionError extends AppError {
  public constructor(message: string, options: Omit<AppErrorOptions, 'severity' | 'code'> = {}) {
    super(message, { code: 'precondition_violated', severity: 'warn', ...options });
    this.name = 'PreconditionError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Error thrown when persisted/incoming data fails validation.
 */
export class ValidationError extends AppError {
  public constructor(message: string, options: Omit<AppErrorOptions, 'severity' | 'code'> = {}) {
    super(message, { code: 'validation_failed', severity: 'warn', ...options });
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Error thrown when a feature is not yet implemented (Sprint 0 stubs).
 */
export class NotImplementedError extends AppError {
  public constructor(feature: string, options: Omit<AppErrorOptions, 'severity' | 'code'> = {}) {
    super(`Not implemented: ${feature}`, { code: 'not_implemented', severity: 'warn', ...options });
    this.name = 'NotImplementedError';
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

/**
 * Type guard.
 */
export const isAppError = (err: unknown): err is AppError => err instanceof AppError;

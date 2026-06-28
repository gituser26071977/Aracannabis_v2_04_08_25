/**
 * HTTP Client — interface definition only.
 *
 * Implementação concreta (fetch wrapper, axios, ky) será plugada em
 * sprint subsequente via DI. Por ora, definimos o contrato e um
 * stub que retorna erro.
 */

import { AppError } from '@shared/errors';

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface HttpRequest<TBody = unknown> {
  readonly method: HttpMethod;
  readonly url: string;
  readonly body?: TBody;
  readonly headers?: Readonly<Record<string, string>>;
  readonly query?: Readonly<Record<string, string | number | boolean>>;
  readonly timeoutMs?: number;
}

export interface HttpResponse<TBody = unknown> {
  readonly status: number;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: TBody;
  readonly durationMs: number;
}

export interface HttpClient {
  request<TResponse, TBody = unknown>(request: HttpRequest<TBody>): Promise<HttpResponse<TResponse>>;
}

export class StubHttpClient implements HttpClient {
  public async request<TResponse, TBody = unknown>(
    _request: HttpRequest<TBody>,
  ): Promise<HttpResponse<TResponse>> {
    throw new AppError('HTTP client not yet wired', {
      code: 'http_not_implemented',
      severity: 'warn',
    });
  }
}

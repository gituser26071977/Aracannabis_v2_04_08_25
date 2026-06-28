/**
 * AraFlow — Dependency Injection Container
 *
 * Container IoC minimalista, type-safe, e sem dependências externas.
 *
 * Princípios:
 *   - Tokens são símbolos (não strings) para type safety.
 *   - Resolução lazy: instâncias são criadas no primeiro `resolve`.
 *   - Singletons por padrão; factories registradas via `registerFactory`.
 *   - O container é INFRAESTRUTURA: features/core importam tokens daqui,
 *     mas não devem manipular o container diretamente fora de bootstrapping.
 *
 * Uso:
 *   const TOKEN = Symbol('MyService');
 *   container.register(TOKEN, () => new MyService());
 *   const svc = container.resolve(TOKEN);
 */

import { logger } from '@infrastructure/logging/logger';

type Token<T> = symbol & { readonly __type?: T };
type Factory<T> = () => T;
type Disposer = () => void;

interface Registration<T> {
  readonly factory: Factory<T>;
  readonly singleton: boolean;
  instance?: T;
  readonly disposer?: Disposer;
}

const log = logger.child({ component: 'container' });

export const createToken = <T>(description: string): Token<T> => {
  return Symbol(description) as Token<T>;
};

export class Container {
  private readonly registry = new Map<Token<unknown>, Registration<unknown>>();
  private disposed = false;

  public register<T>(token: Token<T>, factory: Factory<T>, options?: { singleton?: boolean }): void {
    this.assertAlive();
    const singleton = options?.singleton ?? true;
    this.registry.set(token, { factory, singleton });
  }

  public registerFactory<T>(token: Token<T>, factory: Factory<T>): void {
    this.register(token, factory, { singleton: false });
  }

  public registerSingleton<T>(token: Token<T>, instance: T, disposer?: Disposer): void {
    this.assertAlive();
    this.registry.set(token, {
      factory: () => instance,
      singleton: true,
      instance,
      disposer,
    });
  }

  public resolve<T>(token: Token<T>): T {
    this.assertAlive();
    const registration = this.registry.get(token);
    if (!registration) {
      log.error('container.token_not_registered', { token: String(token) });
      throw new Error(`Token not registered: ${String(token)}`);
    }
    if (registration.singleton) {
      if (registration.instance === undefined) {
        const created = registration.factory();
        registration.instance = created;
        return created;
      }
      return registration.instance as T;
    }
    return registration.factory();
  }

  public tryResolve<T>(token: Token<T>): T | undefined {
    const registration = this.registry.get(token);
    if (!registration) {
      return undefined;
    }
    return this.resolve(token);
  }

  public has<T>(token: Token<T>): boolean {
    return this.registry.has(token);
  }

  public unregister<T>(token: Token<T>): void {
    this.assertAlive();
    this.registry.delete(token);
  }

  public dispose(): void {
    for (const registration of this.registry.values()) {
      if (registration.disposer !== undefined) {
        try {
          registration.disposer();
        } catch {
          // Ignore disposer errors to not throw during teardown
        }
      }
    }
    this.registry.clear();
    this.disposed = true;
  }

  private assertAlive(): void {
    if (this.disposed) {
      throw new Error('Container has been disposed');
    }
  }
}

/**
 * Container global do app. Não dispose em hot reload (apenas em
 * shutdown real do app).
 */
export const container = new Container();

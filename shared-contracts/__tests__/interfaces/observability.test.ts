/**
 * interfaces/observability.ts — Logger, MetricsCollector, Event, EventBus.
 */

import type {
  Logger,
  MetricsCollector,
  Event,
  EventListener,
  EventBus,
  Counter,
  Gauge,
  Histogram,
} from '../../src/interfaces/observability';
import type { Subscription } from '../../src/interfaces/lifecycle';

describe('interfaces/observability', () => {
  describe('Logger', () => {
    it('accepts a sample logger implementation', () => {
      const logged: Array<{ msg: string; ctx?: unknown }> = [];
      const logger: Logger = {
        debug: (msg, ctx) => logged.push({ msg, ctx }),
        info: (msg, ctx) => logged.push({ msg, ctx }),
        warn: (msg, ctx) => logged.push({ msg, ctx }),
        error: (msg, ctx) => logged.push({ msg, ctx }),
        fatal: (msg, ctx) => logged.push({ msg, ctx }),
        log: (entry) => logged.push({ msg: entry.message, ctx: entry.context }),
      };
      logger.debug('d', { x: 1 });
      logger.info('i');
      logger.warn('w');
      logger.error('e');
      logger.fatal('f');
      expect(logged).toHaveLength(5);
    });
  });

  describe('MetricsCollector', () => {
    it('accepts a sample metrics collector', () => {
      const collector: MetricsCollector = {
        incrementCounter: () => undefined,
        setGauge: () => undefined,
        recordHistogram: () => undefined,
        getCounter: (): Counter | null => null,
        getGauge: (): Gauge | null => null,
        getHistogram: (): Histogram | null => null,
        reset: () => undefined,
      };
      expect(collector.getCounter('c')).toBeNull();
      collector.incrementCounter('c', 1, { l: 'v' });
      collector.setGauge('g', 100, { l: 'v' });
      collector.recordHistogram('h', 50, { l: 'v' });
      collector.reset();
    });
  });

  describe('Event', () => {
    it('accepts minimal event', () => {
      const e: Event = { type: 'custom', monotonicMs: 100 };
      expect(e.type).toBe('custom');
      expect(e.monotonicMs).toBe(100);
    });
    it('accepts event with priority/payload', () => {
      const e: Event = {
        type: 'custom',
        monotonicMs: 0,
        priority: 'high',
        payload: { foo: 'bar' },
      };
      expect(e.priority).toBe('high');
      expect(e.payload).toEqual({ foo: 'bar' });
    });
  });

  describe('EventListener', () => {
    it('accepts listener function', () => {
      const listener: EventListener = (e) => {
        expect(e.type).toBe('test');
      };
      listener({ type: 'test', monotonicMs: 0 });
    });
  });

  describe('EventBus', () => {
    it('accepts a sample bus implementation', () => {
      const handlers: Array<(e: Event) => void> = [];
      let typedHandlers = 0;
      const bus: EventBus = {
        publish: (event) => {
          for (const h of handlers) h(event);
        },
        subscribe: (_type, _l) => {
          typedHandlers += 1;
          return {
            unsubscribe: () => undefined,
            active: true,
          } satisfies Subscription;
        },
        subscribeAll: (l) => {
          handlers.push(l);
          return {
            unsubscribe: () => undefined,
            active: true,
          } satisfies Subscription;
        },
        listenerCount: () => handlers.length,
        clear: () => {
          handlers.length = 0;
          typedHandlers = 0;
        },
      };
      let received: Event | null = null;
      bus.subscribeAll((e) => {
        received = e;
      });
      bus.publish({ type: 'tick', monotonicMs: 1 });
      expect(received).toEqual({ type: 'tick', monotonicMs: 1 });
      expect(bus.listenerCount()).toBe(1);
      bus.subscribe('tick', () => undefined);
      expect(typedHandlers).toBe(1);
      bus.clear();
      expect(bus.listenerCount()).toBe(0);
    });
  });
});

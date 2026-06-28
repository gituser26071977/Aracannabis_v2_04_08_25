/**
 * interfaces/infrastructure.ts — Clock, Scheduler.
 */

import type {
  Clock,
  Scheduler,
  ScheduledTask,
  TaskCallback,
} from '../../src/interfaces/infrastructure';

describe('interfaces/infrastructure', () => {
  describe('Clock', () => {
    it('accepts implementations with now/wallNow', () => {
      const clock: Clock = {
        now: () => 1000,
        wallNow: () => 1700000000000,
      };
      expect(clock.now()).toBe(1000);
      expect(clock.wallNow()).toBe(1700000000000);
    });
  });

  describe('Scheduler', () => {
    it('setTimeout returns ScheduledTask', () => {
      const calls: string[] = [];
      let active = true;
      const scheduler: Scheduler = {
        setTimeout: (_cb: TaskCallback, _delay: number): ScheduledTask => {
          return {
            cancel: () => {
              active = false;
            },
            get active() {
              return active;
            },
          };
        },
        setInterval: (_cb: TaskCallback, _period: number): ScheduledTask => {
          return {
            cancel: () => undefined,
            active: true,
          };
        },
      };
      const task = scheduler.setTimeout(() => {
        calls.push('fired');
      }, 100);
      expect(task.active).toBe(true);
      task.cancel();
      expect(task.active).toBe(false);
    });

    it('setInterval returns ScheduledTask', () => {
      const scheduler: Scheduler = {
        setTimeout: () => ({ cancel: () => undefined, active: true }),
        setInterval: () => ({ cancel: () => undefined, active: true }),
      };
      const task = scheduler.setInterval(() => undefined, 50);
      expect(task.active).toBe(true);
      task.cancel();
    });
  });
});

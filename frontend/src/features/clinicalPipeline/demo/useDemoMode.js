// useDemoMode — detects ?demo=1 in the URL and seeds the page with the demo fixture.
// Provides a `runDemo()` function the page calls to inject the deterministic response
// into the same code path as a real pipeline run.
//
// Zero backend. Zero new endpoints. Zero network.

import { useCallback, useEffect, useState } from 'react';
import { DEMO_RUN_RESPONSE, DEMO_SESSIONS, DEMO_REPLAY_RESPONSE } from './fixture';

function readQueryFlag() {
  if (typeof window === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  return params.get('demo') === '1';
}

export function useDemoMode() {
  const [enabled, setEnabled] = useState(readQueryFlag);

  // Allow programmatic toggling (?demo=1 → off, and vice-versa).
  useEffect(() => {
    if (typeof window === 'undefined') return undefined;
    const onPop = () => setEnabled(readQueryFlag());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  const enable = useCallback(() => {
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.set('demo', '1');
      window.history.replaceState({}, '', url.toString());
    }
    setEnabled(true);
  }, []);

  const disable = useCallback(() => {
    if (typeof window !== 'undefined') {
      const url = new URL(window.location.href);
      url.searchParams.delete('demo');
      window.history.replaceState({}, '', url.pathname + (url.search ? `?${url.searchParams}` : '') + url.hash);
    }
    setEnabled(false);
  }, []);

  const runDemo = useCallback(() => {
    // Returns the same { payload, meta } shape the api wrapper returns.
    return {
      payload: DEMO_RUN_RESPONSE.data,
      meta: DEMO_RUN_RESPONSE.meta,
    };
  }, []);

  const listDemoSessions = useCallback(() => DEMO_SESSIONS, []);

  const replayDemo = useCallback(() => {
    return {
      payload: DEMO_REPLAY_RESPONSE.data,
      meta: DEMO_REPLAY_RESPONSE.meta,
    };
  }, []);

  return { enabled, enable, disable, runDemo, listDemoSessions, replayDemo };
}

export default useDemoMode;
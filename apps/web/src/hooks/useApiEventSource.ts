import { useEffect, useRef } from "react";
import { getApiBaseUrl } from "../config";

export interface VsEventMessage {
  type: string;
  payload: Record<string, unknown>;
  ts?: string;
}

/**
 * Browser EventSource to `GET /api/v1/events/stream` (same origin policy: set `VITE_API_URL`).
 * Filters are applied in the callback. No `Authorization` header — use only for non-sensitive
 * dev signals or when the API is same-origin with cookie auth.
 */
export function useApiEventSource(enabled: boolean, onEvent: (msg: VsEventMessage) => void) {
  const cbRef = useRef(onEvent);
  cbRef.current = onEvent;

  useEffect(() => {
    if (!enabled) return;
    const root = getApiBaseUrl();
    if (!root) return;

    const url = `${root}/api/v1/events/stream`;
    const es = new EventSource(url, { withCredentials: true });

    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data) as {
          type?: string;
          payload?: Record<string, unknown>;
          ts?: string;
        };
        if (d.type) {
          cbRef.current({
            type: d.type,
            payload: d.payload ?? {},
            ts: d.ts,
          });
        }
      } catch {
        /* malformed */
      }
    };

    es.onerror = () => {
      /* browser will retry; keep connection */
    };

    return () => {
      es.close();
    };
  }, [enabled]);
}

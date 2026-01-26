"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { EventOccurrenceOut } from "@/types/events";

type EventsState = {
  data: EventOccurrenceOut[] | null;
  error: string | null;
  loading: boolean;
};

export function useEventsForDay(day: string): EventsState {
  const [state, setState] = useState<EventsState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<EventOccurrenceOut[]>(
          `/api/events/day?day=${encodeURIComponent(day)}`
        );
        if (!cancelled) setState({ data: res, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setState({
            data: null,
            error: err instanceof Error ? err.message : String(err),
            loading: false,
          });
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [day]);

  return state;
}

export function useEventsForRange(
  start: string,
  end: string
): EventsState {
  const [state, setState] = useState<EventsState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<EventOccurrenceOut[]>(
          `/api/events/range?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`
        );
        if (!cancelled) setState({ data: res, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setState({
            data: null,
            error: err instanceof Error ? err.message : String(err),
            loading: false,
          });
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [start, end]);

  return state;
}

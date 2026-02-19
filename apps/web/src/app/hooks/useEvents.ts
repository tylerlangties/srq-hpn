"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import type { CategoryOut, EventOccurrenceOut } from "@/types/events";

type EventsState = {
  data: EventOccurrenceOut[] | null;
  error: string | null;
  loading: boolean;
};

type EventCountState = {
  data: number | null;
  error: string | null;
  loading: boolean;
};

type CategoriesState = {
  data: CategoryOut[] | null;
  error: string | null;
  loading: boolean;
};

type EventDiscoveryFilters = {
  category?: string | null;
  freeOnly?: boolean | null;
  venue?: string | null;
};

function getFriendlyEventErrorMessage(err: unknown): string {
  const fallback = "Please check your connection and try again in a moment.";
  const message = err instanceof Error ? err.message.toLowerCase() : String(err).toLowerCase();

  if (message.includes("failed to fetch") || message.includes("network")) {
    return "We are having trouble reaching the events service. Please check your connection and try again.";
  }

  if (message.includes("api 5")) {
    return "Our events service is temporarily unavailable. Please try again shortly.";
  }

  if (message.includes("api 4")) {
    return "We could not load events for this request.";
  }

  return fallback;
}

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
        const res = await apiGet<EventOccurrenceOut[]>(withQuery(API_PATHS.events.day, { day }));
        if (!cancelled) setState({ data: res, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setState({
            data: null,
            error: getFriendlyEventErrorMessage(err),
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
  end: string,
  filters?: EventDiscoveryFilters
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
          withQuery(API_PATHS.events.range, {
            start,
            end,
            category: filters?.category,
            free: filters?.freeOnly,
            venue: filters?.venue,
          })
        );
        if (!cancelled) setState({ data: res, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setState({
            data: null,
            error: getFriendlyEventErrorMessage(err),
            loading: false,
          });
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [end, filters?.category, filters?.freeOnly, filters?.venue, start]);

  return state;
}

export function useEventsThisWeekCount(): EventCountState {
  const [state, setState] = useState<EventCountState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<{ count: number }>(API_PATHS.events.count);
        if (!cancelled) setState({ data: res.count, error: null, loading: false });
      } catch (err) {
        if (!cancelled) {
          setState({
            data: null,
            error: getFriendlyEventErrorMessage(err),
            loading: false,
          });
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}

export function useCategories(): CategoriesState {
  const [state, setState] = useState<CategoriesState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<CategoryOut[]>(API_PATHS.categories.list);
        if (!cancelled) {
          setState({ data: res, error: null, loading: false });
        }
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
  }, []);

  return state;
}

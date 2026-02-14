"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import type { EventOccurrenceOut, VenueDetailOut, VenueOut } from "@/types/events";

type State<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
};

export function useVenues(): State<VenueOut[]> {
  const [state, setState] = useState<State<VenueOut[]>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<VenueOut[]>(API_PATHS.venues.list);
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
  }, []);

  return state;
}

export function useVenueDetail(slug: string): State<VenueDetailOut> {
  const [state, setState] = useState<State<VenueDetailOut>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<VenueDetailOut>(API_PATHS.venues.detail(slug));
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
  }, [slug]);

  return state;
}

export function useVenueEvents(
  slug: string,
  start: string,
  end: string,
  enabled = true
): State<EventOccurrenceOut[]> {
  const [state, setState] = useState<State<EventOccurrenceOut[]>>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    if (!enabled) {
      return () => {
        cancelled = true;
      };
    }

    async function load() {
      try {
        setState({ data: null, error: null, loading: true });
        const res = await apiGet<EventOccurrenceOut[]>(
          withQuery(API_PATHS.venues.events(slug), { start, end })
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
  }, [slug, start, end, enabled]);

  if (!enabled) {
    return { data: [], error: null, loading: false };
  }

  return state;
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiGet } from "@/lib/api";
import { API_PATHS, withQuery } from "@/lib/api-paths";
import { toEventRouteSegment } from "@/lib/event-display";
import type { EventOccurrenceOut } from "@/types/events";

type Props = {
  days?: number;
};

export default function SurpriseMeButton({ days = 7 }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (loading) return;

    try {
      setLoading(true);
      const surprise = await apiGet<EventOccurrenceOut>(
        withQuery(API_PATHS.events.surprise, { days })
      );
      const segment = toEventRouteSegment({
        id: surprise.event.id,
        slug: surprise.event.slug,
      });
      router.push(`/events/${encodeURIComponent(segment)}`);
    } catch {
      router.push("/events");
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="rounded-full border border-charcoal/10 bg-white/80 px-7 py-3.5 text-sm font-semibold text-charcoal shadow-sm transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-70 dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
    >
      {loading ? "Finding one..." : "Surprise me"}
    </button>
  );
}

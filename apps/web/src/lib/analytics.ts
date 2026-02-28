type UmamiEventPayload = {
  [key: string]: string | number | boolean | null | undefined;
};

type UmamiWindow = Window & {
  umami?: {
    track: (eventName: string, payload?: UmamiEventPayload) => void;
  };
};

export type AnalyticsEventName =
  | "event_viewed"
  | "event_link_clicked"
  | "featured_event_impression"
  | "featured_event_clicked";

export type EventAnalyticsProps = {
  event_id: number;
  event_slug: string;
  event_title: string;
  source?: string;
  source_page: string;
  source_component: string;
  venue_id?: number;
  venue_slug?: string;
  venue_name?: string;
  position?: number;
  is_featured?: boolean;
};

export function trackEvent(eventName: AnalyticsEventName, props: EventAnalyticsProps) {
  if (typeof window === "undefined") {
    return;
  }

  const analyticsDebug = process.env.NEXT_PUBLIC_ANALYTICS_DEBUG === "true";
  if (analyticsDebug) {
    const willSend = Boolean(process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID);
    console.info("[analytics]", eventName, { ...props, _umami_send_enabled: willSend });
  }

  if (!process.env.NEXT_PUBLIC_UMAMI_WEBSITE_ID) {
    return;
  }

  const umami = (window as UmamiWindow).umami;
  if (!umami) {
    return;
  }

  umami.track(eventName, props);
}

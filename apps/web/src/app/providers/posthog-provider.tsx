"use client";

import { useEffect } from "react";
import posthog from "posthog-js";

const posthogKey = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const posthogHost = process.env.NEXT_PUBLIC_POSTHOG_HOST ?? "https://us.i.posthog.com";

let initialized = false;

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (initialized || !posthogKey) {
      return;
    }

    posthog.init(posthogKey, {
      api_host: posthogHost,
      defaults: "2026-01-30",
      cookieless_mode: "always",
      autocapture: false,
      capture_pageview: false,
      capture_pageleave: false,
      disable_session_recording: true,
      person_profiles: "never",
    });
    initialized = true;
  }, []);

  return children;
}

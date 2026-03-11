"use client";

import { useEffect } from "react";
import Link from "next/link";
import AppLayout from "./components/AppLayout";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-2xl px-6 py-24 text-center">
        <h1 className="text-3xl font-[var(--font-heading)] font-semibold text-charcoal dark:text-white">
          Something went wrong
        </h1>
        <p className="mt-4 text-muted dark:text-white/60">
          We encountered an unexpected error. Please try again.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            type="button"
            onClick={reset}
            className="inline-flex items-center justify-center rounded-full bg-gulf px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-gulf/90"
          >
            Try again
          </button>
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-6 py-3 text-sm font-semibold text-charcoal dark:text-white transition hover:bg-sand/80 dark:hover:bg-white/10"
          >
            Back to home
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}

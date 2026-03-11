import Link from "next/link";
import AppLayout from "./components/AppLayout";

export default function NotFound() {
  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-2xl px-6 py-24 text-center">
        <h1 className="text-6xl font-[var(--font-heading)] font-bold text-charcoal dark:text-white">
          404
        </h1>
        <p className="mt-4 text-xl font-medium text-muted dark:text-white/60">
          Page not found
        </p>
        <p className="mt-2 text-sm text-muted dark:text-white/50">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-full bg-charcoal px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-charcoal/90 dark:bg-gradient-to-r dark:from-purple-600 dark:to-pink-600 dark:hover:opacity-90"
          >
            Back to home
          </Link>
          <Link
            href="/events"
            className="inline-flex items-center justify-center rounded-full border border-charcoal/15 dark:border-white/20 bg-white/80 dark:bg-white/5 px-6 py-3 text-sm font-semibold text-charcoal dark:text-white transition hover:bg-sand/80 dark:hover:bg-white/10"
          >
            Browse events
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}

"use client";

import Link from "next/link";
import ThemeSwitcher from "./ThemeSwitcher";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-sand/80 dark:bg-[#0a0a0b]/80 border-b border-white/50 dark:border-white/10">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="relative">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-coral to-gulf text-white shadow-lg shadow-coral/30 font-bold text-sm dark:from-purple-500 dark:to-pink-500 dark:shadow-purple-500/30">
              SRQ
            </div>
            <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-emerald-400 border-2 border-sand dark:border-[#0a0a0b] animate-pulse" />
          </div>
          <div>
            <span className="font-[var(--font-heading)] text-xl font-semibold">
              Happenings
            </span>
            <p className="text-xs text-muted dark:text-white/50">Sarasota Events</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-medium text-muted dark:text-white/60 md:flex">
          <Link href="/events" className="transition hover:text-charcoal dark:hover:text-white">
            Events
          </Link>
          <Link href="/articles" className="transition hover:text-charcoal dark:hover:text-white">
            Articles
          </Link>
          <Link href="/venues" className="transition hover:text-charcoal dark:hover:text-white">
            Venues
          </Link>
          <Link href="/submit" className="transition hover:text-charcoal dark:hover:text-white">
            Submit
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden sm:block rounded-full border border-charcoal/10 dark:border-white/20 bg-white/70 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white shadow-sm hover:bg-white dark:hover:bg-white/10 transition"
          >
            Sign in
          </Link>
          <ThemeSwitcher />
        </div>
      </div>
    </header>
  );
}

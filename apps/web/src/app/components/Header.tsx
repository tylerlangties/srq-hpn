"use client";

import Link from "next/link";
import { useState } from "react";
import ThemeSwitcher from "./ThemeSwitcher";

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

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
          <button
            type="button"
            onClick={() => setMobileMenuOpen((value) => !value)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-charcoal/10 bg-white/70 text-charcoal shadow-sm transition hover:bg-white md:hidden dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-site-nav"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5"
                aria-hidden="true"
              >
                <path d="M18 6 6 18" />
                <path d="m6 6 12 12" />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-5 w-5"
                aria-hidden="true"
              >
                <path d="M3 6h18" />
                <path d="M3 12h18" />
                <path d="M3 18h18" />
              </svg>
            )}
          </button>
          <Link
            href="/login"
            className="hidden md:block rounded-full border border-charcoal/10 dark:border-white/20 bg-white/70 dark:bg-white/5 px-4 py-2 text-sm font-medium text-charcoal dark:text-white shadow-sm hover:bg-white dark:hover:bg-white/10 transition"
          >
            Sign in
          </Link>
          <ThemeSwitcher />
        </div>
      </div>

      {mobileMenuOpen ? (
        <div id="mobile-site-nav" className="border-t border-white/50 px-6 py-3 md:hidden dark:border-white/10">
          <nav className="mx-auto flex w-full max-w-7xl flex-col gap-2 text-sm font-semibold text-charcoal dark:text-white/90">
            <Link
              href="/events"
              onClick={closeMobileMenu}
              className="rounded-xl border border-charcoal/10 bg-white/70 px-4 py-3 transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/10"
            >
              Events
            </Link>
            <Link
              href="/articles"
              onClick={closeMobileMenu}
              className="rounded-xl border border-charcoal/10 bg-white/70 px-4 py-3 transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/10"
            >
              Articles
            </Link>
            <Link
              href="/venues"
              onClick={closeMobileMenu}
              className="rounded-xl border border-charcoal/10 bg-white/70 px-4 py-3 transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/10"
            >
              Venues
            </Link>
            <Link
              href="/submit"
              onClick={closeMobileMenu}
              className="rounded-xl border border-charcoal/10 bg-white/70 px-4 py-3 transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:hover:bg-white/10"
            >
              Submit an event
            </Link>
            <Link
              href="/login"
              onClick={closeMobileMenu}
              className="rounded-xl border border-charcoal/10 bg-charcoal px-4 py-3 text-white transition hover:bg-charcoal/90 dark:border-white/20 dark:bg-white/10 dark:text-white dark:hover:bg-white/15"
            >
              Sign in
            </Link>
          </nav>
        </div>
      ) : null}
    </header>
  );
}

"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "../providers/theme-provider";

type Props = {
  className?: string;
};

export default function ThemeSwitcher({ className }: Props) {
  const { theme, toggleTheme } = useTheme();
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false
  );

  if (!mounted) {
    // Return a placeholder with the same dimensions to prevent layout shift
    return (
      <div
        className={`inline-flex h-10 w-10 items-center justify-center rounded-full border border-charcoal/10 bg-white/70 text-charcoal shadow-sm transition hover:bg-white dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10 ${className ?? ""}`}
      >
        <div className="h-5 w-5" />
      </div>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      className={`inline-flex h-10 w-10 items-center justify-center rounded-full border border-charcoal/10 bg-white/70 text-charcoal shadow-sm transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-coral/50 focus-visible:ring-offset-2 focus-visible:ring-offset-sand dark:border-white/20 dark:bg-white/5 dark:text-white dark:hover:bg-white/10 dark:focus-visible:ring-purple-400/40 dark:focus-visible:ring-offset-[#0a0a0b] ${className ?? ""}`}
      aria-label="Toggle theme"
    >
      {theme === "light" ? (
        // Moon icon for dark mode
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-5 h-5 text-gray-700 dark:text-gray-300"
        >
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
        </svg>
      ) : (
        // Sun icon for light mode
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="w-5 h-5 text-yellow-500"
        >
          <circle cx="12" cy="12" r="5" />
          <line x1="12" y1="1" x2="12" y2="3" />
          <line x1="12" y1="21" x2="12" y2="23" />
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
          <line x1="1" y1="12" x2="3" y2="12" />
          <line x1="21" y1="12" x2="23" y2="12" />
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
        </svg>
      )}
    </button>
  );
}
